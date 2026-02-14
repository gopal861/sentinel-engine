import requests
import time
import csv
import os
from collections import Counter
from statistics import mean

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://sentinel-engine-amdw.onrender.com/govern"

OUTPUT_DIR = "proof"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "routing_results.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================
# LONG CONTEXT GENERATOR
# Forces routing to premium model
# ============================================

LONG_CONTEXT = """
Large Language Models (LLMs) are neural networks based on the transformer architecture.
They process tokens using attention mechanisms. Attention allows the model to weigh the importance
of different tokens relative to each other. Transformers consist of encoder and decoder stacks,
multi-head attention layers, feed-forward networks, layer normalization, and residual connections.

Distributed systems rely on consensus algorithms like Raft and Paxos to maintain consistency.
These systems must tolerate node failures, network partitions, and asynchronous communication.

Tokenization converts text into discrete symbols that models can process. Token length directly impacts
inference cost and latency.

Cost governance is critical in production AI systems because inference costs scale with usage volume.
Routing strategies allow systems to select cheaper models for simple tasks and premium models for complex tasks.
""" * 40


SHORT_CONTEXT = "Python is a programming language created by Guido van Rossum."


# ============================================
# BUILD TEST DATASET
# 50 cheap route + 50 premium route
# ============================================

DATASET = []

# Cheap expected routing
for _ in range(50):

    DATASET.append({
        "query": "Who created Python?",
        "context": SHORT_CONTEXT,
        "expected_model": "cheap"
    })


# Premium expected routing
for _ in range(50):

    DATASET.append({
        "query": "Explain transformer architecture and distributed consensus in detail.",
        "context": LONG_CONTEXT,
        "expected_model": "premium"
    })


# ============================================
# EXECUTION
# ============================================

model_counter = Counter()

latencies = []

correct_routes = 0

incorrect_routes = 0

csv_rows = []

print("\nStarting routing governance analysis...\n")

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


    # ============================================
    # ROUTING VALIDATION
    # ============================================

    if item["expected_model"] == "cheap" and model_used == "gpt-4o-mini":

        correct_routes += 1

    elif item["expected_model"] == "premium" and model_used == "gpt-4o":

        correct_routes += 1

    else:

        incorrect_routes += 1


    # ============================================
    # STORE CSV RECORD
    # ============================================

    csv_rows.append({

        "query": item["query"],

        "expected_model": item["expected_model"],

        "model_used": model_used,

        "latency_ms": latency

    })


    print(f"{i+1}/100 → Model used: {model_used}")


# ============================================
# SAVE CSV PROOF FILE (IMMUTABLE TIMESTAMP FILE)
# ============================================

import os
from datetime import datetime

# Ensure proof directory exists
os.makedirs("proof", exist_ok=True)

# Generate timestamp filename
timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

OUTPUT_FILE = f"proof/routing_results_{timestamp}.csv"

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:

    fieldnames = [
        "query",
        "expected_model",
        "model_used",
        "latency_ms"
    ]

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    writer.writerows(csv_rows)


# ============================================
# SUMMARY
# ============================================

total = sum(model_counter.values())

print("\n================================")

print("ROUTING GOVERNANCE ANALYSIS")

print("================================\n")

for model, count in model_counter.items():

    percentage = (count / total) * 100

    print(f"Model: {model}")

    print(f"Requests: {count}")

    print(f"Usage: {percentage:.2f}%\n")

print(f"Total Requests: {total}")

if latencies:

    print(f"Average Latency: {mean(latencies):.2f} ms")

    print(f"Min Latency: {min(latencies):.2f} ms")

    print(f"Max Latency: {max(latencies):.2f} ms")

routing_accuracy = (correct_routes / total) * 100 if total else 0

print("\n================================")

print("ROUTING ACCURACY")

print("================================")

print(f"Correct Routes: {correct_routes}")

print(f"Incorrect Routes: {incorrect_routes}")

print(f"Routing Accuracy: {routing_accuracy:.2f}%")

print(f"\nCSV proof saved at: {OUTPUT_FILE}")

print("\nRouting governance validation complete.")
