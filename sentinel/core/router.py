from sentinel.config import MODEL_MAP, MODEL_ROUTING_THRESHOLD


def route_model(provider: str, estimated_input_tokens: int) -> str:
    if provider not in MODEL_MAP:
        raise ValueError("Unsupported provider.")

    if estimated_input_tokens < MODEL_ROUTING_THRESHOLD:
        return MODEL_MAP[provider]["cheap"]

    return MODEL_MAP[provider]["premium"]
