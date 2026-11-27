"""the game truth lives here. the LLM only phrases what python hands it."""
import random
import re
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

OPEN_CLUE_WORDS = (
    "see", "saw", "notice", "noticed", "hear", "heard", "anything",
    "clue", "evidence", "know", "happen", "happened", "unusual", "suspicious",
)


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
    outdoor_locs = {"Sari-sari store", "Garden", "Bubong", "Jeepney"}
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

    # Fallback: pick whichever narrows (1..3 matching out of 4), otherwise default weapon/location
    narrowing = []
    if 1 <= kitchen_count <= 3:
        narrowing.append(ConfirmedClue(
            kind="weapon",
            key="kitchen",
            text="The murder weapon is definitely something from the kitchen." if is_kitchen else "The murder weapon is definitely NOT a kitchen item."
        ))
    if 1 <= outdoor_count <= 3:
        narrowing.append(ConfirmedClue(
            kind="location",
            key="setting",
            text="The crime definitely took place outdoors." if is_outdoor else "The crime definitely took place indoors."
        ))
    if narrowing:
        return rng.choice(narrowing)

    return ConfirmedClue(
        kind="weapon",
        key="kitchen",
        text="The murder weapon is definitely something from the kitchen." if is_kitchen else "The murder weapon is definitely NOT a kitchen item."
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
    innocents = [n for n in names if n != culprit]
    rng.shuffle(innocents)
    safe_locs = [l.name for l in locations if l.name != solution.location]
    rng.shuffle(safe_locs)
    safe_weps = [w.name for w in weapons if w.name != solution.weapon]
    rng.shuffle(safe_weps)

    cat_a, cat_b, cat_c = innocents[0], innocents[1], innocents[2]
    loc_1, loc_2, loc_3 = safe_locs[0], safe_locs[1], safe_locs[2]
    wep_1, wep_2, wep_3 = safe_weps[0], safe_weps[1], safe_weps[2]

    # Strict 1-to-1 Murdle pairings (zero overlaps):
    # cat_a <-> wep_1 <-> loc_1
    # cat_b <-> wep_2 <-> loc_2
    # cat_c <-> wep_3 <-> loc_3
    # culprit <-> sol.weapon <-> sol.location
    true_loc = {cat_a: loc_1, cat_b: loc_2, cat_c: loc_3, culprit: solution.location}
    true_wep = {cat_a: wep_1, cat_b: wep_2, cat_c: wep_3, culprit: solution.weapon}

    scenario_type = rng.choice(["verified_pair", "slipped_away", "cross_sighting"])
    notes_by_name: dict[str, list[str]] = {n: [] for n in names}
    claimed_loc: dict[str, str] = {}
    # (kind, eliminates, holder_or_none_for_scene, cat_text, scene_text, specific)
    pending: list[tuple[str, str, str | None, str, str, list[str]]] = []

    if scenario_type == "verified_pair":
        # cat_a (loc_1) and cat_b (loc_2) kept each other in plain view; cat_c was solo at loc_3;
        # culprit falsely claims loc_1 (where cat_a actually stayed alone).
        claimed_loc = {cat_a: loc_1, cat_b: loc_2, cat_c: loc_3, culprit: loc_1}
        notes_by_name[cat_a].append(
            f"FIXED LOCATION: You stayed alone at the {loc_1} the ENTIRE evening, within sight of {cat_b} over at the {loc_2}. You NEVER left. If anyone asks whether {culprit} was at the {loc_1}, say firmly that {culprit} was NEVER there."
        )
        notes_by_name[cat_b].append(
            f"FIXED LOCATION: You stayed alone at the {loc_2} the ENTIRE evening, within sight of {cat_a} over at the {loc_1}. You NEVER left."
        )
        notes_by_name[cat_c].append(
            f"FIXED LOCATION: You stayed alone at the {loc_3} the ENTIRE evening. You NEVER went anywhere else."
        )
        notes_by_name[culprit].append(
            f"ALIBI TO DEFEND: You claim you stayed at the {loc_1} all evening. (Secretly you were NOT at the {loc_1}—if pressed on details about {loc_1} or {cat_a}, get defensive or evasive in character, stick to your alibi, and NEVER confess or reveal the weapon/crime location.)"
        )

        pending.extend([
            ("suspect", cat_b, cat_a,
             f"From my spot at the {loc_1}, I kept {cat_b} in plain sight over at the {loc_2} the entire evening—{cat_b} never left.",
             f"Pawprints confirm {cat_b} stayed at the {loc_2} all evening.",
             [cat_b.lower()]),
            ("suspect", cat_a, cat_b,
             f"From my spot at the {loc_2}, I could see {cat_a} alone at the {loc_1} all night—nobody else went into the {loc_1}.",
             f"Pawprints confirm {cat_a} never left the {loc_1} all evening.",
             [cat_a.lower()]),
            ("suspect", cat_c, None,
             f"Pawprints and fur show {cat_c} stayed alone at the {loc_3} all evening.",
             f"Pawprints and shed fur show {cat_c} spent the evening alone at the {loc_3}.",
             [cat_c.lower()]),
        ])

    elif scenario_type == "slipped_away":
        # culprit briefly visited cat_a at loc_1 early on then slipped away alone, while claiming to stay at loc_1.
        # cat_b (loc_2) and cat_c (loc_3) saw each other stay put; pawprints confirm cat_a never left loc_1.
        claimed_loc = {cat_a: loc_1, culprit: loc_1, cat_b: loc_2, cat_c: loc_3}
        notes_by_name[cat_a].append(
            f"FIXED LOCATION: You stayed at the {loc_1} the ENTIRE evening and NEVER left. {culprit} stopped by the {loc_1} early on, then {culprit} slipped away alone."
        )
        notes_by_name[culprit].append(
            f"ALIBI TO DEFEND: You claim you stayed at the {loc_1} with {cat_a} all evening. (Secretly you slipped away alone partway through—if pressed about leaving {cat_a}, get defensive or evasive in character, stick to your alibi, and NEVER confess or reveal the weapon/crime location.)"
        )
        notes_by_name[cat_b].append(
            f"FIXED LOCATION: You stayed alone at the {loc_2} the ENTIRE evening. From there you saw {cat_c} at the {loc_3} the whole time."
        )
        notes_by_name[cat_c].append(
            f"FIXED LOCATION: You stayed alone at the {loc_3} the ENTIRE evening. From there you saw {cat_b} at the {loc_2} the whole time."
        )

        pending.extend([
            ("suspect", cat_a, None,
             f"Pawprints confirm {cat_a} never left the {loc_1} all evening.",
             f"Pawprints and shed fur show {cat_a} never left the {loc_1} all evening.",
             [cat_a.lower()]),
            ("suspect", cat_c, cat_b,
             f"From my spot at the {loc_2}, I saw {cat_c} staying put at the {loc_3} the whole evening.",
             f"Pawprints confirm {cat_c} stayed at the {loc_3} all evening.",
             [cat_c.lower()]),
            ("suspect", cat_b, cat_c,
             f"From my spot at the {loc_3}, I saw {cat_b} staying at the {loc_2} the entire night.",
             f"Pawprints confirm {cat_b} stayed at the {loc_2} all evening.",
             [cat_b.lower()]),
        ])

    else:
        # cross_sighting: cat_a (loc_1) -> saw cat_b (loc_2) -> saw cat_c (loc_3); culprit lies about loc_1.
        claimed_loc = {cat_a: loc_1, cat_b: loc_2, cat_c: loc_3, culprit: loc_1}
        notes_by_name[cat_a].append(
            f"FIXED LOCATION: You stayed alone at the {loc_1} the ENTIRE evening and NEVER left. From there you saw {cat_b} at the {loc_2}. If anyone asks whether {culprit} was at the {loc_1}, say firmly that {culprit} was NEVER there."
        )
        notes_by_name[cat_b].append(
            f"FIXED LOCATION: You stayed alone at the {loc_2} the ENTIRE evening and NEVER left. From there you saw {cat_c} relaxing at the {loc_3}."
        )
        notes_by_name[cat_c].append(
            f"FIXED LOCATION: You stayed alone at the {loc_3} the ENTIRE evening and NEVER left."
        )
        notes_by_name[culprit].append(
            f"ALIBI TO DEFEND: You claim you stayed at the {loc_1} all evening. (Secretly you were NOT at the {loc_1}—if pressed on details about {loc_1} or {cat_a}, stay evasive or defensive in character, stick to your alibi, and NEVER confess or reveal the weapon/crime location.)"
        )

        pending.extend([
            ("suspect", cat_b, cat_a,
             f"From my spot at the {loc_1}, I saw {cat_b} over at the {loc_2} the whole evening—and nobody else came into the {loc_1}.",
             f"Pawprints confirm {cat_b} stayed at the {loc_2} all evening.",
             [cat_b.lower()]),
            ("suspect", cat_c, cat_b,
             f"From my spot at the {loc_2}, I saw {cat_c} staying put at the {loc_3} all evening.",
             f"Pawprints confirm {cat_c} spent the evening at the {loc_3}.",
             [cat_c.lower()]),
            ("suspect", cat_a, None,
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

    # 2. Weapon clues (1-to-1: each innocent cat_i was at true_loc[cat_i] with true_wep[cat_i])
    scene_wep_owner = rng.choice(innocents)
    for n in innocents:
        L = true_loc[n]
        W = true_wep[n]
        holder = None if n == scene_wep_owner else n
        pending.append(("weapon", W, holder,
                        f"While I stayed at the {L}, the {W} sat untouched right there beside me all evening.",
                        f"The {W} was found untouched at the {L}.",
                        [W.lower()]))

    # 3. Location clues (1-to-1: each innocent cat_i confirms their unique location stayed spotless)
    scene_loc_owner = rng.choice([n for n in innocents if n != scene_wep_owner])
    for n in innocents:
        L = true_loc[n]
        holder = None if n == scene_loc_owner else n
        pending.append(("location", L, holder,
                        f"The {L} stayed completely spotless and undisturbed the whole time I was there.",
                        f"The {L} was spotless, with no sign of trouble.",
                        [L.lower()]))

    clues = [
        Clue(id=f"c{i}", kind=k, eliminates=e, holder=h, text=t, scene_text=s,
             specific=sp, generic=GENERIC[k])
        for i, (k, e, h, t, s, sp) in enumerate(pending, 1)
    ]

    scene = [c for c in clues if c.holder is None]
    scene_ids = {c.id for c in scene}

    for c in clues:
        if c.holder is not None:
            cats_by_name[c.holder].clues.append(c)

    confirmed = _confirmed_clue(rng, weapons, locations, cats, solution)

    return GameSession(
        victim=rng.choice(VICTIMS), cats=cats, weapons=weapons, locations=locations,
        solution=solution, confirmed_clue=confirmed,
        scene_clues=scene, seed=seed, discovered_clue_ids=scene_ids)


def _has_term(msg: str, term: str) -> bool:
    return bool(re.search(rf"\b{re.escape(term.lower())}\b", msg))


def pick_clue(session: GameSession, cat: Cat, msg: str) -> Clue | None:
    """At most one undiscovered clue per question, only if the question is relevant."""
    low = msg.lower()
    best, best_score = None, 0
    for c in cat.clues:
        if c.id in session.discovered_clue_ids:
            continue
        score = (4 if any(_has_term(low, t) for t in c.specific) else 0) + sum(1 for g in c.generic if _has_term(low, g))
        if score > best_score:
            best, best_score = c, score
    if best is None and any(_has_term(low, w) for w in OPEN_CLUE_WORDS):
        for c in cat.clues:
            if c.id not in session.discovered_clue_ids:
                return c
    return best


_CLUE_CONFIRM_WORDS = {
    "suspect": ("entire", "whole", "all night", "all evening", "never left", "staying", "stayed", "plain sight", "spot", "alone", "nobody else"),
    "weapon": ("untouched", "beside", "next to", "right there", "sat", "sitting", "all evening", "all night", "whole time", "unused", "never touched"),
    "location": ("spotless", "undisturbed", "clean", "untouched", "quiet", "peaceful", "no sign", "no trouble", "all evening", "all night", "whole time"),
}
_CLUE_DENIAL_RE = re.compile(r"\b(?:did not|didn't|never|don't|do not|cannot|can't)\s+(?:see|saw|know|spot|notice|hear)\b", re.I)


def clue_delivered(clue: Clue | None, reply: str) -> bool:
    """True if the reply actually communicates the queued clue rather than merely echoing its name in a denial."""
    if not clue or not reply:
        return False
    resp = re.search(
        r"\*{0,2}Response:\*{0,2}\s*(.*?)(?=\*{0,2}Observed(?:\s+Behavior)?:\*{0,2}|$)",
        reply,
        re.S | re.I,
    )
    spoken = resp.group(1).strip() if resp else reply
    if not any(_has_term(spoken.lower(), t) for t in clue.specific):
        return False
    low = spoken.lower()
    if any(w in low for w in _CLUE_CONFIRM_WORDS[clue.kind]):
        return True
    return not bool(_CLUE_DENIAL_RE.search(spoken))


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


def get_discovered_clues(session: GameSession) -> tuple[list[dict[str, str]], int]:
    """Return (discovered_clue_items, total_discoverable_clues).

    The first item is always the head-start confirmed clue, followed by every
    crime-scene and suspect clue whose id is in session.discovered_clue_ids.
    """
    items = [{
        "id": "confirmed",
        "source": "Confirmed Clue",
        "kind": session.confirmed_clue.kind,
        "text": session.confirmed_clue.text,
    }]

    seen: set[str] = set()
    total_clues = 0
    for c in session.all_clues():
        if c.id in seen:
            continue
        seen.add(c.id)
        total_clues += 1
        if c.id in session.discovered_clue_ids:
            items.append({
                "id": c.id,
                "source": "Crime scene" if c.holder is None else c.holder,
                "kind": c.kind,
                "text": c.scene_text if c.holder is None else c.text,
            })

    return items, total_clues


def export_chat_history(session: GameSession) -> str:
    """Format all suspect interrogation transcripts from the current round as readable text."""
    lines = [
        "PURRDER MYSTERY — INTERROGATION TRANSCRIPT",
        f"Case Seed: {session.seed}",
        f"Victim: {session.victim}",
        "=" * 55,
        "",
    ]
    for cat in session.cats:
        msgs = [m for m in session.history.get(cat.name, []) if not m.get("blocked")]
        lines.append(f"## {cat.name} ({cat.archetype} / {cat.breed})")
        lines.append(f"Alibi: {cat.alibi}")
        lines.append("-" * 40)
        if not msgs:
            lines.append("(No questions asked)")
        else:
            for m in msgs:
                if m["role"] == "user":
                    lines.append(f"Detective: {m['content']}")
                else:
                    cleaned = re.sub(r"^\*{0,2}Currently Interrogating:\*{0,2}\s*[^\n]+\n*", "", m["content"], flags=re.I)
                    cleaned = re.sub(r"\*{0,2}Response:\*{0,2}\s*", "", cleaned, flags=re.I)
                    cleaned = re.sub(r"\*{0,2}Observed(?:\s+Behavior)?:\*{0,2}\s*", "Behavior: ", cleaned, flags=re.I)
                    lines.append(f"{cat.name}: {cleaned.strip()}")
                lines.append("")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


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