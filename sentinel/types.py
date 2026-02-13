from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ProviderEnum(str, Enum):
    openai = "openai"
    anthropic = "anthropic"


class GovernRequest(BaseModel):
    query: str = Field(..., min_length=1)
    context: str = Field(..., min_length=1)
    provider: ProviderEnum
    policy_config: Optional[dict] = None

    @field_validator("query", "context")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("Field cannot be empty or whitespace.")
        return value


class GovernResponse(BaseModel):
    answer: str
    refusal: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    model_used: str
    estimated_cost: float = Field(..., ge=0.0)
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    latency_ms: int = Field(..., ge=0)
    provider: ProviderEnum


class ErrorResponse(BaseModel):
    error: str
    error_type: Literal[
        "validation_error",
        "provider_error",
        "timeout_error",
        "rate_limit_error",
        "token_overflow",
        "internal_error"
    ]
