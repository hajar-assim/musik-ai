import requests
import json
import logging
from typing import List, Dict
from app.config import settings

logger = logging.getLogger(__name__)


def _create_prompt(tracks: List[Dict[str, str]]) -> str:
    """Create music curator prompt for LLM"""
    track_list = "\n".join([f"- {t['name']} by {t['artist']}" for t in tracks[:10]])

    return f"""You are an expert music curator. Based on this playlist, recommend 15 songs that fit perfectly.

PLAYLIST TRACKS:
{track_list}

INSTRUCTIONS:
1. Match the vibe, genre, and energy
2. Mix popular hits with hidden gems
3. Keep consistent mood and era
4. Ensure variety - limit songs per artist
5. Only recommend real, existing songs

OUTPUT FORMAT:
Return ONLY a JSON array with objects containing "name" and "artist" fields.

Example: [{{"name": "Track", "artist": "Artist"}}]

Now provide 15 recommendations:"""


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
                    {"role": "system", "content": "You are an expert music curator. Always respond with valid JSON only."},
                    {"role": "user", "content": _create_prompt(tracks)}
                ],
                "temperature": 0.7,
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
