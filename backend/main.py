from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from vault_client import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="musik-ai API",
    description="YouTube to Spotify playlist conversion API",
    version="1.0.0"
)

# Configure CORS
# In production, replace ["*"] with specific frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# your redirect URI — must match Spotify dashboard
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# scope required to modify playlists
SCOPE = "playlist-modify-private playlist-modify-public"

# temporary in-memory store for OAuth objects per user (for demo purposes)
oauth_objects = {}

@app.get("/login")
def login(user_id: str):
    """
    Step 1: generate Spotify auth URL for a user
    """
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required and cannot be empty")

    try:
        logger.info(f"Initiating login for user_id: {user_id}")
        sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                client_secret=SPOTIFY_CLIENT_SECRET,
                                redirect_uri=REDIRECT_URI,
                                scope=SCOPE,
                                cache_path=f".cache-{user_id}")  # token cache per user
        oauth_objects[user_id] = sp_oauth
        auth_url = sp_oauth.get_authorize_url()
        logger.info(f"Successfully generated auth URL for user_id: {user_id}")
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error during login for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")


@app.get("/callback")
def callback(request: Request, code: str = None, state: str = None, error: str = None):
    """
    Step 2: Spotify redirects here after user login
    """
    if error:
        logger.error(f"Spotify OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"Spotify authorization failed: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing")

    if not state:
        raise HTTPException(status_code=400, detail="State parameter (user_id) is missing")

    user_id = state  # pass user_id via state if needed

    if user_id not in oauth_objects:
        raise HTTPException(status_code=400, detail=f"No OAuth session found for user_id: {user_id}")

    try:
        logger.info(f"Processing OAuth callback for user_id: {user_id}")
        sp_oauth = oauth_objects[user_id]
        token_info = sp_oauth.get_access_token(code)
        # token_info contains access_token, refresh_token, expires_in
        logger.info(f"Successfully authorized user_id: {user_id}")
        return {"status": "authorized", "user_id": user_id}
    except Exception as e:
        logger.error(f"Error during OAuth callback for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete authorization: {str(e)}")


@app.get("/convert")
def convert(user_id: str, yt_playlist_id: str, playlist_name: str):
    """
    Step 3: convert YouTube playlist to Spotify using the authorized token
    """
    # Validate inputs
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required and cannot be empty")

    if not yt_playlist_id or not yt_playlist_id.strip():
        raise HTTPException(status_code=400, detail="yt_playlist_id is required and cannot be empty")

    if not playlist_name or not playlist_name.strip():
        raise HTTPException(status_code=400, detail="playlist_name is required and cannot be empty")

    # Check if user is authorized
    if user_id not in oauth_objects:
        raise HTTPException(
            status_code=401,
            detail=f"User {user_id} is not authorized. Please complete the login flow first."
        )

    try:
        logger.info(f"Starting conversion for user_id: {user_id}, YouTube playlist: {yt_playlist_id}")
        sp_oauth = oauth_objects[user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        from yt_spotify import get_youtube_playlist_videos, search_track_on_spotify

        # Fetch YouTube playlist videos
        try:
            video_titles = get_youtube_playlist_videos(yt_playlist_id)
            logger.info(f"Fetched {len(video_titles)} videos from YouTube playlist")
        except Exception as e:
            logger.error(f"Failed to fetch YouTube playlist {yt_playlist_id}: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch YouTube playlist. Please check the playlist ID and ensure it's public. Error: {str(e)}"
            )

        if not video_titles:
            raise HTTPException(status_code=400, detail="YouTube playlist is empty or could not be fetched")

        # Search for tracks on Spotify
        track_uris = []
        failed_matches = []
        for title in video_titles:
            try:
                uri = search_track_on_spotify(sp, title)
                if uri:
                    track_uris.append(uri)
                else:
                    failed_matches.append(title)
            except SpotifyException as e:
                logger.error(f"Spotify API error while searching for '{title}': {str(e)}")
                failed_matches.append(title)

        logger.info(f"Matched {len(track_uris)}/{len(video_titles)} tracks on Spotify")

        if not track_uris:
            raise HTTPException(
                status_code=404,
                detail="No matching tracks found on Spotify for this YouTube playlist"
            )

        # Create Spotify playlist
        try:
            current_user_id = sp.current_user()["id"]
            playlist = sp.user_playlist_create(user=current_user_id, name=playlist_name)
            sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris)
            logger.info(f"Successfully created Spotify playlist '{playlist_name}' with {len(track_uris)} tracks")
        except SpotifyException as e:
            logger.error(f"Failed to create Spotify playlist: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Spotify playlist: {str(e)}"
            )

        return {
            "status": "success",
            "playlist_name": playlist_name,
            "playlist_id": playlist["id"],
            "playlist_url": playlist["external_urls"]["spotify"],
            "total_videos": len(video_titles),
            "matched_tracks": len(track_uris),
            "failed_matches": len(failed_matches),
            "failed_match_titles": failed_matches[:10] if failed_matches else []  # Show first 10 failed matches
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
