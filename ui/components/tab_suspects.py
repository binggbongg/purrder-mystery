import re
from game import pick_clue
from guard import (
    MAX_TURNS_PER_CASE,
    SAFE_DEFLECTION,
    build_messages,
    defense_footer,
    is_repetitive,
    is_stonewall,
    new_tag,
    safe_complete,
    screen_input,
)
import prompts
import streamlit as st
from models import GameSession

from ui.components._utils import UI_EXTRAS, esc, md, render_clues_box, render_hint_box

HEIGHT_MARKS = ["5'6\"", "", "5'0\"", "", "4'6\"", "", "4'0\"", "", "3'6\"", "", "3'0\"", ""]


def _mugshot(img_html: str = "") -> str:
    """Height-chart backdrop. `img_html` is the empty image slot for the cat photo."""
    rows = "".join(
        f'<div class="hc-row{" hc-major" if mark else ""}"><span>{mark}</span><i></i></div>'
        for mark in HEIGHT_MARKS
    )
    return f'<div class="mugshot-box"><div class="height-chart">{rows}</div>{img_html}</div>'


def _format_cat_reply(raw: str) -> str:
    text = re.sub(
        r"\*{0,2}Currently Interrogating:\*{0,2}\s*[^\n]+\n*",
        "",
        raw,
        flags=re.I,
    ).strip()

    resp = re.search(
        r"\*{0,2}Response:\*{0,2}\s*(.*?)(?=\*{0,2}Observed(?:\s+Behavior)?:\*{0,2}|$)",
        text,
        re.S | re.I,
    )
    beh = re.search(
        r"\*{0,2}Observed(?:\s+Behavior)?:\*{0,2}\s*([^\n]+?)(?=\s*\*{0,2}(?:Currently Interrogating|Response):|$)",
        text,
        re.S | re.I,
    )

    if resp:
        body = esc(resp.group(1).strip().strip('"'))
        body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
        body = re.sub(r"\*(.+?)\*", r"<em>\1</em>", body)
        out = f"<div>{body}</div>"
        if beh and beh.group(1).strip():
            behavior = esc(beh.group(1).strip().strip("*"))
            out += (
                '<div style="margin-top:0.45rem; font-style:italic; '
                f'font-size:0.88rem; opacity:0.85;">{behavior}</div>'
            )
        return out

    clean = esc(text)
    clean = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", clean)
    clean = re.sub(r"\*(.+?)\*", r"<em>\1</em>", clean)
    return clean


def render(session: GameSession, client):
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
        f'<div class="bubble-user">{esc(m["content"])}</div>'
        if m["role"] == "user"
        else f'<div class="bubble-cat">{_format_cat_reply(m["content"])}</div>'
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

    render_hint_box(session, client, key_prefix="suspect")
    render_clues_box(session, expanded=False)

    if sent and question.strip():
        q = question.strip()
        if session.turns >= MAX_TURNS_PER_CASE:
            messages.append({
                "role": "assistant",
                "content": (
                    "**Response:** The barangay is closing for the night, detective. "
                    "Time to fill out the Incident Report or start a New Round.\n"
                    "**Observed Behavior:** *yawns widely and stretches all four paws*"
                ),
                "blocked": True,
            })
            st.rerun()

        clean, msg = screen_input(q)
        if clean is None:
            messages.append({"role": "user", "content": q, "blocked": True})
            messages.append({"role": "assistant", "content": msg, "blocked": True})
            st.rerun()

        session.turns += 1
        clue = pick_clue(session, cat, clean)
        messages.append({"role": "user", "content": clean})
        llm_history = [m for m in messages if not m.get("blocked")]
        tag = new_tag()
        system = prompts.cat_system(session, cat, clue) + defense_footer(tag)

        with st.spinner(f"{cat.name} is thinking..."):
            reply = safe_complete(
                client,
                system,
                build_messages(llm_history, tag),
                session.solution,
                max_tokens=220,
                reject=lambda r: is_stonewall(r) or is_repetitive(r, llm_history),
            )

        if reply is None:
            messages.pop()
            messages.append({"role": "assistant", "content": SAFE_DEFLECTION, "blocked": True})
        else:
            messages.append({"role": "assistant", "content": reply})
            if clue and not is_stonewall(reply):
                if any(re.search(rf"\b{re.escape(t)}\b", reply, re.I) for t in clue.specific):
                    session.discovered_clue_ids.add(clue.id)
        st.rerun()