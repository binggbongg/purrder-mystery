import sys
from pathlib import Path

import streamlit as st

# Ensure root folder is importable when running `streamlit run ui/app.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

icon_path = Path(__file__).parent / "assets" / "icons" / "meowslock.svg"

from ui.components import grid_drawer, navbar, tab_crime_scene, tab_locations, tab_suspects, tab_weapons
from ui.mock_data import get_mock_session

st.set_page_config(
    page_title="Purrder Mystery",
    page_icon=str(icon_path),
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "styles" / "main.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Initialize mock game session once
if "session" not in st.session_state:
    st.session_state.session = get_mock_session()
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
        tab_crime_scene.render(session)
    with tab2:
        tab_suspects.render(session)
    with tab3:
        tab_weapons.render(session)
    with tab4:
        tab_locations.render(session)