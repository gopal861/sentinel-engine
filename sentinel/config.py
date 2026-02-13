# -----------------------------
# PROVIDER CONFIGURATION
# -----------------------------

ALLOWED_PROVIDERS = {"openai", "anthropic"}


# -----------------------------
# MODEL ROUTING
# -----------------------------

MODEL_MAP = {
    "openai": {
        "cheap": "gpt-4o-mini",
        "premium": "gpt-4o",
    },
    "anthropic": {
        "cheap": "claude-3-haiku",
        "premium": "claude-3-sonnet",
    }
}

MODEL_ROUTING_THRESHOLD = 2000  # input token threshold


# -----------------------------
# TOKEN LIMITS (approximate)
# -----------------------------

MODEL_TOKEN_LIMITS = {
    "gpt-4o-mini": 128_000,
    "gpt-4o": 128_000,
    "claude-3-haiku": 200_000,
    "claude-3-sonnet": 200_000,
}


# -----------------------------
# PRICING TABLE (USD per 1K tokens)
# NOTE: Update manually if provider pricing changes.
# -----------------------------

PRICING_TABLE = {
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.0006,
    },
    "gpt-4o": {
        "input": 0.005,
        "output": 0.015,
    },
    "claude-3-haiku": {
        "input": 0.00025,
        "output": 0.00125,
    },
    "claude-3-sonnet": {
        "input": 0.003,
        "output": 0.015,
    }
}


# -----------------------------
# CONFIDENCE CONFIGURATION
# -----------------------------

CONFIDENCE_THRESHOLD = 0.55


# -----------------------------
# OUTPUT CONTROL
# -----------------------------

MAX_OUTPUT_TOKENS = 500


# -----------------------------
# TIMEOUT CONFIGURATION (seconds)
# -----------------------------

LLM_TIMEOUT_SECONDS = 10
