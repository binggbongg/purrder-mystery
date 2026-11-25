"""the game truth lives here. the LLM only phrases what python hands it."""
import random
from models import Dataset, Cat, Clue, ConfirmedClue, Solution, GameSession, Evaluation

VICTIMS = [
    "Goldie, the household's prized goldfish",
    "Pipit, the neighborhood's favorite pet maya bird",
    "Mochi, the pampered show guinea pig",
]

ALIBI_TEMPLATES = [
    "I was hanging out at the {L} all evening, minding my own business.",
    "I spent the whole night near the {L}. Ask anyone.",
    "I never left the {L} once—not even for merienda.",
]

GENERIC = {
    "suspect": ["alibi", "saw", "seen", "where", "who", "witness"],
    "weapon": ["weapon", "tool", "object", "found", "used"],
    "location": ["room", "place", "scene", "location", "clean", "spotless"],
}


def _confirmed_clue(rng, weapons, locations, cats, sol, scene_clues: list[Clue]) -> ConfirmedClue:
    """One always-true head-start clue that rules out an innocent option without repeating scene clues."""
    already_eliminated = {c.eliminates for c in scene_clues}
    options: list[ConfirmedClue] = []

    for c in cats:
        if c != sol.culprit and c not in already_eliminated:
            options.append(ConfirmedClue(
                kind="suspect", key=c,
                text=f"{c} is definitely NOT the culprit."
            ))
    for w in weapons:
        if w.name != sol.weapon and w.name not in already_eliminated:
            options.append(ConfirmedClue(
                kind="weapon", key=w.name,
                text=f"The {w.name} was definitely NOT the murder weapon."
            ))
    for l in locations:
        if l.name != sol.location and l.name not in already_eliminated:
            options.append(ConfirmedClue(
                kind="location", key=l.name,
                text=f"The crime definitely did NOT take place at the {l.name}."
            ))

    if options:
        return rng.choice(options)

    innocent = rng.choice([c for c in cats if c != sol.culprit])
    return ConfirmedClue(kind="suspect", key=innocent, text=f"{innocent} is definitely NOT the culprit.")


def new_game(dataset: Dataset, seed: int | None = None) -> GameSession:
    seed = random.randrange(10**9) if seed is None else seed
    rng = random.Random(seed)
    profiles = rng.sample(dataset.suspects, 4)
    weapons = rng.sample(dataset.weapons, 4)
    locations = rng.sample(dataset.locations, 4)
    names = [p.name for p in profiles]

    solution = Solution(culprit=rng.choice(names), weapon=rng.choice(weapons).name,
                        location=rng.choice(locations).name)
    culprit = solution.culprit
    safe_locs = [l.name for l in locations if l.name != solution.location]

    # Everyone claims a (non-crime) location. Only innocents get a witness clue.
    alibi_loc = {n: rng.choice(safe_locs) for n in names}
    cats = [Cat(**p.model_dump(),
                alibi=rng.choice(ALIBI_TEMPLATES).format(L=alibi_loc[p.name])) for p in profiles]

    # Elimination clues: each innocent suspect / weapon / location is ruled out once.
    pending = []   # (kind, eliminates, cat_text, scene_text, specific)
    for n in names:
        if n != culprit:
            L = alibi_loc[n]
            pending.append(("suspect", n,
                            f"I saw {n} over at the {L} the whole evening, so it couldn't have been them.",
                            f"Pawprints and shed fur show {n} spent the evening at the {L}.",
                            [n.lower(), n.split()[-1].lower()]))
    for w in weapons:
        if w.name != solution.weapon:
            L = rng.choice(safe_locs)
            pending.append(("weapon", w.name,
                            f"The {w.name} was still sitting by the {L}, completely untouched.",
                            f"The {w.name} was found untouched at the {L}.",
                            [w.name.lower()]))
    for L in safe_locs:
        pending.append(("location", L,
                        f"I passed by the {L} earlier and nothing was out of place—completely spotless.",
                        f"The {L} was spotless, with no sign of trouble.",
                        [L.lower()]))

    clues = [Clue(id=f"c{i}", kind=k, eliminates=e, text=t, scene_text=s,
                  specific=sp, generic=GENERIC[k]) for i, (k, e, t, s, sp) in enumerate(pending, 1)]

    # One clue per category is crime-scene evidence; the rest are held by cats.
    scene = [rng.choice([c for c in clues if c.kind == k]) for k in ("suspect", "weapon", "location")]
    scene_ids = {c.id for c in scene}
    rr = rng.sample(names, 4)
    i = 0
    for c in clues:
        if c.id in scene_ids:
            continue
        if c.kind == "suspect":
            c.holder = rng.choice([n for n in names if n != c.eliminates])
        else:
            c.holder, i = rr[i % 4], i + 1
        next(cat for cat in cats if cat.name == c.holder).clues.append(c)

    confirmed = _confirmed_clue(rng, weapons, locations, names, solution, scene)

    return GameSession(
        victim=rng.choice(VICTIMS), cats=cats, weapons=weapons, locations=locations,
        solution=solution, confirmed_clue=confirmed,
        scene_clues=scene, seed=seed, discovered_clue_ids=scene_ids)


