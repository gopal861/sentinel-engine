# ============================================
# PROVIDER CONFIGURATION
# ============================================

ALLOWED_PROVIDERS = {"openai", "anthropic"}


# ============================================
# ROUTING CONFIGURATION (SINGLE SOURCE OF TRUTH)
# ============================================

MODEL_ROUTING_THRESHOLDS = {
    "openai": {
        "threshold": 500,
        "cheap_model": "gpt-4o-mini",
        "premium_model": "gpt-4o",
    },
    "anthropic": {
        "threshold": 500,
        "cheap_model": "claude-3-haiku",
        "premium_model": "claude-3-sonnet",
    }
}


# ============================================
# TOKEN LIMITS
# ============================================

MODEL_TOKEN_LIMITS = {
    "gpt-4o-mini": 128000,
    "gpt-4o": 128000,
    "claude-3-haiku": 200000,
    "claude-3-sonnet": 200000,
}


# ============================================
# PRICING TABLE (USD per token)
# ============================================

PRICING_TABLE = {
    "gpt-4o-mini": {
        "input": 0.00015 / 1000,
        "output": 0.0006 / 1000,
    },
    "gpt-4o": {
        "input": 0.005 / 1000,
        "output": 0.015 / 1000,
    },
    "claude-3-haiku": {
        "input": 0.00025 / 1000,
        "output": 0.00125 / 1000,
    },
    "claude-3-sonnet": {
        "input": 0.003 / 1000,
        "output": 0.015 / 1000,
    }
}


# ============================================
# CONFIDENCE CONFIGURATION
# ============================================

CONFIDENCE_THRESHOLD = 0.55


# ============================================
# OUTPUT CONTROL
# ============================================

MAX_OUTPUT_TOKENS = 500


# ============================================
# TIMEOUT CONFIGURATION
# ============================================

LLM_TIMEOUT_SECONDS = 20
