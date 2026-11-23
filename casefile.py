"""Builds the 'Clues & Evidence' board. python owns the facts; the LLM only rewrites them,so every round reads differently but stays true and solvable."""
import re
from models import GameSession
from guard import leaks_solution
import prompts


def evidence_facts(s: GameSession) -> list[tuple[str, str]]:
    """(true fact, word the rewrite must keep). Crime-scene clues first, confirmed clue last."""
    facts = [(c.scene_text, c.eliminates) for c in s.scene_clues]
    facts.append((s.confirmed_clue.text, s.confirmed_clue.key))
    return facts


def parse_bullets(raw: str) -> list[str]:
    out = []
    for line in raw.splitlines():
        m = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.*\S)\s*$", line)
        if m:
            out.append(m.group(1).replace("**", "").strip())
    return out


def valid_evidence(bullets: list[str], facts: list[tuple[str, str]], s: GameSession) -> bool:
    if len(bullets) != len(facts):
        return False
    for b, (_, key) in zip(bullets, facts):
        if key.lower() not in b.lower() or len(b) < 15:
            return False
    return not leaks_solution("\n".join(bullets), s.solution)


def generate_evidence(client, s: GameSession, retries: int = 2) -> list[str]:
    facts = evidence_facts(s)
    for _ in range(retries + 1):
        try:
            bullets = parse_bullets(client.complete(prompts.GM_SYSTEM,
                                                    [{"role": "user", "content": prompts.evidence_prompt(s, facts)}],
                                                    600))
        except Exception:
            break
        if valid_evidence(bullets, facts, s):
            return bullets
    return [t for t, _ in facts]            # safe fallback
