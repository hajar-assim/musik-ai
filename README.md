# musik-ai

> Convert YouTube playlists to Spotify and discover new music with AI-powered recommendations

[![Live Demo](https://img.shields.io/badge/demo-live-success)](HOSTED_LINK_HERE)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎵 Features

- **Convert Playlists**: Transform YouTube playlists into Spotify playlists
- **AI Recommendations**: Get personalized song suggestions powered by Groq LLM
- **Enhance Existing Playlists**: Discover new tracks that match your Spotify playlists
- **Smart Matching**: Automatically finds songs on Spotify based on YouTube video titles
- **OAuth Integration**: Secure Spotify authentication

## 🚀 Live Demo

**[Try it here: HOSTED_LINK_HERE](HOSTED_LINK_HERE)**

## ⚠️ Note on Spotify API Changes

In November 2024, Spotify [deprecated key API features](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api) for AI applications, including:
- Audio analysis endpoints
- Audio features (danceability, energy, tempo)
- Track previews for AI use cases

As a result, this project now relies on LLM-based recommendations using Groq's API instead of Spotify's audio feature analysis.

## 🛠️ Tech Stack

### Frontend
- React + TypeScript
- Vite
- TailwindCSS
- Axios

### Backend
- Python 3.11
- FastAPI
- Spotipy (Spotify API wrapper)
- YouTube Data API v3
- Groq API (LLM recommendations)

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Spotify Developer Account
- Google Cloud Project (for YouTube API)
- Groq API Key

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/musik-ai.git
cd musik-ai/backend
```

2. Create virtual environment:
```bash
python -m venv musik-env
source musik-env/bin/activate  # On Windows: musik-env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file (use `.env.example` as template):
```bash
cp .env.example .env
```

5. Add your credentials to `.env`:
```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://127.0.0.1:8888/callback
FRONTEND_URL=http://localhost:5173
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
SPOTIFY_SCOPE=user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private
```

6. Run the backend:
```bash
uvicorn main:app --reload --port 8888
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd ../frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Update `.env` with backend URL:
```env
VITE_API_BASE_URL=http://127.0.0.1:8888
```

5. Run the frontend:
```bash
npm run dev
```

6. Open http://localhost:5173 in your browser

## 🚢 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on deploying to:
- **Backend**: Render (free tier)
- **Frontend**: Vercel (free tier)

Both platforms offer free hosting with automatic deployments from GitHub.

## 🔑 Getting API Keys

### Spotify API
1. Go to https://developer.spotify.com/dashboard
2. Create an app
3. Copy Client ID and Client Secret
4. Add redirect URI: `http://127.0.0.1:8888/callback` (or your production URL)

### YouTube API
1. Go to https://console.cloud.google.com
2. Create a project
3. Enable YouTube Data API v3
4. Create credentials (API Key)

### Groq API
1. Go to https://console.groq.com
2. Sign up for free account
3. Create API key
4. Copy the key to your `.env`

## 📝 Usage

### Convert YouTube Playlist

1. Connect your Spotify account
2. Paste a YouTube playlist URL or ID
3. Click "Convert Playlist"
4. Optionally get AI recommendations
5. Select tracks to add
6. Create the playlist on Spotify

### Enhance Existing Playlist

1. Connect your Spotify account
2. Select "Enhance Playlist" mode
3. Choose a playlist from your library
4. Get AI-powered recommendations
5. Select and add tracks to your playlist

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Spotify for their API (despite the recent restrictions)
- Groq for providing fast LLM inference
- YouTube Data API for playlist data
- The open-source community

## ⚡ Known Limitations

- Spotify free tier on Render spins down after 15 minutes of inactivity (first request may be slow)
- YouTube API has daily quota limits
- LLM recommendations may occasionally suggest non-existent tracks
- Some YouTube videos may not have matching tracks on Spotify

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ and way too much coffee
