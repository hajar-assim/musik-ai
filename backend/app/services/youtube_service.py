from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import re
from app.config import settings

logger = logging.getLogger(__name__)

youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)


def clean_title(title: str) -> str:
    """Remove common video indicators from YouTube title"""
    patterns = [
        r'\[Official (Video|Music Video|Audio|Lyric Video)\]',
        r'\(Official (Video|Music Video|Audio|Lyric Video)\)',
        r'\[Lyrics?\]', r'\(Lyrics?\)',
        r'\[(HD|HQ|4K|OFFICIAL)\]', r'\((HD|HQ|4K|OFFICIAL)\)',
        r'\[(Music Video|Audio)\]', r'\((Music Video|Audio)\)',
    ]
    cleaned = title
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', cleaned).strip()


def parse_artist_track(title: str) -> tuple[str | None, str]:
    """Parse artist and track from title. Returns (artist, track) or (None, title)"""
    cleaned = clean_title(title)

    patterns = [
        (r'^(.+?)\s*[-–—]\s*(.+)$', lambda m: (m.group(1).strip(), m.group(2).strip())),
        (r'^(.+?)\s+by\s+(.+)$', lambda m: (m.group(2).strip(), m.group(1).strip())),
        (r'^(.+?):\s*(.+)$', lambda m: (m.group(1).strip(), m.group(2).strip())),
    ]

    for pattern, extractor in patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            artist, track = extractor(match)
            if len(artist) > 1 and len(track) > 1:
                return artist, track

    return None, cleaned


def get_youtube_playlist_videos(playlist_id: str) -> list[str]:
    """Fetch all video titles from YouTube playlist"""
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
                    raise ValueError(f"Access denied. Playlist may be private: {playlist_id}")
                else:
                    logger.error(f"YouTube API error: {e}")
                    raise

    except HttpError as e:
        logger.error(f"Failed to fetch playlist {playlist_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

    return videos
