# musik-ai 🫐

A web app for converting YouTube playlists to Spotify and discovering new music through AI-powered recommendations.

**Live Demo:** https://musik-ai-amber.vercel.app/

## Why I Built This

I wanted to solve a personal problem: moving my music between platforms and discovering similar tracks without manually searching. This project gave me hands-on experience building a full-stack application with OAuth flows, external APIs, and LLM integration. It also taught me about the challenges of working with third-party APIs and adapting when those APIs change their policies.

## Features

- Convert YouTube playlists to Spotify
- Get AI-powered music recommendations for existing Spotify playlists
- OAuth authentication with Spotify
- Track matching between platforms

## Tech Stack

**Frontend:** React, TypeScript, Vite, TailwindCSS
**Backend:** Python, FastAPI, Spotipy
**APIs:** Spotify Web API, YouTube Data API v3, Groq (LLM)
**Hosting:** Vercel (frontend), Render (backend)

## Current Limitations

In November 2024, Spotify [deprecated key API endpoints](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api) for AI applications, including:
- Audio analysis (tempo, key, time signature)
- Audio features (danceability, energy, valence)
- Track preview URLs

This means the recommendation system now relies entirely on LLM-based text analysis instead of audio feature matching. The recommendations are less accurate than they could have been with full API access.

Other limitations:
- YouTube API has daily quota limits
- Some YouTube videos don't have matching tracks on Spotify
- LLM recommendations can occasionally suggest non-existent tracks
- Render free tier spins down after 15 minutes of inactivity (first request may be slow)

## What I Learned

- **OAuth flows:** Implementing Spotify's OAuth 2.0 authorization code flow
- **API integration:** Working with multiple external APIs (Spotify, YouTube, Groq)
- **LLM prompting:** Crafting effective prompts for music recommendations
- **Deployment:** Setting up CI/CD with free hosting platforms
- **Error handling:** Managing API rate limits, timeouts, and edge cases
- **Adapting to change:** Pivoting the recommendation system when Spotify deprecated key features
- **Full-stack development:** Building and deploying a complete web application end-to-end

## Local Development

1. Clone the repository
2. Set up environment variables (see `.env.example` files in `backend/` and `frontend/`)
3. Install dependencies:
   - Backend: `cd backend && pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`
4. Run both servers:
   - Backend: `uvicorn main:app --reload --port 8888`
   - Frontend: `npm run dev`

See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment instructions.

## License

MIT
