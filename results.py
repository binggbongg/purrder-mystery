import logging
import re

from game import evaluate_accusation
from guard import safe_complete
from investigation import add_final_explanation
from investigation_evaluator import evaluate_pending
from llm import get_evaluator_client
from models import Evaluation, GameSession
import prompts
from scoring import DEFAULT_SCORING, ScoringConfig, calculate_final_score

log = logging.getLogger(__name__)


def score_label(ev: Evaluation) -> str:
    if ev.score is not None:
        return f"{ev.score:g}/100"
    return "Performance score pending" if ev.score_status == "pending" else "Performance score incomplete"


def accusation_rows(session: GameSession, ev: Evaluation):
    solution = session.solution
    return zip(
        ("Suspect", "Weapon", "Location"), ev.accused or ("", "", ""),
        (solution.culprit, solution.weapon, solution.location),
        (ev.culprit_correct, ev.weapon_correct, ev.location_correct),
    )


def fallback_verdict(session: GameSession, ev: Evaluation) -> str:
    outcome = "Case solved" if ev.won else "Case not solved"
    paragraphs = [f"{outcome}. {score_label(ev)}."]
    rows = list(accusation_rows(session, ev))
    for label, guess, actual, correct in rows:
        detail = f"{guess} was correct." if correct else f"You chose {guess}. The correct answer was {actual}."
        paragraphs.append(f"{label} — {detail}")
    if ev.found_clues:
        paragraphs.append(f"You had this in your notes. {ev.found_clues[-1].scene_text}")
    if ev.missed_clues:
        wrong_choices = {guess for _, guess, _, correct in rows if not correct}
        missed = next((clue for clue in ev.missed_clues if clue.eliminates in wrong_choices), None)
        if missed:
            paragraphs.append(f"A missed lead could have ruled out {missed.eliminates}. {missed.scene_text}")
        else:
            paragraphs.append(f"One lead stayed tucked under a paw. {ev.missed_clues[0].scene_text}")
    if ev.score_breakdown:
        metrics = ev.score_breakdown.metrics
        strength = next((e for e in metrics.reasoning_events if e.is_supported and not e.is_duplicate), None)
        if strength:
            paragraphs.append(f"You demonstrated {prompts.REASONING_LABELS[strength.reasoning_type].lower()}.")
        elif metrics.productive:
            paragraphs.append(f"Your questions brought out new leads in {metrics.productive} exchanges.")
        elif metrics.meaningful:
            paragraphs.append(f"You pursued {metrics.meaningful} meaningful lines of inquiry.")
        elif ev.won and metrics.meaningful == 0:
            paragraphs.append("A sharp guess can land on its paws. Build a trail of evidence next time.")
        if metrics.redundant:
            paragraphs.append("Try checking a fresh lead when a witness has already answered.")
    else:
        paragraphs.append("The accusation is recorded. I’m still missing part of the investigation review.")
    return "\n\n".join([*paragraphs, prompts.VERDICT_SIGNATURE])


def _verdict_is_consistent(text: str, ev: Evaluation, session: GameSession) -> bool:
    lines = text.splitlines()
    status = "Case solved" if ev.won else "Case not solved"
    if not lines or lines[0].strip() != f"{status} — {score_label(ev)}":
        return False
    if not text.endswith(prompts.VERDICT_SIGNATURE) or len(text.split()) >= 200:
        return False
    body = " ".join(lines[1:-1]).casefold()
    contrary = (
        r"\b(?:case not solved|did(?: not|n't) solve|failed to solve|you lost)\b" if ev.won else
        r"\b(?:case solved|you (?:solved|cracked|won)|all three (?:were )?correct|spot-on)\b"
    )
    if re.search(contrary, body):
        return False
    if any(score != score_label(ev) for score in re.findall(r"\b\d+(?:\.\d+)?/100\b", text)):
        return False
    return all(correct or (guess.casefold() in body and actual.casefold() in body)
               for _, guess, actual, correct in accusation_rows(session, ev))


def submit_accusation(
    session: GameSession, client, accused: tuple[str, str, str] | None = None, explanation: str = "",
    *, config: ScoringConfig = DEFAULT_SCORING, retry: bool = False,
    checkpoint=None,
) -> Evaluation:
    ev = session.result
    if ev is not None and (ev.score_status == "complete" or (ev.score_status == "incomplete" and not retry)):
        return ev
    if ev is None:
        if accused is None:
            raise ValueError("An accusation is required.")
        ev = evaluate_accusation(session, *accused)
        tracked = sum(t.counts_game_turn for t in session.investigation)
        # Old sessions have no reliable pre-turn snapshots. Never approximate them from later evidence.
        session.investigation_history_complete = session.turns <= tracked and (
            session.hints_used == len(session.delivered_hints)
        )
        add_final_explanation(session, explanation[:config.explanation_limit])
        session.scoring_snapshot = config.model_dump(mode="json")
        session.result = ev
        if checkpoint is not None:
            checkpoint(session)
    elif session.scoring_snapshot is not None:
        config = ScoringConfig.model_validate(session.scoring_snapshot)

    breakdown = None
    if session.investigation_history_complete:
        if any(turn.status != "complete" for turn in session.investigation):
            try:
                evaluator = get_evaluator_client(
                    client, config.evaluation_timeout,
                    local_timeout=config.local_evaluation_timeout,
                    local_batch_size=config.local_batch_size,
                )
            except Exception:
                log.warning("Could not initialize investigation evaluator", exc_info=True)
                evaluator = None
            evaluate_pending(session, evaluator, config, checkpoint=checkpoint)
        breakdown = calculate_final_score(session, ev, config)

    ev = ev.model_copy(update={
        "score": breakdown.total if breakdown else None,
        "score_breakdown": breakdown,
        "score_status": "complete" if breakdown else "incomplete",
    })
    session.result = ev.model_copy(update={"verdict": fallback_verdict(session, ev)})
    if checkpoint is not None:
        checkpoint(session)
    verdict = ""
    if breakdown:
        try:
            verdict = safe_complete(
                client, prompts.GM_SYSTEM,
                [{"role": "user", "content": prompts.verdict_prompt(session, ev, ev.accused)}],
                None,
            ) or ""
        except Exception:
            log.warning("Could not generate verdict", exc_info=True)
    if _verdict_is_consistent(verdict, ev, session):
        session.result = ev.model_copy(update={"verdict": verdict})
    return session.result
