import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ============================================
# CONFIGURATION
# ============================================

PROOF_DIR = "proof"
VISUAL_DIR = "visuals"

CHEAP_MODEL = "gpt-4o-mini"
PREMIUM_MODEL = "gpt-4o"

CHEAP_COST_PER_1K = 0.00015
PREMIUM_COST_PER_1K = 0.005


# ============================================
# PREPARE DIRECTORIES
# ============================================

os.makedirs(VISUAL_DIR, exist_ok=True)

# Find latest routing CSV
csv_files = glob.glob(f"{PROOF_DIR}/routing_results_*.csv")

if not csv_files:
    raise RuntimeError("No routing proof CSV found")

latest_csv = max(csv_files, key=os.path.getctime)

print(f"Using proof file: {latest_csv}")


# ============================================
# LOAD DATA
# ============================================

df = pd.read_csv(latest_csv)


# ============================================
# ROUTING DISTRIBUTION
# ============================================

model_counts = df["model_used"].value_counts()

plt.figure(figsize=(8, 5))

bars = plt.bar(
    model_counts.index,
    model_counts.values
)

plt.title("Routing Distribution")
plt.ylabel("Number of Requests")
plt.xlabel("Model")

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{height}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(f"{VISUAL_DIR}/routing_distribution.png", dpi=300)

plt.close()


# ============================================
# LATENCY PERCENTILES
# ============================================

latencies = df["latency_ms"]

percentiles = [
    np.percentile(latencies, 50),
    np.percentile(latencies, 95),
    np.percentile(latencies, 99)
]

labels = ["P50", "P95", "P99"]

plt.figure(figsize=(8, 5))

bars = plt.bar(labels, percentiles)

plt.title("Latency Percentiles")
plt.ylabel("Latency (ms)")

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{int(height)} ms",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(f"{VISUAL_DIR}/routing_latency_percentiles.png", dpi=300)

plt.close()


# ============================================
# COST COMPARISON
# ============================================

cheap_count = model_counts.get(CHEAP_MODEL, 0)
premium_count = model_counts.get(PREMIUM_MODEL, 0)

baseline_cost = (cheap_count + premium_count) * PREMIUM_COST_PER_1K
sentinel_cost = (
    cheap_count * CHEAP_COST_PER_1K +
    premium_count * PREMIUM_COST_PER_1K
)

labels = ["Baseline (No Routing)", "Sentinel Routing"]
costs = [baseline_cost, sentinel_cost]

plt.figure(figsize=(8, 5))

bars = plt.bar(labels, costs)

plt.title("Cost Comparison")
plt.ylabel("Estimated Cost")

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"${height:.4f}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(f"{VISUAL_DIR}/routing_cost_comparison.png", dpi=300)

plt.close()


# ============================================
# COMPLETE
# ============================================

print("\nVisual proofs generated:")

print(f"{VISUAL_DIR}/routing_distribution.png")

print(f"{VISUAL_DIR}/routing_latency_percentiles.png")

print(f"{VISUAL_DIR}/routing_cost_comparison.png")
