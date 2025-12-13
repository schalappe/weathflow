"""Unit tests for advice response models."""

import json
import unittest

from pydantic import ValidationError

from app.responses.advice import AdviceData, GenerateAdviceRequest
from app.services.advice.models import AdviceResponse as ServiceAdviceResponse
from app.services.advice.models import ProblemArea as ServiceProblemArea


class TestAdviceDataFromJson(unittest.TestCase):
    """Tests for AdviceData.from_json factory method."""

    def test_parses_valid_json_string(self) -> None:
        """From JSON parses valid JSON string with all fields."""
        json_str = json.dumps(
            {
                "analysis": "Votre gestion financière est excellente.",
                "problem_areas": [
                    {"category": "Subscriptions", "amount": 85.0, "trend": "+20%"},
                    {"category": "Dining", "amount": 150.0, "trend": "+15%"},
                    {"category": "Entertainment", "amount": 120.0, "trend": "N/A"},
                ],
                "recommendations": [
                    "Réduire les abonnements.",
                    "Limiter les repas au restaurant.",
                    "Maintenir votre épargne.",
                ],
                "encouragement": "Continuez comme ça!",
            }
        )

        result = AdviceData.from_json(json_str)

        self.assertEqual(result.analysis, "Votre gestion financière est excellente.")
        self.assertEqual(len(result.problem_areas), 3)
        self.assertEqual(result.problem_areas[0].category, "Subscriptions")
        self.assertEqual(result.problem_areas[0].amount, 85.0)
        self.assertEqual(result.problem_areas[0].trend, "+20%")
        self.assertEqual(len(result.recommendations), 3)
        self.assertEqual(result.encouragement, "Continuez comme ça!")


class TestAdviceDataFromServiceResponse(unittest.TestCase):
    """Tests for AdviceData.from_service_response factory method."""

    def test_converts_service_response_correctly(self) -> None:
        """From service response converts DTO to API model."""
        service_response = ServiceAdviceResponse(
            analysis="Test analysis",
            problem_areas=[
                ServiceProblemArea(category="Test", amount=100.0, trend="+10%"),
            ],
            recommendations=["Recommendation 1", "Recommendation 2"],
            encouragement="Keep going!",
        )

        result = AdviceData.from_service_response(service_response)

        self.assertEqual(result.analysis, "Test analysis")
        self.assertEqual(len(result.problem_areas), 1)
        self.assertEqual(result.problem_areas[0].category, "Test")
        self.assertEqual(result.problem_areas[0].amount, 100.0)
        self.assertEqual(result.problem_areas[0].trend, "+10%")
        self.assertEqual(result.recommendations, ["Recommendation 1", "Recommendation 2"])
        self.assertEqual(result.encouragement, "Keep going!")


class TestGenerateAdviceRequestValidation(unittest.TestCase):
    """Tests for GenerateAdviceRequest field validation."""

    def test_validates_year_constraints(self) -> None:
        """Request validates year is between 2000 and 2100."""
        with self.assertRaises(ValidationError):
            GenerateAdviceRequest(year=1999, month=1)

        with self.assertRaises(ValidationError):
            GenerateAdviceRequest(year=2101, month=1)

        request = GenerateAdviceRequest(year=2000, month=1)
        self.assertEqual(request.year, 2000)

        request = GenerateAdviceRequest(year=2100, month=12)
        self.assertEqual(request.year, 2100)

    def test_validates_month_constraints(self) -> None:
        """Request validates month is between 1 and 12."""
        with self.assertRaises(ValidationError):
            GenerateAdviceRequest(year=2025, month=0)

        with self.assertRaises(ValidationError):
            GenerateAdviceRequest(year=2025, month=13)

        request = GenerateAdviceRequest(year=2025, month=1)
        self.assertEqual(request.month, 1)

        request = GenerateAdviceRequest(year=2025, month=12)
        self.assertEqual(request.month, 12)

    def test_regenerate_defaults_to_false(self) -> None:
        """Request regenerate flag defaults to False."""
        request = GenerateAdviceRequest(year=2025, month=1)

        self.assertFalse(request.regenerate)
