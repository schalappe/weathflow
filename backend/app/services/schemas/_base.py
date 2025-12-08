"""Base model configuration for service schemas."""

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Base model for immutable data structures."""

    model_config = ConfigDict(frozen=True)
