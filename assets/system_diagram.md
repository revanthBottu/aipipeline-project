# AI Music Recommender — System Diagram

## Mermaid.js Diagram

```mermaid
flowchart TD
    A(["👤 User\nTypes mood / vibe description"]) --> B

    subgraph UI ["🖥️ Streamlit Web UI  (src/main.py)"]
        B["Text Input\n& Submit Button"]
        I["Results Display\nSong cards + confidence %"]
    end

    B -->|"Step 1 — interpret vibe"| C

    subgraph AI ["🤖 AI Layer  (src/ai_engine.py — Gemini 2.0 Flash)"]
        C["Vibe Parser\nGemini API call\n→ extracts mood, genre,\n  energy, tempo, valence…"]
        H["AI Ranker\nGemini API call\n→ selects best 5 songs\n  + confidence scores\n  + explanations"]
    end

    C -->|"Structured JSON profile"| D[("📋 Parsed Profile\n{mood, genre, energy,\n tempo_bpm, valence,\n danceability, acousticness,\n avoid_moods, avoid_genres}")]

    D -->|"Step 2 — retrieve candidates"| E

    subgraph RAG ["📚 RAG Retrieval  (src/recommender.py)"]
        E["Scoring Algorithm\nWeighted multi-feature scoring\nfor every song vs. profile"]
        F[("🗄️ songs.csv\n100 songs\ndata/songs.csv")]
        E <-->|"reads"| F
    end

    E -->|"Top 15 scored candidates"| G[("🎯 Candidate Pool\n15 best-matching songs")]

    G -->|"Step 3 — rank & explain"| H
    D --> H

    H -->|"Top 5 + confidence + explanations"| I
    I --> J(["🎶 User sees\nranked playlist"])

    C --> L["📝 Logger\nlogs/app.log"]
    E --> L
    H --> L

    subgraph Tests ["🧪 Test Suite  (tests/)"]
        T1["test_recommender.py\nUnit tests — scoring\n& retrieval (no API)"]
        T2["test_ai_engine.py\nMock tests — vibe\nparsing & ranking"]
    end

    T1 -.->|"validates"| E
    T2 -.->|"validates with mocks"| C
    T2 -.->|"validates with mocks"| H
```

## Component Descriptions

| Component | File | Responsibility |
|-----------|------|----------------|
| Streamlit Web UI | `src/main.py` | User input, step-by-step status, song card display |
| Vibe Parser | `src/ai_engine.py` | Gemini converts free-text vibe → structured JSON profile |
| RAG Retriever | `src/recommender.py` | Scores all 100 songs against the profile; returns top 15 |
| AI Ranker | `src/ai_engine.py` | Gemini re-ranks candidates, adds confidence scores & explanations |
| Logger | `logs/app.log` | Records every step, query text, errors, and result counts |
| Test Suite | `tests/` | Unit tests (no API) + mock-based AI function tests |

## Data Flow Summary

```
User free-text vibe
  → Gemini extracts structured profile (mood, genre, energy, …)
  → Scoring algorithm retrieves top 15 candidates from songs.csv
  → Gemini re-ranks candidates, assigns confidence %, writes explanations
  → Streamlit displays ranked songs with confidence badges
```

## Human Checkpoints

- **User review**: The user reads each explanation and confidence score, and can re-run with a different vibe description if results feel off.
- **Logged audit trail**: Every query and result is written to `logs/app.log` for inspection.
- **AI Interpretation details**: An expandable section in the UI shows the raw parsed JSON so users can see exactly how their vibe was interpreted.
