from datetime import datetime, timezone
import logging
import re

from game import get_discovered_clues, next_hint
from guard import looks_like_injection, normalize, safe_complete
from models import GameSession
from scoring_models import DeliveredHint, InvestigationTurn, TurnAssessment

log = logging.getLogger(__name__)
_SCORING_INSTRUCTION = re.compile(
    r"\b(?:give me|assign me|set my|change my|mark (?:this|my)|pretend I discovered)\b"
    r".{0,45}\b(?:score|points?|analytical|clues?)\b", re.I,
)


def begin_turn(
    session: GameSession, message: str, suspect: str | None, request_id: str,
    *, blocked: bool = False,
) -> InvestigationTurn | None:
    if session.result is not None or any(t.id == request_id for t in session.investigation):
        return None
    turn = InvestigationTurn(
        id=request_id,
        number=len(session.investigation) + 1,
        player_message=message,
        suspect=suspect,
        counts_game_turn=suspect is not None and not blocked,
        timestamp=datetime.now(timezone.utc),
        clue_ids_before={item["id"] for item in get_discovered_clues(session)[0]},
        testimony_ids_before=set(session.testimony) | {f"alibi:{c.name}" for c in session.cats},
    )
    if blocked or looks_like_injection(message) or _SCORING_INSTRUCTION.search(normalize(message)):
        turn.status = "complete"
        turn.assessment = TurnAssessment(
            turn_id=turn.id, message_type="irrelevant", questions=[], reasoning_events=[],
        )
    session.investigation.append(turn)
    return turn


def finish_turn(session: GameSession, turn: InvestigationTurn, reply: str, *, testimony: bool) -> None:
    if session.result is not None:
        return
    turn.npc_response = reply
    turn.new_clue_ids = session.discovered_clue_ids - turn.clue_ids_before
    if testimony and reply:
        session.testimony[f"reply:{turn.id}"] = reply


def add_final_explanation(session: GameSession, explanation: str) -> None:
    if explanation := normalize(explanation):
        begin_turn(session, explanation, None, "accusation-explanation")


def deliver_hint(session: GameSession, client) -> DeliveredHint | None:
    from prompts import GM_SYSTEM, hint_prompt

    hint = next_hint(session)
    if hint is None:
        return None
    level, text = hint
    try:
        reply = safe_complete(
            client, GM_SYSTEM, [{"role": "user", "content": hint_prompt(level, text)}],
            session.solution, max_tokens=180,
        )
    except Exception:
        log.warning("Hint wording unavailable; using the original hint", exc_info=True)
        reply = None
    if level == 1:
        kind = "directional" if session.discovered_clue_ids < {c.id for c in session.all_clues()} else "suggestion"
    else:
        kind = "specific"
    delivered = DeliveredHint(level=level, text=reply or text, kind=kind)
    session.delivered_hints.append(delivered)
    session.testimony[f"hint:{level}"] = delivered.text
    return delivered
