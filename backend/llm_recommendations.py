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

        logger.info(f"Raw LLM response: {content[:500]}")

        # Parse JSON response
        try:
            recommendations = json.loads(content)
            logger.info(f"Parsed JSON type: {type(recommendations)}")

            # Handle both array and object with array
            if isinstance(recommendations, dict):
                # Try multiple possible keys
                for key in ['recommendations', 'songs', 'tracks', 'playlist']:
                    if key in recommendations:
                        recommendations = recommendations[key]
                        logger.info(f"Found recommendations under key '{key}'")
                        break
                # If still a dict, might be the recommendations themselves
                if isinstance(recommendations, dict) and 'name' not in recommendations:
                    logger.error(f"Unexpected dict structure: {list(recommendations.keys())}")
                    raise Exception(f"Could not find recommendations array in response. Keys: {list(recommendations.keys())}")

            # Handle nested arrays or mixed content (e.g., example + actual recommendations)
            if isinstance(recommendations, list):
                # Flatten nested arrays and filter out non-dict items
                flattened = []
                for item in recommendations:
                    if isinstance(item, list):
                        # Nested array - flatten it
                        flattened.extend([i for i in item if isinstance(i, dict) and 'name' in i and 'artist' in i])
                    elif isinstance(item, dict) and 'name' in item and 'artist' in item:
                        # Valid recommendation dict
                        # Skip example items like {"name": "Song Title", "artist": "Artist Name"}
                        if item['name'] != "Song Title" and item['artist'] != "Artist Name":
                            flattened.append(item)

                recommendations = flattened
                logger.info(f"Flattened to {len(recommendations)} valid recommendations")

            if isinstance(recommendations, list) and len(recommendations) > 0:
                logger.info(f"✓ Groq returned {len(recommendations)} recommendations")
                return recommendations[:15]
            else:
                logger.error(f"Invalid recommendations format. Type: {type(recommendations)}, Length: {len(recommendations) if isinstance(recommendations, list) else 'N/A'}")
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
