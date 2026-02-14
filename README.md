Sentinel Engine — LLM Governance Layer
=====================================

Sentinel Engine is a production-deployed governance layer that enforces cost control, hallucination prevention, and deterministic routing for large language models.

It operates between applications and LLM providers, ensuring responses are grounded, auditable, and cost-efficient.


Problem
-------

Large language models introduce operational risk in production systems.

Common failure modes include:

• hallucinated responses under incomplete context  
• unbounded inference cost due to uncontrolled routing  
• lack of auditability and execution visibility  
• inability to enforce deterministic safety rules  

Baseline model testing showed:

Fabrication rate: 66.67%

This level of fabrication is unacceptable for production systems.


Solution
--------

Sentinel Engine introduces a deterministic governance layer that enforces:

• confidence-based refusal  
• deterministic model routing  
• cost estimation and tracking  
• audit logging of all requests  
• token and overflow protection  


System Architecture
-------------------

Application  
    ↓  
Sentinel Engine  
    ↓  
Routing + Governance  
    ↓  
LLM Provider  


Governance pipeline:

1. Token estimation
2. Cost estimation
3. Deterministic model routing
4. LLM execution
5. Confidence scoring
6. Refusal enforcement
7. Audit logging


Deployment
----------

Production endpoint:

https://sentinel-engine-amdw.onrender.com/govern

Environment:

Platform: Render  
Runtime: Python 3.14  
Framework: FastAPI  
Database: PostgreSQL  


Measured Results
----------------

Baseline LLM:

Fabrication Rate: 66.67%  
P95 Latency: 1571 ms  


Sentinel Engine:

Fabrication Rate: 0.00%  
P95 Latency: 1462 ms  

Cost per 100 queries:

$0.0303


Routing Distribution:

Cheap Model Usage: 50%  
Premium Model Usage: 50%  

Routing Accuracy: 100%


Key Guarantees
--------------

Sentinel Engine guarantees:

• hallucination prevention via refusal enforcement  
• deterministic routing based on execution policy  
• bounded cost execution  
• full audit logging  
• execution transparency  


Proof Artifacts
---------------

All experimental results are reproducible.

See:

proof/

Contains:

baseline_results.csv  
evaluation_results.csv  
routing_results.csv  

Visual reports:

proof/visualizations/


Example Request
---------------

POST /govern

Input:

{
  "query": "Who created Python?",
  "context": "Python was created by Guido van Rossum.",
  "provider": "openai"
}


Output:

{
  "answer": "Python was created by Guido van Rossum.",
  "refusal": false,
  "confidence_score": 0.78,
  "model_used": "gpt-4o-mini",
  "estimated_cost": 0.000303,
  "latency_ms": 734
}


Core Capabilities
-----------------

Confidence-based refusal  
Deterministic model routing  
Cost estimation and enforcement  
Execution audit logging  
Production deployment  



Use Cases
---------

AI applications requiring safe and auditable inference:

• enterprise copilots  
• financial AI systems  
• healthcare AI systems  
• production LLM APIs  


Project Structure
-----------------

sentinel/
core governance logic

proof/
experimental validation and audit data

visualizations/
impact graphs

reports/
system metrics and summaries



Reproducibility
---------------

To reproduce experiments:

Run:

baseline_evaluate.py  
evaluate.py  
routing_analysis.py  

Results will be generated in proof/



Author
------

Built as a production LLM governance layer demonstrating:

• hallucination risk mitigation  
• cost governance  
• deterministic routing  
• auditable inference systems  
