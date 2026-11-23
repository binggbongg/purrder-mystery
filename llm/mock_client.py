"""Free offline stand-in for a real model. No API calls, no tokens.

It still reads the prompt it is given, so the overview, the evidence board and every suspect's
answer are built from THIS round's cast, weapons, locations and story. It is not smart, but it
never falls back to a stock "I have nothing to add" line."""
import hashlib
import random
import re


def _rng(*parts) -> random.Random:
    return random.Random(int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest(), 16))


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\*+", "", text).replace("\n", " ")
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]


def _lc(s: str) -> str:
    """Lower-case the first letter only for ordinary words, never for a suspect's name."""
    first = s.split(" ", 1)[0].lower()
    return s[:1].lower() + s[1:] if first in {"the", "a", "an", "pawprints", "there", "fur", "paw"} else s


# ------------------------------------------------------------------ overview
def _story(prompt: str) -> str:
    victim = re.search(r"Victim: (.+?)\.\n", prompt).group(1)
    vshort = victim.split(",")[0]
    cats = re.findall(r"^- (.+?): a (.+?), the (.+?) \((.+?); (.+?)\)$", prompt, re.M)
    weapons = re.findall(r"^- (.+?): (.+?) \(made of (.+?)\)$", prompt, re.M)
    places = re.findall(r"^- (.+?) \((indoors|outdoors)\): (.+)$", prompt, re.M)
    r = _rng(prompt)

    occasion = r.choice([
        "the Annual Whisker Gala, with paper lanterns swaying in the breeze",
        "a stormy birthday banquet, with thunder rattling every windowpane",
        "the Best Whiskers contest after-party, with ribbons and trophies everywhere",
        "a moonlit midsummer supper, with the whole household in their finest collars",
        "the grand opening of the manor's new tuna buffet, with a string quartet of crickets",
    ])
    mood = r.choice(["glittered with laughter", "hummed with gossip", "smelled of warm cream and trouble",
                     "buzzed with tail-flicking excitement"])
    p1 = (f"It was the night of {occasion}, and Whiskerton Manor {mood}. Guests purred, glasses clinked and "
          f"nobody suspected a thing. Then the music stopped, and a gasp rolled through the hall. "
          f"**{victim}** had been found lifeless, and the festivities ended on the spot. By morning the whole "
          f"household was whispering, and every paw in the manor seemed to be pointing somewhere different.")

    grudges = [
        f"had been overheard grumbling that {vshort} always got the best of everything",
        f"once quarreled loudly with {vshort} over a missing treat",
        f"owed {vshort} a favor and hated every minute of it",
        f"envied the attention {vshort} received at every gathering",
        f"was seen arguing with {vshort} only days before the party",
        f"swore that {vshort} had been snooping where no one should",
    ]
    r.shuffle(grudges)
    sus = []
    for i, (n, breed, role, zod, pers) in enumerate(cats):
        t = [x.strip().lower() for x in pers.split(",")]
        sus.append(f"**{n}**, the {breed} who serves as {role}, is {t[0]} and {t[-1]}, and {grudges[i % len(grudges)]}.")
    p2 = ("Four cats were under the manor's roof that night, and each of them had their reasons. "
          + " ".join(sus) + " Not one of them can be trusted at face value, which makes them all fascinating.")

    wl = " ".join(f"There was the **{n}**, {d}." if i == 0 else
                  r.choice([f"Nearby sat the **{n}**, {d}.", f"Another oddity was the **{n}**, {d}.",
                            f"Then there was the **{n}**, {d}."])
                  for i, (n, d, _) in enumerate(weapons))
    p3 = ("The manor is not short of things that could do harm in the wrong paws, and the investigators "
          "catalogued every one of them. " + wl)

    pl = " ".join(r.choice([f"The **{n}** is {d}.", f"Guests often wandered into the **{n}**, which is {d}.",
                            f"Nobody forgets the **{n}**, {d}."]) for n, _, d in places)
    p4 = ("The grounds are just as crowded with possibilities, and the guests had drifted through all of them "
          "during the evening. " + pl)

    p5 = (f"Word reached **Mr. Meowslock**, Lead Investigator, just before dawn. He adjusted his monocle, "
          f"sniffed the air and opened a fresh notebook. The board of evidence has been posted, the suspects "
          f"are waiting to be questioned, and somewhere in the manor a very guilty cat is licking a very "
          f"innocent-looking paw. The case is yours, detective.")
    return "\n\n".join([p1, p2, p3, p4, p5])


