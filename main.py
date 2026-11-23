import os
import sys
from dotenv import load_dotenv
from models import Dataset
from game import new_game, pick_clue, next_hint, evaluate_accusation
from guard import looks_like_injection, safe_complete, is_stonewall, SAFE_DEFLECTION
from casefile import generate_evidence
from llm import get_client
import prompts

RED = "\033[31m" if sys.stdout.isatty() else ""
BOLD = "\033[1m" if sys.stdout.isatty() else ""
RESET = "\033[0m" if sys.stdout.isatty() else ""
LINE = "-" * 60

HELP = """commands (they mirror the tabs in the design):
  /scene                 CRIME SCENE: the report, evidence and confirmed clue
  /suspects              SUSPECTS: list everyone
  /interrogate <name>    open that suspect's page (profile, alibi, transcript), then just type questions
  /transcript            re-read the current suspect's conversation
  /weapons               WEAPONS: details and materials
  /locations             LOCATIONS: details and settings
  /clues                 every clue you've uncovered so far
  /hint                  get a hint (3 levels, never the answer)
  /accuse                SUBMIT REPORT: name the suspect, weapon and location
  /new                   start a brand-new case (blank slate)
  /help, /quit"""


def show_scene(s):
    print(f"\n{BOLD}{RED}POLICE INCIDENT REPORT{RESET}\n{LINE}")
    print(f"{BOLD}Overview:{RESET}\n{s.story}\n")
    print(LINE)
    print(f"{BOLD}{'CLUES & EVIDENCE'.center(60)}{RESET}\n")
    for i, e in enumerate(s.evidence):
        last = i == len(s.evidence) - 1          # the always-true confirmed clue, in red
        print(f"  \u2022 {RED if last else ''}{e}{RESET if last else ''}")
    print(LINE)
    print(f"{BOLD}TO-DO: Fill Out Missing Information{RESET}  (use /accuse when you're ready)")
    print(f"  Suspect:  {', '.join(c.name for c in s.cats)}")
    print(f"  Weapon:   {', '.join(w.name for w in s.weapons)}")
    print(f"  Location: {', '.join(l.name for l in s.locations)}")
    print(f"{LINE}\nSignatory: Mr. Meowslock, Lead Investigator\n")


def show_suspects(s):
    print()
    for i, c in enumerate(s.cats, 1):
        print(f"{i}. {c.name} - {c.role} ({c.breed})")
    print()


def show_weapons(s):
    print(f"\n{BOLD}{RED}POSSIBLE WEAPONS{RESET}\n{LINE}")
    for i, w in enumerate(s.weapons, 1):
        print(f"Weapon {i}: {BOLD}{w.name}{RESET}\n  {w.description}\n  Made of: {', '.join(w.material)}\n")


def show_locations(s):
    print(f"\n{BOLD}{RED}POSSIBLE LOCATIONS{RESET}\n{LINE}")
    for i, l in enumerate(s.locations, 1):
        print(f"Location {i}: {BOLD}{l.name}{RESET}\n  {l.description}\n  {l.setting.capitalize()}\n")


def show_transcript(s, cat):
    print(f"\n{BOLD}Interrogation Transcript{RESET} ({cat.name})\n{LINE}")
    hist = s.history.get(cat.name, [])
    if not hist:
        print("(no questions asked yet)")
    for m in hist:
        print(f"You: {m['content']}\n" if m["role"] == "user" else f"{m['content']}\n")
    print(LINE)


def show_suspect_page(s, cat):
    print(f"\n{LINE}")
    print(f"Name:        {cat.name}\nBreed:       {cat.breed}\nRole/Title:  {cat.role}")
    print(f"Zodiac Sign: {cat.zodiac_sign}\nPersonality: {cat.personality}")
    print(f"{LINE}\n{BOLD}Alibi:{RESET} {cat.alibi}")
    show_transcript(s, cat)
    print("Type your questions below.\n")


def choose(label, options):
    """Numbered 'dropdown': accept a number or a name."""
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    ans = input(f"{label} (number or name): ").strip()
    return options[int(ans) - 1] if ans.isdigit() and 1 <= int(ans) <= len(options) else ans


