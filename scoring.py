from math import isclose
from statistics import mean
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from models import Evaluation, GameSession
from scoring_models import (
    Assistance, CategoryScore, Importance, InvestigationMetrics, Question, ReasoningType, ScoreBreakdown,
)

Difficulty = Literal["easy", "medium", "hard", "expert"]


class ScoringConfig(BaseModel, frozen=True):
    accusation_points: tuple[float, float, float] = (20, 10, 10)
    clue_points: float = 20
    question_points: float = 15
    reasoning_caps: dict[ReasoningType, float] = {
        "clue_connection": 3, "contradiction_identification": 2, "hypothesis": 2,
        "suspect_elimination": 2, "hypothesis_revision": 1,
    }
    reasoning_evidence_minimum: dict[ReasoningType, int] = {
        "clue_connection": 2, "contradiction_identification": 2, "hypothesis": 1,
        "suspect_elimination": 1, "hypothesis_revision": 1,
    }
    efficiency_points: tuple[float, float, float] = (4, 4, 2)
    independence_points: float = 5
    independence_enabled: bool = True
    clue_weights: dict[Importance, float] = {
        "critical": 5, "major": 3, "supporting": 2, "minor": 1, "red_herring": 0,
    }
    question_weights: tuple[float, float, float, float, float] = (0.30, 0.20, 0.20, 0.20, 0.10)
    meaningful_rating: float = Field(default=2, ge=0, le=5)
    minimum_questions: int = Field(default=5, gt=0)
    difficulty: Difficulty = "medium"
    budgets: dict[Difficulty, int] = {"easy": 12, "medium": 20, "hard": 30, "expert": 45}
    expected_discovery_rate: float = Field(default=0.40, gt=0, le=1)
    full_efficiency_coverage: float = Field(default=0.5, gt=0, le=1)
    hint_costs: dict[Assistance, float] = {
        "clarification": 0, "suggestion": 0.5, "directional": 1, "specific": 2, "solution": 5,
    }
    ranks: tuple[tuple[float, str], ...] = (
        (90, "Master Detective"), (80, "Expert Investigator"), (65, "Skilled Sleuth"),
        (50, "Promising Detective"), (30, "Apprentice Investigator"), (0, "Curious Kitten"),
    )
    batch_size: int = Field(default=4, gt=0)
    evaluation_attempts: int = Field(default=2, gt=0)
    evaluation_timeout: float = Field(default=20, gt=0)
    local_evaluation_timeout: float = Field(default=90, gt=0)
    local_batch_size: int = Field(default=1, gt=0)
    evaluation_tokens_per_turn: int = Field(default=850, gt=0)
    prior_question_window: int = Field(default=12, gt=0)
    explanation_limit: int = Field(default=600, gt=0)

    @model_validator(mode="after")
    def validate_weights(self):
        points = (*self.accusation_points, self.clue_points, self.question_points,
                  *self.reasoning_caps.values(), *self.efficiency_points, self.independence_points)
        if not isclose(sum(points), 100) or any(not 0 <= value <= 100 for value in points):
            raise ValueError("category point values must be nonnegative and add up to 100")
        if self.independence_points == 100:
            raise ValueError("at least one investigation or accusation category must have points")
        if (not isclose(sum(self.question_weights), 1)
                or any(not 0 <= value <= 1 for value in self.question_weights)):
            raise ValueError("question weights must be nonnegative and add up to 1")
        for name in ("clue_weights", "hint_costs", "reasoning_caps", "reasoning_evidence_minimum", "budgets"):
            defaults = type(self).model_fields[name].default
            values = getattr(self, name)
            if values.keys() != defaults.keys() or any(not 0 <= value < float("inf") for value in values.values()):
                raise ValueError(f"{name} requires a finite, nonnegative value for every defined key")
        if (self.clue_weights["red_herring"] != 0 or self.hint_costs["clarification"] != 0
                or any(value == 0 for value in self.budgets.values())):
            raise ValueError("red herrings and clarifications must be free, and budgets must be positive")
        if any(value == 0 for value in self.reasoning_evidence_minimum.values()):
            raise ValueError("each deduction category must require evidence")
        thresholds = [threshold for threshold, _ in self.ranks]
        if (not thresholds or thresholds[-1] != 0 or not all(0 <= t <= 100 for t in thresholds)
                or any(left <= right for left, right in zip(thresholds, thresholds[1:]))):
            raise ValueError("rank thresholds must descend to zero")
        return self


DEFAULT_SCORING = ScoringConfig()
DISPLAY_PRECISION = 2


