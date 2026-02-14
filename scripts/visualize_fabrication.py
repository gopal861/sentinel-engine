import pandas as pd
import matplotlib.pyplot as plt
import os

# ============================================
# CONFIG
# ============================================

VISUAL_DIR = "visuals"
os.makedirs(VISUAL_DIR, exist_ok=True)

# ============================================
# LOAD BASELINE DATA
# ============================================

baseline = pd.read_csv("baseline_results.csv")

baseline_total = len(baseline)

baseline_fabrications = len(
    baseline[baseline["expected"] == "refuse"]
)

baseline_rate = baseline_fabrications / baseline_total * 100


# ============================================
# LOAD SENTINEL DATA
# ============================================

sentinel = pd.read_csv("evaluation_results.csv")

sentinel_total = len(sentinel)

sentinel_fabrications = len(
    sentinel[
        (sentinel["expected"] == "refuse") &
        (sentinel["refusal"] == False)
    ]
)

sentinel_rate = sentinel_fabrications / sentinel_total * 100


# ============================================
# BUILD GRAPH
# ============================================

labels = ["Baseline LLM", "Sentinel Governed"]

values = [baseline_rate, sentinel_rate]

plt.figure(figsize=(8,5))

bars = plt.bar(labels, values)

plt.title("Hallucination (Fabrication) Rate Comparison")

plt.ylabel("Fabrication Rate (%)")

for bar in bars:

    height = bar.get_height()

    plt.text(
        bar.get_x() + bar.get_width()/2,
        height,
        f"{height:.1f}%",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

output_file = f"{VISUAL_DIR}/fabrication_comparison.png"

plt.savefig(output_file, dpi=300)

plt.close()

print(f"Graph saved at: {output_file}")
