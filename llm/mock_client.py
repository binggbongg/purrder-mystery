"""Free offline stand-in for a real model. No API calls, no tokens.

It still reads the prompt it is given, so the overview and every suspect's
answer are built from THIS round's cast, weapons, locations and story. It is not smart, but it
never falls back to a stock "I have nothing to add" line."""
import hashlib
import random
import re

_WRAP = re.compile(r"<(dtv_\w+)>(.*?)</\1>", re.S)


def _unwrap(text: str) -> str:
    """guard.build_messages wraps player text in a random tag; the mock wants the raw words."""
    m = _WRAP.search(text)
    body = m.group(2) if m else text
    return re.sub(r"\n\n\(Reminder:.*$", "", body, flags=re.S).strip()


def _rng(*parts) -> random.Random:
    return random.Random(int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest(), 16))


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\*+", "", text).replace("\n", " ")
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]


def _lc(s: str) -> str:
    """Lower-case the first letter only for ordinary words, never for a suspect's name."""
    first = s.split(" ", 1)[0].lower()
    return s[:1].lower() + s[1:] if first in {"the", "a", "an", "pawprints", "there", "fur", "paw"} else s


# overview
def _story(prompt: str) -> str:
    victim = re.search(r"Victim: (.+?)\.\n", prompt).group(1)
    names = re.search(r"Suspects \(4 neighborhood cats\): (.+)\n", prompt).group(1)
    clues_block = re.search(r"Confirmed initial scene findings.*?:\n(.*?)\n\nFollow this exact", prompt, re.S).group(1)
    clues = [c.lstrip("- ").strip() for c in clues_block.splitlines() if c.strip() and c.strip() != "- (none)"]

    r = _rng(prompt)
    opener = r.choice([
        f"Chaos struck Barangay Puspin tonight when {victim} was found dramatically knocked out cold!",
        f"Trouble hit Barangay Puspin tonight after a sudden commotion left {victim} in peril!",
        f"A hush fell over Barangay Puspin tonight when {victim} was discovered lifeless after a noisy scuffle!",
    ])
    clue_str = " ".join(clues)
    return (f"{opener} Four neighborhood cats ({names}) were spotted nearby, and early checks show that {_lc(clue_str)} "
            f"Interrogate the suspects, review the evidence, and fill out the Police Incident Report below.")


# suspects
ARCHETYPES = {
    "gossip": ("Naku! Wag mo sabihin kahit kanino ha, pero", "flicks tail excitedly and leans in close"),
    "aristocrat": ("Hmp. Really, my dear detective,", "lifts chin and grooms spotless fur with dignity"),
    "nervous": ("Ah, eh, kasi... I mean, yes detective,", "kneads the air nervously, ears flattened"),
    "mysterious": ("...Listen carefully.", "stares without blinking, tail completely still"),
    "forgetful": ("Ay, hello po! Wait—what was I saying? Oh, right,", "purrs mid-sentence and sniffs the air for bread"),
    "grumpy": ("Hay nako, make it quick,", "scowls with grumpy barangay-tanod energy, tail lashing"),
}

CHORES = ["keeping watch over the street", "my usual evening rounds", "napping away from all the noise",
          "minding my own business"]
DETAILS = ["I remember hearing the neighbors' videoke from down the street.",
           "It was warm enough that a moth kept circling the porch light.",
           "Someone's tsinelas slapped against the pavement outside.",
           "I almost dozed off right there, which is hardly a crime."]


