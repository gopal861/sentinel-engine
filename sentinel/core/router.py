from sentinel.config import MODEL_ROUTING_THRESHOLDS


def route_model(provider: str, input_tokens: int) -> str:
    """
    Deterministic routing based on input token count.

    This happens BEFORE the LLM call.
    This is the core cost governance decision.
    """

    if provider not in MODEL_ROUTING_THRESHOLDS:
        raise ValueError(f"Unsupported provider: {provider}")

    routing_config = MODEL_ROUTING_THRESHOLDS[provider]

    threshold = routing_config["threshold"]
    cheap_model = routing_config["cheap_model"]
    premium_model = routing_config["premium_model"]

    if input_tokens < threshold:
        return cheap_model
    else:
        return premium_model
