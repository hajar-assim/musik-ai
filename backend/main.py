from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from vault_client import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="musik-ai API",
    description="YouTube to Spotify playlist conversion API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redirect URI — must match Spotify dashboard
REDIRECT_URI = "http://127.0.0.1:8888/callback"
FRONTEND_URL = "http://localhost:5173"

# Scope required to modify playlists
SCOPE = "playlist-modify-private playlist-modify-public"

# Store OAuth sessions by session_id
oauth_sessions = {}
# Store authenticated users by spotify_user_id
authenticated_users = {}


@app.get("/login")
def login():
    """
    Step 1: Initiate Spotify OAuth flow
    """
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        logger.info(f"Initiating login with session_id: {session_id}")

        sp_oauth = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=f".cache-{session_id}"
        )

        oauth_sessions[session_id] = sp_oauth

        # Pass session_id as state so we can retrieve it in callback
        auth_url = sp_oauth.get_authorize_url(state=session_id)
        logger.info(f"Generated auth URL for session: {session_id}")

        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")


@app.get("/callback")
def callback(code: str = None, state: str = None, error: str = None):
    """
    Step 2: Spotify redirects here after user authorizes
    """
    if error:
        logger.error(f"Spotify OAuth error: {error}")
        return RedirectResponse(f"{FRONTEND_URL}?error={error}")

    if not code or not state:
        return RedirectResponse(f"{FRONTEND_URL}?error=missing_parameters")

    session_id = state

    if session_id not in oauth_sessions:
        return RedirectResponse(f"{FRONTEND_URL}?error=invalid_session")

    try:
        logger.info(f"Processing OAuth callback for session: {session_id}")
        sp_oauth = oauth_sessions[session_id]

        # Exchange code for access token
        token_info = sp_oauth.get_access_token(code)

        # Get Spotify user info
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        user_info = sp.current_user()
        spotify_user_id = user_info["id"]

        # Store the OAuth session by Spotify user ID
        authenticated_users[spotify_user_id] = sp_oauth

        # Clean up the temporary session
        del oauth_sessions[session_id]

        logger.info(f"Successfully authorized Spotify user: {spotify_user_id}")

        # Redirect back to frontend with success
        return RedirectResponse(f"{FRONTEND_URL}?spotify_user_id={spotify_user_id}&status=success")

    except Exception as e:
        logger.error(f"Error during OAuth callback: {str(e)}")
        return RedirectResponse(f"{FRONTEND_URL}?error=auth_failed")


@app.get("/me")
def get_current_user(spotify_user_id: str):
    """
    Get current authenticated user info
    """
    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        user_info = sp.current_user()

        return {
            "id": user_info["id"],
            "display_name": user_info.get("display_name", user_info["id"]),
            "email": user_info.get("email"),
            "images": user_info.get("images", [])
        }
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user info")


@app.get("/convert")
def convert(spotify_user_id: str, yt_playlist_id: str, playlist_name: str):
    """
    Convert YouTube playlist to Spotify
    """
    # Validate inputs
    if not spotify_user_id or not spotify_user_id.strip():
        raise HTTPException(status_code=400, detail="spotify_user_id is required")

    if not yt_playlist_id or not yt_playlist_id.strip():
        raise HTTPException(status_code=400, detail="yt_playlist_id is required")

    if not playlist_name or not playlist_name.strip():
        raise HTTPException(status_code=400, detail="playlist_name is required")

    # Check if user is authenticated
    if spotify_user_id not in authenticated_users:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in with Spotify first."
        )

    try:
        logger.info(f"Starting conversion for Spotify user: {spotify_user_id}, YouTube playlist: {yt_playlist_id}")

        sp_oauth = authenticated_users[spotify_user_id]
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
            playlist = sp.user_playlist_create(user=spotify_user_id, name=playlist_name)
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
            "failed_match_titles": failed_matches[:10] if failed_matches else []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