# ------------------------------------------------------------------ evidence board
def _evidence(prompt: str) -> str:
    facts = re.findall(r"^FACT \d+: (.+)$", prompt, re.M)
    r = _rng(prompt)
    leads = ["Investigators noted that", "On the evidence board it reads that", "Analysts confirmed that",
             "The paw-print team reports that", "Officers recorded that", "Beyond doubt,"]
    r.shuffle(leads)
    return "\n".join(f"- {leads[i % len(leads)]} {_lc(f)}" for i, f in enumerate(facts))


# ------------------------------------------------------------------ suspects
TRAITS = {
    "rowdy": ("Hah! Alright, alright,", "bats at a loose thread, tail swishing"),
    "impatient": ("Make it quick, detective,", "taps a paw against the floorboards"),
    "prankster": ("Heh, you want the truth? Fine,", "wears a mischievous whisker twitch"),
    "pompous": ("Really, detective,", "lifts chin and smooths whiskers with great dignity"),
    "proper": ("If I may be precise,", "sits ramrod straight, tail curled primly"),
    "sentimental": ("*sniff* Forgive me,", "dabs at one eye with a paw"),
    "anxious": ("Oh, um, yes,", "kneads the rug nervously, ears flat"),
    "overthinker": ("I have thought about this a great deal,", "stares at the ceiling, counting under their breath"),
    "kind-hearted": ("Oh, bless the poor thing,", "ears droop softly"),
    "sassy": ("Honey,", "flicks tail with a flourish"),
    "dramatic": ("Oh, the horror of it all,", "drapes a paw dramatically across the forehead"),
    "attention-seeking": ("Since you are clearly dying to hear my side,", "angles for the best light"),
    "lovable": ("Aw, shucks,", "rolls over a little, purring"),
    "distracted": ("Oh! Sorry, where was I, right,", "eyes follow a passing moth"),
    "snack": ("Mmm, sorry, I was thinking about tuna, right,", "licks whiskers"),
    "cryptic": ("...Listen closely,", "stares unblinking, pupils wide"),
    "loner": ("Fine. I will speak,", "stays at the shadowy edge of the room"),
    "observant": ("I notice things, detective,", "eyes track your every move"),
    "gossipy": ("Between us,", "leans in and lowers voice to a whisper"),
    "charming": ("Darling,", "blinks slowly, purring"),
    "offended": ("How dare you imply anything, but fine,", "sniffs and turns nose up"),
    "sleepy": ("*yawn* Mm, yes,", "blinks slowly, half curled up"),
    "cuddly": ("Mmm, come closer and listen,", "nestles into the nearest cushion"),
    "sharp": ("Let me be clear,", "narrows eyes, suddenly alert"),
}
CHORES = ["a long list of duties", "my usual rounds", "plenty of little jobs nobody thanks you for",
          "far too many chores"]
DETAILS = ["I remember the clock chiming twice while I was there.", "It was quiet enough to hear the lanterns hiss.",
           "A moth kept circling the lamp the whole time.", "I could hear the party muffled in the distance.",
           "I even dozed off for a minute, which is hardly a crime."]


