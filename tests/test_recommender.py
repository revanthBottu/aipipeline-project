import pytest
from src.recommender import score_song, retrieve_candidates

SONGS = [
    {
        "id": 1, "title": "Night Drift", "artist": "Lo-Fi Lab", "genre": "lofi", "mood": "chill",
        "energy": 0.30, "tempo_bpm": 78, "valence": 0.40, "danceability": 0.50, "acousticness": 0.72,
    },
    {
        "id": 2, "title": "Pump It Up", "artist": "EDM Squad", "genre": "edm", "mood": "excited",
        "energy": 0.95, "tempo_bpm": 145, "valence": 0.85, "danceability": 0.92, "acousticness": 0.05,
    },
    {
        "id": 3, "title": "Sad Hours", "artist": "Blue Moon", "genre": "blues", "mood": "sad",
        "energy": 0.25, "tempo_bpm": 68, "valence": 0.20, "danceability": 0.30, "acousticness": 0.85,
    },
    {
        "id": 4, "title": "Jazz Corner", "artist": "Miles Away", "genre": "jazz", "mood": "relaxed",
        "energy": 0.36, "tempo_bpm": 92, "valence": 0.62, "danceability": 0.42, "acousticness": 0.60,
    },
    {
        "id": 5, "title": "City Walk", "artist": "MC Flow", "genre": "hip-hop", "mood": "focused",
        "energy": 0.72, "tempo_bpm": 96, "valence": 0.55, "danceability": 0.82, "acousticness": 0.10,
    },
]


def test_exact_mood_and_genre_match_scores_high():
    profile = {"mood": "chill", "genre": "lofi", "energy": 0.30}
    score = score_song(profile, SONGS[0])
    assert score > 5.0, "Exact mood+genre match should produce a score above 5.0"


def test_mismatched_song_scores_lower():
    profile = {"mood": "chill", "genre": "lofi", "energy": 0.30}
    chill_score = score_song(profile, SONGS[0])
    edm_score = score_song(profile, SONGS[1])
    assert chill_score > edm_score


def test_avoid_moods_reduces_score():
    base_profile = {"mood": "chill", "genre": "lofi", "energy": 0.30}
    penalized_profile = {**base_profile, "avoid_moods": ["chill"]}
    assert score_song(penalized_profile, SONGS[0]) < score_song(base_profile, SONGS[0])


def test_avoid_genres_reduces_score():
    base_profile = {"mood": "chill", "genre": "lofi", "energy": 0.30}
    penalized_profile = {**base_profile, "avoid_genres": ["lofi"]}
    assert score_song(penalized_profile, SONGS[0]) < score_song(base_profile, SONGS[0])


def test_energy_proximity_matters():
    high_energy_profile = {"mood": "excited", "genre": "edm", "energy": 0.95}
    edm_score = score_song(high_energy_profile, SONGS[1])
    blues_score = score_song(high_energy_profile, SONGS[2])
    assert edm_score > blues_score


def test_retrieve_candidates_returns_correct_count():
    profile = {"mood": "chill", "genre": "lofi", "energy": 0.30}
    results = retrieve_candidates(SONGS, profile, top_k=3)
    assert len(results) == 3


def test_retrieve_candidates_top_result_is_best_match():
    profile = {"mood": "chill", "genre": "lofi", "energy": 0.30}
    results = retrieve_candidates(SONGS, profile, top_k=5)
    assert results[0]["id"] == 1, "The lofi/chill song should rank first"


def test_retrieve_candidates_respects_top_k_limit():
    profile = {"mood": "focused", "genre": "hip-hop", "energy": 0.70}
    for k in [1, 2, 5]:
        results = retrieve_candidates(SONGS, profile, top_k=k)
        assert len(results) == k


def test_score_returns_float():
    profile = {"mood": "relaxed", "genre": "jazz", "energy": 0.36}
    result = score_song(profile, SONGS[3])
    assert isinstance(result, float)


def test_valence_target_proximity():
    low_valence_profile = {"mood": "sad", "genre": "blues", "energy": 0.25, "valence": 0.20}
    high_valence_profile = {"mood": "sad", "genre": "blues", "energy": 0.25, "valence": 0.90}
    # Sad/blues song (valence 0.20) should score higher when target valence is low
    score_low = score_song(low_valence_profile, SONGS[2])
    score_high = score_song(high_valence_profile, SONGS[2])
    assert score_low > score_high
