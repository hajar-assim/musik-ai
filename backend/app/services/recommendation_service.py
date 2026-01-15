import requests
import json
import logging
import random
from typing import List, Dict
from app.config import settings

logger = logging.getLogger(__name__)


def _create_prompt(tracks: List[Dict[str, str]]) -> str:
    """Create music curator prompt for LLM with enhanced genre awareness"""
    # Use the last 15 tracks (most recently added) to capture user's current taste
    recent_tracks = tracks[-15:] if len(tracks) > 15 else tracks

    track_list = "\n".join([f"- {t['name']} by {t['artist']}" for t in recent_tracks])

    return f"""You are a professional music curator and AI recommender expert. Your goal is to recommend songs that **closely match the input playlist** in genre, mood, era, and artist style. Focus on **similarity and hidden gems** over popularity.

INPUT PLAYLIST:
{track_list}

RECOMMENDATION RULES (STRICTLY FOLLOW):

1. PRIORITIZE SIMILARITY: All recommendations MUST closely match:
   - Genre / subgenre of the playlist (e.g., indie rock, alternative hip-hop, electronic, synthwave)
   - Mood / energy (e.g., chill, upbeat, melancholic, aggressive)
   - Era / decade (e.g., 90s, 2000s, 2010s, modern)

2. REAL SONGS ONLY: Only suggest songs that exist on Spotify. Avoid made-up or non-existent tracks.

3. SIMILAR ARTISTS: Prefer artists who:
   - Are stylistically closest to artists in the playlist
   - Have a similar sound, instrumentation, or vocal style
   - Include lesser-known artists if they match the vibe

4. ENERGY MATCH: Match the energy level and overall vibe of the playlist tracks.

5. ARTIST DIVERSITY: No more than **2 songs per artist**.

6. HIDDEN GEMS PREFERENCE:
   - Prioritize lesser-known songs over chart-topping hits
   - Hidden gems = songs not in Billboard Top 100 or Spotify Top 50 playlists
   - Only include popular songs if no suitable hidden gem exists

7. EXAMPLES OF SIMILAR HIDDEN GEM SONGS (to match playlist style):
   - "Reptilia" by The Strokes (if playlist is early-2000s indie rock)
   - "Nights" by Frank Ocean (if playlist is alternative R&B)
   - "Midnight City" by M83 (if playlist is synthwave/electronic)

OUTPUT FORMAT (STRICT):
Return exactly **15 songs** in a JSON array.
Each object must have:
- "name": song title
- "artist": artist name

Do NOT include explanations, reasoning, or any text outside the JSON.

Example output:
[
  {{"name": "Song Name", "artist": "Artist Name"}},
  {{"name": "Another Song", "artist": "Another Artist"}}
]

NOW: Provide **exactly 15 song recommendations** that match the playlist style, mood, era, and energy, prioritizing hidden gems over popular hits."""


def _parse_llm_response(content: str) -> List[Dict[str, str]]:
    """Parse and flatten LLM JSON response"""
    recommendations = json.loads(content)

    if isinstance(recommendations, dict):
        for key in ['recommendations', 'songs', 'tracks', 'playlist']:
            if key in recommendations:
                recommendations = recommendations[key]
                break

    if isinstance(recommendations, list):
        flattened = []
        for item in recommendations:
            if isinstance(item, list):
                flattened.extend([i for i in item if isinstance(i, dict) and 'name' in i and 'artist' in i])
            elif isinstance(item, dict) and 'name' in item and 'artist' in item:
                if item['name'] != "Song Title" and item['artist'] != "Artist Name":
                    flattened.append(item)
        recommendations = flattened

    if not isinstance(recommendations, list) or len(recommendations) == 0:
        raise ValueError("Empty or invalid recommendations")

    return recommendations[:15]


def get_llm_recommendations(tracks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Get music recommendations from Groq LLM"""
    if not tracks:
        raise ValueError("No tracks provided")

    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set. Get one from https://console.groq.com")

    try:
        prompt = _create_prompt(tracks)
        logger.info(f"Requesting recommendations from Groq ({settings.GROQ_MODEL})")
        logger.info(f"Full prompt:\n{prompt}")

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert music curator with encyclopedic knowledge of music genres, artists, and songs. You specialize in finding songs that match specific genres and vibes. You only recommend real, existing songs that can be found on Spotify. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )

        if response.status_code != 200:
            error = response.json() if response.text else {}
            raise Exception(f"Groq API error {response.status_code}: {error.get('error', {}).get('message', 'Unknown')}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        logger.debug(f"LLM response: {content[:200]}...")

        recommendations = _parse_llm_response(content)
        logger.info(f"✓ Got {len(recommendations)} recommendations")

        return recommendations

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise Exception(f"Invalid LLM response format: {e}")
    except Exception as e:
        logger.error(f"Recommendation request failed: {e}")
        raise
