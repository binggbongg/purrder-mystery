from models import Dataset, Cat, ConfirmedClue, Solution, GameSession

# Extra UI metadata to match the mockups without altering backend models.py
UI_EXTRAS = {
    "suspects": {
        "Miming": {"role": "Barangay Chismosa", "zodiac": "Gemini", "emoji": "🐱"},
        "Whitey": {"role": "Estate Aristocrat", "zodiac": "Leo", "emoji": "😼"},
        "Choco": {"role": "Alley Runner", "zodiac": "Virgo", "emoji": "🙀"},
        "Blackie": {"role": "Night Watchcat", "zodiac": "Scorpio", "emoji": "🐈‍⬛"},
        "Pandesal": {"role": "Bakery Regular", "zodiac": "Pisces", "emoji": "😺"},
        "Tigre": {"role": "Barangay Tanod", "zodiac": "Aries", "emoji": "🐯"},
    },
    "weapons": {
        "Tsinelas": {"made_of": "Rubber, Mom-level accuracy", "emoji": "🩴"},
        "Walis tambo": {"made_of": "Tiger grass, Rattan", "emoji": "🧹"},
        "Kawali": {"made_of": "Cast iron, Residual heat", "emoji": "🍳"},
        "Sandok": {"made_of": "Hardwood, Suspicious dent", "emoji": "🥄"},
        "Paypay": {"made_of": "Woven buri palm", "emoji": "🪭"},
        "Kandila": {"made_of": "Wax, Lingering smoke", "emoji": "🕯️"},
        "Laser pointer": {"made_of": "Metal, Endless temptation", "emoji": "🔦"},
        "Scratching post": {"made_of": "Sisal rope, Attitude", "emoji": "🪵"},
    },
    "locations": {
        "Sari-sari store": {"setting": "Outdoors", "emoji": "🏪"},
        "Kusina": {"setting": "Indoors", "emoji": "🍽️"},
        "Garden": {"setting": "Outdoors", "emoji": "🌿"},
        "Bubong": {"setting": "Outdoors", "emoji": "🏠"},
        "Sala": {"setting": "Indoors", "emoji": "🛋️"},
        "Jeepney": {"setting": "Outdoors", "emoji": "🚌"},
        "Cat tree": {"setting": "Indoors", "emoji": "🌳"},
        "Sunny windowsill": {"setting": "Indoors", "emoji": "🪟"},
    },
}


def get_mock_session() -> GameSession:
    ds = Dataset.load("dataset.json")
    raw_cats = ds.suspects[:4]
    weapons = ds.weapons[:4]
    locations = ds.locations[:4]

    cats = [
        Cat(**raw_cats[0].model_dump(), alibi="Naku! I was chatting by the Sari-sari store counter the whole time!"),
        Cat(**raw_cats[1].model_dump(), alibi="Hmp. I was grooming on the Bubong, far above such common commotion."),
        Cat(**raw_cats[2].model_dump(), alibi="Ah, eh, kasi... I was just near the Kusina smelling the garlic rice!"),
        Cat(**raw_cats[3].model_dump(), alibi="The Garden was quiet. I stayed by the gate."),
    ]

    return GameSession(
        victim="Kapitan Mingming",
        cats=cats,
        weapons=weapons,
        locations=locations,
        solution=Solution(
            culprit=cats[1].name,
            weapon=weapons[2].name,
            location=locations[1].name,
        ),
        confirmed_clue=ConfirmedClue(
            kind="weapon",
            text=f"The suspect definitely had the {weapons[2].name}.",
            key=weapons[2].name,
        ),
        story=(
            "Chaos struck Barangay Puspin tonight when Kapitan Mingming's prized bowl of "
            "bangus belly vanished—and the Kapitan was found dramatically knocked out cold! "
            "Four neighborhood cats were spotted nearby. Interrogate the suspects, review "
            "the evidence, and fill out the Police Incident Report below."
        ),
        history={
            cat.name: [
                {"role": "assistant", "content": f"*{cat.name} eyes you warily.* Well? Ask your questions, detective."}
            ]
            for cat in cats
        },
    )