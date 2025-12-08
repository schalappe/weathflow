"""Tests for Money Map enums."""

from enum import Enum

from app.db.enums import MoneyMapType, ScoreLabel


def test_money_map_type_values_are_correct_strings() -> None:
    """MoneyMapType should have the expected string values."""
    assert MoneyMapType.INCOME.value == 'INCOME'
    assert MoneyMapType.CORE.value == 'CORE'
    assert MoneyMapType.CHOICE.value == 'CHOICE'
    assert MoneyMapType.COMPOUND.value == 'COMPOUND'
    assert MoneyMapType.EXCLUDED.value == 'EXCLUDED'


def test_score_label_values_match_expected_labels() -> None:
    """ScoreLabel should have human-readable string values."""
    assert ScoreLabel.POOR.value == 'Poor'
    assert ScoreLabel.NEED_IMPROVEMENT.value == 'Need Improvement'
    assert ScoreLabel.OKAY.value == 'Okay'
    assert ScoreLabel.GREAT.value == 'Great'


def test_enums_inherit_from_str_and_enum() -> None:
    """Both enums should inherit from str and Enum for SQLite compatibility."""
    assert issubclass(MoneyMapType, str)
    assert issubclass(MoneyMapType, Enum)
    assert issubclass(ScoreLabel, str)
    assert issubclass(ScoreLabel, Enum)

    # ##>: String inheritance allows direct string comparison without .value.
    assert MoneyMapType.INCOME == 'INCOME'
    assert ScoreLabel.GREAT == 'Great'
