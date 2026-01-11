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

export interface AuthResponse {
  status: string;
  user_id: string;
}

export const musikApi = {
  /**
   * Initiate Spotify OAuth login flow
   */
  login: (userId: string): string => {
    return `${API_BASE_URL}/login?user_id=${encodeURIComponent(userId)}`;
  },

  /**
   * Convert YouTube playlist to Spotify
   */
  convertPlaylist: async (
    userId: string,
    ytPlaylistId: string,
    playlistName: string
  ): Promise<ConversionResponse> => {
    const response = await api.get<ConversionResponse>('/convert', {
      params: {
        user_id: userId,
        yt_playlist_id: ytPlaylistId,
        playlist_name: playlistName,
      },
    });
    return response.data;
  },
};

export default api;
