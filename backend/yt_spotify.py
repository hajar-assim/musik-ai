from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import logging
from .vault_client import YOUTUBE_API_KEY

# Configure logging
logger = logging.getLogger(__name__)

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

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
    Search for a track on Spotify by name.

    Args:
        sp: Spotipy client instance
        track_name: Name of the track to search for

    Returns:
        Spotify track URI if found, None otherwise

    Raises:
        SpotifyException: If Spotify API request fails
    """
    if not track_name or not track_name.strip():
        logger.warning("Empty track name provided for search")
        return None

    try:
        results = sp.search(q=track_name, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if items:
            logger.debug(f"Found match for '{track_name}': {items[0]['name']} by {items[0]['artists'][0]['name']}")
            return items[0]["uri"]
        else:
            logger.debug(f"No match found for '{track_name}'")
            return None
    except Exception as e:
        logger.error(f"Error searching for track '{track_name}': {str(e)}")
        raise
