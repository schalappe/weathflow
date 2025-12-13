"""Unit tests for AdviceRepository."""

from app.db.models.advice import Advice
from app.db.models.month import Month
from app.repositories.advice_repository import AdviceRepository
from tests.conftest import DatabaseTestCase


class TestAdviceRepository(DatabaseTestCase):
    """Test cases for AdviceRepository data access operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        self.month = Month(year=2025, month=1)
        self.session.add(self.month)
        self.session.commit()

    def test_get_by_month_id_returns_advice(self) -> None:
        """get_by_month_id returns advice when it exists."""
        advice = Advice(month_id=self.month.id, advice_text='{"summary": "Test advice"}')
        self.session.add(advice)
        self.session.commit()

        repo = AdviceRepository(self.session)
        result = repo.get_by_month_id(self.month.id)

        assert result is not None
        assert result.advice_text == '{"summary": "Test advice"}'

    def test_get_by_month_id_returns_none_for_missing(self) -> None:
        """get_by_month_id returns None when advice does not exist."""
        repo = AdviceRepository(self.session)
        result = repo.get_by_month_id(self.month.id)

        assert result is None

    def test_upsert_creates_new_advice(self) -> None:
        """upsert creates new advice when none exists."""
        repo = AdviceRepository(self.session)
        result = repo.upsert(self.month.id, '{"summary": "New advice"}')

        assert result.id is not None
        assert result.advice_text == '{"summary": "New advice"}'
        assert result.month_id == self.month.id

    def test_upsert_updates_existing_advice(self) -> None:
        """upsert updates advice when it already exists."""
        advice = Advice(month_id=self.month.id, advice_text='{"summary": "Old advice"}')
        self.session.add(advice)
        self.session.commit()
        original_id = advice.id

        repo = AdviceRepository(self.session)
        result = repo.upsert(self.month.id, '{"summary": "Updated advice"}')

        assert result.id == original_id  # Same record
        assert result.advice_text == '{"summary": "Updated advice"}'

    def test_upsert_updates_generated_at_timestamp(self) -> None:
        """upsert updates generated_at timestamp when updating."""
        advice = Advice(month_id=self.month.id, advice_text='{"summary": "Old advice"}')
        self.session.add(advice)
        self.session.commit()
        original_timestamp = advice.generated_at

        # Allow time difference
        import time

        time.sleep(0.01)

        repo = AdviceRepository(self.session)
        result = repo.upsert(self.month.id, '{"summary": "Updated advice"}')

        assert result.generated_at > original_timestamp

    def test_delete_removes_advice(self) -> None:
        """delete removes advice from database."""
        advice = Advice(month_id=self.month.id, advice_text='{"summary": "To delete"}')
        self.session.add(advice)
        self.session.commit()

        repo = AdviceRepository(self.session)
        repo.delete(advice)
        repo.commit()

        assert repo.get_by_month_id(self.month.id) is None

    def test_commit_persists_changes(self) -> None:
        """commit persists pending changes to database."""
        repo = AdviceRepository(self.session)
        advice = Advice(month_id=self.month.id, advice_text='{"summary": "Test"}')
        self.session.add(advice)

        repo.commit()

        # Verify in new query
        result = repo.get_by_month_id(self.month.id)
        assert result is not None

    def test_rollback_reverts_changes(self) -> None:
        """rollback reverts uncommitted changes."""
        advice = Advice(month_id=self.month.id, advice_text='{"summary": "Original"}')
        self.session.add(advice)
        self.session.commit()

        repo = AdviceRepository(self.session)
        advice.advice_text = '{"summary": "Modified"}'

        repo.rollback()

        # Refresh to get original value
        self.session.refresh(advice)
        assert advice.advice_text == '{"summary": "Original"}'