def _cat_reply(system: str, messages: list[dict]) -> str:
    g = lambda pat, flags=0: (re.search(pat, system, flags) or [None, ""])[1]
    name = g(r"You are (.+?), a .+? cat \(.+?\) being questioned")
    breed = g(r"You are .+?, a (.+?) cat \(.+?\) being questioned")
    archetype = g(r"You are .+?, a .+? cat \((.+?)\) being questioned").lower()
    victim = g(r"Victim: (.+?)\n")
    vshort = victim.split(",")[0] if victim else "the victim"
    story = g(r"What everyone knows: (.+?)\n")
    facts = [b.lstrip("- ").strip() for b in g(r"PUBLIC SCENE FACTS.*?:\n(.*?)\n\nYOUR TRUTH FOR TONIGHT", re.S).splitlines() if b.strip()]
    truth_notes = [b.lstrip("- ").strip() for b in g(r"YOUR TRUTH FOR TONIGHT.*?:\n(.*?)\n\nWHAT YOU ALREADY TOLD", re.S).splitlines() if b.strip()]
    alibi = truth_notes[0] if truth_notes else "I kept to myself all evening."
    others = re.findall(r"^- (.+?): a (.+?) \((.+?)\)$", g(r"Other suspects \(fellow cats\):\n(.*?)\n\nInanimate objects", re.S), re.M)
    weapons = re.findall(r"^- (.+?) \(an inanimate", g(r"Inanimate objects/weapons around.*?:\n(.*?)\n\nPlaces/locations", re.S), re.M)
    places = re.findall(r"^- (.+?) \(a place/location", g(r"Places/locations around.*?:\n(.*?)\n\nHOW TO RESPOND", re.S), re.M)
    clue = g(r'NEW CLUE TO SHARE THIS TURN:.*?: "(.+?)"')
    last = _unwrap(messages[-1]["content"])
    q = last.lower()
    norm = lambda t: re.sub(r"[^a-z ]", "", t.lower()).strip()
    repeats = sum(1 for m in messages[:-1] if m["role"] == "user" and norm(_unwrap(m["content"])) == norm(last))
    r = _rng(name, len(messages), q, repeats)
    sents = _sentences(story)

    matched = [v for k, v in ARCHETYPES.items() if k in archetype]
    opener, behavior = matched[0] if matched else ("Hay nako, detective,", "flicks tail thoughtfully")
    alibi_loc = next((p for p in places if p.lower() in alibi.lower()), "")

    def opinion(o):
        n, obreed, oarch = o
        return r.choice([
            f"Ay grabe, **{n}** is so {oarch}—I wouldn't turn my back on that {obreed} for a second.",
            f"Something about **{n}** bothers me. Being {oarch} makes it easy to hide a grudge.",
            f"If you ask me, keep an eye on **{n}**. All that {oarch} attitude tonight felt suspicious.",
        ])

    mentioned = lambda x: x.lower() in q or (len(x.split()[-1]) > 3 and x.split()[-1].lower() in q)
    named = next((o for o in others if mentioned(o[0])), None)
    weapon = next((w for w in weapons if mentioned(w)), None)
    place = next((p for p in places if mentioned(p)), None)
    vtoks = [t for t in re.findall(r"[a-z]+", victim.lower()) if len(t) > 4]
    parts, mood = [], None
    greeting = bool(re.match(r"\s*(hi|hello|hey|kumusta|good (evening|morning|day))\b", q))

    other_name = r.choice(others)[0] if others else "someone else"
    sample_wep = r.choice(weapons) if weapons else "anything unusual"
    sample_place = r.choice(places) if places else "the neighborhood"

    if re.search(r"did you (kill|do|murder)|you (killed|did it)|guilty|confess|murder", q):
        parts += [f"Me?! Absolutely not! {alibi}", f"I would never harm **{vshort}**, and I resent being accused like that."]
        mood = "ears flat, hackles briefly raised"
    elif re.search(r"why (won'?t|don'?t|not|are you)|add anything|anything else|tell me more|elaborate|explain|come on|hiding|more\b", q) and not (named or weapon or place):
        parts += ["I am telling you what I actually saw from my spot!",
                  f"Ask me specifically about where I was, the **{sample_wep}**, or what **{other_name}** was doing."]
        mood = "tail lashes once, then settles"
    elif greeting:
        parts += [f"Good evening, detective. I am **{name}**.",
                  f"Ask me about the night we lost **{vshort}**, and I will tell you what I saw."]
    elif re.search(r"where (were|was) you|doing|alibi|whereabouts|that night|that evening|last night", q) or (place and place == alibi_loc):
        extra = DETAILS[(repeats + r.randrange(len(DETAILS))) % len(DETAILS)]
        if place and place != alibi_loc and alibi_loc:
            parts.append(f"The **{place}**? I was nowhere near there. {alibi}")
        else:
            parts.append(alibi)
        parts += [f"I was just {r.choice(CHORES)}. {extra}"]
    elif named:
        parts += [opinion(named), "That is just my hunch—I did not see the deed itself."]
    elif weapon:
        parts += [f"The **{weapon}**? I know that item from around the neighborhood.",
                  "From my spot, I did not see anyone strike a blow with it unless I already told you otherwise."]
    elif place:
        parts += [f"The **{place}**? I know that spot well.",
                  f"I stayed put at the **{alibi_loc or 'my spot'}** rather than wandering around the **{place}**."]
    elif re.search(r"victim|dead|body|died|poor|" + "|".join(vtoks or ["xxxx"]), q):
        parts += [f"Poor **{vshort}**. Whoever did this ruined the whole night for everyone.",
                  r.choice(sents[:2]) if sents else "The whole neighborhood is shaken up."]
    elif re.search(r"evidence|clue|happen|found|discover|know|saw|see|notice|hear|heard|witness|tell", q):
        f = r.choice(facts) if facts else alibi
        parts += [f"Everyone already knows that {_lc(f)}",
                  f"Beyond that, ask me about **{other_name}** or one of the places around."]
    elif re.search(r"suspect|trust|think|opinion|suspicious|who", q):
        if others:
            o = r.choice(others)
            parts += [f"If I had to guess, **{o[0]}** bothers me the most. {opinion(o)}"]
        else:
            parts += ["I do not trust anyone wandering out of sight tonight."]
    else:
        parts += [f"I can only speak to what happened around my spot. {alibi}",
                  f"Try asking me about **{other_name}**, the **{sample_wep}**, or the **{sample_place}**."]

    if clue:
        parts.append(r.choice(["Now that you mention it,", "Since you're asking,", "Wait—one thing I did see:"]) + " " + clue)
    lead = ""
    if repeats:
        lead = r.choice(["Again? ", "Like I just told you, ", "You're repeating yourself, detective. "])
        mood = mood or "tail twitches impatiently"
    use_opener = not lead and not greeting and r.random() < 0.65
    text = " ".join([(lead or (opener + " " if use_opener else "")) + parts[0]] + parts[1:])
    return (f"**Currently Interrogating:** {name} ({archetype} / {breed})\n"
            f'**Response:** "{text}"\n'
            f"**Observed Behavior:** *{mood or behavior}*")


class MockClient:
    def complete(self, system, messages, max_tokens=600):
        last = messages[-1]["content"]
        if "Overview of a Police Incident Report" in last:
            return _story(last)
        if "hint level" in last:
            return "(Mock hint) " + last.split("nothing more: ", 1)[-1].split("\n")[0]
        if "The player accused" in last:
            return "(Mock verdict) " + last.split("\n")[1] + "\n— Mr. Meowslock, Lead Investigator"
        return _cat_reply(system, messages)