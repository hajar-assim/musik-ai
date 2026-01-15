import { useState, useEffect } from "react";
import { musikApi } from "./services/api";
import type {
  ConversionResponse,
  UserInfo,
  RecommendedTrack,
  Playlist,
} from "./services/api";
import "./App.css";

interface ConversionState {
  status: "idle" | "loading" | "recommendations" | "success" | "error";
  data?: ConversionResponse;
  error?: string;
  matchedTracks?: string[];
  recommendations?: RecommendedTrack[];
  selectedRecommendations?: Set<string>;
}

const PLAYLIST_NAMES = [
  "LateNightCommits",
  "BackgroundNoiseIRL",
  "HeadphonesOnWorldOff",
  "BurnoutButProductive",
  "FocusButMakeItSad",
  "RainyBusRide",
  "3AMDebugging",
  "CalmBeforeTheDeadline",
  "CoffeeColdStillCoding",
  "LowEnergyHighAnxiety",
  "QuietMotivation",
  "StaringAtTheScreen",
  "SoftBeatsHardThoughts",
  "AlmostDoneIThink",
  "WinterSemesterMood",
  "StudyRoomAfterMidnight",
  "NoLyricsJustVibes",
  "BrainFogAnthems",
  "MusicForOverthinking",
  "OneMoreTaskThenSleep",
  "CodingButEmotionally",
  "MainCharacterOnMute",
  "ExistentialBackgroundMusic",
  "LongWalksNoDestination",
  "FocusedButTired",
  "DeadlineEnergy",
  "LoFiButStressed",
  "MentallyElsewhere",
  "WorkingThroughIt",
  "BackgroundMusicForLife",
  "ImCooked",
  "ActuallyCooked",
  "MentallyCooked",
  "PhysicallyHereMentallyGone",
  "BrainIsFried",
  "RunningOnFumes",
  "BarelyHoldingItTogether",
  "ThisIsFineIRL",
  "IShouldBeSleeping",
  "WhyAmIStillAwake",
  "SoTiredButStillTrying",
  "LowBatteryMode",
  "EmotionallyUnavailable",
  "JustOneMoreSong",
  "ThisPlaylistIsCoping",
  "SurvivingNotThriving",
  "OperatingOnAutopilot",
  "ChronicallyOnlineThoughts",
  "DoingMyBestIThink",
  "PleaseLetMeFocus",
  "SomehowStillWorking",
  "TooTiredToCare",
  "QuietlyLosingIt",
  "HoldingOnByThreads",
];

const getRandomPlaylistName = () => {
  return PLAYLIST_NAMES[Math.floor(Math.random() * PLAYLIST_NAMES.length)];
};

