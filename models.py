import json
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# dataset classes
class Suspect(BaseModel):
    name: str
    breed: str
    role: str
    zodiac_sign: str
    personality: str


class Weapon(BaseModel):
    name: str
    description: str
    material: list[str]

    @field_validator("material")
    @classmethod
    def _lower(cls, v):
        return [m.strip().lower() for m in v if m.strip()]


class Location(BaseModel):
    name: str
    description: str
    setting: Literal["indoors", "outdoors"]


class Dataset(BaseModel):
    suspects: list[Suspect] = Field(min_length=4)
    weapons: list[Weapon] = Field(min_length=4)
    locations: list[Location] = Field(min_length=4)

    @model_validator(mode="after")
    def _unique_names(self):
        for label, items in (("suspects", self.suspects), ("weapons", self.weapons),
                             ("locations", self.locations)):
            names = [i.name.lower() for i in items]
            if len(names) != len(set(names)):
                raise ValueError(f"duplicate names in {label}")
        return self

    @classmethod
    def load(cls, path: str = "dataset.json") -> "Dataset":
        with open(path, encoding="utf-8") as f:
            return cls.model_validate(json.load(f))


#round classes
class Clue(BaseModel):
    id: str
    kind: Literal["suspect", "weapon", "location"]
    eliminates: str                      # the item this clue rules out
    text: str                            # said by a cat, first person
    scene_text: str                      # shown in the crime-scene report, third person
    holder: str | None = None            # none = crime-scene clue, known from the start
    specific: list[str]
    generic: list[str]


class ConfirmedClue(BaseModel):
    """The one always-true head-start clue shown in red on the crime scene page."""
    kind: Literal["material", "setting", "suspect"]
    text: str
    key: str = ""                        # the word a rewrite must keep (material / setting / name)


class Cat(Suspect):
    alibi: str
    clues: list[Clue] = Field(default_factory=list)   # ONLY this cat's knowledge


class Solution(BaseModel):
    culprit: str
    weapon: str
    location: str


class GameSession(BaseModel):
    victim: str
    cats: list[Cat] = Field(min_length=4, max_length=4)
    weapons: list[Weapon] = Field(min_length=4, max_length=4)
    locations: list[Location] = Field(min_length=4, max_length=4)
    solution: Solution
    confirmed_clue: ConfirmedClue
    scene_clues: list[Clue] = Field(default_factory=list)
    story: str = ""
    evidence: list[str] = Field(default_factory=list)   # AI-written "Clues & Evidence" bullets
    seed: int = 0
    discovered_clue_ids: set[str] = Field(default_factory=set)
    hints_used: int = 0
    history: dict[str, list[dict]] = Field(default_factory=dict)   # one transcript per suspect

    @model_validator(mode="after")
    def _solution_in_active_sets(self):
        if self.solution.culprit not in [c.name for c in self.cats]:
            raise ValueError("culprit not in active suspects")
        if self.solution.weapon not in [w.name for w in self.weapons]:
            raise ValueError("weapon not in active weapons")
        if self.solution.location not in [l.name for l in self.locations]:
            raise ValueError("location not in active locations")
        return self

    def get_cat(self, query: str) -> Cat | None:
        q = query.strip().lower()
        if not q:
            return None
        return next((c for c in self.cats if q == c.name.lower()), None) or \
            next((c for c in self.cats if q in c.name.lower()), None)

    def all_clues(self) -> list[Clue]:
        return self.scene_clues + [c for cat in self.cats for c in cat.clues]


class Evaluation(BaseModel):
    culprit_correct: bool
    weapon_correct: bool
    location_correct: bool
    score: int
    found_clues: list[Clue]
    missed_clues: list[Clue]

    @property
    def won(self) -> bool:
        return self.culprit_correct and self.weapon_correct and self.location_correct
