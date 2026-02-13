from sentinel.config import CONFIDENCE_THRESHOLD


def should_refuse(confidence_score: float, context: str) -> bool:
    if not context or not context.strip():
        return True

    if confidence_score < CONFIDENCE_THRESHOLD:
        return True

    return False