function App() {
  const [spotifyUserId, setSpotifyUserId] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [mode, setMode] = useState<"convert" | "enhance">("convert");
  const [ytPlaylistId, setYtPlaylistId] = useState("");
  const [playlistName, setPlaylistName] = useState(getRandomPlaylistName());
  const [wantRecommendations, setWantRecommendations] = useState(true);
  const [conversion, setConversion] = useState<ConversionState>({
    status: "idle",
  });
  const [showAccessRequest, setShowAccessRequest] = useState(false);
  const [accessRequestEmail, setAccessRequestEmail] = useState("");
  const [accessRequestName, setAccessRequestName] = useState("");
  const [accessRequestStatus, setAccessRequestStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [accessRequestMessage, setAccessRequestMessage] = useState("");

  // Enhance mode state
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [playlistSearchQuery, setPlaylistSearchQuery] = useState("");
  const [selectedPlaylist, setSelectedPlaylist] = useState<string | null>(null);
  const [playlistsLoading, setPlaylistsLoading] = useState(false);
  const [enhanceStatus, setEnhanceStatus] = useState<
    "idle" | "loading" | "recommendations" | "success" | "error"
  >("idle");
  const [enhanceRecommendations, setEnhanceRecommendations] = useState<
    RecommendedTrack[]
  >([]);
  const [selectedEnhanceRecs, setSelectedEnhanceRecs] = useState<Set<string>>(
    new Set()
  );
  const [enhanceError, setEnhanceError] = useState<string | null>(null);

  // Check for OAuth callback parameters and stored session
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const userId = params.get("spotify_user_id");
    const status = params.get("status");
    const error = params.get("error");

    if (error) {
      alert(`Authentication error: ${error}`);
      window.history.replaceState({}, "", "/");
      return;
    }

    if (userId && status === "success") {
      localStorage.setItem("spotify_user_id", userId);
      setSpotifyUserId(userId);
      window.history.replaceState({}, "", "/");
      fetchUserInfo(userId);
    } else {
      const storedUserId = localStorage.getItem("spotify_user_id");
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
      console.error("Failed to fetch user info:", error);
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const handleRequestAccess = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!accessRequestEmail.trim()) {
      setAccessRequestMessage("Email is required");
      setAccessRequestStatus("error");
      return;
    }

    setAccessRequestStatus("loading");

    try {
      const result = await musikApi.requestAccess(
        accessRequestEmail,
        accessRequestName || undefined
      );
      setAccessRequestStatus("success");
      setAccessRequestMessage(result.message);
    } catch (error: any) {
      setAccessRequestStatus("error");
      setAccessRequestMessage(
        error.response?.data?.detail ||
          "Failed to submit request. Please try again."
      );
    }
  };

  const handleLogin = () => {
    window.location.href = musikApi.login();
  };

  const handleLogout = () => {
    localStorage.removeItem("spotify_user_id");
    setSpotifyUserId(null);
    setUserInfo(null);
    setConversion({ status: "idle" });
  };

  const extractPlaylistId = (input: string): string => {
    if (input.startsWith("PL")) {
      return input;
    }

    try {
      const url = new URL(input);
      const listParam = url.searchParams.get("list");
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
      alert("Please log in with Spotify first");
      return;
    }

    if (!ytPlaylistId.trim() || !playlistName.trim()) {
      alert("Please fill in all fields");
      return;
    }

    setConversion({ status: "loading" });

    try {
      const playlistId = extractPlaylistId(ytPlaylistId.trim());

      const matchResult = await musikApi.matchTracks(spotifyUserId, playlistId);
      const matchedUris = matchResult.matched_tracks.join(",");

      if (wantRecommendations) {
        try {
          const recommendations = await musikApi.getRecommendations(
            spotifyUserId,
            matchedUris
          );

          setConversion({
            status: "recommendations",
            matchedTracks: matchResult.matched_tracks,
            recommendations: recommendations.recommendations,
            selectedRecommendations: new Set(),
          });
        } catch (recError: any) {
          const recErrorMessage =
            recError.response?.data?.detail ||
            recError.message ||
            "Failed to get recommendations";
          setConversion({
            status: "error",
            error: `${recErrorMessage}\n\nYou can skip recommendations and create the playlist with just the matched tracks.`,
            matchedTracks: matchResult.matched_tracks,
          });
        }
      } else {
        setConversion({
          status: "recommendations",
          matchedTracks: matchResult.matched_tracks,
          recommendations: [],
          selectedRecommendations: new Set(),
        });
      }
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to match tracks";
      setConversion({ status: "error", error: errorMessage });
    }
  };

  const handleCreatePlaylist = async () => {
    if (!spotifyUserId || !conversion.matchedTracks) {
      return;
    }

    setConversion({ ...conversion, status: "loading" });

    try {
      // Combine matched tracks with selected recommendations
      const selectedRecs = Array.from(conversion.selectedRecommendations || []);
      const allTracks = [...conversion.matchedTracks, ...selectedRecs];
      const trackUris = allTracks.join(",");

      const result = await musikApi.createPlaylist(
        spotifyUserId,
        playlistName,
        trackUris
      );
      setConversion({ status: "success", data: result });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to create playlist";
      setConversion({ status: "error", error: errorMessage });
    }
  };

  const toggleRecommendation = (uri: string) => {
    const newSelected = new Set(conversion.selectedRecommendations || []);
    if (newSelected.has(uri)) {
      newSelected.delete(uri);
    } else {
      newSelected.add(uri);
    }
    setConversion({ ...conversion, selectedRecommendations: newSelected });
  };

  const selectAllRecommendations = () => {
    const allUris = new Set(
      conversion.recommendations?.map((track) => track.uri) || []
    );
    setConversion({ ...conversion, selectedRecommendations: allUris });
  };

  const deselectAllRecommendations = () => {
    setConversion({ ...conversion, selectedRecommendations: new Set() });
  };

  // Fetch playlists when switching to Enhance mode
  useEffect(() => {
    if (
      mode === "enhance" &&
      spotifyUserId &&
      playlists.length === 0 &&
      !playlistsLoading
    ) {
      const fetchPlaylists = async () => {
        setPlaylistsLoading(true);
        try {
          const response = await musikApi.getUserPlaylists(spotifyUserId);
          setPlaylists(response.playlists);
        } catch (error: any) {
          console.error("Error fetching playlists:", error);
          setEnhanceError("Failed to fetch playlists");
        } finally {
          setPlaylistsLoading(false);
        }
      };
      fetchPlaylists();
    }
  }, [mode, spotifyUserId, playlists.length, playlistsLoading]);

  const handleEnhancePlaylist = async () => {
    if (!spotifyUserId || !selectedPlaylist) {
      return;
    }

    setEnhanceStatus("loading");
    setEnhanceError(null);

    try {
      const response = await musikApi.getPlaylistRecommendations(
        spotifyUserId,
        selectedPlaylist
      );
      setEnhanceRecommendations(response.recommendations);
      setSelectedEnhanceRecs(new Set());
      setEnhanceStatus("recommendations");
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to get recommendations";
      setEnhanceError(errorMessage);
      setEnhanceStatus("error");
    }
  };

  const handleAddToPlaylist = async () => {
    if (!spotifyUserId || !selectedPlaylist || selectedEnhanceRecs.size === 0) {
      return;
    }

    setEnhanceStatus("loading");

    try {
      const trackUris = Array.from(selectedEnhanceRecs).join(",");
      await musikApi.addTracksToPlaylist(
        spotifyUserId,
        selectedPlaylist,
        trackUris
      );
      setEnhanceStatus("success");
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || error.message || "Failed to add tracks";
      setEnhanceError(errorMessage);
      setEnhanceStatus("error");
    }
  };

  const toggleEnhanceRecommendation = (uri: string) => {
    const newSelected = new Set(selectedEnhanceRecs);
    if (newSelected.has(uri)) {
      newSelected.delete(uri);
    } else {
      newSelected.add(uri);
    }
    setSelectedEnhanceRecs(newSelected);
  };

  const selectAllEnhanceRecs = () => {
    const allUris = new Set(enhanceRecommendations.map((track) => track.uri));
    setSelectedEnhanceRecs(allUris);
  };

  const deselectAllEnhanceRecs = () => {
    setSelectedEnhanceRecs(new Set());
  };

  return (
    <div className="min-h-screen bg-cararra flex flex-col">
      {/* Header */}
      <header className="bg-chambray shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-cararra tracking-tight font-display">
                musik-ai
              </h1>
              <p className="text-botticelli text-sm mt-1">
                just another music tool
              </p>
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
                    <p className="font-medium text-cararra text-sm">
                      {userInfo.display_name}
                    </p>
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
      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full">
        {!spotifyUserId ? (
          /* Login View */
          <div className="bg-white rounded-xl shadow-lg border border-botticelli p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-chambray rounded-full flex items-center justify-center mx-auto mb-6">
                <svg
                  className="w-8 h-8 text-cararra"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-chambray mb-3">
                welcome to musik-ai
              </h2>
              <p className="text-falcon mb-8 leading-relaxed">
                Connect Spotify to convert playlists and discover new music with
                AI recommendations.
              </p>
              <button
                onClick={handleLogin}
                className="w-full bg-chambray hover:bg-waikawa text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md"
              >
                Connect with Spotify
              </button>
              <div className="mt-6 text-center">
                <p className="text-falcon text-sm mb-2">
                  Don't have access yet?
                </p>
                <button
                  onClick={() => setShowAccessRequest(true)}
                  className="text-chambray hover:text-waikawa font-semibold text-sm underline"
                >
                  Request Access
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Mode Tabs */}
            <div className="bg-white rounded-xl shadow-lg border border-botticelli mb-6 overflow-hidden">
              <div className="flex border-b-2 border-botticelli">
                <button
                  onClick={() => setMode("convert")}
                  className={`flex-1 py-4 px-6 font-semibold transition-all ${
                    mode === "convert"
                      ? "bg-chambray text-cararra"
                      : "bg-cararra text-falcon hover:bg-botticelli"
                  }`}
                >
                  Convert Playlist
                </button>
                <button
                  onClick={() => setMode("enhance")}
                  className={`flex-1 py-4 px-6 font-semibold transition-all ${
                    mode === "enhance"
                      ? "bg-chambray text-cararra"
                      : "bg-cararra text-falcon hover:bg-botticelli"
                  }`}
                >
                  Enhance Playlist
                </button>
              </div>
            </div>

            {/* Convert Mode */}
            {mode === "convert" && (
              <div className="bg-white rounded-xl shadow-lg border border-botticelli p-8 mb-6">
                <h2 className="text-2xl font-bold text-chambray mb-3">
                  Convert Playlist
                </h2>
                <p className="text-falcon mb-2 text-sm leading-relaxed">
                  Enter a YouTube playlist ID to convert it to Spotify. We'll
                  match the tracks and give you AI-powered recommendations to
                  discover similar music you'll love.
                </p>

                <form onSubmit={handleConvert} className="space-y-6">
                  <div>
                    <label
                      htmlFor="ytPlaylistId"
                      className="block text-sm font-semibold text-falcon mb-2"
                    >
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
                    <label
                      htmlFor="playlistName"
                      className="block text-sm font-semibold text-falcon mb-2"
                    >
                      Spotify Playlist Name
                    </label>
                    <input
                      type="text"
                      id="playlistName"
                      value={playlistName}
                      onChange={(e) => setPlaylistName(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-botticelli rounded-lg focus:ring-2 focus:ring-chambray focus:border-chambray outline-none transition-all bg-cararra text-falcon"
                      required
                    />
                  </div>

                  <div className="flex items-center gap-3 p-4 bg-botticelli rounded-lg">
                    <input
                      type="checkbox"
                      id="wantRecommendations"
                      checked={wantRecommendations}
                      onChange={(e) => setWantRecommendations(e.target.checked)}
                      className="w-5 h-5 text-chambray border-2 border-nepal rounded focus:ring-2 focus:ring-chambray cursor-pointer"
                    />
                    <label
                      htmlFor="wantRecommendations"
                      className="text-sm text-falcon cursor-pointer select-none"
                    >
                      Get AI-powered recommendations after conversion
                    </label>
                  </div>

                  <button
                    type="submit"
                    disabled={conversion.status === "loading"}
                    className="w-full bg-chambray hover:bg-waikawa disabled:bg-nepal disabled:cursor-not-allowed text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:transform-none shadow-md"
                  >
                    {conversion.status === "loading"
                      ? "Converting..."
                      : "Convert Playlist"}
                  </button>
                </form>
              </div>
            )}

            {/* Enhance Mode */}
            {mode === "enhance" && enhanceStatus === "idle" && (
              <div className="bg-white rounded-xl shadow-lg border border-botticelli p-8 mb-6">
                <h2 className="text-2xl font-bold text-chambray mb-3 font-display">
                  Enhance Playlist
                </h2>
                <p className="text-falcon mb-6 text-sm leading-relaxed italic">
                  Have no friends to recommend you music &lt;/3? That's okay, I
                  am here.
                </p>
                <p className="text-falcon mb-6 text-sm leading-relaxed">
                  Select one of your existing Spotify playlists and we'll
                  analyze it to recommend similar tracks you'll love.
                </p>

                {playlistsLoading ? (
                  <div className="text-center py-12">
                    <p className="text-nepal">Loading your playlists...</p>
                  </div>
                ) : playlists.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-nepal">No playlists found</p>
                  </div>
                ) : (
                  <>
                    {/* Search Box */}
                    <div className="mb-4">
                      <input
                        type="text"
                        placeholder="Search playlists..."
                        value={playlistSearchQuery}
                        onChange={(e) => setPlaylistSearchQuery(e.target.value)}
                        className="w-full px-4 py-3 border-2 border-nepal rounded-lg focus:outline-none focus:border-chambray transition-colors bg-cararra text-falcon placeholder-nepal"
                      />
                      <div className="flex items-start justify-between mt-2">
                        <p className="text-xs text-nepal">
                          Showing {playlists.filter((p) => p.name.toLowerCase().includes(playlistSearchQuery.toLowerCase())).length} of {playlists.length} playlists
                        </p>
                        <p className="text-xs text-nepal italic text-right">
                          Not finding your playlist? Make sure it's on your Spotify profile publicly.
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6 max-h-96 overflow-y-auto">
                      {playlists
                        .filter((playlist) =>
                          playlist.name.toLowerCase().includes(playlistSearchQuery.toLowerCase())
                        )
                        .map((playlist) => (
                        <div
                          key={playlist.id}
                          onClick={() => setSelectedPlaylist(playlist.id)}
                          className={`cursor-pointer rounded-lg border-2 p-4 transition-all ${
                            selectedPlaylist === playlist.id
                              ? "border-chambray bg-botticelli"
                              : "border-nepal bg-cararra hover:border-chambray"
                          }`}
                        >
                          <div className="flex gap-3">
                            {playlist.image && (
                              <img
                                src={playlist.image}
                                alt={playlist.name}
                                className="w-16 h-16 rounded object-cover flex-shrink-0"
                              />
                            )}
                            <div className="flex-1 min-w-0">
                              <h3 className="font-semibold text-chambray text-sm truncate">
                                {playlist.name}
                              </h3>
                              <p className="text-falcon text-xs mt-1">
                                {playlist.tracks_count} tracks
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <button
                      onClick={handleEnhancePlaylist}
                      disabled={!selectedPlaylist}
                      className="w-full bg-chambray hover:bg-waikawa disabled:bg-nepal disabled:cursor-not-allowed text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:transform-none shadow-md"
                    >
                      Get Recommendations
                    </button>
                  </>
                )}

                {enhanceError && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-700 text-sm">{enhanceError}</p>
                  </div>
                )}
              </div>
            )}

            {/* Enhance: Loading */}
            {mode === "enhance" && enhanceStatus === "loading" && (
              <div className="bg-white rounded-xl shadow-lg border border-botticelli p-8 mb-6">
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-chambray mx-auto mb-4"></div>
                  <p className="text-nepal text-lg font-semibold">
                    Getting recommendations...
                  </p>
                  <p className="text-falcon text-sm">
                    This may take a moment...
                  </p>
                </div>
              </div>
            )}

            {/* Enhance: Recommendations */}
            {mode === "enhance" && enhanceStatus === "recommendations" && (
              <div className="bg-white rounded-xl shadow-lg border border-botticelli p-8 mb-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-chambray mb-2 font-display">
                    Fresh tracks for your playlist!
                  </h2>
                  <p className="text-falcon mb-4">
                    Select the tracks you want to add to your playlist:
                  </p>

                  <div className="flex gap-3">
                    <button
                      onClick={selectAllEnhanceRecs}
                      className="px-4 py-2 bg-botticelli hover:bg-nepal text-chambray font-medium rounded-lg transition-colors duration-200 text-sm"
                    >
                      Select All
                    </button>
                    <button
                      onClick={deselectAllEnhanceRecs}
                      className="px-4 py-2 bg-cararra hover:bg-nepal text-falcon font-medium rounded-lg transition-colors duration-200 text-sm border border-nepal"
                    >
                      Deselect All
                    </button>
                    <button
                      onClick={() => {
                        setEnhanceStatus("idle");
                        setEnhanceRecommendations([]);
                        setSelectedEnhanceRecs(new Set());
                        setSelectedPlaylist(null);
                      }}
                      className="px-4 py-2 bg-cararra hover:bg-nepal text-falcon font-medium rounded-lg transition-colors duration-200 text-sm border border-nepal"
                    >
                      Back to Playlists
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                  {enhanceRecommendations.map((track) => {
                    const isSelected = selectedEnhanceRecs.has(track.uri);
                    return (
                      <div
                        key={track.uri}
                        onClick={() => toggleEnhanceRecommendation(track.uri)}
                        className={`cursor-pointer rounded-lg border-2 p-4 transition-all ${
                          isSelected
                            ? "border-chambray bg-botticelli"
                            : "border-nepal bg-cararra hover:border-chambray"
                        }`}
                      >
                        <div className="flex gap-3">
                          {track.image && (
                            <img
                              src={track.image}
                              alt={track.name}
                              className="w-16 h-16 rounded object-cover flex-shrink-0"
                            />
                          )}
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-chambray text-sm truncate">
                              {track.name}
                            </h3>
                            <p className="text-falcon text-xs truncate">
                              {track.artist}
                            </p>
                            <p className="text-nepal text-xs truncate mt-1">
                              {track.album}
                            </p>
                          </div>
                        </div>
                        <div className="mt-3 flex items-center justify-between">
                          <div
                            className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              isSelected
                                ? "bg-chambray border-chambray"
                                : "border-nepal"
                            }`}
                          >
                            {isSelected && (
                              <svg
                                className="w-3 h-3 text-cararra"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={3}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                            )}
                          </div>
                          {track.preview_url && (
                            <audio
                              controls
                              className="h-8 w-full max-w-[120px]"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <source
                                src={track.preview_url}
                                type="audio/mpeg"
                              />
                            </audio>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="flex flex-col items-center gap-2">
                  {selectedEnhanceRecs.size > 0 && (
                    <p className="text-sm text-nepal">
                      {selectedEnhanceRecs.size} track
                      {selectedEnhanceRecs.size !== 1 ? "s" : ""} selected
                    </p>
                  )}
                  <button
                    onClick={handleAddToPlaylist}
                    disabled={selectedEnhanceRecs.size === 0}
                    className="w-full bg-chambray hover:bg-waikawa disabled:bg-nepal disabled:cursor-not-allowed text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:transform-none shadow-md"
                  >
                    Add to Playlist
                  </button>
                </div>
              </div>
            )}

            {/* Enhance: Success */}
            {mode === "enhance" && enhanceStatus === "success" && (
              <div className="bg-white border-2 border-cashmere rounded-xl p-8 shadow-lg">
                <div className="text-center">
                  <div className="w-20 h-20 bg-cashmere rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg
                      className="w-10 h-10 text-chambray"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-chambray mb-3 font-display">
                    Playlist Enhanced!
                  </h2>
                  <p className="text-falcon mb-6">
                    {selectedEnhanceRecs.size} track
                    {selectedEnhanceRecs.size !== 1 ? "s" : ""} added to your
                    playlist.
                  </p>
                  <button
                    onClick={() => {
                      setEnhanceStatus("idle");
                      setEnhanceRecommendations([]);
                      setSelectedEnhanceRecs(new Set());
                      setSelectedPlaylist(null);
                    }}
                    className="bg-chambray hover:bg-waikawa text-cararra font-semibold py-3 px-8 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md"
                  >
                    Enhance Another Playlist
                  </button>
                </div>
              </div>
            )}

            {/* Enhance: Error */}
            {mode === "enhance" &&
              enhanceStatus === "error" &&
              enhanceError && (
                <div className="bg-white border-2 border-red-200 rounded-xl p-8 shadow-lg">
                  <div className="text-center">
                    <h2 className="text-2xl font-bold text-red-700 mb-3 font-display">
                      Oops!
                    </h2>
                    <p className="text-falcon mb-6">{enhanceError}</p>
                    <button
                      onClick={() => {
                        setEnhanceStatus("idle");
                        setEnhanceError(null);
                      }}
                      className="bg-chambray hover:bg-waikawa text-cararra font-semibold py-3 px-8 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              )}

            {/* Loading State */}
            {conversion.status === "loading" && (
              <div className="bg-botticelli border-2 border-nepal rounded-xl p-6 shadow-md">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="animate-spin rounded-full h-8 w-8 border-4 border-nepal border-t-chambray"></div>
                  </div>
                  <div>
                    <p className="text-chambray font-semibold">
                      Finding more bangers for you
                    </p>
                    <p className="text-falcon text-sm">
                      This may take a moment...
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations State */}
            {conversion.status === "recommendations" &&
              conversion.recommendations && (
                <div className="bg-white rounded-xl shadow-lg border border-botticelli p-8">
                  {conversion.recommendations.length > 0 ? (
                    <>
                      <div className="mb-6">
                        <h2 className="text-2xl font-bold text-chambray mb-2 font-display">
                          We found more bangers for you!
                        </h2>
                        <p className="text-falcon mb-4">
                          Based on your playlist, here are some tracks you might
                          vibe with. Select the ones you want to add:
                        </p>

                        {/* Select All / Deselect All Buttons */}
                        <div className="flex gap-3">
                          <button
                            onClick={selectAllRecommendations}
                            className="px-4 py-2 bg-botticelli hover:bg-nepal text-chambray font-medium rounded-lg transition-colors duration-200 text-sm"
                          >
                            Select All
                          </button>
                          <button
                            onClick={deselectAllRecommendations}
                            className="px-4 py-2 bg-cararra hover:bg-nepal text-falcon font-medium rounded-lg transition-colors duration-200 text-sm border border-nepal"
                          >
                            Deselect All
                          </button>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                        {conversion.recommendations.map((track) => {
                          const isSelected =
                            conversion.selectedRecommendations?.has(
                              track.uri
                            ) || false;
                          return (
                            <div
                              key={track.uri}
                              onClick={() => toggleRecommendation(track.uri)}
                              className={`cursor-pointer rounded-lg border-2 p-4 transition-all ${
                                isSelected
                                  ? "border-chambray bg-botticelli"
                                  : "border-nepal bg-cararra hover:border-chambray"
                              }`}
                            >
                              <div className="flex gap-3">
                                {track.image && (
                                  <img
                                    src={track.image}
                                    alt={track.name}
                                    className="w-16 h-16 rounded object-cover flex-shrink-0"
                                  />
                                )}
                                <div className="flex-1 min-w-0">
                                  <h3 className="font-semibold text-chambray text-sm truncate">
                                    {track.name}
                                  </h3>
                                  <p className="text-falcon text-xs truncate">
                                    {track.artist}
                                  </p>
                                  <p className="text-nepal text-xs truncate mt-1">
                                    {track.album}
                                  </p>
                                </div>
                              </div>
                              <div className="mt-3 flex items-center justify-between">
                                <div
                                  className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                                    isSelected
                                      ? "bg-chambray border-chambray"
                                      : "border-nepal"
                                  }`}
                                >
                                  {isSelected && (
                                    <svg
                                      className="w-3 h-3 text-cararra"
                                      fill="none"
                                      stroke="currentColor"
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={3}
                                        d="M5 13l4 4L19 7"
                                      />
                                    </svg>
                                  )}
                                </div>
                                {track.preview_url && (
                                  <audio
                                    controls
                                    className="h-8 w-full max-w-[120px]"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <source
                                      src={track.preview_url}
                                      type="audio/mpeg"
                                    />
                                  </audio>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      <div className="flex flex-col items-center gap-2">
                        {conversion.selectedRecommendations?.size || 0 > 0 ? (
                          <p className="text-sm text-nepal">
                            {conversion.selectedRecommendations?.size}{" "}
                            recommendation
                            {conversion.selectedRecommendations?.size !== 1
                              ? "s"
                              : ""}{" "}
                            selected
                          </p>
                        ) : null}
                        <button
                          onClick={handleCreatePlaylist}
                          className="w-full bg-chambray hover:bg-waikawa text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md"
                        >
                          Create Playlist
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="mb-6">
                        <h2 className="text-2xl font-bold text-chambray mb-2 font-display">
                          Ready to create your playlist!
                        </h2>
                        <p className="text-falcon mb-4">
                          We've matched your YouTube tracks to Spotify. Click
                          below to create your playlist.
                        </p>
                      </div>

                      <div className="flex flex-col items-center gap-2">
                        <button
                          onClick={handleCreatePlaylist}
                          className="w-full bg-chambray hover:bg-waikawa text-cararra font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md"
                        >
                          Create Playlist
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}

            {/* Success State */}
            {conversion.status === "success" && conversion.data && (
              <div className="bg-white border-2 border-cashmere rounded-xl p-8 shadow-lg">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 bg-cashmere rounded-full flex items-center justify-center flex-shrink-0">
                    <svg
                      className="w-6 h-6 text-falcon"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-chambray mb-2">
                      Conversion Successful!
                    </h3>
                    <p className="text-falcon mb-6">
                      Your playlist has been created on Spotify
                    </p>

                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">
                          Playlist Name
                        </p>
                        <p className="text-chambray font-semibold">
                          {conversion.data.playlist_name}
                        </p>
                      </div>
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">
                          Total Videos
                        </p>
                        <p className="text-chambray font-semibold">
                          {conversion.data.total_videos}
                        </p>
                      </div>
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">
                          Matched Tracks
                        </p>
                        <p className="text-chambray font-semibold">
                          {conversion.data.matched_tracks}
                        </p>
                      </div>
                      <div className="bg-cararra rounded-lg p-4">
                        <p className="text-nepal text-sm font-medium">
                          Failed Matches
                        </p>
                        <p className="text-falcon font-semibold">
                          {conversion.data.failed_matches}
                        </p>
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
                        <p className="font-semibold text-falcon mb-3">
                          Tracks that couldn't be matched:
                        </p>
                        <ul className="space-y-2">
                          {conversion.data.failed_match_titles.map(
                            (title, index) => (
                              <li
                                key={index}
                                className="text-sm text-nepal flex items-start gap-2"
                              >
                                <span className="text-pharlap">•</span>
                                <span>{title}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Error State */}
            {conversion.status === "error" && (
              <div className="bg-white border-2 border-pharlap rounded-xl p-8 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-pharlap rounded-full flex items-center justify-center flex-shrink-0">
                    <svg
                      className="w-6 h-6 text-cararra"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-2xl font-bold text-falcon mb-2">
                      Conversion Failed
                    </h3>
                    <p className="text-falcon mb-6 break-words overflow-wrap-anywhere whitespace-pre-line">
                      {conversion.error}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <button
                        onClick={() => setConversion({ status: "idle" })}
                        className="bg-falcon hover:bg-pharlap text-cararra font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-md"
                      >
                        Try Again
                      </button>
                      {conversion.matchedTracks &&
                        conversion.matchedTracks.length > 0 && (
                          <button
                            onClick={handleCreatePlaylist}
                            className="bg-chambray hover:bg-waikawa text-cararra font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-md"
                          >
                            Skip Recommendations & Create Playlist
                          </button>
                        )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Request Access Modal */}
      {showAccessRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-8">
            <h2 className="text-2xl font-bold text-chambray mb-4 font-display">
              Request Access
            </h2>
            <p className="text-falcon mb-6 text-sm">
              This app is in development mode. Submit your email and we'll add
              you within 24 hours.
            </p>

            {accessRequestStatus === "success" ? (
              <div className="bg-cashmere border-2 border-cashmere rounded-lg p-6 mb-6">
                <p className="text-falcon font-semibold mb-2">
                  Request Submitted!
                </p>
                <p className="text-falcon text-sm">{accessRequestMessage}</p>
                <button
                  onClick={() => {
                    setShowAccessRequest(false);
                    setAccessRequestStatus("idle");
                    setAccessRequestEmail("");
                    setAccessRequestName("");
                  }}
                  className="mt-4 w-full bg-chambray hover:bg-waikawa text-cararra font-semibold py-3 px-6 rounded-lg transition-all"
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={handleRequestAccess} className="space-y-4">
                <div>
                  <label
                    htmlFor="requestName"
                    className="block text-sm font-semibold text-falcon mb-2"
                  >
                    Name (Optional)
                  </label>
                  <input
                    type="text"
                    id="requestName"
                    value={accessRequestName}
                    onChange={(e) => setAccessRequestName(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-botticelli rounded-lg focus:ring-2 focus:ring-chambray focus:border-chambray outline-none transition-all bg-cararra text-falcon"
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <label
                    htmlFor="requestEmail"
                    className="block text-sm font-semibold text-falcon mb-2"
                  >
                    Email Address *
                  </label>
                  <input
                    type="email"
                    id="requestEmail"
                    value={accessRequestEmail}
                    onChange={(e) => setAccessRequestEmail(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-botticelli rounded-lg focus:ring-2 focus:ring-chambray focus:border-chambray outline-none transition-all bg-cararra text-falcon"
                    placeholder="your.email@example.com"
                    required
                  />
                </div>

                {accessRequestStatus === "error" && (
                  <div className="bg-pharlap bg-opacity-10 border border-pharlap rounded-lg p-3">
                    <p className="text-falcon text-sm">
                      {accessRequestMessage}
                    </p>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAccessRequest(false);
                      setAccessRequestStatus("idle");
                      setAccessRequestMessage("");
                    }}
                    className="flex-1 bg-nepal hover:bg-botticelli text-falcon font-semibold py-3 px-6 rounded-lg transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={accessRequestStatus === "loading"}
                    className="flex-1 bg-chambray hover:bg-waikawa disabled:bg-nepal disabled:cursor-not-allowed text-cararra font-semibold py-3 px-6 rounded-lg transition-all"
                  >
                    {accessRequestStatus === "loading"
                      ? "Submitting..."
                      : "Submit Request"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-8">
        <div className="border-t border-botticelli pt-8 text-center">
          <p className="text-nepal text-sm">
            built with blood sweat and tears (mostly tears)
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
