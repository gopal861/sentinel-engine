import matplotlib.pyplot as plt
import pandas as pd

# ================================
# CONFIGURATION (Hardcoded from your real metrics)
# ================================

BASELINE = {
    "fabrication_rate": 66.67,
    "p95_latency": 1571.44,
    "cost_per_100": 0.00  # Baseline cost not governed
}

SENTINEL = {
    "fabrication_rate": 0.00,
    "p95_latency": 1462.00,
    "cost_per_100": 0.0303
}

# ================================
# STYLE (Executive Minimal)
# ================================

plt.style.use("seaborn-v0_8-whitegrid")

def save_bar_chart(title, baseline_value, sentinel_value, ylabel, filename):
    labels = ["Baseline LLM", "Sentinel Engine"]
    values = [baseline_value, sentinel_value]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values)

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.2f}",
            ha='center',
            va='bottom'
        )

    plt.title(title, fontsize=14, weight="bold")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

# ================================
# GENERATE VISUALS
# ================================

save_bar_chart(
    "Fabrication Rate Comparison (%)",
    BASELINE["fabrication_rate"],
    SENTINEL["fabrication_rate"],
    "Fabrication Rate (%)",
    "fabrication_comparison.png"
)

save_bar_chart(
    "P95 Latency Comparison (ms)",
    BASELINE["p95_latency"],
    SENTINEL["p95_latency"],
    "Latency (ms)",
    "latency_p95_comparison.png"
)

save_bar_chart(
    "Cost per 100 Queries ($)",
    BASELINE["cost_per_100"],
    SENTINEL["cost_per_100"],
    "Cost ($)",
    "cost_comparison.png"
)

print("Visual reports generated successfully.")
