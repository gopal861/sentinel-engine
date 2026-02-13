import time
from typing import Tuple

from openai import OpenAI
import anthropic

from sentinel.config import LLM_TIMEOUT_SECONDS, MAX_OUTPUT_TOKENS
from sentinel.prompts.grounding_prompt import build_grounding_prompt


openai_client = OpenAI()
anthropic_client = anthropic.Anthropic()


def call_llm(
    provider: str,
    model: str,
    query: str,
    context: str,
) -> Tuple[str, int, int, int]:

    prompt = build_grounding_prompt(query, context)

    start_time = time.time()

    try:
        if provider == "openai":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_OUTPUT_TOKENS,
                timeout=LLM_TIMEOUT_SECONDS,
            )

            answer = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

        elif provider == "anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}],
                timeout=LLM_TIMEOUT_SECONDS,
            )

            answer = response.content[0].text

            usage = getattr(response, "usage", None)
            if usage:
                input_tokens = getattr(usage, "input_tokens", 0)
                output_tokens = getattr(usage, "output_tokens", 0)
            else:
                input_tokens = 0
                output_tokens = 0

        else:
            raise ValueError("provider_error")

    except Exception as e:
        error_str = str(e).lower()
        if "timeout" in error_str:
            raise ValueError("timeout_error")

        if "rate" in error_str:
            raise ValueError("rate_limit_error")

        raise ValueError("provider_error")

    latency_ms = int((time.time() - start_time) * 1000)

    return answer, input_tokens, output_tokens, latency_ms
