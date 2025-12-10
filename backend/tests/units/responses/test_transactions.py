"""Tests for transaction update request/response models."""

import pytest
from pydantic import ValidationError

from app.db.enums import MoneyMapType


class TestUpdateTransactionRequest:
    """Tests for UpdateTransactionRequest model validation."""

    def test_valid_money_map_type_accepted(self) -> None:
        """Valid MoneyMapType enum values are accepted."""
        from app.responses.transactions import UpdateTransactionRequest

        for money_map_type in MoneyMapType:
            request = UpdateTransactionRequest(
                money_map_type=money_map_type,
                money_map_subcategory=None,
            )
            assert request.money_map_type == money_map_type

    def test_invalid_money_map_type_returns_validation_error(self) -> None:
        """Invalid MoneyMapType value raises ValidationError."""
        from app.responses.transactions import UpdateTransactionRequest

        with pytest.raises(ValidationError) as exc_info:
            UpdateTransactionRequest(
                money_map_type="INVALID_TYPE",
                money_map_subcategory=None,
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("money_map_type",)

    def test_subcategory_accepts_valid_string(self) -> None:
        """Valid subcategory string is accepted."""
        from app.responses.transactions import UpdateTransactionRequest

        request = UpdateTransactionRequest(
            money_map_type=MoneyMapType.CORE,
            money_map_subcategory="Groceries",
        )
        assert request.money_map_subcategory == "Groceries"
