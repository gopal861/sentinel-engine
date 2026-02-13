import re


def _tokenize(text: str) -> set:
    # Simple alphanumeric tokenizer
    tokens = re.findall(r"\b\w+\b", text.lower())
    return set(tokens)


def _lexical_overlap(answer: str, context: str) -> float:
    answer_tokens = _tokenize(answer)
    context_tokens = _tokenize(context)

    if not answer_tokens or not context_tokens:
        return 0.0

    overlap = answer_tokens.intersection(context_tokens)
    return len(overlap) / len(answer_tokens)


def _context_utilization(answer: str, context: str) -> float:
    answer_tokens = _tokenize(answer)
    context_tokens = _tokenize(context)

    if not context_tokens:
        return 0.0

    overlap = answer_tokens.intersection(context_tokens)
    return len(overlap) / len(context_tokens)


def _length_sanity(answer: str, context: str) -> float:
    answer_len = len(answer.strip())
    context_len = len(context.strip())

    if context_len == 0:
        return 0.0

    ratio = answer_len / context_len

    # Cap ratio to prevent over-inflation
    if ratio > 1:
        ratio = 1.0

    return ratio


def compute_confidence(answer: str, context: str) -> float:
    lexical_score = _lexical_overlap(answer, context)
    utilization_score = _context_utilization(answer, context)
    length_score = _length_sanity(answer, context)

    weighted_score = (
        0.5 * lexical_score +
        0.3 * utilization_score +
        0.2 * length_score
    )

    # Clamp to [0, 1]
    return max(0.0, min(1.0, round(weighted_score, 4)))
