import requests
import json
import logging
from typing import List, Dict
from app.config import settings

logger = logging.getLogger(__name__)


def _create_prompt(tracks: List[Dict[str, str]]) -> str:
    """Create music curator prompt for LLM with enhanced genre awareness"""
    track_list = "\n".join([f"- {t['name']} by {t['artist']}" for t in tracks[:15]])

    return f"""You are an expert music curator with deep knowledge of genres, subgenres, and music similarity.

ANALYZE THIS PLAYLIST:
{track_list}

CRITICAL REQUIREMENTS:
1. **GENRE CONSISTENCY**: First identify the dominant genre(s) of the playlist (e.g., hip-hop, indie rock, electronic, R&B, pop, etc.)
2. **STAY IN GENRE**: ALL recommendations MUST be from the same genre or closely related subgenres
3. **REAL SONGS ONLY**: Only recommend songs that actually exist on Spotify
4. **SIMILAR ARTISTS**: Prioritize artists with similar sound/style to those in the playlist
5. **ERA CONSISTENCY**: Match the time period (90s, 2000s, 2010s, modern, etc.)
6. **ENERGY MATCH**: Match the energy level (chill, upbeat, aggressive, mellow)
7. **ARTIST DIVERSITY**: Maximum 2 songs per artist
8. **POPULARITY MIX**: Include both popular and lesser-known tracks

ANALYSIS PROCESS:
1. Identify the primary genre(s)
2. Identify the mood/vibe (upbeat, melancholic, aggressive, chill, etc.)
3. Identify similar artists in that genre
4. Find tracks that match BOTH genre and mood

OUTPUT FORMAT:
Return ONLY a JSON array with objects containing "name" and "artist" fields.
DO NOT include explanations, reasoning, or any text outside the JSON.

Example: [{{"name": "Song Name", "artist": "Artist Name"}}]

Now provide exactly 15 recommendations that match the genre and vibe:"""


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
        logger.info(f"Requesting recommendations from Groq ({settings.GROQ_MODEL})")

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
                    {"role": "user", "content": _create_prompt(tracks)}
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
