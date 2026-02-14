Proof Artifacts — Sentinel Engine Validation
===========================================

This directory contains reproducible experimental evidence demonstrating Sentinel Engine's governance capabilities.

All data in this directory was generated from live execution against the production deployment.


Purpose
-------

These artifacts exist to validate three core governance guarantees:

1. Hallucination prevention  
2. Deterministic routing enforcement  
3. Cost and latency governance  


Files Overview
--------------

baseline_results.csv

Contains raw execution results from direct LLM calls without Sentinel governance.

Purpose:
Establish baseline fabrication behavior.

Observed result:

Fabrication rate: 66.67%


evaluation_results.csv

Contains execution results routed through Sentinel Engine.

Purpose:
Measure governance effectiveness.

Observed result:

Fabrication rate: 0.00%


routing_results_*.csv

Contains routing decision records for each request.

Each row includes:

query  
expected_model  
model_used  
latency_ms  

Purpose:
Validate routing correctness and model selection behavior.

Observed result:

Routing accuracy: 100%


visualizations/

Contains generated charts derived from proof data.

These include:

Cost comparison graphs  
Latency distribution graphs  
Routing distribution graphs  


Governance Guarantees Proven
----------------------------

These artifacts demonstrate that Sentinel Engine successfully enforces:

• hallucination prevention  
• deterministic routing  
• cost governance  
• audit logging  


Experimental Method
-------------------

Baseline Phase:

Direct calls to LLM provider without governance layer.

Governance Phase:

Same dataset executed through Sentinel Engine endpoint.

Routing Phase:

Controlled dataset designed to trigger both cheap and premium routing paths.


Deployment Environment
----------------------

Platform: Render  
Runtime: Python 3.14  
Database: PostgreSQL  
API Framework: FastAPI  


Reproducibility
---------------

To regenerate artifacts:

Run:

baseline_evaluate.py

evaluate.py

routing_analysis.py


All output will regenerate in this directory.


Integrity Guarantee
-------------------

All data in this directory is generated from live execution against a deployed governance system.

No synthetic or fabricated data is included.


Conclusion
----------

These artifacts provide verifiable evidence that Sentinel Engine enforces safe, auditable, and cost-efficient LLM execution.
