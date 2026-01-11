import { useState, useEffect } from 'react';
import { musikApi } from './services/api';
import type { ConversionResponse, UserInfo } from './services/api';
import './App.css';

interface ConversionState {
  status: 'idle' | 'loading' | 'success' | 'error';
  data?: ConversionResponse;
  error?: string;
}

function App() {
  const [spotifyUserId, setSpotifyUserId] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [ytPlaylistId, setYtPlaylistId] = useState('');
  const [playlistName, setPlaylistName] = useState('');
  const [conversion, setConversion] = useState<ConversionState>({ status: 'idle' });

  // Check for OAuth callback parameters and stored session
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const userId = params.get('spotify_user_id');
    const status = params.get('status');
    const error = params.get('error');

    if (error) {
      alert(`Authentication error: ${error}`);
      window.history.replaceState({}, '', '/');
      return;
    }

    if (userId && status === 'success') {
      // Save to localStorage
      localStorage.setItem('spotify_user_id', userId);
      setSpotifyUserId(userId);
      // Clean URL
      window.history.replaceState({}, '', '/');
      // Fetch user info
      fetchUserInfo(userId);
    } else {
      // Check localStorage for existing session
      const storedUserId = localStorage.getItem('spotify_user_id');
      if (storedUserId) {
        setSpotifyUserId(storedUserId);
        fetchUserInfo(storedUserId);
      }
    }
  }, []);

  const fetchUserInfo = async (userId: string) => {
    try {
      const info = await musikApi.getCurrentUser(userId);
      setUserInfo(info);
    } catch (error: any) {
      console.error('Failed to fetch user info:', error);
      // If auth fails, clear session
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const handleLogin = () => {
    // Redirect to backend OAuth flow
    window.location.href = musikApi.login();
  };

  const handleLogout = () => {
    localStorage.removeItem('spotify_user_id');
    setSpotifyUserId(null);
    setUserInfo(null);
    setConversion({ status: 'idle' });
  };

  const extractPlaylistId = (input: string): string => {
    // If it's already just an ID (starts with PL), return it
    if (input.startsWith('PL')) {
      return input;
    }

    // Try to extract from URL
    try {
      const url = new URL(input);
      const listParam = url.searchParams.get('list');
      if (listParam) {
        return listParam;
      }
    } catch {
      // Not a valid URL, might be just an ID
    }

    // Return original input if we couldn't extract
    return input;
  };

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!spotifyUserId) {
      alert('Please log in with Spotify first');
      return;
    }

    if (!ytPlaylistId.trim() || !playlistName.trim()) {
      alert('Please fill in all fields');
      return;
    }

    setConversion({ status: 'loading' });

    try {
      // Extract playlist ID from URL if needed
      const playlistId = extractPlaylistId(ytPlaylistId.trim());
      const result = await musikApi.convertPlaylist(spotifyUserId, playlistId, playlistName);
      setConversion({ status: 'success', data: result });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Conversion failed';
      setConversion({ status: 'error', error: errorMessage });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-400 via-blue-500 to-purple-600 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-extrabold text-white mb-2">
            musik-ai
          </h1>
          <p className="text-xl text-white opacity-90">
            Convert YouTube playlists to Spotify seamlessly
          </p>
        </div>

        {!spotifyUserId ? (
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <div className="text-center space-y-6">
              <p className="text-lg text-gray-700">
                Connect your Spotify account to get started
              </p>
              <button
                onClick={handleLogin}
                className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 transform hover:scale-105"
              >
                Login with Spotify
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* User Info */}
            {userInfo && (
              <div className="bg-white rounded-2xl shadow-2xl p-6 mb-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {userInfo.images?.[0]?.url && (
                      <img
                        src={userInfo.images[0].url}
                        alt="Profile"
                        className="w-12 h-12 rounded-full"
                      />
                    )}
                    <div>
                      <p className="font-semibold text-gray-900">{userInfo.display_name}</p>
                      <p className="text-sm text-gray-500">{userInfo.email}</p>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-gray-600 hover:text-gray-800 underline"
                  >
                    Logout
                  </button>
                </div>
              </div>
            )}

            {/* Conversion Form */}
            <div className="bg-white rounded-2xl shadow-2xl p-8 mb-6">
              <form onSubmit={handleConvert} className="space-y-6">
                <div>
                  <label htmlFor="ytPlaylistId" className="block text-sm font-medium text-gray-700 mb-2">
                    YouTube Playlist URL or ID
                  </label>
                  <input
                    type="text"
                    id="ytPlaylistId"
                    value={ytPlaylistId}
                    onChange={(e) => setYtPlaylistId(e.target.value)}
                    placeholder="Paste full YouTube URL or just the playlist ID"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                    required
                  />
                  <p className="mt-2 text-sm text-gray-500">
                    You can paste the full YouTube URL or just the playlist ID
                  </p>
                </div>

                <div>
                  <label htmlFor="playlistName" className="block text-sm font-medium text-gray-700 mb-2">
                    Spotify Playlist Name
                  </label>
                  <input
                    type="text"
                    id="playlistName"
                    value={playlistName}
                    onChange={(e) => setPlaylistName(e.target.value)}
                    placeholder="e.g., My Converted Playlist"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={conversion.status === 'loading'}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 transform hover:scale-105 disabled:transform-none disabled:cursor-not-allowed"
                >
                  {conversion.status === 'loading' ? 'Converting...' : 'Convert Playlist'}
                </button>
              </form>
            </div>
          </>
        )}

        {/* Loading Indicator */}
        {conversion.status === 'loading' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <p className="text-blue-700 font-medium">Converting your playlist... This may take a moment.</p>
            </div>
          </div>
        )}

        {/* Success Message */}
        {conversion.status === 'success' && conversion.data && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-green-800 mb-4">Conversion Successful!</h2>
            <div className="space-y-2 text-green-700">
              <p><strong>Playlist:</strong> {conversion.data.playlist_name}</p>
              <p><strong>Total Videos:</strong> {conversion.data.total_videos}</p>
              <p><strong>Matched Tracks:</strong> {conversion.data.matched_tracks}</p>
              <p><strong>Failed Matches:</strong> {conversion.data.failed_matches}</p>
              {conversion.data.playlist_url && (
                <a
                  href={conversion.data.playlist_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-4 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-lg transition duration-200"
                >
                  Open in Spotify
                </a>
              )}
            </div>
            {conversion.data.failed_match_titles.length > 0 && (
              <div className="mt-4">
                <p className="font-semibold text-green-800 mb-2">Failed to match:</p>
                <ul className="list-disc list-inside text-sm text-green-600">
                  {conversion.data.failed_match_titles.map((title, index) => (
                    <li key={index}>{title}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {conversion.status === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-red-800 mb-2">Conversion Failed</h2>
            <p className="text-red-700">{conversion.error}</p>
            <button
              onClick={() => setConversion({ status: 'idle' })}
              className="mt-4 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-6 rounded-lg transition duration-200"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