def question_rating(question: Question, config: ScoringConfig) -> float:
    dimensions = (question.relevance, question.specificity, question.context_awareness,
                  question.information_value, question.novelty)
    return round(sum(rating * weight for rating, weight in zip(dimensions, config.question_weights)), 10)


def investigation_metrics(
    session: GameSession, config: ScoringConfig, *, discovered_ids: set[str] | None = None,
) -> InvestigationMetrics:
    turns = session.investigation
    questions = [q for turn in turns if turn.assessment for q in turn.assessment.questions]
    investigative = [q for q in questions if q.is_investigative]
    unique_ratings = [question_rating(q, config) for q in investigative if not q.is_redundant]
    clue_weights = {clue.id: config.clue_weights[clue.importance] for clue in session.all_clues()}
    discovered = clue_weights.keys() & (session.discovered_clue_ids if discovered_ids is None else discovered_ids)
    available_weight = sum(clue_weights.values())
    return InvestigationMetrics(
        player_messages=sum(turn.suspect is not None for turn in turns),
        questions=len(investigative),
        meaningful=sum(rating >= config.meaningful_rating for rating in unique_ratings),
        productive=sum(turn.productive for turn in turns),
        redundant=sum(q.is_redundant for q in investigative),
        irrelevant=sum(q.question_type == "irrelevant" for q in questions),
        average_rating=mean(unique_ratings) if unique_ratings else 0,
        discovered_ids=tuple(sorted(discovered)),
        clues_discovered=len(discovered),
        clues_missed=len(clue_weights) - len(discovered),
        weighted_coverage=sum(clue_weights[c] for c in sorted(discovered)) / available_weight if available_weight else 0,
        reasoning_events=tuple(event for turn in turns for event in turn.reasoning_events),
        hints_delivered=len(session.delivered_hints),
        hint_cost=sum(config.hint_costs[hint.kind] for hint in session.delivered_hints),
        pending_evaluations=sum(turn.status == "pending" for turn in turns),
        completed_evaluations=sum(turn.status == "complete" for turn in turns),
        failed_evaluations=sum(turn.status == "failed" for turn in turns),
    )


def calculate_final_score(
    session: GameSession, ev: Evaluation, config: ScoringConfig = DEFAULT_SCORING,
) -> ScoreBreakdown | None:
    if session.result and session.result.score_breakdown:
        return session.result.score_breakdown
    if not session.investigation_history_complete:
        return None
    metrics = investigation_metrics(session, config, discovered_ids={c.id for c in ev.found_clues})
    if metrics.pending_evaluations or metrics.failed_evaluations:
        return None
    accuracy = sum(points * correct for points, correct in zip(
        config.accusation_points, (ev.culprit_correct, ev.weapon_correct, ev.location_correct),
    ))
    participation = min(1, metrics.meaningful / config.minimum_questions)
    quality = config.question_points * (metrics.average_rating / 5) * participation
    reasoning = sum(
        min(cap, sum(event.strength for event in metrics.reasoning_events
                     if event.reasoning_type == kind and event.is_supported and not event.is_duplicate))
        for kind, cap in config.reasoning_caps.items()
    )
    efficiency = 0.0
    if metrics.questions:
        count_points, discovery_points, novelty_points = config.efficiency_points
        count = count_points * min(1, config.budgets[config.difficulty] / metrics.questions) * participation
        discovery = discovery_points * min(
            1, metrics.productive / metrics.questions / config.expected_discovery_rate,
        )
        novelty = novelty_points * (1 - metrics.redundant / metrics.questions)
        efficiency = (count + discovery + novelty) * min(
            1, metrics.weighted_coverage / config.full_efficiency_coverage,
        )
    categories = [
        ("Accusation accuracy", accuracy, sum(config.accusation_points)),
        ("Clue discovery", config.clue_points * metrics.weighted_coverage, config.clue_points),
        ("Question quality", quality, config.question_points),
        ("Deductive reasoning", reasoning, sum(config.reasoning_caps.values())),
        ("Investigation efficiency", efficiency, sum(config.efficiency_points)),
    ]
    if config.independence_enabled:
        categories.append(("Investigation independence", config.independence_points - metrics.hint_cost,
                           config.independence_points))
    scale = 100 / sum(maximum for _, _, maximum in categories)
    scores = tuple(
        CategoryScore(name=name, earned=min(maximum, max(0, earned)) * scale, maximum=maximum * scale)
        for name, earned, maximum in categories if maximum
    )
    total = round(min(100, sum(score.earned for score in scores)), DISPLAY_PRECISION)
    rank = next(rank for threshold, rank in config.ranks if total >= threshold)
    return ScoreBreakdown(categories=scores, total=total, rank=rank, metrics=metrics)
