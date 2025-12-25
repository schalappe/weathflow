"""Advice generation service using Claude API."""

import json
from typing import Any, ClassVar

import anthropic
from anthropic import Anthropic
from loguru import logger

from app.services.advice.models import (
    AdviceResponse,
    MonthData,
    MonthlyGoal,
    ProblemArea,
    ProgressReview,
    Recommendation,
    SpendingPattern,
)
from app.services.advice.prompt import ADVICE_SYSTEM_PROMPT
from app.services.exceptions import (
    AdviceAPIError,
    AdviceGenerationError,
    AdviceParseError,
    InsufficientDataError,
)


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
    MAX_RETRIES: ClassVar[int] = 3
    MIN_THINKING_BUDGET: ClassVar[int] = 1000
    MAX_THINKING_BUDGET: ClassVar[int] = 100000
    DEFAULT_THINKING_BUDGET: ClassVar[int] = 10000

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str | None = None,
        thinking_enabled: bool | None = None,
        thinking_budget: int | None = None,
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
        thinking_enabled : bool | None
            Enable extended thinking mode for complex reasoning. Defaults to settings.
        thinking_budget : int | None
            Token budget for thinking. Defaults to settings.anthropic_thinking_budget.
        """
        from app.config.settings import get_settings

        settings = get_settings()
        self._client = Anthropic(api_key=api_key, base_url=base_url, max_retries=self.MAX_RETRIES)
        self._model = model if model is not None else settings.anthropic_model
        self._thinking_enabled = (
            thinking_enabled if thinking_enabled is not None else settings.anthropic_thinking_enabled
        )

        # ##>: Validate and clamp thinking budget to valid range.
        raw_budget = thinking_budget if thinking_budget is not None else settings.anthropic_thinking_budget
        if not (self.MIN_THINKING_BUDGET <= raw_budget <= self.MAX_THINKING_BUDGET):
            logger.warning(
                "Invalid thinking budget {}. Must be between {} and {}. Using default {}.",
                raw_budget,
                self.MIN_THINKING_BUDGET,
                self.MAX_THINKING_BUDGET,
                self.DEFAULT_THINKING_BUDGET,
            )
            self._thinking_budget = self.DEFAULT_THINKING_BUDGET
        else:
            self._thinking_budget = raw_budget

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
        logger.info("Starting advice generation for {}-{:02d}", current_month.year, current_month.month)

        self._validate_data(current_month, history)
        logger.debug("Data validation passed with {} history months", len(history))

        prompt = self._build_user_prompt(current_month, history)
        logger.debug("User prompt built ({} characters)", len(prompt))

        response_text = self._call_claude_api(prompt)
        logger.debug("Claude API response received ({} characters)", len(response_text))

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

            # ##>: Include all transactions for pattern analysis and personalized recommendations.
            if month.transactions:
                month_dict["transactions"] = {
                    category: [tx.model_dump() for tx in txs] for category, txs in month.transactions.items()
                }

            # ##>: Include past advice to track if recommendations were followed.
            if month.past_advice:
                month_dict["past_advice"] = month.past_advice

            months_data.append(month_dict)

        # ##>: Embed system instructions in user message for Claude Pro compatibility.
        return (
            f"{ADVICE_SYSTEM_PROMPT}\n\n"
            "---\n\n"
            "Analyse les données financières suivantes et génère des conseils personnalisés. "
            "Analyse TOUTES les transactions pour identifier des patterns et recommandations SPÉCIFIQUES.\n"
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
            # ##>: Build API call parameters based on thinking mode configuration.
            create_params: dict[str, Any] = {
                "model": self._model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": user_prompt}],
            }

            if self._thinking_enabled:
                # ##>: Extended thinking mode for deeper financial analysis.
                create_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self._thinking_budget,
                }
                logger.debug("Using extended thinking mode with budget: {}", self._thinking_budget)
            else:
                # ##>: Request high-quality output via effort API (beta feature, model-agnostic).
                create_params["extra_headers"] = {"anthropic-beta": "effort-2025-11-24"}
                create_params["extra_body"] = {"output_config": {"effort": "high"}}

            response = self._client.messages.create(**create_params)
        except anthropic.AuthenticationError as e:
            logger.error("Anthropic authentication failed: {}", e)
            raise AdviceGenerationError(
                "Invalid Anthropic API key. Please check your ANTHROPIC_API_KEY environment variable."
            ) from e
        except anthropic.APIConnectionError as e:
            logger.error("Claude API connection failed after {} retries: {}", self.MAX_RETRIES, e)
            raise AdviceAPIError(retry_count=self.MAX_RETRIES) from e
        except anthropic.RateLimitError as e:
            logger.error("Claude API rate limit exceeded after {} retries: {}", self.MAX_RETRIES, e)
            raise AdviceAPIError(retry_count=self.MAX_RETRIES) from e
        except anthropic.APIStatusError as e:
            logger.error("Anthropic API error (status {}): {}", e.status_code, e.message)
            raise AdviceAPIError(retry_count=self.MAX_RETRIES) from e

        # ##>: Extract text content from response. Handle both regular and thinking mode responses.
        if not response.content:
            logger.error("Claude API returned empty content array")
            raise AdviceParseError("Claude API returned empty response content")

        # ##>: Find the text block, skipping thinking blocks if present.
        response_text: str | None = None
        for content_block in response.content:
            if hasattr(content_block, "type") and content_block.type == "thinking":
                logger.debug("Thinking block received ({} chars)", len(getattr(content_block, "thinking", "")))
                continue
            if hasattr(content_block, "text"):
                response_text = content_block.text
                break

        if response_text is None:
            logger.error(
                "Claude API returned no text block. Content types: {}",
                [getattr(b, "type", type(b).__name__) for b in response.content],
            )
            raise AdviceParseError("Claude API returned no text content")

        return response_text

    def _parse_response(self, response_text: str) -> AdviceResponse:
        """
        Parse Claude's JSON response into AdviceResponse.

        Handles both the new enriched format and legacy format for backward compatibility.

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
            logger.error("JSON parse error: {}. Response text: {}", e, response_text[:1000])
            raise AdviceParseError(response_text) from e

        if not isinstance(data, dict):
            logger.error("Claude API returned non-object JSON type: {}", type(data).__name__)
            raise AdviceParseError(response_text)

        try:
            # ##>: Parse spending patterns (new format).
            spending_patterns = [
                SpendingPattern(
                    pattern_type=item["pattern_type"],
                    description=item["description"],
                    monthly_cost=item["monthly_cost"],
                    occurrences=item["occurrences"],
                    insight=item["insight"],
                )
                for item in data.get("spending_patterns", [])
            ]

            # ##>: Parse problem areas with optional new fields.
            problem_areas = [
                ProblemArea(
                    category=item["category"],
                    amount=item["amount"],
                    trend=item["trend"],
                    root_cause=item.get("root_cause"),
                    impact=item.get("impact"),
                )
                for item in data["problem_areas"]
            ]

            # ##>: Parse recommendations - handle both new dict format and legacy string format.
            raw_recommendations = data.get("recommendations", [])
            if raw_recommendations and isinstance(raw_recommendations[0], dict):
                recommendations = [
                    Recommendation(
                        priority=item["priority"],
                        action=item["action"],
                        details=item["details"],
                        expected_savings=item["expected_savings"],
                        difficulty=item["difficulty"],
                        quick_win=item.get("quick_win", False),
                    )
                    for item in raw_recommendations
                ]
            else:
                # ##>: Legacy format: recommendations as list of strings.
                recommendations = [
                    Recommendation(
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
                progress_review = ProgressReview(
                    previous_advice_followed=pr["previous_advice_followed"],
                    wins=pr.get("wins", []),
                    areas_for_growth=pr.get("areas_for_growth", []),
                )

            # ##>: Parse monthly goal (new format).
            monthly_goal = None
            if "monthly_goal" in data:
                mg = data["monthly_goal"]
                monthly_goal = MonthlyGoal(
                    objective=mg["objective"],
                    target_amount=mg["target_amount"],
                    strategy=mg["strategy"],
                )

            return AdviceResponse(
                analysis=data["analysis"],
                spending_patterns=spending_patterns,
                problem_areas=problem_areas,
                recommendations=recommendations,
                progress_review=progress_review,
                monthly_goal=monthly_goal,
                encouragement=data["encouragement"],
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.error("Failed to parse advice response: {}", e)
            raise AdviceParseError(response_text) from e
