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

export const musikApi = {
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
   * Convert YouTube playlist to Spotify
   */
  convertPlaylist: async (
    spotifyUserId: string,
    ytPlaylistId: string,
    playlistName: string
  ): Promise<ConversionResponse> => {
    const response = await api.get<ConversionResponse>('/convert', {
      params: {
        spotify_user_id: spotifyUserId,
        yt_playlist_id: ytPlaylistId,
        playlist_name: playlistName,
      },
    });
    return response.data;
  },
};

export default api;
