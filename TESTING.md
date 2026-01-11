# Testing musik-ai

This guide will walk you through testing the musik-ai application locally.

## Prerequisites

Before testing, make sure you have:
1. **YouTube API Key** - Get from [Google Cloud Console](https://console.cloud.google.com/)
2. **Spotify Client ID & Secret** - Get from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
3. **HashiCorp Vault** installed - `brew install vault` (macOS) or download from [vaultproject.io](https://www.vaultproject.io/downloads)

## Setup Steps

### 1. Set Environment Variables

```bash
# Export your API credentials
export YOUTUBE_API_KEY="your_youtube_api_key_here"
export SPOTIFY_CLIENT_ID="your_spotify_client_id_here"
export SPOTIFY_CLIENT_SECRET="your_spotify_client_secret_here"
```

### 2. Start HashiCorp Vault

```bash
# Run the Vault initialization script
./start_vault.sh

# This will:
# - Start Vault in dev mode
# - Store your API credentials securely
# - Export VAULT_TOKEN for the backend
```

**Important:** Keep this terminal window open! The script will output something like:
```
export VAULT_TOKEN='hvs.xxxxxx'
```

Copy and run that export command in your terminal.

### 3. Start the Backend

Open a new terminal window:

```bash
cd /Users/hajarassim/Documents/projects/musik-ai

# Activate virtual environment
source musik-env/bin/activate

# Make sure VAULT_TOKEN is set (from step 2)
echo $VAULT_TOKEN  # Should show the token

# Start the FastAPI server
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8888
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8888
```

### 4. Start the Frontend

Open another new terminal window:

```bash
cd /Users/hajarassim/Documents/projects/musik-ai/frontend

# Start the Vite dev server
npm run dev
```

You should see:
```
VITE v7.x.x  ready in xxx ms

œ  Local:   http://localhost:5173/
```

### 5. Configure Spotify Redirect URI

Before testing OAuth, add the redirect URI to your Spotify app:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click on your app
3. Click "Edit Settings"
4. Under "Redirect URIs", add: `http://127.0.0.1:8888/callback`
5. Click "Save"

## Testing the Application

### Test Flow

1. **Open the app** - Navigate to `http://localhost:5173/` in your browser

2. **Login Page**
   - Enter a user ID (e.g., "test-user")
   - Click "Login with Spotify"
   - You'll be redirected to Spotify
   - Authorize the app
   - You'll be redirected back to the callback URL

3. **After OAuth (for testing)**
   - Since the OAuth callback doesn't redirect back to the frontend yet, click "Back" in your browser
   - Click "Skip (for testing)" button to bypass OAuth for now
   - This simulates being authenticated

4. **Convert a Playlist**
   - Enter your user ID again (same as step 2)
   - Enter a YouTube playlist ID (find one on YouTube - look for `list=XXX` in the URL)
   - Enter a name for your Spotify playlist
   - Click "Convert Playlist"
   - Wait for the conversion (you'll see a loading spinner)

5. **View Results**
   - See how many tracks matched
   - See which tracks failed to match
   - Click "Open in Spotify" to view your new playlist

## Testing Tips

### Finding a YouTube Playlist ID

1. Go to any YouTube playlist
2. Look at the URL: `https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf`
3. Copy everything after `list=` ’ `PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf`

### Testing with Different Scenarios

- **Small playlist** (5-10 songs) - Quick test
- **Large playlist** (50+ songs) - Tests pagination
- **Music playlist** - Best match rate
- **Non-music playlist** - See error handling

### Common Issues

**"VAULT_TOKEN not set"**
- Make sure you ran `./start_vault.sh` and exported the token
- Check with `echo $VAULT_TOKEN`

**"CORS error" in browser console**
- Make sure backend is running on port 8888
- Check CORS middleware is configured

**"No matching tracks found"**
- YouTube playlist might be private
- Playlist might contain non-music videos
- Check backend logs for errors

**"User not authorized"**
- Complete the OAuth flow first
- Or use the "Skip" button for testing

## Checking Logs

### Backend Logs
Watch the terminal where you started the backend:
```
INFO:     127.0.0.1:xxxxx - "GET /convert?..." 200 OK
```

### Frontend Logs
Open browser DevTools (F12) ’ Console tab to see API calls and errors

## Next Steps

Once testing is complete, you can:
1. Improve the OAuth callback to redirect back to frontend
2. Add proper state management
3. Deploy to production
4. Add more features!
