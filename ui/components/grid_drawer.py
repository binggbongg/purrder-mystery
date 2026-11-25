"""Deduction Grid (Murdle style).

The player taps a square to cycle:  blank -> X (ruled out) -> dot (confirmed) -> blank.
Marks live in st.session_state.grid_marks, so they survive tab switches and reruns.

Icons come from the dataset: each suspect / weapon / location may have an `icon`
field (see dataset.json). It can be:
  - a file under ui/assets/icons/   e.g. "weapons/kawali.png" (png, jpg, svg, webp, gif)
  - an emoji / short text           e.g. "🍳"
If it is empty or the file is missing, the item's name is shown instead.
"""
import base64
import mimetypes
import re
from functools import lru_cache
from pathlib import Path

import streamlit as st

from ui.components._utils import esc, md

ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
IMAGE_EXT = re.compile(r"\.(png|jpe?g|gif|svg|webp)$", re.I)

MARKS = ["", "✕", "●"]          # state 0 / 1 / 2
N = 4                            # items per category (models.py enforces exactly 4)
BLANK = "\u200b"                 # zero-width space: Streamlit needs a non-empty button label


# ---------------------------------------------------------------- icons
@lru_cache(maxsize=128)
def _data_uri(path: str, mtime: float) -> str:
    p = Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def _icon_html(item) -> str:
    """Icon (or name fallback) for one suspect / weapon / location."""
    name = item.name
    icon = (getattr(item, "icon", "") or "").strip()
    inner = None
    if icon:
        path = ICON_DIR / icon
        if path.is_file():
            inner = f'<img src="{_data_uri(str(path), path.stat().st_mtime)}" alt="{esc(name)}" />'
        elif not IMAGE_EXT.search(icon):
            inner = f'<span class="grid-icon-emoji">{esc(icon)}</span>'
    if inner is None:
        inner = f'<span class="grid-icon-text">{esc(name)}</span>'
    return f'<div class="grid-icon" title="{esc(name)}">{inner}</div>'


# ---------------------------------------------------------------- state
def _cycle(pair: str) -> None:
    marks = st.session_state.grid_marks
    marks[pair] = (marks.get(pair, 0) + 1) % len(MARKS)


def _reset() -> None:
    st.session_state.grid_marks = {}


# ---------------------------------------------------------------- cells
def _edges(r: int, c: int, block: str) -> list[str]:
    """Which sides of this square get the thick Murdle outline."""
    last = N - 1
    edges = []
    if block in ("ws", "wl") and r == 0:
        edges.append("top")
    if block in ("ws", "ls") and c == 0:
        edges.append("left")
    if c == last:
        edges.append("right")
    if r == last:
        edges.append("bottom")
    return edges


def _cell(block: str, r: int, c: int, row_name: str, col_name: str) -> None:
    pair = f"{block}:{row_name}|{col_name}"
    state = st.session_state.grid_marks.get(pair, 0)
    # The key carries the mark state + edge flags so CSS can colour / outline each square.
    key = f"gc_s{state}_{block}_{r}{c}" + "".join(f"_e{e}" for e in _edges(r, c, block))
    st.button(
        MARKS[state] or BLANK,
        key=key,
        on_click=_cycle,
        args=(pair,),
        help=f"{row_name} × {col_name}",
        use_container_width=True,
    )


# ---------------------------------------------------------------- view
def render(session=None):
    session = session or st.session_state.session
    if "grid_marks" not in st.session_state:
        st.session_state.grid_marks = {}

    cats = session.cats[:N]
    weapons = session.weapons[:N]
    locs = session.locations[:N]

    with st.container(key="grid_panel"):
        with st.container(key="paper_outer_grid"):
            with st.container(key="paper_inner_grid"):
                md(
                    """
                    <div class="report-title">Deduction Grid</div>
                    <hr class="section-divider" />
                    """
                )

                with st.container(key="grid_board"):
                    # --- header: group titles + suspect / location icons
                    with st.container(key="grid_head"):
                        md(
                            """
                            <div class="grid-titles">
                            <span style="grid-column: 2 / span 4;">SUSPECTS</span>
                            <span style="grid-column: 6 / span 4;">LOCATIONS</span>
                            </div>
                            """
                        )
                        cols = st.columns(1 + 2 * N, gap="small")
                        for i, cat in enumerate(cats):
                            with cols[1 + i]:
                                md(_icon_html(cat))
                        for i, loc in enumerate(locs):
                            with cols[1 + N + i]:
                                md(_icon_html(loc))

                    # --- weapons rows: [weapon icon | weapon x suspects | weapon x locations]
                    with st.container(key="grid_sec_w"):
                        for r, weapon in enumerate(weapons):
                            cols = st.columns(1 + 2 * N, gap="small")
                            with cols[0]:
                                md(_icon_html(weapon))
                            for c, cat in enumerate(cats):
                                with cols[1 + c]:
                                    _cell("ws", r, c, weapon.name, cat.name)
                            for c, loc in enumerate(locs):
                                with cols[1 + N + c]:
                                    _cell("wl", r, c, weapon.name, loc.name)

                    # --- location rows: [location icon | location x suspects | (legend)]
                    with st.container(key="grid_sec_l"):
                        md(
                            """
                            <div class="grid-legend">
                            <div class="grid-legend-title">How to use</div>
                            <div>Tap a square to mark it.</div>
                            <div><span class="lg-box"></span> not checked</div>
                            <div><span class="lg-box">✕</span> ruled out</div>
                            <div><span class="lg-box">●</span> confirmed</div>
                            </div>
                            """
                        )
                        for r, loc_row in enumerate(locs):
                            cols = st.columns(1 + 2 * N, gap="small")
                            with cols[0]:
                                md(_icon_html(loc_row))
                            for c, cat in enumerate(cats):
                                with cols[1 + c]:
                                    _cell("ls", r, c, loc_row.name, cat.name)

                btn_a, btn_b, _ = st.columns([1.3, 1.6, 3], gap="small")
                btn_a.button("Clear grid", key="grid_reset", on_click=_reset, use_container_width=True)
                if btn_b.button("Back to the case file", key="grid_back", use_container_width=True):
                    st.session_state.show_grid = False
                    st.rerun()