def start_case(client, dataset):
    session = new_game(dataset)          # fresh object
    session.story = safe_complete(client, prompts.GM_SYSTEM,
                                  [{"role": "user", "content": prompts.story_prompt(session)}],
                                  session.solution, max_tokens=1200) or "A mystery awaits, detective!"
    session.evidence = generate_evidence(client, session)   # AI-worded, Python-verified
    show_scene(session)
    return session


def main():
    load_dotenv()
    client = get_client()
    dataset = Dataset.load(os.getenv("DATASET_PATH", "mockup_dataset.json"))
    print("\n=== PURRDER MYSTERY ===")
    if type(client).__name__ == "MockClient":
        print("[OFFLINE MOCK MODE: no API calls, no tokens used]")
    session, current = start_case(client, dataset), None
    print(HELP + "\n")

    while True:
        text = input(f"[{current or 'detective'}] > ").strip()
        if not text:
            continue
        cmd, _, arg = text.partition(" ")

        if cmd == "/quit":
            break
        elif cmd == "/help":
            print(HELP)
        elif cmd == "/new":
            session, current = start_case(client, dataset), None
        elif cmd == "/scene":
            show_scene(session)
        elif cmd == "/suspects":
            show_suspects(session)
        elif cmd == "/weapons":
            show_weapons(session)
        elif cmd == "/locations":
            show_locations(session)
        elif cmd == "/interrogate":
            cat = session.get_cat(arg)
            if cat:
                current = cat.name
                show_suspect_page(session, cat)
            else:
                print("No such suspect. Try /suspects.")
        elif cmd == "/transcript":
            if current:
                show_transcript(session, session.get_cat(current))
            else:
                print("Open a suspect first: /interrogate <name>")
        elif cmd == "/clues":
            print(f"{RED}[confirmed] {session.confirmed_clue.text}{RESET}")
            for c in session.all_clues():
                if c.id in session.discovered_clue_ids:
                    src = "Crime scene" if c.holder is None else c.holder
                    print(f"[{c.id}] {src}: {c.scene_text if c.holder is None else c.text}")
        elif cmd == "/hint":
            h = next_hint(session)
            if not h:
                print("That's all the hints I can give. The rest is up to you, detective!")
                continue
            reply = safe_complete(client, prompts.GM_SYSTEM,
                                  [{"role": "user", "content": prompts.hint_prompt(*h)}], session.solution)
            print(reply or h[1])
        elif cmd == "/accuse":
            print(f"\n{BOLD}TO-DO: Fill Out Missing Information{RESET}")
            try:
                sus = choose("Suspect", [c.name for c in session.cats])
                weapon = choose("Weapon", [w.name for w in session.weapons])
                loc = choose("Location", [l.name for l in session.locations])
                ev = evaluate_accusation(session, sus, weapon, loc)
            except ValueError as e:
                print(e)
                continue
            print("\n" + (safe_complete(client, prompts.GM_SYSTEM,
                                        [{"role": "user", "content": prompts.verdict_prompt(session, ev, (sus, weapon, loc))}],
                                        None) or ""))
            print("\nCase closed. /new for another case, or /quit.")
            current = None
        elif text.startswith("/"):
            print("Unknown command. /help")
        else:
            if not current:
                print("Pick someone first: /interrogate <name>")
                continue
            if looks_like_injection(text):
                print(SAFE_DEFLECTION)
                continue
            cat = session.get_cat(current)
            clue = pick_clue(session, cat, text)
            hist = session.history.setdefault(cat.name, [])
            hist.append({"role": "user", "content": text})
            reply = safe_complete(client, prompts.cat_system(session, cat, clue), hist, session.solution,
                                  reject=is_stonewall)
            if reply is None:
                hist.pop()
                print(SAFE_DEFLECTION)
                continue
            hist.append({"role": "assistant", "content": reply})
            if clue:
                session.discovered_clue_ids.add(clue.id)
            print("\n" + reply + "\n")


if __name__ == "__main__":
    main()
