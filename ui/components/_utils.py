"""Shared helpers for the Purrder UI components."""
import html

import streamlit as st


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