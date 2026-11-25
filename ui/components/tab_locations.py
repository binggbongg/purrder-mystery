from models import GameSession

from ui.components._utils import render_gallery
from ui.mock_data import UI_EXTRAS


def render(session: GameSession):
    entries = []
    for loc in session.locations:
        extras = UI_EXTRAS["locations"].get(loc.name, {"setting": "Indoors"})
        entries.append((loc.name, loc.description, extras["setting"]))

    render_gallery("Possible Locations", "Location", entries)