"""the game truth lives here. the LLM only phrases what python hands it."""
import random
from models import Dataset, Cat, Clue, ConfirmedClue, Solution, GameSession, Evaluation

VICTIMS = [
    "Kapitan Mingming's prized bowl of bangus belly",
    "Goldie, Barangay Puspin's prized goldfish",
    "Pipit, the neighborhood's favorite pet maya bird",
]

ALIBI_TEMPLATES = [
    "I was hanging out at the {L} all evening, minding my own business.",
    "I spent the whole night near the {L}. Ask anyone.",
    "I never left the {L} once—not even for merienda.",
    "I was curled up by the {L} the entire time, completely out of the way.",
]

GENERIC = {
    "suspect": ["alibi", "saw", "seen", "where", "who", "witness"],
    "weapon": ["weapon", "tool", "object", "found", "used"],
    "location": ["room", "place", "scene", "location", "clean", "spotless"],
}


def _confirmed_clue(rng, weapons, locations, cats: list[Cat], sol: Solution) -> ConfirmedClue:
    """One always-true head-start clue based on a trait of the solution—never naming a suspect/weapon/location."""
    culprit_cat = next(c for c in cats if c.name == sol.culprit)
    options: list[ConfirmedClue] = []

    # 1. Suspect breed/coat trait clues (only if it narrows 4 suspects down to 2-3)
    is_puspin = "puspin" in culprit_cat.breed.lower()
    puspin_count = sum(1 for c in cats if "puspin" in c.breed.lower())
    if 2 <= puspin_count <= 3:
        options.append(ConfirmedClue(
            kind="suspect",
            key="puspin",
            text="The culprit is definitely a puspin." if is_puspin else "The culprit is definitely NOT a puspin."
        ))

    is_patterned = any(k in culprit_cat.breed.lower() for k in ("tabby", "calico"))
    patterned_count = sum(1 for c in cats if any(k in c.breed.lower() for k in ("tabby", "calico")))
    if 2 <= patterned_count <= 3:
        options.append(ConfirmedClue(
            kind="suspect",
            key="patterned",
            text="The culprit definitely has patterned fur." if is_patterned else "The culprit is definitely solid- or cream-coated."
        ))

    # 2. Weapon category clues
    kitchen_weapons = {"Kawali", "Sandok", "Kandila"}
    is_kitchen = sol.weapon in kitchen_weapons
    kitchen_count = sum(1 for w in weapons if w.name in kitchen_weapons)
    if 2 <= kitchen_count <= 3:
        options.append(ConfirmedClue(
            kind="weapon",
            key="kitchen",
            text="The murder weapon is definitely something from the kitchen." if is_kitchen else "The murder weapon is definitely NOT a kitchen item."
        ))

    # 3. Location setting clues
    outdoor_locs = {"Garden", "Bubong", "Jeepney"}
    is_outdoor = sol.location in outdoor_locs
    outdoor_count = sum(1 for l in locations if l.name in outdoor_locs)
    if 2 <= outdoor_count <= 3:
        options.append(ConfirmedClue(
            kind="location",
            key="setting",
            text="The crime definitely took place outdoors." if is_outdoor else "The crime definitely took place indoors."
        ))

    if options:
        return rng.choice(options)

    return ConfirmedClue(
        kind="weapon",
        key=sol.weapon,
        text="The culprit definitely used an everyday household object."
    )


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

    # Shuffle safe locations and templates so each cat gets a distinct alibi and spread-out locations
    shuffled_locs = rng.sample(safe_locs, len(safe_locs))
    shuffled_templates = rng.sample(ALIBI_TEMPLATES, len(ALIBI_TEMPLATES))

    alibi_loc = {n: shuffled_locs[i % len(shuffled_locs)] for i, n in enumerate(names)}
    cats = [
        Cat(
            **p.model_dump(),
            alibi=shuffled_templates[i % len(shuffled_templates)].format(L=alibi_loc[p.name])
        )
        for i, p in enumerate(profiles)
    ]

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

    confirmed = _confirmed_clue(rng, weapons, locations, cats, solution)

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