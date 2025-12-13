"""Advice generation service using Claude API."""

import json
import logging
from typing import ClassVar

import anthropic
from anthropic import Anthropic

from app.services.advice.models import AdviceResponse, MonthData, ProblemArea
from app.services.advice.prompt import ADVICE_SYSTEM_PROMPT
from app.services.exceptions import (
    AdviceAPIError,
    AdviceGenerationError,
    AdviceParseError,
    InsufficientDataError,
)

logger = logging.getLogger(__name__)


def calculate_trend(current: float, previous: float) -> str:
    """
    Calculate percentage trend between two values.

    Parameters
    ----------
    current : float
        Current period value.
    previous : float
        Previous period value.

    Returns
    -------
    str
        Formatted trend string (e.g., '+15%', '-8%', 'N/A').
    """
    if previous == 0:
        return "N/A"

    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{round(change)}%"


class AdviceGenerator:
    """
    Generate personalized financial advice using Claude API.

    Analyzes historical financial data and generates recommendations
    based on the Money Map (50/30/20) framework.

    Examples
    --------
    >>> generator = AdviceGenerator(api_key="sk-ant-...")
    >>> current = MonthData(year=2025, month=1, ...)
    >>> history = [MonthData(year=2024, month=12, ...)]
    >>> advice = generator.generate_advice(current, history)
    >>> advice.recommendations
    ['Réduire les dépenses en restauration', ...]
    """

    MIN_MONTHS_REQUIRED: ClassVar[int] = 2
    MAX_TOKENS: ClassVar[int] = 1024
    MAX_RETRIES: ClassVar[int] = 3

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Initialize advice generator with API key.

        Parameters
        ----------
        api_key : str
            Anthropic API key for Claude API calls.
        base_url : str | None
            Optional base URL for Anthropic API.
        model : str | None
            Claude model to use. Defaults to settings.anthropic_model.
        """
        from app.config.settings import get_settings

        self._client = Anthropic(api_key=api_key, base_url=base_url, max_retries=self.MAX_RETRIES)
        self._model = model if model is not None else get_settings().anthropic_model

    def generate_advice(self, current_month: MonthData, history: list[MonthData]) -> AdviceResponse:
        """
        Generate personalized financial advice based on historical data.

        Parameters
        ----------
        current_month : MonthData
            Current month's financial data.
        history : list[MonthData]
            Historical months (at least 1 required).

        Returns
        -------
        AdviceResponse
            Generated advice with analysis, problem areas, and recommendations.

        Raises
        ------
        InsufficientDataError
            If fewer than 2 months of data provided.
        AdviceAPIError
            If Claude API is unreachable after retries.
        AdviceParseError
            If response cannot be parsed.
        """
        logger.info("Starting advice generation for %d-%02d", current_month.year, current_month.month)

        self._validate_data(current_month, history)
        logger.debug("Data validation passed with %d history months", len(history))

        prompt = self._build_user_prompt(current_month, history)
        logger.debug("User prompt built (%d characters)", len(prompt))

        response_text = self._call_claude_api(prompt)
        logger.debug("Claude API response received (%d characters)", len(response_text))

        advice = self._parse_response(response_text)
        logger.info("Advice generation completed successfully")

        return advice

    def _validate_data(self, current_month: MonthData, history: list[MonthData]) -> None:
        """
        Validate that sufficient data is provided for advice generation.

        Parameters
        ----------
        current_month : MonthData
            Current month's data.
        history : list[MonthData]
            Historical months.

        Raises
        ------
        InsufficientDataError
            If fewer than MIN_MONTHS_REQUIRED months total.
        """
        # ##>: Need current + at least 1 history month = 2 minimum.
        if len(history) < 1:
            raise InsufficientDataError(min_months_required=self.MIN_MONTHS_REQUIRED)

    def _build_user_prompt(self, current_month: MonthData, history: list[MonthData]) -> str:
        """
        Build user prompt with financial data for Claude.

        Embeds system instructions in the user message to ensure compatibility
        with Claude Pro proxies that may not properly forward system prompts.

        Parameters
        ----------
        current_month : MonthData
            Current month's data.
        history : list[MonthData]
            Historical months.

        Returns
        -------
        str
            Formatted user prompt with embedded instructions.
        """
        all_months = [*history, current_month]

        months_data: list[dict[str, object]] = []
        for month in all_months:
            month_dict: dict[str, object] = {
                "year": month.year,
                "month": month.month,
                "total_income": month.total_income,
                "total_core": month.total_core,
                "total_choice": month.total_choice,
                "total_compound": month.total_compound,
                "core_percentage": month.core_percentage,
                "choice_percentage": month.choice_percentage,
                "compound_percentage": month.compound_percentage,
                "score": month.score,
                "score_label": month.score_label,
            }

            if month.category_breakdown:
                month_dict["category_breakdown"] = month.category_breakdown

            months_data.append(month_dict)

        # ##>: Embed system instructions in user message for Claude Pro compatibility.
        return (
            f"{ADVICE_SYSTEM_PROMPT}\n\n"
            "---\n\n"
            "Analyse les données financières suivantes et génère des conseils personnalisés. "
            "Retourne UNIQUEMENT un objet JSON, sans markdown ni texte additionnel.\n\n"
            f"{json.dumps(months_data, ensure_ascii=False, indent=2)}"
        )

    def _call_claude_api(self, user_prompt: str) -> str:
        """
        Call Claude API with the advice prompt.

        Parameters
        ----------
        user_prompt : str
            Formatted user prompt with financial data.

        Returns
        -------
        str
            Response text from Claude.

        Raises
        ------
        AdviceGenerationError
            If authentication fails.
        AdviceAPIError
            If API is unreachable after retries.
        AdviceParseError
            If response is empty.
        """
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self.MAX_TOKENS,
                system=ADVICE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.AuthenticationError as e:
            logger.error("Anthropic authentication failed: %s", e)
            raise AdviceGenerationError(
                "Invalid Anthropic API key. Please check your ANTHROPIC_API_KEY environment variable."
            ) from e
        except anthropic.APIConnectionError as e:
            logger.error("Claude API connection failed after %d retries: %s", self.MAX_RETRIES, e)
            raise AdviceAPIError(retry_count=self.MAX_RETRIES) from e
        except anthropic.RateLimitError as e:
            logger.error("Claude API rate limit exceeded after %d retries: %s", self.MAX_RETRIES, e)
            raise AdviceAPIError(retry_count=self.MAX_RETRIES) from e
        except anthropic.APIStatusError as e:
            logger.error("Anthropic API error (status %s): %s", e.status_code, e.message)
            raise AdviceAPIError(retry_count=self.MAX_RETRIES) from e

        # ##>: Extract text content from response.
        if not response.content:
            logger.error("Claude API returned empty content array")
            raise AdviceParseError("Claude API returned empty response content")

        content_block = response.content[0]
        if not hasattr(content_block, "text"):
            logger.error("Claude API returned unexpected content type: %s", type(content_block).__name__)
            raise AdviceParseError(f"Unexpected response content type: {type(content_block).__name__}")

        return content_block.text

    def _parse_response(self, response_text: str) -> AdviceResponse:
        """
        Parse Claude's JSON response into AdviceResponse.

        Parameters
        ----------
        response_text : str
            Raw response text from Claude.

        Returns
        -------
        AdviceResponse
            Parsed advice response.

        Raises
        ------
        AdviceParseError
            If JSON is malformed or missing required fields.
        """
        cleaned = response_text.strip()

        # ##>: Strip markdown code blocks if present.
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:]).rsplit("```", 1)[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("JSON parse error: %s. Response text: %s", e, response_text[:1000])
            raise AdviceParseError(response_text) from e

        if not isinstance(data, dict):
            logger.error("Claude API returned non-object JSON type: %s", type(data).__name__)
            raise AdviceParseError(response_text)

        try:
            problem_areas = [
                ProblemArea(
                    category=item["category"],
                    amount=item["amount"],
                    trend=item["trend"],
                )
                for item in data["problem_areas"]
            ]

            return AdviceResponse(
                analysis=data["analysis"],
                problem_areas=problem_areas,
                recommendations=data["recommendations"],
                encouragement=data["encouragement"],
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.error("Failed to parse advice response: %s", e)
            raise AdviceParseError(response_text) from e
