import csv
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def load_songs(csv_path: str) -> List[Dict]:
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                }
            )
    logger.info("Loaded %d songs from %s", len(songs), csv_path)
    return songs


def score_song(profile: Dict, song: Dict) -> float:
    """Score a single song against an AI-extracted profile dict.

    Profile keys (all optional except mood/genre/energy):
      mood, genre, energy, tempo_bpm, valence, danceability, acousticness,
      avoid_moods (list), avoid_genres (list)
    """
    score = 0.0

    if song["mood"] == profile.get("mood", ""):
        score += 3.0
    if song["genre"] == profile.get("genre", ""):
        score += 2.0

    energy_diff = abs(float(song["energy"]) - float(profile.get("energy", 0.5)))
    score += (1.0 - energy_diff) * 2.0

    target_dance = profile.get("danceability")
    if target_dance is not None:
        score += (1.0 - abs(float(song["danceability"]) - float(target_dance))) * 1.5
    else:
        score += float(song["danceability"]) * 1.5

    target_valence = profile.get("valence")
    if target_valence is not None:
        score += (1.0 - abs(float(song["valence"]) - float(target_valence))) * 1.0
    else:
        score += float(song["valence"]) * 1.0

    target_tempo = profile.get("tempo_bpm")
    if target_tempo:
        tempo_diff = abs(float(song["tempo_bpm"]) - float(target_tempo)) / 120.0
        score += max(0.0, 1.0 - tempo_diff) * 0.5
    else:
        tempo_norm = max(0.0, min(1.0, (float(song["tempo_bpm"]) - 60) / 120.0))
        score += tempo_norm * 0.5

    target_ac = profile.get("acousticness")
    if target_ac is not None:
        score += (1.0 - abs(float(song["acousticness"]) - float(target_ac))) * 0.5
    else:
        score += (1.0 - float(song["acousticness"])) * 0.5

    for mood in profile.get("avoid_moods", []):
        if song["mood"] == mood:
            score -= 1.5

    for genre in profile.get("avoid_genres", []):
        if song["genre"] == genre:
            score -= 1.0

    return round(score, 3)


def retrieve_candidates(songs: List[Dict], profile: Dict, top_k: int = 15) -> List[Dict]:
    """RAG retrieval step: score every song and return the top_k candidates."""
    scored = sorted(
        ((song, score_song(profile, song)) for song in songs),
        key=lambda x: x[1],
        reverse=True,
    )
    candidates = [song for song, _ in scored[:top_k]]
    logger.info("Retrieved %d candidates (top_k=%d)", len(candidates), top_k)
    return candidates
