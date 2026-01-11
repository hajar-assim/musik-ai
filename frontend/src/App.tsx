import { useState } from 'react';
import { musikApi } from './services/api';
import type { ConversionResponse } from './services/api';
import './App.css';

interface ConversionState {
  status: 'idle' | 'loading' | 'success' | 'error';
  data?: ConversionResponse;
  error?: string;
}

function App() {
  const [userId, setUserId] = useState('');
  const [ytPlaylistId, setYtPlaylistId] = useState('');
  const [playlistName, setPlaylistName] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [conversion, setConversion] = useState<ConversionState>({ status: 'idle' });

  const handleLogin = () => {
    if (!userId.trim()) {
      alert('Please enter a user ID');
      return;
    }
    // Redirect to backend OAuth flow
    window.location.href = musikApi.login(userId);
  };

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!userId.trim() || !ytPlaylistId.trim() || !playlistName.trim()) {
      alert('Please fill in all fields');
      return;
    }

    setConversion({ status: 'loading' });

    try {
      const result = await musikApi.convertPlaylist(userId, ytPlaylistId, playlistName);
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

        <div className="bg-white rounded-2xl shadow-2xl p-8 mb-6">
          {!isAuthenticated ? (
            <div className="space-y-6">
              <div>
                <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-2">
                  User ID
                </label>
                <input
                  type="text"
                  id="userId"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="Enter a unique user ID"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                />
                <p className="mt-2 text-sm text-gray-500">
                  Choose any ID to identify your session (e.g., your name or email)
                </p>
              </div>

              <button
                onClick={handleLogin}
                className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 transform hover:scale-105"
              >
                Login with Spotify
              </button>

              <button
                onClick={() => setIsAuthenticated(true)}
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-3 px-6 rounded-lg transition duration-200"
              >
                Skip (for testing - assumes already authenticated)
              </button>
            </div>
          ) : (
            <form onSubmit={handleConvert} className="space-y-6">
              <div>
                <label htmlFor="userId-convert" className="block text-sm font-medium text-gray-700 mb-2">
                  User ID
                </label>
                <input
                  type="text"
                  id="userId-convert"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="Enter your user ID"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                  required
                />
              </div>

              <div>
                <label htmlFor="ytPlaylistId" className="block text-sm font-medium text-gray-700 mb-2">
                  YouTube Playlist ID
                </label>
                <input
                  type="text"
                  id="ytPlaylistId"
                  value={ytPlaylistId}
                  onChange={(e) => setYtPlaylistId(e.target.value)}
                  placeholder="e.g., PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                  required
                />
                <p className="mt-2 text-sm text-gray-500">
                  Find this in the YouTube playlist URL after "list="
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

              <button
                type="button"
                onClick={() => setIsAuthenticated(false)}
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition duration-200"
              >
                Back to Login
              </button>
            </form>
          )}
        </div>

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
