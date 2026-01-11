from googleapiclient.discovery import build
import os
from .vault_client import YOUTUBE_API_KEY

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_youtube_playlist_videos(playlist_id: str):
    videos = []
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )
    while request:
        response = request.execute()
        for item in response["items"]:
            videos.append(item["snippet"]["title"])
        request = youtube.playlistItems().list_next(request, response)
    return videos

def search_track_on_spotify(sp, track_name: str):
    results = sp.search(q=track_name, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    return items[0]["uri"] if items else None
