import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# Ensure root folder is importable when running `streamlit run ui/app.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

from models import Dataset
from game import new_game
from guard import safe_complete
from llm import get_client
import prompts
from ui.components import grid_drawer, navbar, tab_crime_scene, tab_locations, tab_suspects, tab_weapons

icon_path = Path(__file__).parent / "assets" / "icons" / "meowslock.svg"

st.set_page_config(
    page_title="Purrder Mystery",
    page_icon=str(icon_path) if icon_path.exists() else "🐾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "styles" / "main.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource
def load_backend():
    client = get_client()
    dataset_path = ROOT_DIR / os.getenv("DATASET_PATH", "dataset.json")
    dataset = Dataset.load(str(dataset_path))
    print(f"[Purrder Mystery] Active LLM client: {type(client).__name__}")
    return client, dataset


def start_new_case(client, dataset):
    session = new_game(dataset)
    with st.spinner("Drafting the Police Incident Report..."):
        session.story = (
            safe_complete(
                client,
                prompts.GM_SYSTEM,
                [{"role": "user", "content": prompts.story_prompt(session)}],
                session.solution,
                max_tokens=1200,
            )
            or "A mystery awaits, detective!"
        )
    return session


client, dataset = load_backend()

# Initialize real game session once
if "session" not in st.session_state:
    st.session_state.session = start_new_case(client, dataset)
if "show_grid" not in st.session_state:
    st.session_state.show_grid = False

session = st.session_state.session

# Top navigation bar + clipboard button (toggles the deduction grid)
navbar.render()

if st.session_state.show_grid:
    grid_drawer.render(session)
else:
    # Manila folder tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Crime Scene", "Suspects", "Weapons", "Locations"])

    with tab1:
        tab_crime_scene.render(session, client)
    with tab2:
        tab_suspects.render(session, client)
    with tab3:
        tab_weapons.render(session)
    with tab4:
        tab_locations.render(session)