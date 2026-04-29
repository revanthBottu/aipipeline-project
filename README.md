# AI Music Recommender

An end-to-end AI-powered music recommendation system that takes a natural-language mood or vibe description and returns a personalized playlist — powered by Google Gemini and a RAG (Retrieval-Augmented Generation) pipeline.

---Video Link:https://www.loom.com/share/b0616294d9994c67a09ca40c090d781f

## Original Project

**Original project:** CSV-Based Music Recommender (Modules 1-3)

The original project was a command-line Python application that recommended songs from a curated 100-song CSV database. Users selected from 8 pre-defined taste profiles (e.g., "Gym Warrior", "Deep Focus", "Rainy Day Feels"), and a weighted multi-feature scoring algorithm ranked songs by mood, genre, energy, tempo, valence, danceability, and acousticness. The system had no natural-language input, no AI, and no web interface.

---

## What This Project Does

This redesign replaces the static profile system with a conversational AI pipeline. Instead of picking a profile from a list, users type anything and the system:

1. Uses Gemini AI to interpret the description into structured music preferences
2. Runs a RAG retrieval step that scores all 100 songs against those preferences
3. Sends the top 15 candidates back to Gemini for final ranking with confidence scores and personalized explanations


---

## Architecture Overview

```
User input (free text)
  -> Gemini Vibe Parser  ->  Structured profile JSON
  -> RAG Retriever        ->  Top 15 scored candidates
  -> Gemini AI Ranker     ->  Top 5 songs + confidence % + explanations
  -> Streamlit UI         ->  Rendered song cards
```
---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd ai-pipeline-project
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Get a free key at [https://aistudio.google.com/](https://aistudio.google.com/), then either:

**Option A — `.env` file (recommended):**
```bash
cp .env.example .env
# Edit .env and replace the placeholder with your actual key
```

**Option B — enter it in the app sidebar** when the app launches.

### 5. Run the app

```bash
streamlit run src/main.py
```

The app will open at `http://localhost:8501`.

### 6. Run the tests

```bash
pytest tests/ -v
```

---

## Sample Interactions

### Example 1 — Late-night coding

**Input:** `"Chill lofi beats for a late-night coding session, focused and not too distracting"`

**AI Interpretation:**
```json
{
  "mood": "focused",
  "genre": "lofi",
  "energy": 0.32,
  "tempo_bpm": 82,
  "valence": 0.45,
  "interpretation": "A calm, focused late-night session with soft lofi beats"
}
```

**Recommendations (sample):**
| # | Song | Artist | Confidence | Explanation |
|---|------|--------|------------|-------------|
| 1 | Midnight Loops | Lo-Fi Lab | 94% | Deep lofi groove with a focused, undistracted energy perfect for late-night work. |
| 2 | Rain Code | Lo Wave | 88% | Soft atmospheric texture and a steady 80 BPM tempo ideal for sustained concentration. |
| 3 | Still Hours | Ambient Co. | 81% | Minimal lofi arrangement that fades into the background without breaking flow. |

---

## Design Decisions

Using Gemini in two separate steps gives the best of both worlds: the first call extracts precise structured features (which the scoring algorithm needs), while the second call does semantic understanding of "fit" — something a pure feature-matching algorithm can't do well. Splitting the calls also makes each step testable independently.

Sending all 100 songs to Gemini in one call would be slow, expensive, and hit context-length limits. The RAG scoring algorithm acts as a cheap pre-filter that narrows 100 songs to 15 strong candidates, letting Gemini focus on nuanced ranking rather than brute-force search.

### Trade-offs
- Latency vs. quality:Two Gemini API calls add ~2-4 seconds. A single call would be faster but less accurate.
- Fixed song database: The 100-song CSV is small and static. A production system would use a vector database (e.g., Pinecone) with embeddings for true semantic retrieval.
- Confidence scores are AI estimates: Gemini's confidence values reflect its reasoning, not a calibrated probability. They should be treated as relative indicators, not absolute certainty.

---

## Project Structure

```
ai-pipeline-project/
├── data/
│   └── songs.csv              # 100 songs with audio features
├── src/
│   ├── main.py                # Streamlit web app
│   ├── ai_engine.py           # Gemini API calls (parse + rank)
│   └── recommender.py         # RAG scoring & retrieval
├── tests/
│   ├── test_recommender.py    # Unit tests (no API required)
│   └── test_ai_engine.py      # Mock-based AI function tests
├── assets/
│   └── system_diagram.md      # Mermaid.js system diagram
├── logs/
│   └── app.log                # Runtime audit log (auto-created)
├── model_card.md              # Ethical reflection & limitations
├── .env.example               # API key template
└── requirements.txt
```

## Reflection

One thing I learned about AI pipelines is that compartmenting the problem into different parts of each feature makes testing and debugging way easier. By breaking down the part for Retrieval, and a new part for Generation, and a new part for Ranking and Justification, it became easy to build.

One part of using Claude as an AI assistant was that it would sometimes underestimate the capabilities of the smaller models and make the algorithm for RAG messy.

