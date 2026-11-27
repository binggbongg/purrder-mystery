"""Shared helpers for the Purrder UI components."""
import html

import streamlit as st
from game import get_discovered_clues, next_hint
from guard import safe_complete
import prompts

UI_EXTRAS = {
    "suspects": {
        "Miming": {"role": "Barangay Chismosa", "zodiac": "Gemini"},
        "Whitey": {"role": "Estate Aristocrat", "zodiac": "Leo"},
        "Choco": {"role": "Alley Runner", "zodiac": "Virgo"},
        "Blackie": {"role": "Night Watchcat", "zodiac": "Scorpio"},
        "Pandesal": {"role": "Bakery Regular", "zodiac": "Pisces"},
        "Tigre": {"role": "Barangay Tanod", "zodiac": "Aries"},
    },
    "weapons": {
        "Tsinelas": {"made_of": "Rubber, Mom-level accuracy"},
        "Walis tambo": {"made_of": "Tiger grass, Rattan"},
        "Kawali": {"made_of": "Cast iron, Residual heat"},
        "Sandok": {"made_of": "Hardwood, Suspicious dent"},
        "Paypay": {"made_of": "Woven buri palm"},
        "Kandila": {"made_of": "Wax, Lingering smoke"},
        "Laser pointer": {"made_of": "Metal, Endless temptation"},
        "Scratching post": {"made_of": "Sisal rope, Attitude"},
    },
    "locations": {
        "Sari-sari store": {"setting": "Outdoors"},
        "Kusina": {"setting": "Indoors"},
        "Garden": {"setting": "Outdoors"},
        "Bubong": {"setting": "Outdoors"},
        "Sala": {"setting": "Indoors"},
        "Jeepney": {"setting": "Outdoors"},
        "Cat tree": {"setting": "Indoors"},
        "Sunny windowsill": {"setting": "Indoors"},
    },
}


def esc(text) -> str:
    """Escape user / data supplied text before putting it inside HTML."""
    return html.escape(str(text))


def clean(markup: str) -> str:
    """Strip indentation and blank lines.

    Streamlit renders markdown first. Indented lines (4+ spaces) or blank lines
    inside raw HTML make it render the HTML as a code block, which is what
    broke the old tab layouts. Flattening the HTML avoids that.
    """
    return "\n".join(line.strip() for line in markup.splitlines() if line.strip())


def md(markup: str) -> None:
    st.markdown(clean(markup), unsafe_allow_html=True)


def polaroid(idx: int, img_html: str = "") -> str:
    """Polaroid frame. `img_html` is the empty image slot.

    To add pictures later, pass something like:
        '<img src="data:image/png;base64,...." />'
    (the .polaroid-img-box CSS already makes <img> fill the frame).
    """
    tilt = "tilt-left" if idx % 2 else "tilt-right"
    return (
        f'<div class="polaroid-frame {tilt}">'
        f'<div class="polaroid-img-box">{img_html}</div>'
        f"</div>"
    )


def render_clues_box(session, expanded: bool = False) -> None:
    """Collapsible notebook listing the confirmed clue + all uncovered scene/suspect clues."""
    items, total = get_discovered_clues(session)
    found_count = len(items) - 1  # exclude the head-start confirmed clue from x/9 count
    with st.expander(f"Uncovered Clues ({found_count}/{total} found)", expanded=expanded):
        rows = []
        for item in items:
            is_conf = item["id"] == "confirmed"
            cls = "clue-card clue-card-confirmed" if is_conf else "clue-card"
            badge = f'{esc(item["source"])}' if is_conf else f'{esc(item["source"])} • {esc(item["kind"].title())}'
            rows.append(
                f'<div class="{cls}">'
                f'<div class="clue-badge">{badge}</div>'
                f'<div class="clue-text">{esc(item["text"])}</div>'
                f'</div>'
            )
        md("".join(rows))


def render_hint_box(session, client, key_prefix: str = "suspect") -> None:
    """Renders a 3-use Hint button + saved hint cards for the current round."""
    hint_key = f"hints_log_{session.seed}"
    if hint_key not in st.session_state:
        st.session_state[hint_key] = []
    remaining = max(0, 3 - session.hints_used)
    label = (
        f"Ask Mr. Meowslock for a Hint ({remaining}/3 left)"
        if remaining > 0
        else "No Hints Remaining (0/3)"
    )
    with st.container(key=f"hint_wrap_{key_prefix}"):
        if st.button(label, disabled=remaining == 0, key=f"{key_prefix}_hint_btn", use_container_width=True):
            h = next_hint(session)
            if h:
                with st.spinner("Mr. Meowslock is checking his notes..."):
                    reply = safe_complete(
                        client,
                        prompts.GM_SYSTEM,
                        [{"role": "user", "content": prompts.hint_prompt(*h)}],
                        session.solution,
                        max_tokens=180,
                    )
                st.session_state[hint_key].append((h[0], reply or h[1]))
                st.rerun()
        for lvl, text in st.session_state[hint_key]:
            md(
                f'<div class="hint-card">'
                f'<strong>Hint {lvl}/3 — Mr. Meowslock:</strong> {esc(text)}'
                f'</div>'
            )


def render_gallery(title: str, label: str, entries: list[tuple[str, str, str]]) -> None:
    """Paper sheet with polaroid rows. entries = (name, description, meta_line)."""
    rows = ""
    for idx, (name, desc, meta) in enumerate(entries, start=1):
        rows += (
            '<div class="item-row">'
            f'<div class="item-photo">{polaroid(idx)}</div>'
            '<div class="item-body">'
            f'<div class="item-title">{esc(label)} {idx}: {esc(name)}</div>'
            f'<p class="desc-text">{esc(desc)}</p>'
            f'<div class="item-meta">{esc(meta)}</div>'
            "</div></div>"
        )

    md(
        f"""
        <div class="paper-outer"><div class="paper-inner">
        <div class="report-title">{esc(title)}</div>
        <hr class="section-divider" />
        {rows}
        </div></div>
        """
    )