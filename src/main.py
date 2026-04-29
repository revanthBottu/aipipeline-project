import sys
import os
import logging
from pathlib import Path

# Ensure src/ is on the path when running via `streamlit run src/main.py`
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Set up logging before importing app modules
_logs_dir = Path(__file__).parent.parent / "logs"
_logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_logs_dir / "app.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

import streamlit as st
from recommender import load_songs, retrieve_candidates
from ai_engine import parse_vibe, rank_songs

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Music Recommender",
    page_icon="🎵",
    layout="centered",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    api_key = os.getenv("GROQ_API_KEY", "")
    if api_key:
        st.success("API key loaded from environment")
    else:
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Get a free key at https://console.groq.com/",
        )

    st.divider()
    st.markdown("**How it works**")
    st.markdown("1. You describe a mood or vibe")
    st.markdown("2. Groq AI interprets your description")
    st.markdown("3. The system searches 100 songs")
    st.markdown("4. Groq selects the best matches")
    st.divider()
    st.caption("Powered by Llama 3.3 70B · RAG pipeline")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎵 AI Music Recommender")
st.markdown("*Describe your mood or vibe — AI will find the perfect songs for you.*")
st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
user_input = st.text_area(
    "What's your vibe?",
    placeholder=(
        "Try something like:\n"
        "  • \"Chill late-night coding session, lofi beats, low energy...\"\n"
        "  • \"Hype workout music, fast and intense, no sad stuff...\"\n"
        "  • \"Melancholic rainy Sunday, acoustic and a little sad...\""
    ),
    height=130,
)

col_btn, col_num = st.columns([3, 1])
with col_btn:
    find_btn = st.button("🎯  Find My Songs", type="primary", use_container_width=True)
with col_num:
    num_results = st.selectbox("Show", [5, 10], index=0, label_visibility="visible")

# ── Main logic ────────────────────────────────────────────────────────────────
if find_btn:
    if not user_input.strip():
        st.warning("Please describe your vibe first!")
        st.stop()
    if not api_key:
        st.error("Enter your Gemini API key in the sidebar to continue.")
        st.stop()

    try:
        songs = load_songs(str(DATA_PATH))
    except FileNotFoundError:
        st.error(f"Songs database not found at `{DATA_PATH}`. Check your project setup.")
        logger.error("songs.csv not found at %s", DATA_PATH)
        st.stop()

    st.divider()

    with st.status("🤖  AI is finding your songs…", expanded=True) as status:

        # Step 1 — Vibe parsing
        st.write("🧠 **Step 1:** Interpreting your vibe with Groq AI…")
        try:
            parsed = parse_vibe(user_input, api_key)
        except Exception as e:
            logger.error("Vibe parsing failed: %s", e)
            status.update(label="Failed to interpret vibe", state="error")
            st.error(f"Could not interpret your vibe: {e}")
            st.stop()

        st.write(
            f"✅  Detected **{parsed.get('mood')}** mood · "
            f"**{parsed.get('genre')}** genre · "
            f"energy **{parsed.get('energy')}**"
        )
        st.caption(f"_{parsed.get('interpretation', '')}_")

        # Step 2 — RAG retrieval
        st.write(f"📚 **Step 2:** Searching {len(songs)} songs in the database…")
        candidates = retrieve_candidates(songs, parsed, top_k=15)
        st.write(f"✅  Found **{len(candidates)} candidate songs** matching your profile")

        # Step 3 — AI ranking
        st.write("🎯 **Step 3:** Gemini is selecting the best matches and scoring confidence…")
        try:
            ranked = rank_songs(user_input, parsed, candidates, api_key)
        except Exception as e:
            logger.error("Song ranking failed: %s", e)
            status.update(label="Failed to rank songs", state="error")
            st.error(f"Could not rank songs: {e}")
            st.stop()

        st.write(f"✅  Selected top **{len(ranked)} songs** with confidence scores")
        status.update(label="✨  Recommendations ready!", state="complete", expanded=False)

    # ── Results ───────────────────────────────────────────────────────────────
    st.subheader("🎶 Your Personalized Playlist")

    for i, rec in enumerate(ranked[:num_results], 1):
        conf = int(rec.get("confidence", 0))
        if conf >= 80:
            color, label = "#22c55e", "Excellent"
        elif conf >= 65:
            color, label = "#f59e0b", "Good"
        else:
            color, label = "#64748b", "Fair"

        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"**{i}. {rec.get('title', 'Unknown')}**")
                st.markdown(f"*{rec.get('artist', 'Unknown artist')}*")
                st.markdown(f"> {rec.get('explanation', '')}")
            with right:
                st.markdown(
                    f"<div style='text-align:center;padding:10px;border-radius:8px;"
                    f"background:{color}22;border:1px solid {color};'>"
                    f"<div style='font-size:1.6rem;font-weight:700;color:{color};'>{conf}%</div>"
                    f"<div style='font-size:0.7rem;color:{color};'>{label}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with st.expander("🔍 View AI Interpretation Details"):
        st.json(parsed)

    logger.info(
        "Recommendation complete — %d songs returned for query '%.40s'",
        len(ranked),
        user_input,
    )
