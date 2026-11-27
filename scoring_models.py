from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


Importance = Literal["critical", "major", "supporting", "minor", "red_herring"]
Assistance = Literal["clarification", "suggestion", "directional", "specific", "solution"]
ReasoningType = Literal[
    "clue_connection", "contradiction_identification", "hypothesis",
    "suspect_elimination", "hypothesis_revision",
]
Rating = Annotated[int, Field(strict=True, ge=0, le=5)]


class Question(BaseModel, extra="forbid"):
    text: str = Field(min_length=1)
    question_type: Literal["irrelevant", "generic", "exploratory", "targeted", "evidence_based", "analytical"]
    relevance: Rating
    specificity: Rating
    context_awareness: Rating
    information_value: Rating
    novelty: Rating
    is_investigative: bool
    is_redundant: bool
    is_valid_follow_up: bool
    referenced_clue_ids: list[str]
    reason: str
    repeated_turn_id: str | None = None


class Deduction(BaseModel, extra="forbid"):
    reasoning_type: ReasoningType
    player_excerpt: str = Field(min_length=1)
    referenced_clue_ids: list[str]
    strength: float = Field(strict=True, ge=0, le=1)
    is_supported: bool
    is_duplicate: bool
    explanation: str


class ReasoningEvent(Deduction):
    id: str
    turn_id: str


class TurnAssessment(BaseModel, extra="forbid"):
    turn_id: str
    message_type: Literal["investigative", "irrelevant", "social", "clarification", "reasoning", "mixed"]
    questions: list[Question]
    reasoning_events: list[Deduction]


class AssessmentBatch(BaseModel, extra="forbid"):
    turns: list[TurnAssessment]


class InvestigationTurn(BaseModel):
    id: str
    number: int
    player_message: str
    suspect: str | None
    counts_game_turn: bool = False
    timestamp: datetime
    clue_ids_before: set[str]
    testimony_ids_before: set[str]
    npc_response: str = ""
    new_clue_ids: set[str] = Field(default_factory=set)
    status: Literal["pending", "complete", "failed"] = "pending"
    assessment: TurnAssessment | None = None
    reasoning_events: list[ReasoningEvent] = Field(default_factory=list)
    productive: bool = False

    @property
    def question_count(self) -> int:
        return sum(q.is_investigative for q in self.assessment.questions) if self.assessment else 0


class DeliveredHint(BaseModel, frozen=True):
    level: int
    text: str
    kind: Assistance


class InvestigationMetrics(BaseModel, frozen=True):
    player_messages: int
    questions: int
    meaningful: int
    productive: int
    redundant: int
    irrelevant: int
    average_rating: float
    discovered_ids: tuple[str, ...]
    clues_discovered: int
    clues_missed: int
    weighted_coverage: float
    reasoning_events: tuple[ReasoningEvent, ...]
    hints_delivered: int
    hint_cost: float
    pending_evaluations: int
    completed_evaluations: int
    failed_evaluations: int


class CategoryScore(BaseModel, frozen=True):
    name: str
    earned: float
    maximum: float


class ScoreBreakdown(BaseModel, frozen=True):
    categories: tuple[CategoryScore, ...]
    total: float
    rank: str
    metrics: InvestigationMetrics
