"""Shared type literals for API schemas."""

from typing import Literal

# ##>: Valid score labels matching the ScoreLabel enum in db/enums.py.
ScoreLabelLiteral = Literal["Poor", "Need Improvement", "Okay", "Great"]
