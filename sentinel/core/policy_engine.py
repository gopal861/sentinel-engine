from typing import Dict

from sentinel.core.cost_estimator import (
    estimate_input_tokens,
    estimate_output_tokens,
    estimate_cost,
    check_token_overflow,
)
from sentinel.core.router import route_model
from sentinel.core.llm_client import call_llm
from sentinel.core.confidence import compute_confidence
from sentinel.core.refusal import should_refuse


def execute_governance(
    query: str,
    context: str,
    provider: str,
) -> Dict:

    # Step 1 — Estimate input tokens (initial using cheap model assumption)
    # Temporary model choice for token estimation
    temp_model = route_model(provider, 0)

    input_tokens = estimate_input_tokens(query, context, provider, temp_model)

    # Step 2 — Route model based on estimated input tokens
    model = route_model(provider, input_tokens)

    # Step 3 — Estimate output tokens
    output_tokens_est = estimate_output_tokens()

    # Step 4 — Overflow protection
    check_token_overflow(input_tokens, output_tokens_est, model)

    # Step 5 — Estimate pre-call cost
    estimated_cost = estimate_cost(input_tokens, output_tokens_est, model)

    # Step 6 — Call LLM
    answer, actual_input_tokens, actual_output_tokens, latency_ms = call_llm(
        provider=provider,
        model=model,
        query=query,
        context=context,
    )

    # Step 7 — Compute actual cost
    actual_cost = estimate_cost(
        actual_input_tokens,
        actual_output_tokens,
        model,
    )

    # Step 8 — Confidence scoring
    confidence_score = compute_confidence(answer, context)

    # Step 9 — Refusal decision
    refusal_flag = should_refuse(confidence_score, context)

    if refusal_flag:
        answer = "Request refused due to low confidence in context grounding."

    return {
        "answer": answer,
        "refusal": refusal_flag,
        "confidence_score": confidence_score,
        "model_used": model,
        "estimated_cost": estimated_cost,
        "actual_cost": actual_cost,
        "input_tokens": actual_input_tokens,
        "output_tokens": actual_output_tokens,
        "latency_ms": latency_ms,
        "provider": provider,
    }
