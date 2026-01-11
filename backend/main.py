from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from .vault_client import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

app = FastAPI()

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
    sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                            client_secret=SPOTIFY_CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=f".cache-{user_id}")  # token cache per user
    oauth_objects[user_id] = sp_oauth
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)


@app.get("/callback")
def callback(request: Request, code: str = None, state: str = None, error: str = None):
    """
    Step 2: Spotify redirects here after user login
    """
    user_id = state  # pass user_id via state if needed
    sp_oauth = oauth_objects[user_id]
    token_info = sp_oauth.get_access_token(code)
    # token_info contains access_token, refresh_token, expires_in
    return {"status": "authorized", "user_id": user_id}


@app.get("/convert")
def convert(user_id: str, yt_playlist_id: str, playlist_name: str):
    """
    Step 3: convert YouTube playlist to Spotify using the authorized token
    """
    sp_oauth = oauth_objects[user_id]
    sp = spotipy.Spotify(auth_manager=sp_oauth)

    from yt_spotify import get_youtube_playlist_videos, search_track_on_spotify

    video_titles = get_youtube_playlist_videos(yt_playlist_id)
    track_uris = [search_track_on_spotify(sp, title) for title in video_titles if search_track_on_spotify(sp, title)]

    current_user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=current_user_id, name=playlist_name)
    sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris)

    return {"status": "success", "playlist_name": playlist_name, "track_count": len(track_uris)}
