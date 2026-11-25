from models import Dataset, Cat, Clue, ConfirmedClue, Solution, GameSession

def get_mock_session() -> GameSession:
    ds = Dataset.load("dataset.json")
    
    # Pick first 4 from dataset.json
    raw_cats = ds.suspects[:4]
    weapons = ds.weapons[:4]
    locations = ds.locations[:4]

    cats = [
        Cat(**raw_cats[0].model_dump(), alibi="I was gossiping by the Sari-sari store counter all evening, Naku!"),
        Cat(**raw_cats[1].model_dump(), alibi="I was grooming on the Bubong, far above such common drama."),
        Cat(**raw_cats[2].model_dump(), alibi="Ah, eh, kasi... I was just near the Kusina smelling the garlic rice!"),
        Cat(**raw_cats[3].model_dump(), alibi="The Garden was quiet. I saw nothing."),
    ]

    return GameSession(
        victim="Kapitan Mingming",
        cats=cats,
        weapons=weapons,
        locations=locations,
        solution=Solution(
            culprit=cats[1].name,      # Whitey
            weapon=weapons[2].name,    # Kawali
            location=locations[1].name # Kusina
        ),
        confirmed_clue=ConfirmedClue(
            kind="weapon",
            text="Fur samples prove the culprit was definitely carrying the Kawali.",
            key="Kawali"
        ),
        story=(
            "Chaos struck Barangay Puspin tonight when Kapitan Mingming's prized bowl of "
            "bangus belly vanished—and the Kapitan was found dramatically knocked out cold! "
            "Four neighborhood cats were spotted nearby. Interrogate the suspects, inspect the "
            "evidence, and fill out the Police Incident Report."
        ),
        evidence=[
            "A faint smell of garlic rice lingers near the crime scene.",
            "Muddy paw prints lead away from the Garden gate."
        ],
        history={cat.name: [] for cat in cats}
    )