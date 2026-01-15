import { useState, useEffect } from 'react';
import { musikApi } from './services/api';
import type { ConversionResponse, UserInfo } from './services/api';
import './App.css';

interface ConversionState {
  status: 'idle' | 'loading' | 'success' | 'error';
  data?: ConversionResponse;
  error?: string;
}

const PLAYLIST_NAMES = [
  'DepressingJams123',
  'MidnightVibes247',
  'SunshineAndBops',
  'CozyMorningMix',
  'WorkoutBangers',
  'ChaoticEnergy',
  'VintageVibes',
  'GoodVibesOnly',
  'MainCharacterMusic',
  'UnhingedPlaylist',
  'RetroRoadtrip',
  'StudyModeActivated',
  'WeekendAnthems',
  'GroceryStoreBops',
  'ImTheVillain',
];

const getRandomPlaylistName = () => {
  return PLAYLIST_NAMES[Math.floor(Math.random() * PLAYLIST_NAMES.length)];
};

function App() {
  const [spotifyUserId, setSpotifyUserId] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [ytPlaylistId, setYtPlaylistId] = useState('');
  const [playlistName, setPlaylistName] = useState('');
  const [placeholderName] = useState(getRandomPlaylistName());
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
      localStorage.setItem('spotify_user_id', userId);
      setSpotifyUserId(userId);
      window.history.replaceState({}, '', '/');
      fetchUserInfo(userId);
    } else {
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
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const handleLogin = () => {
    window.location.href = musikApi.login();
  };

  const handleLogout = () => {
    localStorage.removeItem('spotify_user_id');
    setSpotifyUserId(null);
    setUserInfo(null);
    setConversion({ status: 'idle' });
  };

  const extractPlaylistId = (input: string): string => {
    if (input.startsWith('PL')) {
      return input;
    }

    try {
      const url = new URL(input);
      const listParam = url.searchParams.get('list');
      if (listParam) {
        return listParam;
      }
    } catch {
      // Not a valid URL
    }

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
      const playlistId = extractPlaylistId(ytPlaylistId.trim());
      const result = await musikApi.convertPlaylist(spotifyUserId, playlistId, playlistName);
      setConversion({ status: 'success', data: result });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Conversion failed';
      setConversion({ status: 'error', error: errorMessage });
    }
  };

  return (
    <div className="min-h-screen bg-cararra">
      {/* Header */}
      <header className="bg-chambray shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-cararra tracking-tight">musik-ai</h1>
              <p className="text-botticelli text-sm mt-1">YouTube to Spotify playlist converter</p>
            </div>
            {userInfo && (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3">
                  {userInfo.images?.[0]?.url && (
                    <img
                      src={userInfo.images[0].url}
                      alt="Profile"
                      className="w-10 h-10 rounded-full border-2 border-botticelli object-cover"
                    />
                  )}
                  <div className="text-right">
                    <p className="font-medium text-cararra text-sm">{userInfo.display_name}</p>
                    <p className="text-botticelli text-xs">{userInfo.email}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-botticelli hover:text-cararra transition-colors text-sm underline"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!spotifyUserId ? (
          /* Login View */
          <div className="bg-white rounded-xl shadow-lg border border-botticelli p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-chambray rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-cararra" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-chambray mb-3">Welcome to musik-ai</h2>
              <p className="text-falcon mb-8 leading-relaxed">
                Connect your Spotify account to start converting YouTube playlists to Spotify seamlessly
              </p>
              <button
                onClick={handleLogin}
                className="w-full bg-chambray hover:bg-waikawa text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md"
              >
                Connect with Spotify
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Conversion Form */}
            <div className="bg-white rounded-xl shadow-lg border border-botticelli p-8 mb-6">
              <h2 className="text-2xl font-bold text-chambray mb-6">Convert Playlist</h2>

              <form onSubmit={handleConvert} className="space-y-6">
                <div>
                  <label htmlFor="ytPlaylistId" className="block text-sm font-semibold text-falcon mb-2">
                    YouTube Playlist URL or ID
                  </label>
                  <input
                    type="text"
                    id="ytPlaylistId"
                    value={ytPlaylistId}
                    onChange={(e) => setYtPlaylistId(e.target.value)}
                    placeholder="Paste YouTube playlist URL or ID"
                    className="w-full px-4 py-3 border-2 border-botticelli rounded-lg focus:ring-2 focus:ring-chambray focus:border-chambray outline-none transition-all bg-cararra text-falcon placeholder-nepal"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="playlistName" className="block text-sm font-semibold text-falcon mb-2">
                    Spotify Playlist Name
                  </label>
                  <input
                    type="text"
                    id="playlistName"
                    value={playlistName}
                    onChange={(e) => setPlaylistName(e.target.value)}
                    placeholder={placeholderName}
                    className="w-full px-4 py-3 border-2 border-botticelli rounded-lg focus:ring-2 focus:ring-chambray focus:border-chambray outline-none transition-all bg-cararra text-falcon placeholder-nepal"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={conversion.status === 'loading'}
                  className="w-full bg-chambray hover:bg-waikawa disabled:bg-nepal disabled:cursor-not-allowed text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:transform-none shadow-md"
                >
                  {conversion.status === 'loading' ? 'Converting...' : 'Convert Playlist'}
                </button>
              </form>
            </div>

            {/* Loading State */}
            {conversion.status === 'loading' && (
              <div className="bg-botticelli border-2 border-nepal rounded-xl p-6 shadow-md">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="animate-spin rounded-full h-8 w-8 border-4 border-nepal border-t-chambray"></div>
                  </div>
                  <div>
                    <p className="text-chambray font-semibold">Converting your playlist</p>
                    <p className="text-falcon text-sm">This may take a moment...</p>
                  </div>
                </div>
              </div>
            )}

            {/* Success State */}
            {conversion.status === 'success' && conversion.data && (
              <div className="bg-white border-2 border-cashmere rounded-xl p-8 shadow-lg">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 bg-cashmere rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-6 h-6 text-falcon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-chambray mb-2">Conversion Successful!</h3>
                    <p className="text-falcon mb-6">Your playlist has been created on Spotify</p>

                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">Playlist Name</p>
                        <p className="text-chambray font-semibold">{conversion.data.playlist_name}</p>
                      </div>
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">Total Videos</p>
                        <p className="text-chambray font-semibold">{conversion.data.total_videos}</p>
                      </div>
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">Matched Tracks</p>
                        <p className="text-chambray font-semibold">{conversion.data.matched_tracks}</p>
                      </div>
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">Failed Matches</p>
                        <p className="text-falcon font-semibold">{conversion.data.failed_matches}</p>
                      </div>
                    </div>

                    {conversion.data.playlist_url && (
                      <a
                        href={conversion.data.playlist_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block bg-chambray hover:bg-waikawa text-cararra font-semibold py-3 px-8 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md"
                      >
                        Open in Spotify
                      </a>
                    )}

                    {conversion.data.failed_match_titles.length > 0 && (
                      <div className="mt-6 pt-6 border-t-2 border-botticelli">
                        <p className="font-semibold text-falcon mb-3">Tracks that couldn't be matched:</p>
                        <ul className="space-y-2">
                          {conversion.data.failed_match_titles.map((title, index) => (
                            <li key={index} className="text-sm text-nepal flex items-start gap-2">
                              <span className="text-pharlap">•</span>
                              <span>{title}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Error State */}
            {conversion.status === 'error' && (
              <div className="bg-white border-2 border-pharlap rounded-xl p-8 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-pharlap rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-6 h-6 text-cararra" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-falcon mb-2">Conversion Failed</h3>
                    <p className="text-falcon mb-6">{conversion.error}</p>
                    <button
                      onClick={() => setConversion({ status: 'idle' })}
                      className="bg-falcon hover:bg-pharlap text-cararra font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-md"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 mt-12">
        <div className="border-t border-botticelli pt-8 text-center">
          <p className="text-nepal text-sm">
            Built with blood sweat and tears (mostly tears)
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
