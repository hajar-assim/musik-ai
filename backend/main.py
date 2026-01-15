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


@app.get("/match-tracks")
def match_tracks(spotify_user_id: str, yt_playlist_id: str):
    """
    Match YouTube playlist tracks to Spotify without creating a playlist
    Returns matched track URIs for recommendations
    """
    if not spotify_user_id or not spotify_user_id.strip():
        raise HTTPException(status_code=400, detail="spotify_user_id is required")

    if not yt_playlist_id or not yt_playlist_id.strip():
        raise HTTPException(status_code=400, detail="yt_playlist_id is required")

    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        logger.info(f"Matching tracks for user: {spotify_user_id}, YouTube playlist: {yt_playlist_id}")

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
                detail=f"Failed to fetch YouTube playlist. Error: {str(e)}"
            )

        if not video_titles:
            raise HTTPException(status_code=400, detail="YouTube playlist is empty")

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

        logger.info(f"Matched {len(track_uris)}/{len(video_titles)} tracks")

        if not track_uris:
            raise HTTPException(
                status_code=404,
                detail="No matching tracks found on Spotify"
            )

        return {
            'status': 'success',
            'matched_tracks': track_uris,
            'total_videos': len(video_titles),
            'failed_matches': failed_matches[:10]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching tracks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to match tracks: {str(e)}")


@app.get("/recommendations")
def get_recommendations(spotify_user_id: str, track_uris: str):
    """
    Get AI-powered track recommendations based on matched tracks
    """
    if not spotify_user_id or not spotify_user_id.strip():
        raise HTTPException(status_code=400, detail="spotify_user_id is required")

    if not track_uris or not track_uris.strip():
        raise HTTPException(status_code=400, detail="track_uris is required")

    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        # Parse comma-separated track URIs
        uris = [uri.strip() for uri in track_uris.split(',') if uri.strip()]

        # Extract track IDs from URIs (spotify:track:ID -> ID)
        track_ids = []
        for uri in uris[:5]:  # Use up to 5 seed tracks
            if uri.startswith('spotify:track:'):
                track_id = uri.split(':')[-1]
            else:
                # Already a track ID
                track_id = uri

            # Validate track ID format (should be 22 characters, alphanumeric)
            if track_id and len(track_id) == 22:
                track_ids.append(track_id)
            else:
                logger.warning(f"Skipping invalid track ID: {track_id}")

        logger.info(f"Getting recommendations for user {spotify_user_id} based on {len(track_ids)} seed tracks: {track_ids}")

        if not track_ids:
            raise HTTPException(status_code=400, detail="No valid track IDs found. Track IDs must be 22 characters.")

        if len(track_ids) < 1:
            raise HTTPException(status_code=400, detail="At least 1 seed track is required for recommendations")

        # Get recommendations from Spotify
        # Try without market first, then fall back to user's market if needed
        try:
            logger.info("Attempting to get recommendations without market parameter")
            recommendations = sp.recommendations(seed_tracks=track_ids, limit=15)
        except SpotifyException as market_error:
            # Try with user's market from their profile
            logger.warning(f"Recommendations failed without market: {market_error}. Trying with user market...")
            try:
                user_profile = sp.current_user()
                user_market = user_profile.get('country', 'US')
                logger.info(f"Using user market: {user_market}")
                recommendations = sp.recommendations(seed_tracks=track_ids, limit=15, market=user_market)
            except Exception as retry_error:
                logger.error(f"Recommendations failed with market parameter: {retry_error}")
                raise

        recommended_tracks = []
        for track in recommendations['tracks']:
            recommended_tracks.append({
                'uri': track['uri'],
                'name': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'preview_url': track.get('preview_url'),
            })

        logger.info(f"Found {len(recommended_tracks)} recommendations")

        return {
            'status': 'success',
            'recommendations': recommended_tracks
        }

    except SpotifyException as e:
        logger.error(f"Spotify API error while getting recommendations: {str(e)}")
        logger.error(f"Spotify error details - HTTP status: {e.http_status}, Code: {e.code}, Message: {e.msg}")
        raise HTTPException(status_code=500, detail=f"Spotify API error: {e.msg or str(e)}")
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/convert")
def convert(spotify_user_id: str, playlist_name: str, track_uris: str, yt_playlist_id: str = None):
    """
    Create Spotify playlist from track URIs
    Can optionally fetch from YouTube playlist if yt_playlist_id is provided
    """
    # Validate inputs
    if not spotify_user_id or not spotify_user_id.strip():
        raise HTTPException(status_code=400, detail="spotify_user_id is required")

    if not playlist_name or not playlist_name.strip():
        raise HTTPException(status_code=400, detail="playlist_name is required")

    # Check if user is authenticated
    if spotify_user_id not in authenticated_users:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in with Spotify first."
        )

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        # Parse track URIs from comma-separated string
        uris = [uri.strip() for uri in track_uris.split(',') if uri.strip()]

        if not uris:
            raise HTTPException(status_code=400, detail="No valid track URIs provided")

        logger.info(f"Creating playlist '{playlist_name}' for user {spotify_user_id} with {len(uris)} tracks")

        # Create Spotify playlist
        try:
            playlist = sp.user_playlist_create(user=spotify_user_id, name=playlist_name)
            sp.playlist_add_items(playlist_id=playlist["id"], items=uris)
            logger.info(f"Successfully created Spotify playlist '{playlist_name}' with {len(uris)} tracks")
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
            "total_tracks": len(uris),
            "matched_tracks": len(uris),
            "total_videos": len(uris),
            "failed_matches": 0,
            "failed_match_titles": []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during playlist creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create playlist: {str(e)}")
