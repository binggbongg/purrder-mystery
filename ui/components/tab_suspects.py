import streamlit as st
from models import GameSession

from ui.components._utils import esc, md
from ui.mock_data import UI_EXTRAS

HEIGHT_MARKS = ["5'6\"", "", "5'0\"", "", "4'6\"", "", "4'0\"", "", "3'6\"", "", "3'0\"", ""]


def _mugshot(img_html: str = "") -> str:
    """Height-chart backdrop. `img_html` is the empty image slot for the cat photo."""
    rows = "".join(
        f'<div class="hc-row{" hc-major" if mark else ""}"><span>{mark}</span><i></i></div>'
        for mark in HEIGHT_MARKS
    )
    return f'<div class="mugshot-box"><div class="height-chart">{rows}</div>{img_html}</div>'


def render(session: GameSession):
    if "suspect_idx" not in st.session_state:
        st.session_state.suspect_idx = 0

    cats = session.cats
    total = len(cats)

    # --- Suspect flipper (small tabs above the dossier) ---
    with st.container(key="suspect_nav"):
        nav_cols = st.columns([0.8] + [2] * total + [0.8], vertical_alignment="center", gap="small")

        if nav_cols[0].button("◀", key="prev_suspect", help="Previous suspect", use_container_width=True):
            st.session_state.suspect_idx = (st.session_state.suspect_idx - 1) % total
            st.rerun()

        for idx, c in enumerate(cats):
            is_active = idx == st.session_state.suspect_idx
            if nav_cols[idx + 1].button(
                c.name,
                key=f"select_cat_{idx}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state.suspect_idx = idx
                st.rerun()

        if nav_cols[total + 1].button("▶", key="next_suspect", help="Next suspect", use_container_width=True):
            st.session_state.suspect_idx = (st.session_state.suspect_idx + 1) % total
            st.rerun()

    cat = cats[st.session_state.suspect_idx]
    extras = UI_EXTRAS["suspects"].get(cat.name, {"role": "Neighborhood Cat", "zodiac": "Unknown"})

    fields = [
        ("Name:", cat.name),
        ("Breed:", cat.breed),
        ("Role/Title:", extras["role"]),
        ("Zodiac Sign:", extras["zodiac"]),
        ("Personality:", cat.archetype.title()),
    ]
    info_rows = "".join(
        f'<div class="dossier-row"><span class="dossier-label">{esc(k)}</span>'
        f'<span class="dossier-value">{esc(v)}</span></div>'
        for k, v in fields
    )

    messages = session.history.setdefault(cat.name, [])
    bubbles = "".join(
        f'<div class="{"bubble-user" if m["role"] == "user" else "bubble-cat"}">{esc(m["content"])}</div>'
        for m in messages
    )

    # Outer sheet -> flush inner box (dossier, alibi, transcript, input all share one border)
    with st.container(key="paper_outer_suspects"):
        with st.container(key="paper_inner_flush"):
            md(
                f"""
                <div class="dossier-grid">
                {_mugshot()}
                <div class="dossier-info">{info_rows}</div>
                </div>
                <div class="alibi-box">
                <div class="label-heading">Alibi:</div>
                <p class="desc-text alibi-text">{esc(cat.alibi)}</p>
                </div>
                <div class="transcript-box"><div class="transcript-inner">
                <div class="transcript-title">Interrogation Transcript</div>
                {bubbles}
                </div></div>
                """
            )

            with st.form(f"chat_form_{cat.name}", clear_on_submit=True, border=False):
                inp_col, send_col = st.columns([8, 1], vertical_alignment="center", gap="small")
                question = inp_col.text_input(
                    "Question",
                    placeholder="Type your questions here...",
                    label_visibility="collapsed",
                )
                sent = send_col.form_submit_button("↑")

    if sent and question.strip():
        messages.append({"role": "user", "content": question.strip()})
        # Temporary frontend placeholder reply until this is wired to game.py / the LLM
        messages.append(
            {
                "role": "assistant",
                "content": f"*{cat.name} flicks their tail ({cat.archetype}).* "
                f"Why are you asking me about '{question.strip()}'? I already told you my alibi!",
            }
        )
        st.rerun()