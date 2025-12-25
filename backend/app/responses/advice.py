"""Pydantic models for Advice API endpoints."""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.services.advice.models import AdviceResponse as ServiceAdviceResponse


class SpendingPatternResponse(BaseModel):
    """Recurring spending pattern identified in transaction data."""

    pattern_type: str
    description: str
    monthly_cost: float
    occurrences: int
    insight: str


class ProblemAreaResponse(BaseModel):
    """Problem area identified in financial analysis."""

    category: str
    amount: float
    trend: str
    root_cause: str | None = None
    impact: str | None = None


class RecommendationResponse(BaseModel):
    """Prioritized actionable recommendation."""

    priority: int
    action: str
    details: str
    expected_savings: str
    difficulty: str
    quick_win: bool = False


class ProgressReviewResponse(BaseModel):
    """Review of progress on previous advice."""

    previous_advice_followed: str
    wins: list[str] = Field(default_factory=list)
    areas_for_growth: list[str] = Field(default_factory=list)


class MonthlyGoalResponse(BaseModel):
    """Specific measurable goal for the next month."""

    objective: str
    target_amount: float
    strategy: str


class AdviceData(BaseModel):
    """Structured advice content for API responses."""

    analysis: str
    spending_patterns: list[SpendingPatternResponse] = Field(default_factory=list)
    problem_areas: list[ProblemAreaResponse]
    recommendations: list[RecommendationResponse] = Field(default_factory=list)
    progress_review: ProgressReviewResponse | None = None
    monthly_goal: MonthlyGoalResponse | None = None
    encouragement: str

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """
        Parse AdviceData from stored JSON string.

        Handles both new enriched format and legacy format for backward compatibility.

        Parameters
        ----------
        json_str : str
            JSON string from advice_text column.

        Returns
        -------
        AdviceData
            Parsed advice data.

        Raises
        ------
        ValueError
            If JSON is malformed or missing required fields.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as error:
            raise ValueError(f"Malformed advice JSON: {error}") from error

        try:
            # ##>: Parse spending patterns (new format).
            spending_patterns = [
                SpendingPatternResponse(
                    pattern_type=sp["pattern_type"],
                    description=sp["description"],
                    monthly_cost=sp["monthly_cost"],
                    occurrences=sp["occurrences"],
                    insight=sp["insight"],
                )
                for sp in data.get("spending_patterns", [])
            ]

            # ##>: Parse problem areas with optional new fields.
            problem_areas = [
                ProblemAreaResponse(
                    category=pa["category"],
                    amount=pa["amount"],
                    trend=pa["trend"],
                    root_cause=pa.get("root_cause"),
                    impact=pa.get("impact"),
                )
                for pa in data["problem_areas"]
            ]

            # ##>: Parse recommendations - handle both new dict format and legacy string format.
            raw_recommendations = data.get("recommendations", [])
            if raw_recommendations and isinstance(raw_recommendations[0], dict):
                recommendations = [
                    RecommendationResponse(
                        priority=rec["priority"],
                        action=rec["action"],
                        details=rec["details"],
                        expected_savings=rec["expected_savings"],
                        difficulty=rec["difficulty"],
                        quick_win=rec.get("quick_win", False),
                    )
                    for rec in raw_recommendations
                ]
            else:
                # ##>: Legacy format: recommendations as list of strings.
                recommendations = [
                    RecommendationResponse(
                        priority=idx + 1,
                        action=rec,
                        details=rec,
                        expected_savings="Non spécifié",
                        difficulty="Modéré",
                        quick_win=False,
                    )
                    for idx, rec in enumerate(raw_recommendations)
                ]

            # ##>: Parse progress review (new format).
            progress_review = None
            if "progress_review" in data:
                pr = data["progress_review"]
                progress_review = ProgressReviewResponse(
                    previous_advice_followed=pr["previous_advice_followed"],
                    wins=pr.get("wins", []),
                    areas_for_growth=pr.get("areas_for_growth", []),
                )

            # ##>: Parse monthly goal (new format).
            monthly_goal = None
            if "monthly_goal" in data:
                mg = data["monthly_goal"]
                monthly_goal = MonthlyGoalResponse(
                    objective=mg["objective"],
                    target_amount=mg["target_amount"],
                    strategy=mg["strategy"],
                )

            return cls(
                analysis=data["analysis"],
                spending_patterns=spending_patterns,
                problem_areas=problem_areas,
                recommendations=recommendations,
                progress_review=progress_review,
                monthly_goal=monthly_goal,
                encouragement=data["encouragement"],
            )
        except KeyError as error:
            raise ValueError(f"Advice JSON missing required field: {error}") from error

    @classmethod
    def from_service_response(cls, response: "ServiceAdviceResponse") -> Self:
        """
        Convert service AdviceResponse to API AdviceData.

        Parameters
        ----------
        response : ServiceAdviceResponse
            Advice response from AdviceGenerator.

        Returns
        -------
        AdviceData
            API response model.
        """
        # ##>: Convert spending patterns.
        spending_patterns = [
            SpendingPatternResponse(
                pattern_type=sp.pattern_type,
                description=sp.description,
                monthly_cost=sp.monthly_cost,
                occurrences=sp.occurrences,
                insight=sp.insight,
            )
            for sp in response.spending_patterns
        ]

        # ##>: Convert problem areas with new fields.
        problem_areas = [
            ProblemAreaResponse(
                category=pa.category,
                amount=pa.amount,
                trend=pa.trend,
                root_cause=pa.root_cause,
                impact=pa.impact,
            )
            for pa in response.problem_areas
        ]

        # ##>: Convert recommendations.
        recommendations = [
            RecommendationResponse(
                priority=rec.priority,
                action=rec.action,
                details=rec.details,
                expected_savings=rec.expected_savings,
                difficulty=rec.difficulty,
                quick_win=rec.quick_win,
            )
            for rec in response.recommendations
        ]

        # ##>: Convert progress review.
        progress_review = None
        if response.progress_review:
            progress_review = ProgressReviewResponse(
                previous_advice_followed=response.progress_review.previous_advice_followed,
                wins=response.progress_review.wins,
                areas_for_growth=response.progress_review.areas_for_growth,
            )

        # ##>: Convert monthly goal.
        monthly_goal = None
        if response.monthly_goal:
            monthly_goal = MonthlyGoalResponse(
                objective=response.monthly_goal.objective,
                target_amount=response.monthly_goal.target_amount,
                strategy=response.monthly_goal.strategy,
            )

        return cls(
            analysis=response.analysis,
            spending_patterns=spending_patterns,
            problem_areas=problem_areas,
            recommendations=recommendations,
            progress_review=progress_review,
            monthly_goal=monthly_goal,
            encouragement=response.encouragement,
        )


class GenerateAdviceRequest(BaseModel):
    """Request body for POST /api/advice/generate."""

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    regenerate: bool = False


class GenerateAdviceResponse(BaseModel):
    """Response for POST /api/advice/generate."""

    success: bool
    advice: AdviceData
    generated_at: datetime
    was_cached: bool


class EligibilityInfo(BaseModel):
    """Eligibility information for advice generation."""

    can_generate: bool
    is_first_advice: bool
    reason: str | None = None


class GetAdviceResponse(BaseModel):
    """Response for GET /api/advice/{year}/{month}."""

    success: bool
    advice: AdviceData | None
    generated_at: datetime | None
    exists: bool
    eligibility: EligibilityInfo
