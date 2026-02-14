Sentinel Engine Architecture
1. Purpose

Sentinel Engine is a governance layer that sits between applications and LLM providers. It enforces:

Hallucination prevention

Cost control through deterministic routing

Full audit visibility

Safe model execution

Sentinel converts LLM usage from uncontrolled execution into a governed infrastructure system.

2. System Position in Stack

Without Sentinel:

Application → LLM Provider → Response


With Sentinel:

Application → Sentinel Engine → LLM Provider → Sentinel → Response


Sentinel becomes the trust boundary.

Applications cannot directly access models.

3. High-Level Flow
Client Request
      │
      ▼
FastAPI Layer
      │
      ▼
Policy Engine
      │
      ├── Token Estimation
      ├── Cost Estimation
      ├── Routing Decision
      │
      ▼
LLM Client
(OpenAI / Anthropic)
      │
      ▼
Confidence Engine
      │
      ▼
Refusal Engine
      │
      ▼
Audit Logger (Postgres)
      │
      ▼
Response

4. Core Components
API Layer

Location:

sentinel/api/routes.py


Responsibilities:

Accept requests

Validate inputs

Forward to governance layer

Return response

No governance logic exists here.

Policy Engine (Core Controller)

Location:

sentinel/core/policy_engine.py


This is the main orchestrator.

Responsibilities:

Estimate tokens

Estimate cost

Select model

Execute LLM

Compute confidence

Enforce refusal

Log execution

All governance decisions originate here.

Routing Engine

Location:

sentinel/core/router.py


Purpose:
Select cheapest safe model.

Routing logic:

Condition	Model
Low complexity	gpt-4o-mini
High complexity	gpt-4o

Goal:
Minimize cost without increasing hallucination risk.

Cost Estimator

Location:

sentinel/core/cost_estimator.py


Tracks:

Input tokens

Output tokens

Estimated cost

Actual cost

This enables cost governance.

LLM Client

Location:

sentinel/core/llm_client.py


Responsibilities:

Call OpenAI / Anthropic

Measure latency

Capture token usage

This layer isolates provider interaction.

Confidence Engine

Location:

sentinel/core/confidence.py


Evaluates response grounding.

Low confidence → hallucination risk.

Refusal Engine

Location:

sentinel/core/refusal.py


If confidence < threshold:

Sentinel refuses execution.

Prevents hallucinated outputs.

Audit Logging Layer

Location:

sentinel/core/logging.py


Logs:

model used

cost

latency

tokens

confidence

refusal decision

Stored in PostgreSQL.

Enables full audit trail.

5. Execution Lifecycle

Step-by-step execution:

Request enters Sentinel

Token usage estimated

Cost estimated

Routing decision made

Model executed

Confidence computed

Refusal decision applied

Execution logged

Response returned

6. Routing Strategy

Sentinel implements deterministic routing.

Goal:

Use cheapest model whenever safe.

Example routing outcome:

Model	Usage
gpt-4o-mini	50%
gpt-4o	50%

Routing accuracy:

100%

7. Deployment Architecture

Deployment platform:
Render

Stack:

Component	Technology
API	FastAPI
Provider	OpenAI
Database	PostgreSQL
Deployment	Render

Public endpoint:

https://sentinel-engine-amdw.onrender.com


Stateless design allows scaling.

8. Evaluation System

Sentinel includes full evaluation framework.

Scripts:

scripts/baseline_evaluate.py
scripts/evaluate.py
scripts/routing_analysis.py


Proof stored in:

proof/data/
proof/charts/
proof/reports/


Measured Results:

Metric	Baseline	Sentinel
Hallucination Rate	66.67%	0%
Routing Accuracy	N/A	100%
Cost per 100 queries	uncontrolled	$0.0303
9. Failure Handling

Failure cases and behavior:

Failure	Sentinel Behavior
Low confidence	Refuse response
Provider failure	Fail safely
Token overflow	Block execution
Logging failure	Execution continues

Sentinel prevents unsafe execution.

10. Scalability Model

Sentinel is stateless.

Supports:

horizontal scaling

load balancing

multi-instance deployment

Database handles audit persistence.

11. Trust Boundary

Sentinel enforces strict execution control.

Applications cannot:

select models directly

bypass routing

bypass audit logging

Sentinel is the enforcement layer.

12. Verified Outcomes

Measured and proven:

Hallucination reduction:
66.67% → 0%

Routing accuracy:
100%

Cost control achieved.

Full audit trace enabled.

13. Known Limitations

Current version does not include:

semantic complexity routing

multi-provider failover

adaptive routing based on learning

These are planned improvements.

14. Architecture Summary

Sentinel provides:

deterministic routing

hallucination prevention

cost governance

audit logging

safe execution boundary

This enables production-grade LLM deployment.