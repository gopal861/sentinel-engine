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

 
    # STEP 1 — Estimate input tokens
    

    temp_model = route_model(provider, 0)

    input_tokens = estimate_input_tokens(
        query,
        context,
        provider,
        temp_model,
    )

    # ============================================
    # STEP 2 — Deterministic routing (CORE CONTROL)
    # ============================================

    model_used = route_model(
        provider=provider,
        input_tokens=input_tokens,
    )

    # ============================================
    # STEP 3 — Estimate output tokens
    # ============================================

    output_tokens_est = estimate_output_tokens()

    # ============================================
    # STEP 4 — Token overflow protection
    # ============================================

    check_token_overflow(
        input_tokens,
        output_tokens_est,
        model_used,
    )

    # ============================================
    # STEP 5 — Estimate cost BEFORE call
    # ============================================

    estimated_cost = estimate_cost(
        input_tokens,
        output_tokens_est,
        model_used,
    )

    # ============================================
    # STEP 6 — Call LLM (using routed model)
    # ============================================

    answer, actual_input_tokens, actual_output_tokens, latency_ms = call_llm(
        provider=provider,
        model=model_used,
        query=query,
        context=context,
    )

    # ============================================
    # STEP 7 — Compute actual cost
    # ============================================

    actual_cost = estimate_cost(
        actual_input_tokens,
        actual_output_tokens,
        model_used,
    )

    # ============================================
    # STEP 8 — Confidence scoring
    # ============================================

    confidence_score = compute_confidence(
        answer,
        context,
    )

    # ============================================
    # STEP 9 — Refusal enforcement
    # ============================================

    refusal_flag = should_refuse(
        confidence_score,
        context,
    )

    if refusal_flag:
        answer = "Request refused due to low confidence in context grounding."

    # ============================================
    # STEP 10 — Return governed response
    # ============================================

    return {
        "answer": answer,
        "refusal": refusal_flag,
        "confidence_score": confidence_score,
        "model_used": model_used,
        "estimated_cost": estimated_cost,
        "actual_cost": actual_cost,
        "input_tokens": actual_input_tokens,
        "output_tokens": actual_output_tokens,
        "latency_ms": latency_ms,
        "provider": provider,
    }
