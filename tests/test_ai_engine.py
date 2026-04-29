import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai_engine import parse_vibe, rank_songs, _extract_json

# ── Shared fixtures ────────────────────────────────────────────────────────────

MOCK_PARSE_JSON = {
    "mood": "chill",
    "genre": "lofi",
    "energy": 0.30,
    "tempo_bpm": 80,
    "valence": 0.40,
    "danceability": 0.50,
    "acousticness": 0.70,
    "avoid_moods": [],
    "avoid_genres": [],
    "interpretation": "A calm late-night coding session with soft lofi beats.",
}

MOCK_RANK_JSON = [
    {"id": 1,  "title": "Night Drift",   "artist": "Lo-Fi Lab",  "confidence": 92, "explanation": "Perfect lofi chill."},
    {"id": 4,  "title": "Mellow Keys",   "artist": "Solo Piano", "confidence": 85, "explanation": "Ambient and soft."},
    {"id": 7,  "title": "Rainy Focus",   "artist": "Lo Wave",    "confidence": 78, "explanation": "Great for focus."},
    {"id": 2,  "title": "Coffee Haze",   "artist": "Drift Co.",  "confidence": 71, "explanation": "Warm background."},
    {"id": 9,  "title": "Study Hall",    "artist": "Beats Lab",  "confidence": 65, "explanation": "Steady lofi energy."},
]

CANDIDATES = [
    {"id": i, "title": f"Song {i}", "artist": f"Artist {i}", "genre": "lofi",
     "mood": "chill", "energy": 0.30, "tempo_bpm": 80, "valence": 0.40}
    for i in range(1, 16)
]


def _mock_client(response_text: str):
    """Build a mock genai.Client whose models.generate_content returns response_text."""
    mock_resp = MagicMock()
    mock_resp.text = response_text
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_resp
    mock_client = MagicMock()
    mock_client.models = mock_models
    return mock_client


# ── parse_vibe tests ───────────────────────────────────────────────────────────

@patch("src.ai_engine.genai")
def test_parse_vibe_returns_dict_with_required_keys(mock_genai):
    mock_genai.Client.return_value = _mock_client(json.dumps(MOCK_PARSE_JSON))
    result = parse_vibe("late night coding session", "fake-key")
    assert isinstance(result, dict)
    for key in ("mood", "genre", "energy", "tempo_bpm", "valence", "danceability", "acousticness"):
        assert key in result, f"Missing key: {key}"


@patch("src.ai_engine.genai")
def test_parse_vibe_energy_in_valid_range(mock_genai):
    mock_genai.Client.return_value = _mock_client(json.dumps(MOCK_PARSE_JSON))
    result = parse_vibe("chill vibes", "fake-key")
    assert 0.0 <= result["energy"] <= 1.0


@patch("src.ai_engine.genai")
def test_parse_vibe_handles_markdown_wrapped_json(mock_genai):
    wrapped = f"```json\n{json.dumps(MOCK_PARSE_JSON)}\n```"
    mock_genai.Client.return_value = _mock_client(wrapped)
    result = parse_vibe("chill vibes", "fake-key")
    assert result["mood"] == "chill"


@patch("src.ai_engine.genai")
def test_parse_vibe_raises_on_invalid_json(mock_genai):
    mock_genai.Client.return_value = _mock_client("this is not json at all")
    with pytest.raises(Exception):
        parse_vibe("broken response", "fake-key")


# ── rank_songs tests ───────────────────────────────────────────────────────────

@patch("src.ai_engine.genai")
def test_rank_songs_returns_five_results(mock_genai):
    mock_genai.Client.return_value = _mock_client(json.dumps(MOCK_RANK_JSON))
    result = rank_songs("chill lofi vibes", MOCK_PARSE_JSON, CANDIDATES, "fake-key")
    assert len(result) == 5


@patch("src.ai_engine.genai")
def test_rank_songs_all_have_confidence_scores(mock_genai):
    mock_genai.Client.return_value = _mock_client(json.dumps(MOCK_RANK_JSON))
    result = rank_songs("chill lofi vibes", MOCK_PARSE_JSON, CANDIDATES, "fake-key")
    for song in result:
        assert "confidence" in song
        assert 0 <= song["confidence"] <= 100


@patch("src.ai_engine.genai")
def test_rank_songs_all_have_explanations(mock_genai):
    mock_genai.Client.return_value = _mock_client(json.dumps(MOCK_RANK_JSON))
    result = rank_songs("chill lofi vibes", MOCK_PARSE_JSON, CANDIDATES, "fake-key")
    for song in result:
        assert "explanation" in song
        assert len(song["explanation"]) > 0


@patch("src.ai_engine.genai")
def test_rank_songs_sorted_descending_by_confidence(mock_genai):
    mock_genai.Client.return_value = _mock_client(json.dumps(MOCK_RANK_JSON))
    result = rank_songs("chill lofi vibes", MOCK_PARSE_JSON, CANDIDATES, "fake-key")
    confidences = [r["confidence"] for r in result]
    assert confidences == sorted(confidences, reverse=True)


# ── _extract_json helper tests ─────────────────────────────────────────────────

def test_extract_json_from_plain_object():
    text = '{"mood": "chill", "energy": 0.3}'
    assert json.loads(_extract_json(text)) == {"mood": "chill", "energy": 0.3}


def test_extract_json_from_markdown_block():
    text = '```json\n{"key": "value"}\n```'
    assert json.loads(_extract_json(text)) == {"key": "value"}


def test_extract_json_from_array():
    text = '[{"id": 1}, {"id": 2}]'
    parsed = json.loads(_extract_json(text))
    assert len(parsed) == 2


def test_extract_json_strips_surrounding_text():
    text = 'Here is the result:\n{"mood": "happy"}\nDone.'
    assert json.loads(_extract_json(text)) == {"mood": "happy"}
