# Deployment Guide

This guide covers deploying musik-ai to free hosting platforms.

## Architecture

- **Frontend**: Vercel (free, unlimited)
- **Backend**: Render (free, 750 hours/month)

## Prerequisites

1. GitHub account
2. Render account (sign up at render.com)
3. Vercel account (sign up at vercel.com)
4. Your environment variables ready:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `GROQ_API_KEY`

## Step 1: Deploy Backend to Render

1. **Push code to GitHub** (if not already done):
   ```bash
   git push origin main
   ```

2. **Go to Render Dashboard**: https://dashboard.render.com

3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `musik-ai` repository

4. **Configure Service**:
   - **Name**: `musik-ai-backend`
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: Leave empty (render.yaml handles this)
   - **Runtime**: Python 3
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

5. **Add Environment Variables** in Render dashboard:
   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=llama-3.3-70b-versatile
   SPOTIFY_SCOPE=user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private
   REDIRECT_URI=https://your-backend-url.onrender.com/callback
   FRONTEND_URL=https://your-frontend-url.vercel.app
   ```

   **Important**: You'll need to update `REDIRECT_URI` and `FRONTEND_URL` after deployment.

6. **Deploy**: Click "Create Web Service"

7. **Note your backend URL**: It will be something like `https://musik-ai-backend.onrender.com`

8. **Update Spotify App Settings**:
   - Go to https://developer.spotify.com/dashboard
   - Select your app
   - Click "Settings"
   - Add Redirect URI: `https://musik-ai-backend.onrender.com/callback`
   - Save

9. **Update Render Environment Variables**:
   - Go back to Render dashboard → Your service → Environment
   - Update `REDIRECT_URI` to `https://musik-ai-backend.onrender.com/callback`
   - Update `FRONTEND_URL` to your Vercel URL (after Step 2)

## Step 2: Deploy Frontend to Vercel

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard

2. **Import Project**:
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Select the `musik-ai` repository

3. **Configure Project**:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

4. **Add Environment Variable**:
   - Click "Environment Variables"
   - Add: `VITE_API_BASE_URL` = `https://musik-ai-backend.onrender.com` (your Render URL)

5. **Deploy**: Click "Deploy"

6. **Note your frontend URL**: It will be something like `https://musik-ai.vercel.app`

7. **Update Render Backend Environment Variables**:
   - Go back to Render dashboard → Your service → Environment
   - Update `FRONTEND_URL` to your Vercel URL
   - Save changes (this will redeploy)

## Step 3: Verify Deployment

1. **Visit your frontend**: `https://your-app.vercel.app`
2. **Test OAuth flow**: Click "Connect with Spotify"
3. **Test playlist conversion**: Try converting a YouTube playlist
4. **Test recommendations**: Try the Enhance Playlist feature

## Troubleshooting

### Backend Issues

- **Check logs**: Render Dashboard → Your service → Logs
- **Common issues**:
  - Missing environment variables
  - Wrong `REDIRECT_URI` (must match Spotify app settings)
  - CORS errors (check `FRONTEND_URL` is correct)

### Frontend Issues

- **Check deployment logs**: Vercel Dashboard → Your project → Deployments → View logs
- **Common issues**:
  - Wrong `VITE_API_BASE_URL`
  - CORS errors (backend not allowing frontend origin)

### Free Tier Limitations

**Render Free Tier**:
- 750 hours/month (roughly 31 days if always on)
- Spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds

**Vercel Free Tier**:
- Unlimited deployments
- 100GB bandwidth/month
- No cold starts

## Automatic Deployments

Both platforms automatically redeploy when you push to `main`:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

- **Render**: Auto-deploys backend
- **Vercel**: Auto-deploys frontend

## Costs

- **Render**: Free (750 hours/month)
- **Vercel**: Free (unlimited)
- **Groq API**: Free tier (rate limits apply)
- **Spotify API**: Free

**Total Cost**: $0/month 🎉

## Notes

- Keep your environment variables secure (never commit them)
- Render free tier spins down after inactivity (first request may be slow)
- Consider upgrading if you need 24/7 uptime
