import base64
from pathlib import Path
import streamlit as st

from ui.components._utils import md

ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

ROUND_STATE_KEYS = (
    "session",
    "verdict_result",
    "grid_marks",
    "suspect_idx",
    "show_grid",
    "guess_suspect",
    "guess_weapon",
    "guess_location",
    "accusation_explanation",
)


def _load_icon_img(filename: str) -> str:
    icon_path = ICON_DIR / filename
    ext = icon_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime = mime_types.get(ext, "image/png")
    b64 = base64.b64encode(icon_path.read_bytes()).decode("utf-8")
    return f'<img class="purrder-magnifier" src="data:{mime};base64,{b64}" alt="Magnifying glass" />'


def _reset_round():
    for key in ROUND_STATE_KEYS:
        st.session_state.pop(key, None)
    if "case" in st.query_params:
        del st.query_params["case"]


def render():
    magnifier_img = _load_icon_img("magnifying-glass.svg")

    with st.container(key="purrder_nav"):
        col_logo, col_scene, col_new, _ = st.columns(
            [2.4, 1.8, 1.6, 2.8], vertical_alignment="center", gap="small"
        )
        with col_logo:
            md(f'<div class="purrder-logo">PURRDER{magnifier_img}</div>')
        with col_scene:
            if st.button("The crime scene", key="nav_scene_btn"):
                st.session_state.show_grid = False
                st.rerun()
        with col_new:
            if st.button(
                "New Round",
                key="new_round_btn",
                help="Start a fresh case and clear all chat history & grid marks",
                on_click=_reset_round,
            ):
                st.rerun()

    # Round clipboard button (positioned by CSS: .st-key-clipboard_btn).
    # Clicking it toggles the Deduction Grid view (ui/components/grid_drawer.py).
    if st.button("📋", key="clipboard_btn", help="Open / close the Deduction Grid"):
        st.session_state.show_grid = not st.session_state.get("show_grid", False)
        st.rerun()
