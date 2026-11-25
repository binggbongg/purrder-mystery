import re
from models import Solution

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"(developer|debug|admin|dan) mode",
    r"system prompt",
    r"reveal (the )?(solution|answer|culprit|killer)",
    r"who (is|was) the (killer|culprit|murderer)",
    r"you are now",
    r"act as (a|an) (?!cat)",
]
SAFE_DEFLECTION = ("*flicks tail and turns away* Hmm? I only talk about the case, darling. "
                   "Ask me about what I saw that evening.")


def looks_like_injection(text: str) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in INJECTION_PATTERNS)


def leaks_solution(reply: str, sol: Solution) -> bool:
    low = reply.lower()
    for sent in re.split(r"[.!?\n]+", low):          # one sentence naming all three
        if all(x.lower() in sent for x in (sol.culprit, sol.weapon, sol.location)):
            return True
    name = re.escape(sol.culprit.lower())
    return bool(re.search(rf"(culprit|killer|murderer)\s+(is|was)\s+(?:the\s+)?{name}\b", low)
                or re.search(rf"{name}\s+(is|was)\s+(the\s+)?(culprit|killer|murderer)\b", low))


STONEWALL_PATTERNS = [
    r"nothing (more |else )?to (add|say|share)",
    r"no comment",
    r"i have nothing",
    r"i('d| would) rather not (say|talk)",
]


def is_stonewall(reply: str) -> bool:
    """true for the lazy canned 'I have nothing to add' kind of answer."""
    resp = re.search(r'\*\*Response:\*\*\s*(.*?)(?:\*\*Observed|$)', reply, re.S)
    low = (resp.group(1) if resp else reply).lower()
    return any(re.search(p, low) for p in STONEWALL_PATTERNS) or len(low.split()) < 12


def safe_complete(client, system: str, messages: list[dict], sol: Solution | None,
                  retries: int = 2, max_tokens: int = 600, reject=None):
    """calls the LLM; retry on a leak (or when `reject(reply)` is true). returns None only if every attempt leaks; a merely rejected reply is still returned as a last resort."""
    fallback = None
    for _ in range(retries + 1):
        reply = client.complete(system, messages, max_tokens)
        if sol is not None and leaks_solution(reply, sol):
            continue
        if reject is None or not reject(reply):
            return reply
        fallback = reply
    return fallback
