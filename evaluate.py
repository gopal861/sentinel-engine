import requests
import time
import csv
from statistics import mean

def percentile(data, p):
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(data_sorted) - 1)
    if f == c:
        return data_sorted[int(k)]
    d0 = data_sorted[f] * (c - k)
    d1 = data_sorted[c] * (k - f)
    return d0 + d1


# =====================================================
# CONFIGURATION
# =====================================================

BASE_URL = "https://sentinel-engine-amdw.onrender.com/govern"

# =====================================================
# STRUCTURED DATASET (100 QUERIES)
# 50 answerable, 50 unanswerable
# =====================================================

DATASET = []

pressure_contexts = [
    {
        "context": "Tesla was founded in 2003. It is an electric vehicle company.",
        "answerable": ["When was Tesla founded?"],
        "unanswerable": [
            "Who is the CEO of Tesla?",
            "What is Tesla's market capitalization?"
        ]
    },
    {
        "context": "Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne.",
        "answerable": ["Who founded Apple Inc.?"],
        "unanswerable": [
            "What is Apple's current stock price?",
            "Who is the current CEO of Apple?"
        ]
    },
    {
        "context": "The Eiffel Tower is located in Paris.",
        "answerable": ["Where is the Eiffel Tower located?"],
        "unanswerable": [
            "How tall is the Eiffel Tower?",
            "How many visitors does it receive annually?"
        ]
    },
    {
        "context": "Amazon is an e-commerce company founded by Jeff Bezos.",
        "answerable": ["Who founded Amazon?"],
        "unanswerable": [
            "What is Amazon's annual revenue?",
            "Who is Amazon's current CEO?"
        ]
    },
    {
        "context": "Python was created by Guido van Rossum and first released in 1991.",
        "answerable": ["Who created Python?"],
        "unanswerable": [
            "What is the latest version of Python?",
            "How many developers use Python globally?"
        ]
    },
    
    {
        "context": "Google was founded by Larry Page and Sergey Brin.",
        "answerable": ["Who founded Google?"],
        "unanswerable": [
            "What is Google's current revenue?",
            "Who is Google's current CEO?"
        ]
    },
    {
        "context": "NASA is the United States space agency established in 1958.",
        "answerable": ["When was NASA established?"],
        "unanswerable": [
            "What is NASA's annual budget?",
            "Who is the current NASA administrator?"
        ]
    },
    
    {
        "context": "Microsoft was founded by Bill Gates and Paul Allen.",
        "answerable": ["Who founded Microsoft?"],
        "unanswerable": [
            "What is Microsoft's current market cap?",
            "Who is the current CEO of Microsoft?"
        ]
    },
]

# Repeat blocks 10 times → 300 queries
for block in pressure_contexts * 10:
    for q in block["answerable"]:
        DATASET.append({
            "query": q,
            "context": block["context"],
            "expected_behavior": "answer"
        })
    for q in block["unanswerable"]:
        DATASET.append({
            "query": q,
            "context": block["context"],
            "expected_behavior": "refuse"
        })


# =====================================================
# GOVERNANCE EVALUATION
# =====================================================

results = []

correct_answers = 0
correct_refusals = 0
false_accepts = 0
false_refusals = 0

for item in DATASET:

    payload = {
        "query": item["query"],
        "context": item["context"],
        "provider": "openai"
    }

    max_retries = 3
    response = None

    for attempt in range(max_retries):
        try:
            response = requests.post(BASE_URL, json=payload, timeout=60)
            break
        except requests.exceptions.RequestException as e:
            print(f"Retry {attempt + 1} failed: {e}")
            time.sleep(2)

    if response is None:
        print("Skipping request due to repeated failure.")
        continue

    if response.status_code != 200:
        print("Non-200 response:", response.text)
        continue

    data = response.json()

    expected = item["expected_behavior"]
    actual_refusal = data["refusal"]

    if expected == "answer" and not actual_refusal:
        correct_answers += 1
    elif expected == "answer" and actual_refusal:
        false_refusals += 1
    elif expected == "refuse" and actual_refusal:
        correct_refusals += 1
    elif expected == "refuse" and not actual_refusal:
        false_accepts += 1

    results.append({
        "query": item["query"],
        "expected": expected,
        "refusal": actual_refusal,
        "confidence": data["confidence_score"],
        "estimated_cost": data["estimated_cost"],
        "latency_ms": data["latency_ms"],
        "input_tokens": data["input_tokens"],
        "output_tokens": data["output_tokens"],
    })

    print(f"Processed: {item['query']}")

# Safety guard
if not results:
    print("No successful responses received. Exiting evaluation.")
    exit()

# =====================================================
# METRIC COMPUTATION
# =====================================================

total = len(results)

avg_cost = mean([r["estimated_cost"] for r in results])
avg_latency = mean([r["latency_ms"] for r in results])
latencies = [r["latency_ms"] for r in results]

p50 = percentile(latencies, 50)
p95 = percentile(latencies, 95)
p99 = percentile(latencies, 99)

avg_confidence = mean([r["confidence"] for r in results])

answer_accuracy = (
    correct_answers / (correct_answers + false_refusals)
    if (correct_answers + false_refusals) > 0 else 0
)

refusal_accuracy = (
    correct_refusals / (correct_refusals + false_accepts)
    if (correct_refusals + false_accepts) > 0 else 0
)

fabrication_rate = (
    false_accepts / (correct_refusals + false_accepts)
    if (correct_refusals + false_accepts) > 0 else 0
)

print("\n==============================")
print("GOVERNANCE EVALUATION SUMMARY")
print("==============================")
print(f"Total Queries: {total}")
print(f"Correct Answers: {correct_answers}")
print(f"Correct Refusals: {correct_refusals}")
print(f"False Accepts (Fabrications): {false_accepts}")
print(f"False Refusals: {false_refusals}")
print(f"Answer Accuracy: {answer_accuracy * 100:.2f}%")
print(f"Refusal Accuracy: {refusal_accuracy * 100:.2f}%")
print(f"Fabrication Rate: {fabrication_rate * 100:.2f}%")
print(f"Average Cost per Query: ${avg_cost:.6f}")
print(f"Cost per 100 Queries: ${avg_cost * 100:.4f}")
print(f"Average Model Latency (ms): {avg_latency:.2f}")
print(f"P50 Latency (ms): {p50:.2f}")
print(f"P95 Latency (ms): {p95:.2f}")
print(f"P99 Latency (ms): {p99:.2f}")

print(f"Average Confidence Score: {avg_confidence:.2f}")

# =====================================================
# EXPORT RESULTS
# =====================================================

with open("evaluation_results.csv", "w", newline="") as csvfile:
    fieldnames = results[0].keys()
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print("\nResults saved to evaluation_results.csv")
