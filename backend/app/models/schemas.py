from pydantic import BaseModel
from typing import List, Optional


class UserInfo(BaseModel):
    id: str
    display_name: str
    email: Optional[str] = None
    images: List[dict] = []


class RecommendedTrack(BaseModel):
    uri: str
    name: str
    artist: str
    album: str
    image: Optional[str] = None
    preview_url: Optional[str] = None


class ConversionResponse(BaseModel):
    status: str
    playlist_name: str
    playlist_id: str
    playlist_url: str
    total_tracks: int
    matched_tracks: int
    total_videos: int
    failed_matches: int
    failed_match_titles: List[str]


class MatchTracksResponse(BaseModel):
    status: str
    matched_tracks: List[str]
    total_videos: int
    failed_matches: List[str]


class RecommendationsResponse(BaseModel):
    status: str
    recommendations: List[RecommendedTrack]
