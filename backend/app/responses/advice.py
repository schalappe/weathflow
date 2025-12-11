"""Pydantic models for Advice API endpoints."""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.services.dto.advice import AdviceResponse as ServiceAdviceResponse


class ProblemAreaResponse(BaseModel):
    """Problem area identified in financial analysis."""

    category: str
    amount: float
    trend: str


class AdviceData(BaseModel):
    """Structured advice content for API responses."""

    analysis: str
    problem_areas: list[ProblemAreaResponse]
    recommendations: list[str]
    encouragement: str

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """
        Parse AdviceData from stored JSON string.

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
            return cls(
                analysis=data["analysis"],
                problem_areas=[
                    ProblemAreaResponse(
                        category=pa["category"],
                        amount=pa["amount"],
                        trend=pa["trend"],
                    )
                    for pa in data["problem_areas"]
                ],
                recommendations=data["recommendations"],
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
        return cls(
            analysis=response.analysis,
            problem_areas=[
                ProblemAreaResponse(
                    category=pa.category,
                    amount=pa.amount,
                    trend=pa.trend,
                )
                for pa in response.problem_areas
            ],
            recommendations=list(response.recommendations),
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


class GetAdviceResponse(BaseModel):
    """Response for GET /api/advice/{year}/{month}."""

    success: bool
    advice: AdviceData | None
    generated_at: datetime | None
    exists: bool
