import streamlit as st
from models import Evaluation, GameSession
from results import accusation_rows, score_label, submit_accusation
from scoring import DEFAULT_SCORING

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


def render(session: GameSession, client, *, checkpoint=None):
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
                """
            )

            if session.result is not None:
                with st.container(key="investigation_results"):
                    _render_results(session, session.result, client, checkpoint)
                return

            md('<div class="todo-title">TO-DO: Fill Out Missing Information</div>')

            # The form is wrapped in a keyed container so CSS can turn it into the bordered table.
            with st.container(key="report_wrap"):
                with st.form("accusation_form", border=False):
                    with st.container(key="report_table"):
                        suspect = _field_row("Suspect:", "Select a suspect...", [c.name for c in session.cats], "guess_suspect")
                        weapon = _field_row("Weapon:", "Select a weapon...", [w.name for w in session.weapons], "guess_weapon")
                        location = _field_row("Location:", "Select a location...", [l.name for l in session.locations], "guess_location")

                    explanation = st.text_area(
                        "Explain your deduction (optional)", max_chars=DEFAULT_SCORING.explanation_limit,
                        key="accusation_explanation",
                    )

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
                with st.spinner("The other investigators are now reviewing your report..."):
                    submit_accusation(session, client, (suspect, weapon, location), explanation,
                                      checkpoint=checkpoint)
                st.rerun()
            except ValueError as e:
                st.error(str(e))


def _render_results(session: GameSession, ev: Evaluation, client, checkpoint):
    if ev.won:
        st.success("Case solved")
    else:
        st.error("Case not solved")
    breakdown = ev.score_breakdown
    if breakdown:
        st.write(f"**{score_label(ev)} · {breakdown.rank}**")
    else:
        st.info(score_label(ev))
        if not session.investigation_history_complete:
            st.caption("This case began before investigation scoring was available.")
        elif st.button("Retry performance review", key="retry_performance_review"):
            with st.spinner("Reviewing the remaining investigation notes..."):
                submit_accusation(session, client, retry=True, checkpoint=checkpoint)
            st.rerun()

    md('<div class="label-heading">Accusation</div>')
    for label, guess, actual, correct in accusation_rows(session, ev):
        st.write(f"**{label}** · {'✅ Correct' if correct else '❌ Incorrect'}  \n"
                 f"You chose **{guess}** · Actual **{actual}**")

    md('<div class="label-heading">Investigation</div>')
    found, missed, hints = st.columns(3)
    found.metric("Clues discovered", len(ev.found_clues))
    missed.metric("Clues missed", len(ev.missed_clues))
    hints.metric("Hints delivered", len(session.delivered_hints))
    if breakdown:
        metrics = breakdown.metrics
        questions, meaningful, productive, redundant = st.columns(4)
        questions.metric("Questions", metrics.questions)
        meaningful.metric("Meaningful", metrics.meaningful)
        productive.metric("Productive", metrics.productive)
        redundant.metric("Redundant", metrics.redundant)
        st.caption(f"Weighted clue coverage {metrics.weighted_coverage:.0%}")
        md('<div class="label-heading">Performance Breakdown</div>')
        for category in breakdown.categories:
            st.progress(min(1.0, category.earned / category.maximum),
                        text=f"{category.name} · {category.earned:.2f} / {category.maximum:.2f}")
    if ev.verdict:
        md('<div class="label-heading">Mr. Meowslock’s Verdict</div>')
        st.markdown(ev.verdict)
