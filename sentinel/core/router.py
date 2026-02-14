from sentinel.config import MODEL_MAP, MODEL_ROUTING_THRESHOLD



from typing import Dict


CHEAP_MODEL = "gpt-4o-mini"
PREMIUM_MODEL = "gpt-4o"


CONFIDENCE_THRESHOLD = 0.75


def select_model(confidence_score: float) -> str:
    """
    Deterministically select model based on confidence.

    High confidence → cheap model
    Low confidence → premium model
    """

    if confidence_score >= CONFIDENCE_THRESHOLD:
        return CHEAP_MODEL

    return PREMIUM_MODEL


def route_request(confidence_score: float, provider: str) -> Dict:
    """
    Returns routing decision.

    Output format:
    {
        provider: str,
        model: str
    }
    """

    model = select_model(confidence_score)

    return {
        "provider": provider,
        "model": model
    }
