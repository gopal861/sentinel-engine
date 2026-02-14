import requests
import time
from collections import Counter

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://sentinel-engine-amdw.onrender.com/govern"

# Test dataset designed to trigger both routing paths
DATASET = [
    {
        "query": "What is Python?",
        "context": "Python is a programming language created by Guido van Rossum."
    },
    {
        "query": "Explain the architecture of distributed consensus systems in detail.",
        "context": "Distributed consensus ensures agreement between nodes in distributed systems."
    },
    {
        "query": "Who founded Microsoft?",
        "context": "Microsoft was founded by Bill Gates and Paul Allen."
    },
    {
        "query": "Explain transformer attention mechanism mathematically.",
        "context": "Transformers use attention mechanisms to weigh input tokens."
    }
] * 25  # 100 total requests


# ============================================
# ROUTING ANALYSIS
# ============================================

model_counter = Counter()
latencies = []

print("\nStarting routing analysis...\n")

for i, item in enumerate(DATASET):

    payload = {
        "query": item["query"],
        "context": item["context"],
        "provider": "openai"
    }

    start = time.time()

    try:
        response = requests.post(BASE_URL, json=payload, timeout=60)
    except Exception as e:
        print(f"Request failed: {e}")
        continue

    if response.status_code != 200:
        print(f"Request failed with status: {response.status_code}")
        continue

    latency = (time.time() - start) * 1000

    data = response.json()

    model_used = data["model_used"]

    model_counter[model_used] += 1
    latencies.append(latency)

    print(f"{i+1}/100 → Model used: {model_used}")

# ============================================
# RESULTS
# ============================================

total = sum(model_counter.values())

print("\n================================")
print("ROUTING DISTRIBUTION ANALYSIS")
print("================================\n")

for model, count in model_counter.items():

    percentage = (count / total) * 100

    print(f"Model: {model}")
    print(f"Requests: {count}")
    print(f"Usage: {percentage:.2f}%\n")

print(f"Total Requests: {total}")

if latencies:
    avg_latency = sum(latencies) / len(latencies)
    print(f"Average Network Latency: {avg_latency:.2f} ms")

print("\nRouting analysis complete.")
