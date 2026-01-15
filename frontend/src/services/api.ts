import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export interface ConversionResponse {
  status: string;
  playlist_name: string;
  playlist_id: string;
  playlist_url: string;
  total_videos: number;
  matched_tracks: number;
  failed_matches: number;
  failed_match_titles: string[];
}

export interface UserInfo {
  id: string;
  display_name: string;
  email?: string;
  images: Array<{ url: string }>;
}

export interface RecommendedTrack {
  uri: string;
  name: string;
  artist: string;
  album: string;
  image: string | null;
  preview_url: string | null;
}

export interface RecommendationsResponse {
  status: string;
  recommendations: RecommendedTrack[];
}

export interface MatchTracksResponse {
  status: string;
  matched_tracks: string[];
  total_videos: number;
  failed_matches: string[];
}

export interface Playlist {
  id: string;
  name: string;
  tracks_count: number;
  image: string | null;
  external_url: string;
}

export interface PlaylistsResponse {
  status: string;
  playlists: Playlist[];
}

export interface AddTracksResponse {
  status: string;
  tracks_added: number;
}

export const musikApi = {
  /**
   * Request access to the app
   */
  requestAccess: async (email: string, name?: string): Promise<{ status: string; message: string }> => {
    const response = await api.post('/request-access', null, {
      params: {
        email,
        ...(name && { name })
      }
    });
    return response.data;
  },

  /**
   * Initiate Spotify OAuth login flow
   */
  login: (): string => {
    return `${API_BASE_URL}/login`;
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (spotifyUserId: string): Promise<UserInfo> => {
    const response = await api.get<UserInfo>('/me', {
      params: { spotify_user_id: spotifyUserId },
    });
    return response.data;
  },

  /**
   * Match YouTube playlist tracks to Spotify
   */
  matchTracks: async (
    spotifyUserId: string,
    ytPlaylistId: string
  ): Promise<MatchTracksResponse> => {
    const response = await api.get<MatchTracksResponse>('/match-tracks', {
      params: {
        spotify_user_id: spotifyUserId,
        yt_playlist_id: ytPlaylistId,
      },
    });
    return response.data;
  },

  /**
   * Get AI-powered track recommendations
   */
  getRecommendations: async (
    spotifyUserId: string,
    trackUris: string
  ): Promise<RecommendationsResponse> => {
    const response = await api.get<RecommendationsResponse>('/recommendations', {
      params: {
        spotify_user_id: spotifyUserId,
        track_uris: trackUris,
      },
    });
    return response.data;
  },

  /**
   * Create Spotify playlist from track URIs
   */
  createPlaylist: async (
    spotifyUserId: string,
    playlistName: string,
    trackUris: string
  ): Promise<ConversionResponse> => {
    const response = await api.get<ConversionResponse>('/convert', {
      params: {
        spotify_user_id: spotifyUserId,
        playlist_name: playlistName,
        track_uris: trackUris,
      },
    });
    return response.data;
  },

  /**
   * Get user's Spotify playlists
   */
  getUserPlaylists: async (spotifyUserId: string): Promise<PlaylistsResponse> => {
    const response = await api.get<PlaylistsResponse>('/playlists', {
      params: { spotify_user_id: spotifyUserId },
    });
    return response.data;
  },

  /**
   * Get AI recommendations for an existing playlist
   */
  getPlaylistRecommendations: async (
    spotifyUserId: string,
    playlistId: string
  ): Promise<RecommendationsResponse> => {
    const response = await api.get<RecommendationsResponse>('/enhance-playlist', {
      params: {
        spotify_user_id: spotifyUserId,
        playlist_id: playlistId,
      },
    });
    return response.data;
  },

  /**
   * Add tracks to an existing playlist
   */
  addTracksToPlaylist: async (
    spotifyUserId: string,
    playlistId: string,
    trackUris: string
  ): Promise<AddTracksResponse> => {
    const response = await api.post<AddTracksResponse>('/add-to-playlist', null, {
      params: {
        spotify_user_id: spotifyUserId,
        playlist_id: playlistId,
        track_uris: trackUris,
      },
    });
    return response.data;
  },
};

export default api;
