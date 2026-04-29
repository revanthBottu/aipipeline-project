import google.generativeai as genai
import json
import logging
import re

logger = logging.getLogger(__name__)

VALID_MOODS = [
    "happy", "chill", "intense", "focused", "moody",
    "relaxed", "sad", "excited", "nostalgic", "romantic",
]
VALID_GENRES = [
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave", "indie pop",
    "metal", "classical", "hip-hop", "blues", "r&b", "edm", "folk",
    "soul", "electronic", "country",
]

_PARSE_PROMPT = """You are a music taste analyst. Extract music preferences from the user's vibe description.

User's vibe: "{user_input}"

Available moods: {moods}
Available genres: {genres}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "mood": "<one mood from the list above>",
  "genre": "<one genre from the list above>",
  "energy": <float 0.0-1.0>,
  "tempo_bpm": <integer 60-180>,
  "valence": <float 0.0-1.0, where 0=dark/negative and 1=bright/positive>,
  "danceability": <float 0.0-1.0>,
  "acousticness": <float 0.0-1.0>,
  "avoid_moods": [<list of moods to avoid, can be empty>],
  "avoid_genres": [<list of genres to avoid, can be empty>],
  "interpretation": "<one sentence summarizing how you interpreted the vibe>"
}}"""

_RANK_PROMPT = """You are a music recommendation expert. The user wants: "{user_input}"

Select and rank the BEST 5 songs from these candidates that match the vibe:
{candidates}

Return ONLY a JSON array of exactly 5 objects (no markdown, no extra text):
[
  {{
    "id": <integer song id>,
    "title": "<song title>",
    "artist": "<artist name>",
    "confidence": <integer 0-100, how well this fits the vibe>,
    "explanation": "<1-2 sentences why this song fits>"
  }}
]

Rank from best match (index 0) to worst match. Be specific in explanations."""


def _extract_json(text: str) -> str:
    text = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return text


def parse_vibe(user_input: str, api_key: str) -> dict:
    """Call Gemini to convert a natural-language vibe into structured music preferences."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = _PARSE_PROMPT.format(
        user_input=user_input,
        moods=", ".join(VALID_MOODS),
        genres=", ".join(VALID_GENRES),
    )

    logger.info("Parsing vibe: '%.50s'", user_input)
    response = model.generate_content(prompt)
    raw = response.text.strip()
    logger.debug("Gemini parse raw response: %s", raw)

    parsed = json.loads(_extract_json(raw))
    logger.info(
        "Parsed vibe — mood=%s genre=%s energy=%s",
        parsed.get("mood"),
        parsed.get("genre"),
        parsed.get("energy"),
    )
    return parsed


def rank_songs(user_input: str, parsed_vibe: dict, candidates: list, api_key: str) -> list:
    """Call Gemini to re-rank RAG candidates and generate per-song explanations."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    candidates_text = "\n".join(
        f"ID:{s['id']} | {s['title']} by {s['artist']} | "
        f"genre:{s['genre']} mood:{s['mood']} energy:{s['energy']} "
        f"bpm:{s['tempo_bpm']} valence:{s['valence']}"
        for s in candidates
    )

    prompt = _RANK_PROMPT.format(user_input=user_input, candidates=candidates_text)

    logger.info("Ranking %d candidates with Gemini", len(candidates))
    response = model.generate_content(prompt)
    raw = response.text.strip()
    logger.debug("Gemini rank raw response: %s", raw)

    ranked = json.loads(_extract_json(raw))
    top5 = ranked[:5]
    logger.info(
        "Ranked songs — top confidence: %s%%",
        top5[0].get("confidence") if top5 else "N/A",
    )
    return top5
