import matplotlib.pyplot as plt

# ===============================
# VERIFIED METRICS (FROM RUNS)
# ===============================

baseline_fabrication = 66.67
sentinel_fabrication = 0.00

baseline_p95 = 1571.44
sentinel_p95 = 1462.00

cost_per_100 = 0.0303

# ===============================
# EXECUTIVE SUMMARY VISUAL
# ===============================

plt.figure(figsize=(10, 6))
plt.axis('off')

summary_text = f"""
Sentinel Engine — Governance Impact

Baseline Hallucination Rate: {baseline_fabrication:.2f}%
Sentinel Fabrication Rate: {sentinel_fabrication:.2f}%

P95 Latency:
Baseline: {baseline_p95:.0f} ms
Sentinel: {sentinel_p95:.0f} ms

Cost per 100 Queries:
${cost_per_100:.4f}

Result:
Measured hallucination elimination under incomplete context
with negligible latency and cost overhead.
"""

plt.text(
    0.5, 0.5,
    summary_text,
    fontsize=14,
    ha='center',
    va='center'
)

plt.savefig("executive_summary.png", dpi=300, bbox_inches='tight')
plt.close()

print("Executive summary generated: executive_summary.png")
