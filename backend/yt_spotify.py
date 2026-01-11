from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import logging
import re
from .vault_client import YOUTUBE_API_KEY

# Configure logging
logger = logging.getLogger(__name__)

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def clean_youtube_title(title: str) -> str:
    """
    Clean YouTube video title by removing common extras like [Official Video], (Audio), etc.

    Args:
        title: Raw YouTube video title

    Returns:
        Cleaned title
    """
    # Remove common video type indicators
    patterns_to_remove = [
        r'\[Official Video\]',
        r'\[Official Music Video\]',
        r'\[Official Audio\]',
        r'\[Official Lyric Video\]',
        r'\(Official Video\)',
        r'\(Official Music Video\)',
        r'\(Official Audio\)',
        r'\(Official Lyric Video\)',
        r'\[Lyrics?\]',
        r'\(Lyrics?\)',
        r'\[HD\]',
        r'\[HQ\]',
        r'\(HD\)',
        r'\(HQ\)',
        r'\[4K\]',
        r'\(4K\)',
        r'\[Music Video\]',
        r'\(Music Video\)',
        r'\[Audio\]',
        r'\(Audio\)',
        r'\[OFFICIAL\]',
        r'\(OFFICIAL\)',
    ]

    cleaned = title
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def parse_artist_and_track(title: str) -> tuple[str, str]:
    """
    Parse YouTube video title to extract artist and track name.

    Handles common formats like:
    - "Artist - Track"
    - "Track by Artist"
    - "Artist: Track"

    Args:
        title: YouTube video title

    Returns:
        Tuple of (artist, track) or (None, original_title) if parsing fails
    """
    # Clean the title first
    cleaned = clean_youtube_title(title)

    # Try pattern: "Artist - Track" or "Artist – Track" (em dash)
    match = re.match(r'^(.+?)\s*[-–—]\s*(.+)$', cleaned)
    if match:
        artist = match.group(1).strip()
        track = match.group(2).strip()
        # Make sure neither is too short
        if len(artist) > 1 and len(track) > 1:
            return artist, track

    # Try pattern: "Track by Artist"
    match = re.match(r'^(.+?)\s+by\s+(.+)$', cleaned, flags=re.IGNORECASE)
    if match:
        track = match.group(1).strip()
        artist = match.group(2).strip()
        if len(artist) > 1 and len(track) > 1:
            return artist, track

    # Try pattern: "Artist: Track"
    match = re.match(r'^(.+?):\s*(.+)$', cleaned)
    if match:
        artist = match.group(1).strip()
        track = match.group(2).strip()
        if len(artist) > 1 and len(track) > 1:
            return artist, track

    # If no pattern matches, return None for artist and cleaned title for track
    return None, cleaned


def get_youtube_playlist_videos(playlist_id: str):
    """
    Fetch all video titles from a YouTube playlist.

    Args:
        playlist_id: YouTube playlist ID

    Returns:
        List of video titles

    Raises:
        ValueError: If playlist_id is invalid
        HttpError: If YouTube API request fails
    """
    if not playlist_id or not playlist_id.strip():
        raise ValueError("playlist_id cannot be empty")

    videos = []
    try:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50
        )

        while request:
            try:
                response = request.execute()
                for item in response.get("items", []):
                    title = item.get("snippet", {}).get("title")
                    if title:
                        videos.append(title)
                request = youtube.playlistItems().list_next(request, response)
            except HttpError as e:
                if e.resp.status == 404:
                    raise ValueError(f"YouTube playlist not found: {playlist_id}")
                elif e.resp.status == 403:
                    raise ValueError(f"Access denied to YouTube playlist: {playlist_id}. The playlist may be private.")
                else:
                    logger.error(f"YouTube API error: {str(e)}")
                    raise

    except HttpError as e:
        logger.error(f"Failed to fetch YouTube playlist {playlist_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching YouTube playlist {playlist_id}: {str(e)}")
        raise

    return videos

def search_track_on_spotify(sp, track_name: str):
    """
    Search for a track on Spotify by name with improved matching.

    Uses title parsing to extract artist and track name for better search results.

    Args:
        sp: Spotipy client instance
        track_name: Name of the track to search for (can include artist)

    Returns:
        Spotify track URI if found, None otherwise

    Raises:
        SpotifyException: If Spotify API request fails
    """
    if not track_name or not track_name.strip():
        logger.warning("Empty track name provided for search")
        return None

    try:
        # Parse artist and track from the title
        artist, track = parse_artist_and_track(track_name)

        # Build search query
        if artist:
            # If we have artist info, use it for more accurate search
            search_query = f"artist:{artist} track:{track}"
            logger.debug(f"Searching with artist filter: {search_query}")
        else:
            # Fall back to simple search
            search_query = track
            logger.debug(f"Searching without artist filter: {search_query}")

        # First attempt: with parsed query
        results = sp.search(q=search_query, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])

        if items:
            found_track = items[0]
            logger.debug(
                f"Found match for '{track_name}': "
                f"{found_track['name']} by {found_track['artists'][0]['name']}"
            )
            return found_track["uri"]

        # Second attempt: if no results and we had artist, try without artist filter
        if artist:
            logger.debug(f"No results with artist filter, trying broad search: {track}")
            results = sp.search(q=track, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if items:
                found_track = items[0]
                logger.debug(
                    f"Found match on retry for '{track_name}': "
                    f"{found_track['name']} by {found_track['artists'][0]['name']}"
                )
                return found_track["uri"]

        # Third attempt: if still no results, try the original title
        if artist or track != track_name:
            logger.debug(f"No results with parsed query, trying original title: {track_name}")
            results = sp.search(q=track_name, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if items:
                found_track = items[0]
                logger.debug(
                    f"Found match with original title '{track_name}': "
                    f"{found_track['name']} by {found_track['artists'][0]['name']}"
                )
                return found_track["uri"]

        logger.debug(f"No match found for '{track_name}' after all attempts")
        return None

    except Exception as e:
        logger.error(f"Error searching for track '{track_name}': {str(e)}")
        raise
