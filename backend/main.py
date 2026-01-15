from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import logging
import uuid

from app.config import settings
from app.services import (
    get_youtube_playlist_videos,
    search_track_on_spotify,
    send_signup_notification,
    get_llm_recommendations
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="musik-ai API",
    description="YouTube to Spotify playlist conversion with AI recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth_sessions = {}
authenticated_users = {}


@app.get("/")
def root():
    """API root endpoint"""
    return {
        "name": "musik-ai API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/",
            "login": "/login",
            "callback": "/callback"
        }
    }


@app.post("/request-access")
def request_access(email: str, name: str = None):
    """Request access to the app (Spotify dev mode limitation)"""
    if not email or not email.strip() or '@' not in email or '.' not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    try:
        email_sent = send_signup_notification(email, name)
        return {
            "status": "success",
            "message": "Access request submitted. Admin will add you within 24 hours."
        }
    except Exception as e:
        logger.error(f"Error processing access request: {e}")
        raise HTTPException(status_code=500, detail="Failed to process request")


@app.get("/login")
def login():
    """Initiate Spotify OAuth flow"""
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Login initiated: {session_id}")

        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.REDIRECT_URI,
            scope=settings.SPOTIFY_SCOPE,
            cache_path=f".cache-{session_id}"
        )

        oauth_sessions[session_id] = sp_oauth
        auth_url = sp_oauth.get_authorize_url(state=session_id)

        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {e}")


@app.get("/callback")
def callback(code: str = None, state: str = None, error: str = None):
    """Spotify OAuth callback"""
    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error={error}")

    if not code or not state or state not in oauth_sessions:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=invalid_session")

    try:
        sp_oauth = oauth_sessions[state]
        token_info = sp_oauth.get_access_token(code)

        sp = spotipy.Spotify(auth_manager=sp_oauth)
        user_info = sp.current_user()
        spotify_user_id = user_info["id"]

        authenticated_users[spotify_user_id] = sp_oauth
        del oauth_sessions[state]

        logger.info(f"User authorized: {spotify_user_id}")
        return RedirectResponse(f"{settings.FRONTEND_URL}?spotify_user_id={spotify_user_id}&status=success")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=auth_failed")


@app.get("/me")
def get_current_user(spotify_user_id: str):
    """Get current authenticated user info"""
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
        logger.error(f"Error fetching user info: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user info")


@app.get("/playlists")
def get_user_playlists(spotify_user_id: str):
    """Get user's Spotify playlists"""
    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        playlists = []
        results = sp.current_user_playlists(limit=50)

        while results:
            for item in results['items']:
                playlists.append({
                    'id': item['id'],
                    'name': item['name'],
                    'tracks_count': item['tracks']['total'],
                    'image': item['images'][0]['url'] if item['images'] else None,
                    'external_url': item['external_urls']['spotify']
                })

            if results['next']:
                results = sp.next(results)
            else:
                results = None

        logger.info(f"Fetched {len(playlists)} playlists")
        return {
            'status': 'success',
            'playlists': playlists
        }
    except Exception as e:
        logger.error(f"Error fetching playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch playlists")


