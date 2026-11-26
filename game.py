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
    "I never left the {L} once—not even for a snack.",
    "I was curled up by the {L} the entire time, completely out of the way.",
]

GENERIC = {
    "suspect": ["alibi", "saw", "seen", "where", "who", "witness"],
    "weapon": ["weapon", "tool", "object", "found", "used"],
    "location": ["room", "place", "scene", "location", "clean", "spotless"],
}


def _confirmed_clue(rng, weapons, locations, cats: list[Cat], sol: Solution) -> ConfirmedClue:
    """One always-true head-start clue narrowing down the weapon or location—never about the suspects."""
    options: list[ConfirmedClue] = []

    # 1. Weapon category clues (only when it narrows the 4 active weapons down to 2-3)
    kitchen_weapons = {"Kawali", "Sandok", "Kandila"}
    is_kitchen = sol.weapon in kitchen_weapons
    kitchen_count = sum(1 for w in weapons if w.name in kitchen_weapons)
    if 2 <= kitchen_count <= 3:
        options.append(ConfirmedClue(
            kind="weapon",
            key="kitchen",
            text="The murder weapon is definitely something from the kitchen." if is_kitchen else "The murder weapon is definitely NOT a kitchen item."
        ))

    play_weapons = {"Laser pointer", "Scratching post"}
    is_play = sol.weapon in play_weapons
    play_count = sum(1 for w in weapons if w.name in play_weapons)
    if 2 <= play_count <= 3:
        options.append(ConfirmedClue(
            kind="weapon",
            key="play",
            text="The murder weapon is definitely a cat toy or scratching item." if is_play else "The murder weapon is definitely NOT a cat toy or scratching item."
        ))

    # 2. Location setting clues (only when it narrows the 4 active locations down to 2-3)
    outdoor_locs = {"Garden", "Bubong", "Jeepney"}
    is_outdoor = sol.location in outdoor_locs
    outdoor_count = sum(1 for l in locations if l.name in outdoor_locs)
    if 2 <= outdoor_count <= 3:
        options.append(ConfirmedClue(
            kind="location",
            key="setting",
            text="The crime definitely took place outdoors." if is_outdoor else "The crime definitely took place indoors."
        ))

    elevated_locs = {"Bubong", "Cat tree", "Sunny windowsill"}
    is_elevated = sol.location in elevated_locs
    elevated_count = sum(1 for l in locations if l.name in elevated_locs)
    if 2 <= elevated_count <= 3:
        options.append(ConfirmedClue(
            kind="location",
            key="elevated",
            text="The crime definitely happened up high off the floor." if is_elevated else "The crime definitely happened at ground level."
        ))

    if options:
        return rng.choice(options)

    # Fallback: guaranteed weapon or location clue (never suspect)
    return rng.choice([
        ConfirmedClue(
            kind="weapon",
            key=sol.weapon,
            text="The murder weapon is definitely something from the kitchen." if is_kitchen else "The murder weapon is definitely NOT a kitchen item."
        ),
        ConfirmedClue(
            kind="location",
            key=sol.location,
            text="The crime definitely took place outdoors." if is_outdoor else "The crime definitely took place indoors."
        ),
    ])

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
    innocents = [n for n in names if n != culprit]
    rng.shuffle(innocents)
    safe_locs = [l.name for l in locations if l.name != solution.location]
    rng.shuffle(safe_locs)

    cat_a, cat_b, cat_c = innocents[0], innocents[1], innocents[2]
    loc_1, loc_2, loc_3 = safe_locs[0], safe_locs[1], safe_locs[2]

    scenario_type = rng.choice(["verified_pair", "slipped_away", "cross_sighting"])
    notes_by_name: dict[str, list[str]] = {n: [] for n in names}
    claimed_loc: dict[str, str] = {}
    pending = []   # (kind, eliminates, cat_text, scene_text, specific)

    if scenario_type == "verified_pair":
        claimed_loc = {cat_a: loc_1, cat_b: loc_1, cat_c: loc_2, culprit: loc_3}
        notes_by_name[cat_a].append(f"You stayed at the {loc_1} with {cat_b} the entire evening. You never went anywhere else.")
        notes_by_name[cat_b].append(f"You stayed at the {loc_1} with {cat_a} the entire evening. You never went anywhere else.")
        notes_by_name[cat_c].append(f"You stayed alone at the {loc_2} the entire evening. You never went anywhere else.")
        notes_by_name[culprit].append(f"You claim you stayed alone at the {loc_3} the entire evening. Nobody was with you.")

        pending.extend([
            ("suspect", cat_b,
             f"I was at the {loc_1} with {cat_b} the entire evening—neither of us ever left.",
             f"Both {cat_a} and {cat_b} were confirmed together at the {loc_1} all evening.",
             [cat_b.lower()]),
            ("suspect", cat_a,
             f"I stayed at the {loc_1} with {cat_a} all night long.",
             f"Pawprints confirm {cat_a} never left the {loc_1} all evening.",
             [cat_a.lower()]),
            ("suspect", cat_c,
             f"Pawprints and fur show {cat_c} stayed alone at the {loc_2} all evening.",
             f"Pawprints and shed fur show {cat_c} spent the evening at the {loc_2}.",
             [cat_c.lower()]),
        ])

    elif scenario_type == "slipped_away":
        claimed_loc = {cat_a: loc_1, culprit: loc_1, cat_b: loc_2, cat_c: loc_2}
        notes_by_name[cat_a].append(
            f"You stayed at the {loc_1} all evening. {culprit} was with you early on, then {culprit} slipped away alone."
        )
        notes_by_name[culprit].append(
            f"You started at the {loc_1} with {cat_a} then snuck away alone, though you claim you stayed at the {loc_1} with {cat_a} all evening."
        )
        notes_by_name[cat_b].append(f"You stayed at the {loc_2} with {cat_c} the entire evening. You never went anywhere else.")
        notes_by_name[cat_c].append(f"You stayed at the {loc_2} with {cat_b} the entire evening. You never went anywhere else.")

        pending.extend([
            ("suspect", cat_a,
             f"Pawprints confirm {cat_a} never left the {loc_1} all evening.",
             f"Pawprints and shed fur show {cat_a} never left the {loc_1} all evening.",
             [cat_a.lower()]),
            ("suspect", cat_c,
             f"I was at the {loc_2} with {cat_c} the whole evening—we never separated.",
             f"Both {cat_b} and {cat_c} were confirmed together at the {loc_2} all evening.",
             [cat_c.lower()]),
            ("suspect", cat_b,
             f"I stayed at the {loc_2} with {cat_b} the entire night.",
             f"Pawprints confirm {cat_b} stayed at the {loc_2} all evening.",
             [cat_b.lower()]),
        ])

    else:
        claimed_loc = {cat_a: loc_1, cat_b: loc_2, cat_c: loc_3, culprit: loc_1}
        notes_by_name[cat_a].append(
            f"You stayed alone at the {loc_1} the entire evening. From there you saw {cat_b} at the {loc_2}, and {culprit} was NEVER at the {loc_1}."
        )
        notes_by_name[cat_b].append(
            f"You stayed alone at the {loc_2} the entire evening, and from there you saw {cat_c} relaxing at the {loc_3}."
        )
        notes_by_name[cat_c].append(
            f"You stayed alone at the {loc_3} the entire evening. You never went anywhere else."
        )
        notes_by_name[culprit].append(
            f"You falsely claim you stayed at the {loc_1} all evening, even though you were not there."
        )

        pending.extend([
            ("suspect", cat_b,
             f"From my spot at the {loc_1}, I saw {cat_b} over at the {loc_2} the whole evening—and nobody else came into the {loc_1}.",
             f"Pawprints confirm {cat_b} stayed at the {loc_2} all evening.",
             [cat_b.lower()]),
            ("suspect", cat_c,
             f"From my spot at the {loc_2}, I saw {cat_c} staying put at the {loc_3} all evening.",
             f"Pawprints confirm {cat_c} spent the evening at the {loc_3}.",
             [cat_c.lower()]),
            ("suspect", cat_a,
             f"Pawprints and shed fur show {cat_a} spent the evening alone at the {loc_1}.",
             f"Pawprints and shed fur show {cat_a} spent the evening alone at the {loc_1}.",
             [cat_a.lower()]),
        ])

    # Build Cat objects with matching alibis and scenario memory
    shuffled_templates = rng.sample(ALIBI_TEMPLATES, len(ALIBI_TEMPLATES))
    cats_by_name = {
        p.name: Cat(
            **p.model_dump(),
            alibi=shuffled_templates[i % len(shuffled_templates)].format(L=claimed_loc[p.name]),
            world_notes=notes_by_name[p.name],
        )
        for i, p in enumerate(profiles)
    }
    cats = [cats_by_name[n] for n in names]

    # 2. Weapon clues (only safe weapons, placed at safe locations)
    innocent_locs = [claimed_loc[n] for n in innocents]
    for idx, w in enumerate(w for w in weapons if w.name != solution.weapon):
        L = innocent_locs[idx % len(innocent_locs)]
        pending.append(("weapon", w.name,
                        f"While I was at the {L}, the {w.name} stayed sitting right there untouched all evening.",
                        f"The {w.name} was found untouched at the {L}.",
                        [w.name.lower()]))

    # 3. Location clues: each safe location stays clean
    for L in safe_locs:
        pending.append(("location", L,
                        f"The {L} stayed completely spotless and undisturbed the whole time I was there.",
                        f"The {L} was spotless, with no sign of trouble.",
                        [L.lower()]))

    clues = [Clue(id=f"c{i}", kind=k, eliminates=e, text=t, scene_text=s,
                  specific=sp, generic=GENERIC[k]) for i, (k, e, t, s, sp) in enumerate(pending, 1)]

    # Scene clues: pick the solo-trace suspect clue + 1 weapon + 1 location
    scene_sus = next(c for c in clues if c.kind == "suspect" and "Pawprints" in c.text)
    scene_wep = rng.choice([c for c in clues if c.kind == "weapon"])
    scene_loc = rng.choice([c for c in clues if c.kind == "location"])
    scene = [scene_sus, scene_wep, scene_loc]
    scene_ids = {c.id for c in scene}

    # Assign remaining clues ONLY to the cat who was actually at that location!
    for c in clues:
        if c.id in scene_ids:
            continue
        if c.kind == "suspect" and c.eliminates == cat_b:
            c.holder = cat_a
        elif c.kind == "suspect" and c.eliminates == cat_a:
            c.holder = cat_b
        else:
            witnesses = [n for n in innocents if claimed_loc[n].lower() in c.scene_text.lower()]
            c.holder = rng.choice(witnesses) if witnesses else rng.choice(innocents)

        holder_cat = cats_by_name[c.holder]
        holder_cat.clues.append(c)
        holder_cat.world_notes.append(c.text)

    # 3. Location clues (all 3 safe locations)
    for L in safe_locs:
        pending.append(("location", L,
                        f"I checked the {L} earlier and nothing was out of place—completely spotless.",
                        f"The {L} was spotless, with no sign of trouble.",
                        [L.lower()]))

    clues = [Clue(id=f"c{i}", kind=k, eliminates=e, text=t, scene_text=s,
                  specific=sp, generic=GENERIC[k]) for i, (k, e, t, s, sp) in enumerate(pending, 1)]

    # One clue per category goes to the Crime Scene Overview
    scene_sus = next(c for c in clues if c.kind == "suspect" and c.eliminates == cat_c)
    scene_wep = rng.choice([c for c in clues if c.kind == "weapon"])
    scene_loc = rng.choice([c for c in clues if c.kind == "location"])
    scene = [scene_sus, scene_wep, scene_loc]
    scene_ids = {c.id for c in scene}

    # Assign remaining clues to holders matching who actually witnessed them
    for c in clues:
        if c.id in scene_ids:
            continue
        if c.kind == "suspect" and c.eliminates == cat_b:
            c.holder = cat_a
        elif c.kind == "suspect" and c.eliminates == cat_a:
            c.holder = cat_b
        else:
            witnesses = [n for n in innocents if claimed_loc[n] in c.scene_text]
            c.holder = rng.choice(witnesses) if witnesses else rng.choice(innocents)

        holder_cat = cats_by_name[c.holder]
        holder_cat.clues.append(c)
        holder_cat.world_notes.append(f"What you also saw: {c.text}")

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
    score = round(100 * (cc + wc + lc) / 3)
    return Evaluation(culprit_correct=cc, weapon_correct=wc, location_correct=lc,
                      score=score, found_clues=found, missed_clues=missed)