def _cat_reply(system: str, messages: list[dict]) -> str:
    g = lambda pat, flags=0: (re.search(pat, system, flags) or [None, ""])[1]
    name = g(r"You are (.+?), a suspect")
    role = g(r"working as the (.+?)\.")
    traits = [t.strip().lower() for t in g(r"Personality: (.+?)\.\n").split(",") if t.strip()]
    victim = g(r"The victim is (.+?)\.\n")
    vshort = victim.split(",")[0]
    story = g(r"THE CASE.*?:\n(.*?)\nEVIDENCE BOARD", re.S)
    board = [b.lstrip("- ").strip() for b in g(r"EVIDENCE BOARD.*?:\n(.*?)\nThe other suspects", re.S).splitlines() if b.strip()]
    others = re.findall(r"^- (.+?): (.+?), a (.+?) \((.+?)\)$", g(r"The other suspects:\n(.*?)\nWeapons:", re.S), re.M)
    weapons = [w.strip() for w in g(r"^Weapons: (.+)$", re.M).split(",")]
    places = [p.strip() for p in g(r"^Locations: (.+)$", re.M).split(",")]
    alibi = g(r"never contradict it\): (.+)")
    clue = g(r'in your own voice: "(.+?)"')
    last = messages[-1]["content"]
    q = last.lower()
    norm = lambda t: re.sub(r"[^a-z ]", "", t.lower()).strip()
    repeats = sum(1 for m in messages[:-1] if m["role"] == "user" and norm(m["content"]) == norm(last))
    r = _rng(name, len(messages), q, repeats)
    sents = _sentences(story)

    pairs = [(k, v) for k, v in TRAITS.items() if any(k in t for t in traits)]
    opener, behavior = pairs[0][1] if pairs else ("Well, detective,", "flicks tail thoughtfully")
    opener = opener.rstrip(",") + ("." if opener.endswith(",") else "")
    if len(pairs) > 1:
        behavior = pairs[1][1][1]
    alibi_loc = next((p for p in places if p.lower() in alibi.lower()), "")

    def story_line(*keys):
        keys = [k.lower() for k in keys if k]
        hit = [s for s in sents if any(k in s.lower() for k in keys)]
        return r.choice(hit) if hit else None

    def opinion(o):
        n, orole, _, otr = o
        t = [x.strip().lower() for x in otr.split(",")]
        return r.choice([
            f"{n} is {t[0]} and {t[-1]}, and as the {orole} had the run of the manor, so I wouldn't turn my back on that one.",
            f"Something about {n} bothers me. I find that a {t[0]} cat is hard to read, and a grudge is easy to hide.",
            f"I would keep an eye on {n}. All that {t[-1]} behavior is a bit much for a night like this, in my humble opinion.",
        ])

    mentioned = lambda x: x.lower() in q or (len(x.split()[-1]) > 3 and x.split()[-1].lower() in q)
    named = next((o for o in others if mentioned(o[0])), None)
    weapon = next((w for w in weapons if mentioned(w)), None)
    place = next((p for p in places if mentioned(p)), None)
    vtoks = [t for t in re.findall(r"[a-z]+", victim.lower()) if len(t) > 4]
    parts, mood = [], None
    greeting = bool(re.match(r"\s*(hi|hello|hey|good (evening|morning|day))\b", q))

    if re.search(r"did you (kill|do|murder)|you (killed|did it)|guilty|confess|murder", q):
        parts += [f"Me? Absolutely not! {alibi}", f"I would never harm {vshort}, and I resent being asked.",
                  "If you want my advice, spend your time on who had a grudge and who had the opportunity."]
        mood = "ears flat, hackles briefly raised"
    elif re.search(r"why (won'?t|don'?t|not|are you)|add anything|anything else|tell me more|elaborate|explain|come on|hiding|more\b", q) and not (named or weapon or place):
        o = r.choice(others)
        parts += ["Add anything? Detective, I have been talking your ear off!",
                  f"If you want more, ask something specific: where I was, what I make of the weapons or the locations, or what I think of {o[0]}.",
                  "Cats answer better when the question has a point."]
        mood = "tail lashes once, then settles"
    elif greeting:
        parts += [f"Good evening, detective. I am {name}, the {role}.",
                  f"Ask me about the night we lost {vshort}, and I will tell you what I can."]
    elif re.search(r"where (were|was) you|doing|alibi|whereabouts|that night|that evening|last night", q) or (place and place == alibi_loc):
        extra = DETAILS[(repeats + r.randrange(len(DETAILS))) % len(DETAILS)]
        if place and place != alibi_loc and alibi_loc:
            parts.append(f"The {place}? I was nowhere near it. {alibi}")
        else:
            parts.append(alibi)
        parts += [f"As the {role}, I had {r.choice(CHORES)} to get through. {extra}"]
        sl = story_line(alibi_loc)
        if sl:
            parts.append(f'The report says as much about it: "{sl}"')
    elif named:
        parts += [opinion(named), "That is only my opinion, mind you. I do not have proof of anything."]
    elif weapon:
        sl = story_line(weapon)
        parts += [f'The {weapon}? I know it well. The report puts it this way: "{sl}"' if sl else f"The {weapon}? I know it well, everyone does.",
                  f"I will not say whether it was used, because I did not see. But a thing like that makes a {role} think."]
    elif place:
        sl = story_line(place)
        parts += [f'The {place}? The report says: "{sl}"' if sl else f"The {place}? Everyone knows it.",
                  "Whether anything happened there, I cannot say. I only know what I did myself and what is on the board."]
    elif re.search(r"victim|dead|body|died|poor|" + "|".join(vtoks or ["xxxx"]), q):
        parts += [f"Poor {vshort}. Whoever did this spoiled a perfectly good evening.",
                  r.choice(sents[:2]) if sents else "The whole manor is shaken.", "I want this solved as much as you do."]
    elif re.search(r"evidence|clue|board|report|story|happen|found|discover", q) and board:
        b = r.choice(board)
        parts += [f'It says on the board: "{b}"', "That makes a cat think, does it not? Ask me about whichever part puzzles you."]
    elif re.search(r"suspect|trust|think|opinion|suspicious|who", q):
        o = r.choice(others)
        parts += [f"If I must wager, {o[0]} bothers me most. {opinion(o)}", "That is instinct, not fact, detective."]
    elif re.search(r"know|saw|see|notice|hear|heard|witness|tell", q):
        parts += [alibi, "What I know beyond that is what is in the report and on the evidence board.",
                  f"Try asking me about {r.choice(others)[0]}, or the weapons. I have opinions."]
    else:
        words = set(re.findall(r"[a-z]{4,}", q))
        scored = sorted(sents, key=lambda s: -len(words & set(re.findall(r"[a-z]{4,}", s.lower()))))
        sl = scored[0] if scored and words & set(re.findall(r"[a-z]{4,}", scored[0].lower())) else (r.choice(sents) if sents else None)
        parts += [f'Hmm. What I keep coming back to is this line from the report: "{sl}"' if sl else "Hmm, an interesting question.",
                  "I am not sure what you are driving at. Be more specific and I will tell you what I can."]

    if clue:
        parts.append(r.choice(["Now that you mention it,", "Since you are asking,", "One thing I can tell you:"]) + " " + clue)
    lead = ""
    if repeats:
        lead = r.choice(["Again? ", "As I already said, ", "You do repeat yourself, detective. "])
        mood = mood or "tail twitches impatiently"
    use_opener = not lead and not greeting and r.random() < 0.6      # not on every line
    text = " ".join([(lead or (opener + " " if use_opener else "")) + parts[0]] + parts[1:])
    return (f"**Currently Interrogating:** {name}\n"
            f'**Response:** "{text}"\n'
            f"**Observed Behavior:** *{mood or behavior}*")


class MockClient:
    def complete(self, system, messages, max_tokens=600):
        last = messages[-1]["content"]
        if "Overview of a Police Incident Report" in last:
            return _story(last)
        if 'CLUES & EVIDENCE" board' in last:
            return _evidence(last)
        if "hint level" in last:
            return "(Mock hint) " + last.split("nothing more: ", 1)[-1].split("\n")[0]
        if "The player accused" in last:
            return "(Mock verdict) " + last.split("\n")[1] + "\n— Mr. Meowslock, Lead Investigator"
        return _cat_reply(system, messages)
