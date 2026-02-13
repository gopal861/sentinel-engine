from typing import Tuple
import math
import tiktoken

from sentinel.config import (
    PRICING_TABLE,
    MAX_OUTPUT_TOKENS,
    MODEL_TOKEN_LIMITS,
)


def _estimate_openai_tokens(text: str, model: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def _estimate_anthropic_tokens(text: str) -> int:
    # Heuristic approximation
    return math.ceil(len(text) / 4)


def estimate_input_tokens(query: str, context: str, provider: str, model: str) -> int:
    combined = f"{query}\n{context}"

    if provider == "openai":
        return _estimate_openai_tokens(combined, model)

    if provider == "anthropic":
        return _estimate_anthropic_tokens(combined)

    raise ValueError("Unsupported provider for token estimation.")


def estimate_output_tokens() -> int:
    return MAX_OUTPUT_TOKENS


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> float:
    pricing = PRICING_TABLE[model]

    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]

    return round(input_cost + output_cost, 8)


def check_token_overflow(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> None:
    model_limit = MODEL_TOKEN_LIMITS[model]

    if input_tokens + output_tokens > model_limit:
        raise ValueError("token_overflow")
