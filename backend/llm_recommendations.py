"""
LLM-based music recommendations using Groq
"""
import requests
import json
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def create_recommendation_prompt(tracks: List[Dict[str, str]]) -> str:
    """
    Create a well-crafted prompt for music recommendations

    Args:
        tracks: List of dicts with 'name' and 'artist' keys
    """
    track_list = "\n".join([f"- {track['name']} by {track['artist']}" for track in tracks[:10]])

    prompt = f"""You are an expert music curator with excellent taste. Based on this playlist, recommend 15 songs that would fit perfectly.

PLAYLIST TRACKS:
{track_list}

INSTRUCTIONS:
1. Recommend songs that match the vibe, genre, and energy of these tracks
2. Mix popular hits with hidden gems
3. Keep the same mood and era (if applicable)
4. Ensure variety - don't recommend too many songs from the same artist
5. Only recommend real, existing songs

OUTPUT FORMAT (CRITICAL - FOLLOW EXACTLY):
Return ONLY a JSON array, nothing else. Each song should be an object with "name" and "artist" fields.

Example format:
[
  {{"name": "Song Title", "artist": "Artist Name"}},
  {{"name": "Another Song", "artist": "Another Artist"}}
]

Now provide 15 recommendations:"""

    return prompt


def get_groq_recommendations(tracks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Get recommendations from Groq API

    Returns:
        List of dicts with 'name' and 'artist' keys

    Raises:
        Exception if Groq API fails
    """
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not set. Get a free API key from https://console.groq.com")

    try:
        logger.info(f"Requesting recommendations from Groq ({GROQ_MODEL})...")

        prompt = create_recommendation_prompt(tracks)

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert music curator. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )

        if response.status_code != 200:
            error_detail = response.json() if response.text else {}
            logger.error(f"Groq API error: {response.status_code} - {error_detail}")
            raise Exception(f"Groq API returned {response.status_code}: {error_detail.get('error', {}).get('message', 'Unknown error')}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON response
        try:
            recommendations = json.loads(content)
            # Handle both array and object with array
            if isinstance(recommendations, dict):
                recommendations = recommendations.get("recommendations", recommendations.get("songs", []))
            if isinstance(recommendations, list) and len(recommendations) > 0:
                logger.info(f"✓ Groq returned {len(recommendations)} recommendations")
                return recommendations[:15]
            else:
                raise Exception("Groq returned empty or invalid recommendations")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq JSON response: {e}")
            logger.error(f"Raw response: {content[:500]}")
            raise Exception(f"Could not parse LLM response as JSON: {e}")

    except Exception as e:
        logger.error(f"Groq request failed: {str(e)}")
        raise


def get_llm_recommendations(tracks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Get recommendations using Groq LLM

    Args:
        tracks: List of dicts with 'name' and 'artist' keys

    Returns:
        List of dicts with 'name' and 'artist' keys

    Raises:
        Exception if API fails
    """
    if not tracks:
        raise ValueError("No tracks provided for recommendations")

    return get_groq_recommendations(tracks)
