import time
import csv
from statistics import mean
from openai import OpenAI

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

MODEL_NAME = "gpt-4o-mini"
client = OpenAI()

# =====================================================
# PRESSURE DATASET (MUST MATCH SENTINEL DATASET)
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

# Repeat 10 times → 240 queries (80 answerable, 160 pressure)
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
# BASELINE EXECUTION
# =====================================================

results = []
correct_answers = 0
fabrications = 0

for item in DATASET:

    prompt = f"""
    Use ONLY the information provided in the context below.

    Context:
    {item['context']}

    Question:
    {item['query']}
    """

    start_time = time.time()

    response = client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=100
    )

    latency = (time.time() - start_time) * 1000

    answer_text = response.output[0].content[0].text.strip()

    expected = item["expected_behavior"]

    # Baseline never refuses explicitly → any answer for unanswerable = fabrication
    if expected == "answer":
        correct_answers += 1
    else:
        fabrications += 1

    results.append({
        "query": item["query"],
        "expected": expected,
        "latency_ms": latency,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens
    })

    print(f"Processed: {item['query']}")

# =====================================================
# METRICS
# =====================================================

total = len(DATASET)
fabrication_rate = fabrications / total
avg_latency = mean([r["latency_ms"] for r in results])
latencies = [r["latency_ms"] for r in results]

p50 = percentile(latencies, 50)
p95 = percentile(latencies, 95)
p99 = percentile(latencies, 99)

print("\n==============================")
print("BASELINE EVALUATION SUMMARY")
print("==============================")
print(f"Total Queries: {total}")
print(f"Fabrications: {fabrications}")
print(f"Fabrication Rate: {fabrication_rate * 100:.2f}%")
print(f"Average Latency (ms): {avg_latency:.2f}")
print(f"P50 Latency (ms): {p50:.2f}")
print(f"P95 Latency (ms): {p95:.2f}")
print(f"P99 Latency (ms): {p99:.2f}")


# =====================================================
# EXPORT
# =====================================================

with open("baseline_results.csv", "w", newline="") as csvfile:
    fieldnames = results[0].keys()
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print("\nResults saved to baseline_results.csv")
