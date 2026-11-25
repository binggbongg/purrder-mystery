from models import GameSession

from ui.components._utils import render_gallery
from ui.mock_data import UI_EXTRAS


def render(session: GameSession):
    entries = []
    for weapon in session.weapons:
        extras = UI_EXTRAS["weapons"].get(weapon.name, {"made_of": "Unknown"})
        entries.append((weapon.name, weapon.description, f"Made of: {extras['made_of']}"))

    render_gallery("Possible Weapons", "Weapon", entries)