def pick_clue(session: GameSession, cat: Cat, msg: str) -> Clue | None:
    """At most one undiscovered clue per question, only if the question is relevant."""
    msg, best, best_score = msg.lower(), None, 0
    for c in cat.clues:
        if c.id in session.discovered_clue_ids:
            continue
        score = (3 if any(t in msg for t in c.specific) else 0) + sum(1 for g in c.generic if g in msg)
        if score > best_score:
            best, best_score = c, score
    return best


def next_hint(session: GameSession) -> tuple[int, str] | None:
    """3-level ladder: nudge -> clears one innocent -> narrows to two. Never the answer."""
    level = session.hints_used + 1
    if level > 3:
        return None
    sol = session.solution
    innocents = [c.name for c in session.cats if c.name != sol.culprit]
    if level == 1:
        left = [c for c in session.all_clues() if c.id not in session.discovered_clue_ids]
        if left:
            c = left[0]
            text = f"{c.holder} knows something about a {c.kind} you haven't asked about yet."
        else:
            text = "You've heard every clue. Time to put them together!"
    else:
        a = random.Random(session.seed + 2).choice(innocents)
        if level == 2:
            text = f"{a} is NOT the culprit."
        else:
            b = random.Random(session.seed + 3).choice([i for i in innocents if i != a])
            pair = sorted([sol.culprit, b], key=lambda x: random.Random(session.seed + 4).random())
            text = f"The culprit is one of these two: {pair[0]} or {pair[1]}."
    session.hints_used = level
    return level, text


def _match(value: str, options: list[str], label: str) -> str:
    v = value.strip().lower()
    for o in options:
        if o.lower() == v:
            return o
    hits = [o for o in options if v and v in o.lower()]
    if len(hits) == 1:
        return hits[0]
    raise ValueError(f"'{value}' is not an active {label}. Options: {', '.join(options)}")


def evaluate_accusation(session: GameSession, suspect: str, weapon: str, location: str) -> Evaluation:
    s = _match(suspect, [c.name for c in session.cats], "suspect")
    w = _match(weapon, [x.name for x in session.weapons], "weapon")
    l = _match(location, [x.name for x in session.locations], "location")
    sol = session.solution
    cc, wc, lc = s == sol.culprit, w == sol.weapon, l == sol.location
    found = [c for c in session.all_clues() if c.id in session.discovered_clue_ids]
    missed = [c for c in session.all_clues() if c.id not in session.discovered_clue_ids]
    total = len(found) + len(missed)
    score = 20 * (cc + wc + lc) + (round(40 * len(found) / total) if total else 0)
    return Evaluation(culprit_correct=cc, weapon_correct=wc, location_correct=lc,
                      score=score, found_clues=found, missed_clues=missed)