@app.get("/match-tracks")
def match_tracks(spotify_user_id: str, yt_playlist_id: str):
    """Match YouTube playlist tracks to Spotify"""
    if not spotify_user_id or not yt_playlist_id:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        video_titles = get_youtube_playlist_videos(yt_playlist_id)
        logger.info(f"Fetched {len(video_titles)} videos")

        if not video_titles:
            raise HTTPException(status_code=400, detail="YouTube playlist is empty")

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
                logger.error(f"Spotify error for '{title}': {e}")
                failed_matches.append(title)

        logger.info(f"Matched {len(track_uris)}/{len(video_titles)} tracks")

        if not track_uris:
            raise HTTPException(status_code=404, detail="No matching tracks found")

        return {
            'status': 'success',
            'matched_tracks': track_uris,
            'total_videos': len(video_titles),
            'failed_matches': failed_matches[:10]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching tracks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommendations")
def get_recommendations(spotify_user_id: str, track_uris: str):
    """Get AI-powered track recommendations"""
    if not spotify_user_id or not track_uris:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        uris = [uri.strip() for uri in track_uris.split(',') if uri.strip()]

        track_info_list = []
        for uri in uris[:10]:
            try:
                track_id = uri.split(':')[-1] if uri.startswith('spotify:track:') else uri
                track_info = sp.track(track_id)

                if track_info:
                    track_info_list.append({
                        'name': track_info['name'],
                        'artist': track_info['artists'][0]['name']
                    })
            except Exception as e:
                logger.warning(f"Could not get info for {uri}: {e}")

        if not track_info_list:
            raise HTTPException(status_code=400, detail="Could not get track information")

        llm_recommendations = get_llm_recommendations(track_info_list)
        logger.info(f"LLM suggested {len(llm_recommendations)} tracks")

        recommended_tracks = []
        for rec in llm_recommendations:
            try:
                query = f"{rec['name']} {rec['artist']}"
                results = sp.search(q=query, type='track', limit=1)

                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    recommended_tracks.append({
                        'uri': track['uri'],
                        'name': track['name'],
                        'artist': ', '.join([a['name'] for a in track['artists']]),
                        'album': track['album']['name'],
                        'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    })
            except Exception as e:
                logger.warning(f"Error searching for {rec['name']}: {e}")

        if not recommended_tracks:
            raise HTTPException(status_code=404, detail="No recommendations found on Spotify")

        logger.info(f"Found {len(recommended_tracks)} recommendations")

        return {
            'status': 'success',
            'recommendations': recommended_tracks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/enhance-playlist")
def get_playlist_recommendations(spotify_user_id: str, playlist_id: str):
    """Get AI recommendations for an existing playlist"""
    if not spotify_user_id or not playlist_id:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        # Fetch playlist tracks
        results = sp.playlist_tracks(playlist_id, limit=50)
        tracks = results['items']

        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])

        # Extract track info for LLM
        track_info_list = []
        for item in tracks[:20]:
            if item['track'] and item['track']['name']:
                track_info_list.append({
                    'name': item['track']['name'],
                    'artist': item['track']['artists'][0]['name']
                })

        if not track_info_list:
            raise HTTPException(status_code=400, detail="Playlist is empty")

        # Get LLM recommendations
        llm_recommendations = get_llm_recommendations(track_info_list)
        logger.info(f"LLM suggested {len(llm_recommendations)} tracks")

        # Search for recommendations on Spotify
        recommended_tracks = []
        for rec in llm_recommendations:
            try:
                query = f"{rec['name']} {rec['artist']}"
                results = sp.search(q=query, type='track', limit=1)

                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    recommended_tracks.append({
                        'uri': track['uri'],
                        'name': track['name'],
                        'artist': ', '.join([a['name'] for a in track['artists']]),
                        'album': track['album']['name'],
                        'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    })
            except Exception as e:
                logger.warning(f"Error searching for {rec['name']}: {e}")

        if not recommended_tracks:
            raise HTTPException(status_code=404, detail="No recommendations found on Spotify")

        logger.info(f"Found {len(recommended_tracks)} recommendations")

        return {
            'status': 'success',
            'recommendations': recommended_tracks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing playlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-to-playlist")
def add_tracks_to_playlist(spotify_user_id: str, playlist_id: str, track_uris: str):
    """Add tracks to an existing playlist"""
    if not spotify_user_id or not playlist_id or not track_uris:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        uris = [uri.strip() for uri in track_uris.split(',') if uri.strip()]

        if not uris:
            raise HTTPException(status_code=400, detail="No valid track URIs")

        sp.playlist_add_items(playlist_id=playlist_id, items=uris)

        logger.info(f"Added {len(uris)} tracks to playlist {playlist_id}")

        return {
            'status': 'success',
            'tracks_added': len(uris)
        }

    except HTTPException:
        raise
    except SpotifyException as e:
        logger.error(f"Failed to add tracks: {e}")
        raise HTTPException(status_code=500, detail=f"Spotify error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/convert")
def convert(spotify_user_id: str, playlist_name: str, track_uris: str, yt_playlist_id: str = None):
    """Create Spotify playlist from track URIs"""
    if not spotify_user_id or not playlist_name or not track_uris:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    if spotify_user_id not in authenticated_users:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sp_oauth = authenticated_users[spotify_user_id]
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        uris = [uri.strip() for uri in track_uris.split(',') if uri.strip()]

        if not uris:
            raise HTTPException(status_code=400, detail="No valid track URIs")

        logger.info(f"Creating playlist '{playlist_name}' with {len(uris)} tracks")

        playlist = sp.user_playlist_create(user=spotify_user_id, name=playlist_name)
        sp.playlist_add_items(playlist_id=playlist["id"], items=uris)

        logger.info(f"Successfully created playlist '{playlist_name}'")

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
    except SpotifyException as e:
        logger.error(f"Failed to create playlist: {e}")
        raise HTTPException(status_code=500, detail=f"Spotify error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
