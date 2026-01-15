import logging
from .youtube_service import parse_artist_track

logger = logging.getLogger(__name__)


def search_track_on_spotify(sp, track_name: str) -> str | None:
    """Search for track on Spotify with intelligent parsing"""
    if not track_name or not track_name.strip():
        logger.warning("Empty track name")
        return None

    try:
        artist, track = parse_artist_track(track_name)

        # Attempt 1: Artist + track query
        if artist:
            query = f"artist:{artist} track:{track}"
            logger.debug(f"Searching: {query}")
            results = sp.search(q=query, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if items:
                found = items[0]
                logger.debug(f"Found: {found['name']} by {found['artists'][0]['name']}")
                return found["uri"]

        # Attempt 2: Track only
        if artist:
            logger.debug(f"Retry without artist filter: {track}")
            results = sp.search(q=track, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if items:
                found = items[0]
                logger.debug(f"Found on retry: {found['name']} by {found['artists'][0]['name']}")
                return found["uri"]

        # Attempt 3: Original title
        if artist or track != track_name:
            logger.debug(f"Trying original title: {track_name}")
            results = sp.search(q=track_name, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if items:
                found = items[0]
                logger.debug(f"Found with original: {found['name']} by {found['artists'][0]['name']}")
                return found["uri"]

        logger.debug(f"No match found for '{track_name}'")
        return None

    except Exception as e:
        logger.error(f"Error searching '{track_name}': {e}")
        raise
