import base64
from pathlib import Path
import streamlit as st

from ui.components._utils import md

ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


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

def render():
    magnifier_img = _load_icon_img("magnifying-glass.svg")

    md(
        f"""
        <div class="purrder-nav">
        <div class="purrder-logo">PURRDER{magnifier_img}</div>
        <span class="purrder-nav-link active">The crime scene</span>
        <span class="purrder-nav-link">About Us</span>
        </div>
        """
    )

    # Round clipboard button (positioned by CSS: .st-key-clipboard_btn).
    # Clicking it toggles the Deduction Grid view (ui/components/grid_drawer.py).
    if st.button("📋", key="clipboard_btn", help="Open / close the Deduction Grid"):
        st.session_state.show_grid = not st.session_state.get("show_grid", False)
        st.rerun()