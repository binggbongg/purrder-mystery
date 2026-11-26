from game import evaluate_accusation
from guard import safe_complete
import prompts
import streamlit as st
from models import GameSession

from ui.components._utils import esc, md


def _field_row(label: str, placeholder: str, options: list[str], key: str):
    c1, c2 = st.columns([1, 3.4], gap="small", vertical_alignment="center")
    with c1:
        md(f'<div class="field-label">{label}</div>')
    with c2:
        return st.selectbox(
            label,
            options,
            index=None,
            placeholder=placeholder,
            label_visibility="collapsed",
            key=key,
        )


def render(session: GameSession, client):
    with st.container(key="paper_outer_scene"):
        with st.container(key="paper_inner_scene"):
            md(
                f"""
                <div class="report-title">Police Incident Report</div>
                <hr class="section-divider" />
                <div class="label-heading">Overview:</div>
                <p class="desc-text" style="margin:0.2rem 0 0.8rem 0; white-space: pre-line;">{esc(session.story)}</p>
                <p class="confirmed-clue">{esc(session.confirmed_clue.text)}</p>
                <hr class="section-divider" style="margin-top:1.6rem;" />
                <div class="todo-title">TO-DO: Fill Out Missing Information</div>
                """
            )

            # The form is wrapped in a keyed container so CSS can turn it into the bordered table.
            with st.container(key="report_wrap"):
                with st.form("accusation_form", border=False):
                    with st.container(key="report_table"):
                        suspect = _field_row("Suspect:", "Select a suspect...", [c.name for c in session.cats], "guess_suspect")
                        weapon = _field_row("Weapon:", "Select a weapon...", [w.name for w in session.weapons], "guess_weapon")
                        location = _field_row("Location:", "Select a location...", [l.name for l in session.locations], "guess_location")

                    md(
                        """
                        <hr class="section-divider" style="margin:1.1rem 0 0.9rem 0;" />
                        <div class="label-heading">Signatories</div>
                        """
                    )
                    _, btn_col, _ = st.columns([1, 1.5, 1])
                    submitted = btn_col.form_submit_button("Click to Submit Report", use_container_width=True)

                    md(
                        """
                        <div class="sig-line"></div>
                        <div class="sig-name">Mr. Meowslock, Lead Investigator</div>
                        """
                    )

    if submitted:
        if not (suspect and weapon and location):
            st.warning("Fill out Suspect, Weapon, and Location before submitting.")
        else:
            try:
                ev = evaluate_accusation(session, suspect, weapon, location)
                with st.spinner("The other investigators are now reviewing your report..."):
                    verdict = safe_complete(
                        client,
                        prompts.GM_SYSTEM,
                        [{"role": "user", "content": prompts.verdict_prompt(session, ev, (suspect, weapon, location))}],
                        None,
                    )
                st.session_state.verdict_result = (ev, verdict or "")
            except ValueError as e:
                st.error(str(e))

    if "verdict_result" in st.session_state:
        ev, verdict = st.session_state.verdict_result
        if ev.won:
            st.success(f"Case Solved! Score: {ev.score}/100")
        else:
            st.error(f"Not quite, detective! Score: {ev.score}/100")
        st.markdown(verdict)