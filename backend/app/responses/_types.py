"""Shared type literals for API schemas."""

from typing import Literal

# ##>: Valid score labels matching the ScoreLabel enum in db/enums.py.
ScoreLabelLiteral = Literal["Poor", "Need Improvement", "Okay", "Great"]

# ##>: Valid money map types matching the MoneyMapType enum in db/enums.py.
MoneyMapTypeLiteral = Literal["INCOME", "CORE", "CHOICE", "COMPOUND", "EXCLUDED"]

# ##>: Valid score trends for historical data API.
ScoreTrendLiteral = Literal["improving", "declining", "stable"]
