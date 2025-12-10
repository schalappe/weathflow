"""Tests for history service functions."""

from app.db.models.month import Month
from app.services import months as months_service
from tests.conftest import DatabaseTestCase


class TestGetMonthsHistory(DatabaseTestCase):
    """Tests for get_months_history function."""

    def test_returns_correct_months_when_limit_less_than_available(self) -> None:
        """Should return only the requested number of months."""
        # ##>: Create 5 months.
        for i in range(1, 6):
            month = Month(year=2025, month=i, score=i % 4, score_label="Okay")
            self.session.add(month)
        self.session.commit()

        result = months_service.get_months_history(self.session, limit=3)

        self.assertEqual(len(result), 3)
        # ##>: Should return most recent 3 months (March, April, May) in chronological order.
        self.assertEqual(result[0].month, 3)
        self.assertEqual(result[1].month, 4)
        self.assertEqual(result[2].month, 5)

    def test_returns_all_months_when_limit_exceeds_available(self) -> None:
        """Should return all available months when limit > available."""
        # ##>: Create only 2 months.
        month1 = Month(year=2025, month=1, score=2, score_label="Okay")
        month2 = Month(year=2025, month=2, score=3, score_label="Great")
        self.session.add_all([month1, month2])
        self.session.commit()

        result = months_service.get_months_history(self.session, limit=12)

        self.assertEqual(len(result), 2)
        # ##>: Should be in chronological order (oldest first).
        self.assertEqual(result[0].month, 1)
        self.assertEqual(result[1].month, 2)

    def test_returns_empty_list_when_no_months_exist(self) -> None:
        """Should return empty list when no months in database."""
        result = months_service.get_months_history(self.session, limit=12)

        self.assertEqual(result, [])


class TestCalculateScoreTrend(DatabaseTestCase):
    """Tests for _calculate_score_trend function."""

    def test_returns_improving_when_recent_higher(self) -> None:
        """Should return 'improving' when last 3 months avg > previous 3 months avg."""
        # ##>: Previous 3 months: scores 1, 1, 1 (avg=1). Recent 3 months: scores 3, 3, 3 (avg=3).
        months: list[Month] = []
        for i in range(1, 7):
            score = 1 if i <= 3 else 3
            months.append(Month(year=2025, month=i, score=score, score_label="Okay"))

        result = months_service._calculate_score_trend(months)

        self.assertEqual(result, "improving")

    def test_returns_declining_when_recent_lower(self) -> None:
        """Should return 'declining' when last 3 months avg < previous 3 months avg."""
        # ##>: Previous 3 months: scores 3, 3, 3 (avg=3). Recent 3 months: scores 1, 1, 1 (avg=1).
        months: list[Month] = []
        for i in range(1, 7):
            score = 3 if i <= 3 else 1
            months.append(Month(year=2025, month=i, score=score, score_label="Okay"))

        result = months_service._calculate_score_trend(months)

        self.assertEqual(result, "declining")

    def test_returns_stable_when_averages_equal(self) -> None:
        """Should return 'stable' when averages are exactly equal."""
        # ##>: All months have same score.
        months: list[Month] = []
        for i in range(1, 7):
            months.append(Month(year=2025, month=i, score=2, score_label="Okay"))

        result = months_service._calculate_score_trend(months)

        self.assertEqual(result, "stable")

    def test_returns_stable_when_fewer_than_6_months(self) -> None:
        """Should return 'stable' when fewer than 6 months of data."""
        months: list[Month] = []
        for i in range(1, 5):  # Only 4 months
            months.append(Month(year=2025, month=i, score=i, score_label="Okay"))

        result = months_service._calculate_score_trend(months)

        self.assertEqual(result, "stable")

    def test_correctly_identifies_best_and_worst_months(self) -> None:
        """Should identify best (highest score) and worst (lowest score) months."""
        months: list[Month] = []
        scores = [1, 2, 3, 0, 2, 1]  # Best=3 (month 3), Worst=0 (month 4)
        for i, score in enumerate(scores, start=1):
            months.append(Month(year=2025, month=i, score=score, score_label="Okay"))

        summary = months_service.calculate_history_summary(months)

        self.assertIsNotNone(summary.best_month)
        self.assertIsNotNone(summary.worst_month)
        assert summary.best_month is not None
        assert summary.worst_month is not None
        self.assertEqual(summary.best_month.month, 3)
        self.assertEqual(summary.best_month.score, 3)
        self.assertEqual(summary.worst_month.month, 4)
        self.assertEqual(summary.worst_month.score, 0)


class TestCalculateHistorySummary(DatabaseTestCase):
    """Tests for calculate_history_summary function."""

    def test_returns_zeroed_summary_for_empty_list(self) -> None:
        """Should return zeroed summary when no months provided."""
        result = months_service.calculate_history_summary([])

        self.assertEqual(result.total_months, 0)
        self.assertEqual(result.average_score, 0.0)
        self.assertEqual(result.score_trend, "stable")
        self.assertIsNone(result.best_month)
        self.assertIsNone(result.worst_month)

    def test_calculates_correct_average_score(self) -> None:
        """Should calculate correct average score across months."""
        months: list[Month] = []
        scores = [1, 2, 3]  # avg = 2.0
        for i, score in enumerate(scores, start=1):
            months.append(Month(year=2025, month=i, score=score, score_label="Okay"))

        result = months_service.calculate_history_summary(months)

        self.assertEqual(result.average_score, 2.0)

    def test_most_recent_month_wins_tie_for_best(self) -> None:
        """Should select most recent month when multiple have same best score."""
        # ##>: Months 1, 2, 3 all have score 3.
        months: list[Month] = []
        for i in range(1, 4):
            months.append(Month(year=2025, month=i, score=3, score_label="Great"))

        result = months_service.calculate_history_summary(months)

        assert result.best_month is not None
        # ##>: Month 3 is most recent, should win tie.
        self.assertEqual(result.best_month.month, 3)

    def test_most_recent_month_wins_tie_for_worst(self) -> None:
        """Should select most recent month when multiple have same worst score."""
        # ##>: Months 1, 2, 3 all have score 0.
        months: list[Month] = []
        for i in range(1, 4):
            months.append(Month(year=2025, month=i, score=0, score_label="Poor"))

        result = months_service.calculate_history_summary(months)

        assert result.worst_month is not None
        # ##>: Month 3 is most recent, should win tie.
        self.assertEqual(result.worst_month.month, 3)
