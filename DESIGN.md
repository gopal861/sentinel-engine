# Sentinel Engine — System Design Document

**Author:** Gopal Khandare
**Date:** February 2026  
**Status:** Production  
**Version:** 1.0

---

## 1. Design Goals

The system was designed with four primary objectives:

### 1.1 Eliminate Hallucination Exposure

When LLMs operate without constraints, they generate confident responses even when context is insufficient. The system aims to prevent these responses from reaching users through post-call validation.

**Goal:** Reduce out-of-context answer exposure to zero (or near-zero).

**Mechanism:** Confidence-based refusal gate. If the system cannot ground an answer in provided context, refuse execution rather than expose the response.

**Constraint:** Validation happens after LLM call, so cost is already incurred. This is accepted as a trade-off for safety.

### 1.2 Enforce Deterministic Cost Control

Uncontrolled LLM usage leads to unbounded inference costs. The system must enforce cost governance through routing decisions that are reproducible and auditable.

**Goal:** Reduce per-query cost by 40-50% on simple workloads without increasing hallucination risk.

**Mechanism:** Token-count-based routing. Queries below complexity threshold route to cheaper models; complex queries route to capable models.

**Constraint:** Routing must be deterministic (same input always routes the same way) to enable cost prediction.

### 1.3 Provide Complete Auditability

Standard model execution leaves no trail. Every request, response, confidence score, routing decision, and cost must be logged for compliance and debugging.

**Goal:** Every request is auditable and reproducible.

**Mechanism:** Fail-closed PostgreSQL logging. If logging fails, execution fails (doesn't silently skip).

**Constraint:** Logging cannot block execution path. Must be fast enough to not introduce latency.

### 1.4 Maintain Operational Transparency

The system must be debuggable. Operations teams need visibility into why decisions were made, what happened, and why it failed.

**Goal:** Any issue can be diagnosed from logs.

**Mechanism:** Log 11 metrics per request: timestamp, query_hash, provider, model, cost (estimated/actual), confidence, refusal, latency, tokens (input/output).

**Constraint:** Logs must not expose user queries (use SHA256 hash instead of plaintext).

---

## 2. Design Constraints

The system operates under the following constraints:

### 2.1 Cost Constraint

**Problem:** LLM API costs scale linearly with usage. A 10x increase in queries = 10x increase in cost.

**Constraint:** System must reduce per-query cost without sacrificing safety.

**How it's solved:**
- Route 50% of queries to gpt-4o-mini ($0.00000015 per input token)
- Route 50% of queries to gpt-4o ($0.000005 per input token)
- Result: ~50% cost reduction on routed queries

**Trade-off:** Routing decision relies on token count, not actual query complexity. Simple heuristic that's fast to compute.

### 2.2 Latency Constraint

**Problem:** Every governance layer adds latency. If too slow, users see degraded experience.

**Constraint:** Governance overhead must be < 50ms (negligible vs typical LLM 1000-2000ms latency).

**How it's solved:**
- Token estimation: ~2ms (cached encoders)
- Confidence scoring: ~5ms (simple math)
- Routing decision: <1ms (single comparison)
- Refusal logic: <1ms (threshold check)
- Audit logging: ~10ms (async to PostgreSQL)
- **Total: ~20ms overhead**

**Actual result:** P95 latency improved 7% (1571ms → 1462ms) because routing benefit exceeded overhead.

### 2.3 Reliability Constraint

**Problem:** If governance layer fails, must fail safely (never expose hallucinated response).

**Constraint:** All error paths must either refuse or fail-closed.

**How it's solved:**
- Token overflow check blocks execution before LLM call
- Confidence check happens on all responses (no bypass paths)
- Logging failure causes system error, doesn't skip silently
- No graceful degradation: either governed or failed

### 2.4 Dependency Constraint

**Problem:** System depends on external LLM providers (OpenAI, Anthropic), PostgreSQL, and external APIs.

**Constraint:** No hard dependency on any single external service except the LLM provider.

**How it's solved:**
- PostgreSQL logging failure returns error (acceptable, audit is critical)
- LLM provider failure returns error (expected, no fallback)
- Retry logic: minimal (single attempt per request)
- No circuit breaker or failover (out of scope for this version)

---

## 3. Architectural Patterns Used

### 3.1 Layered Architecture

The system uses strict layering:

```
Layer 1: API Layer (routes.py)
         ├─ HTTP request handling
         ├─ Input validation
         ├─ Response serialization
         └─ No business logic

Layer 2: Policy Engine (policy_engine.py)
         ├─ Orchestration logic
         ├─ Decision making
         ├─ Governance enforcement
         └─ Calls all other components

Layer 3: Component Layer (routing, confidence, refusal, etc.)
         ├─ Isolated responsibilities
         ├─ No cross-component calls
         └─ Composable

Layer 4: Infrastructure Layer (logger, llm_client)
         ├─ External service interaction
         ├─ Abstraction boundaries
         └─ Implementation details hidden
```

**Why layering?** Allows changing lower layers without affecting upper layers. If cost calculation changes, only cost_estimator.py changes.

### 3.2 Command-Query Responsibility Segregation (Implicit)

The system separates what it asks (query) from what it commands (refusal):

**Query:** "What is your confidence in this answer?"  
**Command:** "If confidence < 0.55, refuse this response."

The confidence engine is pure (no side effects). The refusal engine is deterministic (same confidence always produces same result).

**Why?** Makes testing easy. Can test confidence scoring independently of refusal logic.

### 3.3 Fail-Closed Pattern

Every error path either:
1. Blocks execution (token overflow)
2. Refuses answer (low confidence)
3. Returns error (provider failure)

**Never silently degrades or skips governance.**

Example from logger.py:
```python
except Exception:
    raise RuntimeError("logging_failure")
    # Don't continue if logging fails
```

**Why?** Audit integrity is non-negotiable. If logging fails, system must fail rather than execute ungoverned.

### 3.4 Template Method Pattern (Implicit)

The policy_engine.py defines a 10-step template:
1. Estimate tokens
2. Route model
3. Estimate output tokens
4. Check overflow
5. Estimate cost
6. Execute LLM
7. Score confidence
8. Refusal decision
9. Calculate actual cost
10. Log execution

Each step calls a specific component (router, confidence, refusal, etc.). The template is orchestration; components are implementation details.

**Why?** Makes the governance flow visible in one place. Can see entire governance pipeline in policy_engine.py without reading other files.

### 3.5 Strategy Pattern (Routing)

Two routing strategies:
- **Cheap strategy:** Use gpt-4o-mini (tokens < 500)
- **Premium strategy:** Use gpt-4o (tokens >= 500)

The routing decision is a strategy selection. Could be extended to:
- Token-based (current)
- Time-based ("rush" queries need premium)
- User-based (VIP users get premium)
- Cost-based (budget-aware routing)

**Why?** The system is extensible. Routing logic is isolated in router.py. Changing routing strategy doesn't affect confidence or refusal.

---

## 4. Abstraction Layers

### 4.1 Cost Abstraction

**What's hidden:** How much queries actually cost.

**What's exposed:** `estimate_cost(input_tokens, output_tokens, model) → float`

**Why?** Cost is an implementation detail. System cares about cost, not token prices. If OpenAI raises prices, only PRICING_TABLE changes.

### 4.2 Token Abstraction

**What's hidden:** How text is tokenized (tiktoken for OpenAI, heuristic for Anthropic).

**What's exposed:** `estimate_input_tokens(query, context, provider) → int`

**Why?** Different providers tokenize differently. System doesn't care about tokenization method, only the token count.

### 4.3 Provider Abstraction

**What's hidden:** OpenAI and Anthropic API details.

**What's exposed:** `call_llm(provider, model, query, context) → (answer, input_tokens, output_tokens, latency_ms)`

**Why?** System can support multiple providers without changing governance logic. If Anthropic changes their API, only llm_client.py changes.

### 4.4 Confidence Abstraction

**What's hidden:** How confidence is calculated (lexical overlap, context utilization, length sanity).

**What's exposed:** `compute_confidence(answer, context) → float (0.0 to 1.0)`

**Why?** System uses confidence score, not the calculation method. If we switch to semantic similarity, refusal logic doesn't change.

### 4.5 Audit Abstraction

**What's hidden:** PostgreSQL schema, connection pooling, SQL details.

**What's exposed:** `log_request(record: Dict) → None`

**Why?** System doesn't care where logs go. If we switch to BigQuery or Datadog, only logger.py changes.

---

## 5. Orchestration Design

### 5.1 Sequential Pipeline

The policy_engine.py executes a strict sequence:

```
Token Est. → Routing → Output Est. → Overflow Check → Cost Est. → LLM Call → Confidence → Refusal → Cost Calc. → Logging → Return
     ↓         ↓           ↓            ↓               ↓           ↓         ↓        ↓        ↓        ↓
  Tokens    Model      Output      Block or      Budget      Answer   Score   Refuse?  Actual  Record  Response
                       Tokens      Continue      Check       Tokens             (0-1)    Cost
```

**Why sequential?** Each step depends on output of previous step. Token count determines routing. Routing determines cost estimate. Confidence depends on LLM answer. No parallelization possible.

### 5.2 No Cross-Component Dependencies

Components do not call each other directly. All interaction goes through policy_engine.py:

**Not allowed:**
```python
# DON'T DO THIS:
confidence_score = compute_confidence(answer, context)
if confidence_score < THRESHOLD:
    should_refuse = should_refuse(...)
```

**Allowed:**
```python
# DO THIS:
confidence_score = compute_confidence(answer, context)
should_refuse = should_refuse(confidence_score, context)
# Policy engine coordinates
```

**Why?** Decoupling. If confidence calculation changes, only policy_engine.py needs to coordinate. Components don't know about each other.

### 5.3 Explicit State Transitions

Each step produces clear output:

**Step 1 → Output:** `input_tokens: int`  
**Step 2 → Output:** `model_used: str`  
**Step 3 → Output:** `output_tokens_est: int`  
**Step 4 → Output:** `None (block or continue)`  
**Step 5 → Output:** `estimated_cost: float`  
**Step 6 → Output:** `(answer, actual_input_tokens, actual_output_tokens, latency_ms)`  
**Step 7 → Output:** `confidence_score: float`  
**Step 8 → Output:** `refusal_flag: bool`  
**Step 9 → Output:** `actual_cost: float`  
**Step 10 → Output:** `None`  
**Step 11 → Output:** `GovernResponse`

**Why?** Each step has clear inputs/outputs. Easy to test, debug, and reason about.

---

## 6. Isolation Boundaries

### 6.1 API Boundary

**Boundary:** Between HTTP and governance logic

**API Layer (routes.py):**
- Accepts: JSON request
- Validates: Input schema
- Returns: JSON response
- Raises: HTTPException for errors

**Policy Engine Layer:**
- Accepts: Validated query, context, provider
- Returns: Governance result (dict)
- Raises: ValueError for logic errors

**Why isolation?** API is framework-specific (FastAPI). Governance is framework-agnostic. Can move governance to Flask, Django, or async handler without changing business logic.

### 6.2 Provider Boundary

**Boundary:** Between governance and LLM providers

**System side:**
- Sends: query, context, max_tokens
- Receives: answer, token_counts, latency
- Handles: timeouts, rate limits, errors

**Provider side:**
- OpenAI API
- Anthropic API

**Why isolation?** Providers are external. If OpenAI's API changes, only llm_client.py changes.

### 6.3 Database Boundary

**Boundary:** Between governance and PostgreSQL

**System side:**
- Sends: log record (dict)
- Receives: None (async)
- Expects: Success or RuntimeError

**Database side:**
- PostgreSQL table: sentinel_logs
- 12 columns: timestamp, query_hash, provider, model, costs, confidence, refusal, latency, tokens

**Why isolation?** Database is implementation detail. Could switch to MongoDB, BigQuery, or Datadog without changing governance logic.

### 6.4 Configuration Boundary

**Boundary:** Between code and config (config.py)

**Code side:**
- References: CONFIDENCE_THRESHOLD, MODEL_ROUTING_THRESHOLDS, PRICING_TABLE
- Doesn't hardcode: values

**Config side:**
- Defines: All thresholds, prices, model selection

**Why isolation?** Can tune thresholds without recompiling. Confidence threshold (0.55) is config, not code. Routing threshold (500 tokens) is config, not code.

---

## 7. Safety Mechanisms

### 7.1 Confidence Threshold

**Mechanism:** If confidence < 0.55, refuse answer

**Safety net:** Prevents low-confidence responses from reaching users

**Weakness:** Lexical-based only. Misses semantic errors.

**Tuning:** Currently static (0.55). Could be dynamic per use-case, but that's not implemented.

### 7.2 Token Overflow Check

**Mechanism:** If (input_tokens + output_tokens) > model_limit, block

**Safety net:** Prevents crashes from tokens exceeding model limits

**Current behavior:** Raises ValueError("token_overflow"). System fails.

**Better behavior (not implemented):** Reduce output_tokens or chunk query. Currently accepted as acceptable failure mode.

### 7.3 Grounding Prompt

**Mechanism:** "Use ONLY provided context. Do not fabricate."

**Safety net:** First line of defense. LLM sees explicit instructions.

**Weakness:** LLMs can ignore instructions. This is why post-call validation is needed.

### 7.4 Fail-Closed Logging

**Mechanism:** If logging fails, raise RuntimeError("logging_failure")

**Safety net:** Audit trail is guaranteed. Never silently skip logging.

**Weakness:** Makes system less resilient (logging failure = execution failure). Trade-off is intentional.

### 7.5 Query Hashing

**Mechanism:** Store SHA256(query) instead of plaintext

**Safety net:** User privacy. Queries aren't stored in plaintext in logs.

**Note:** Hash is one-way. Cannot recover original query from hash.

---

## 8. Observability Design

### 8.1 What Gets Logged

Per request:
```
timestamp               - When request happened
query_hash            - SHA256 of query (privacy-preserving)
provider              - "openai" or "anthropic"
model_used            - "gpt-4o-mini", "gpt-4o", etc.
estimated_cost        - Cost estimate before LLM call
actual_cost           - Cost after API response
confidence_score      - Grounding confidence (0.0 - 1.0)
refusal_flag          - Was response refused? (bool)
latency_ms            - End-to-end latency (ms)
input_tokens          - Actual tokens from API
output_tokens         - Actual tokens from API
```

### 8.2 Why These Metrics

**timestamp:** Enables time-series analysis. Can track trends over time.

**query_hash:** Enables query deduplication analysis. Which queries are repeated? Can pre-cache responses.

**provider:** Enables provider comparison. OpenAI vs Anthropic cost/quality trade-offs.

**model_used:** Enables routing analysis. Is routing working as intended? Are 50/50 split?

**estimated vs actual cost:** Enables cost prediction accuracy. Are estimates close? Can adjust heuristics.

**confidence_score:** Enables threshold tuning. What % of queries are refused? Is threshold too high/low?

**refusal_flag:** Enables refusal rate analysis. Are we over-refusing? Under-refusing?

**latency_ms:** Enables performance monitoring. Is system degrading? When?

**input/output_tokens:** Enables cost calculation verification. Do logs match actual API bills?

### 8.3 Analysis Capabilities

From these 11 metrics, can answer:

```
"What was our total cost last week?"
→ SUM(actual_cost) grouped by timestamp

"Which model is more cost-effective?"
→ AVG(actual_cost) grouped by model_used

"Is routing working?"
→ COUNT(*) grouped by model_used (should be 50/50)

"Are we over-refusing?"
→ COUNT(refusal_flag=true) / COUNT(*) × 100

"What's our average latency trend?"
→ AVG(latency_ms) grouped by date

"Which queries get refused most?"
→ query_hash grouped by refusal_flag=true
```

---

## 9. Error Handling Strategy

### 9.1 Error Categories

**Token Overflow:**
```
Severity: HIGH (prevents execution)
Handler: Raise ValueError("token_overflow")
Result: User sees 400 Bad Request
Action: Query is too long, user must shorten
```

**Provider Error:**
```
Severity: HIGH (cannot execute)
Handler: Raise ValueError("provider_error")
Result: User sees 400 Bad Request
Action: Provider is down, retry later
```

**Timeout Error:**
```
Severity: HIGH (cannot execute)
Handler: Raise ValueError("timeout_error")
Result: User sees 400 Bad Request
Action: LLM took too long (> 20 seconds), retry with shorter context
```

**Rate Limit Error:**
```
Severity: HIGH (cannot execute)
Handler: Raise ValueError("rate_limit_error")
Result: User sees 400 Bad Request
Action: Too many requests, implement backoff
```

**Logging Failure:**
```
Severity: CRITICAL (audit integrity)
Handler: Raise RuntimeError("logging_failure")
Result: User sees 503 Service Unavailable
Action: Database is down, cannot guarantee audit trail, fail safely
```

### 9.2 Error Propagation

```
policy_engine.py
    ↓ (calls)
  router.py, cost_estimator.py, llm_client.py, confidence.py, refusal.py, logger.py
    ↓ (raises)
  ValueError, RuntimeError
    ↓ (caught by)
routes.py
    ↓ (converts to)
HTTPException
    ↓ (returns to)
User (HTTP response)
```

**Design principle:** Errors bubble up. Only routes.py converts to HTTP. Policy engine doesn't know about HTTP.

---

## 10. Testing Surface

The system is designed to be testable:

### 10.1 Unit Test Boundaries

**Testable independently:**
```
✓ confidence.py - compute_confidence(answer, context) → score
✓ router.py - route_model(provider, tokens) → model
✓ refusal.py - should_refuse(confidence, context) → bool
✓ cost_estimator.py - estimate_cost(tokens, model) → float
```

**Easy to test:** Each function is pure (no side effects). Same input = same output.

### 10.2 Integration Test Boundaries

**Testable as system:**
```
✓ policy_engine.py (orchestrates all components)
✓ routes.py (HTTP interface)
```

**Requires:** Real or mocked LLM provider, real or mocked PostgreSQL

### 10.3 End-to-End Test

**Can test:** Entire flow from HTTP request to PostgreSQL log entry

**Requires:** Real deployment (Render), real database, real API keys

---

## 11. Performance Design

### 11.1 Latency Budget (Per Request)

```
Token estimation:        ~2ms   (tiktoken is cached)
Routing decision:        <1ms   (single if statement)
Output token estimation: <1ms   (constant lookup)
Token overflow check:    <1ms   (arithmetic)
Cost estimation:         <1ms   (multiply, round)
LLM call:                1000-2000ms   (external, unavoidable)
Confidence scoring:      ~5ms   (string tokenization + math)
Refusal decision:        <1ms   (threshold check)
Cost calculation:        <1ms   (multiply, round)
Audit logging:           ~10ms  (network I/O to PostgreSQL)
───────────────────
Total governance:        ~20ms  (negligible vs LLM)
Total with LLM:          1020-2020ms
```

**Result:** P95 latency improved 7% (routing benefit exceeded overhead).

### 11.2 Cost Budget (Per Query)

**gpt-4o-mini (50% of queries):**
```
Input: 95 tokens × $0.00000015 = $0.00001425
Output: 9 tokens × $0.0000006 = $0.0000054
Per query: $0.00001965
```

**gpt-4o (50% of queries):**
```
Input: 95 tokens × $0.000005 = $0.000475
Output: 9 tokens × $0.000015 = $0.000135
Per query: $0.00061
```

**Average:** ($0.00001965 + $0.00061) / 2 = $0.00031483 per query

**Per 100 queries:** $0.031483 (measured: $0.0303, ±3% variance)

---

## 12. Known Trade-offs

### 12.1 Post-Call Validation (vs Pre-Call Filtering)

**Current:** LLM is called, then response is validated and potentially refused.

**Trade-off:** Costs money for answers that get refused.

**Alternative:** Pre-filter queries, only call LLM if query is answerable.

**Why current approach?** Simpler to implement. Pre-filtering would require understanding query semantics (hard). Post-call is easier: just check confidence.

**Cost of this trade-off:** If 10% of queries get refused, that's 10% wasted cost. Acceptable because confidence is usually high on answerable questions.

### 12.2 Lexical-Only Confidence (vs Semantic)

**Current:** Confidence measures token overlap, not semantic correctness.

**Trade-off:** Detects low-overlap hallucinations, misses semantic errors.

**Alternative:** Use embedding-based similarity or external fact-check API.

**Why current approach?** Semantic validation requires ML model or API call. Adds latency and cost. Lexical is fast and cheap.

**Cost of this trade-off:** System claims "hallucination prevention" but only prevents low-overlap errors. Accurate claim would be "out-of-context answer prevention."

### 12.3 Static Thresholds (vs Adaptive)

**Current:** Confidence threshold = 0.55 (fixed). Token threshold = 500 (fixed).

**Trade-off:** Cannot tune per use-case (conservative medicine vs diagnostic reasoning).

**Alternative:** Make thresholds dynamic based on query type, user, or domain.

**Why current approach?** Simpler. Dynamic thresholds require per-request configuration. Static thresholds work for broad use cases.

**Cost of this trade-off:** Some use cases might over-refuse or under-refuse. Requires manual threshold tuning if needed.

### 12.4 No Failover (vs Multi-Provider)

**Current:** OpenAI or Anthropic, pick one provider per request.

**Trade-off:** No failover if provider is down.

**Alternative:** Try OpenAI first, fallback to Anthropic on failure.

**Why current approach?** Adds complexity. Failover logic requires retry loops, state tracking, timeout coordination. Out of scope for governance layer.

**Cost of this trade-off:** Provider outage = service outage. No graceful degradation.

### 12.5 Synchronous Logging (vs Async)

**Current:** Log write happens during request handling.

**Trade-off:** Logging latency affects request latency.

**Alternative:** Queue logs to message broker, write asynchronously.

**Why current approach?** Simpler. No need for message queue infrastructure. Logging is fast enough (~10ms).

**Cost of this trade-off:** If database is slow, requests slow down. Acceptable for current scale.

---

## 13. Scalability Model

### 13.1 Horizontal Scaling

**Constraint:** System is stateless.

**How it scales:**
```
1 instance → 10 instances: Just add more servers
No shared state → No coordination needed
PostgreSQL is bottleneck (not the app)
```

**Bottleneck:** PostgreSQL write throughput.

**Mitigation:** Connection pooling (psycopg2), batch logging (not implemented), log rotation.

### 13.2 Data Scaling

**Growth:** 1000 queries/day → 1M queries/day

**Impact:**
```
PostgreSQL table grows (more rows)
Query latency on logs increases
Disk usage increases
```

**Mitigation:**
```
Add database indexes on timestamp, query_hash
Partition table by date (for old data)
Archive old logs to cold storage (S3)
```

### 13.3 Cost Scaling

**Current:** $0.0303 per 100 queries

**At 1M queries/day:** $303/day cost

**At 10M queries/day:** $3,030/day cost

**Mitigation:** Routing continues to save 50% on simple queries. Cost scales linearly but predictably.

---

## 14. Security Design

### 14.1 Query Privacy

**What's stored:** SHA256(query), not plaintext

**Protection:** One-way hash. Cannot recover original query.

**Risk:** Hash doesn't hide query length. Attackers might infer query type from hash.

**Mitigation:** Acceptable trade-off. Hash is for honest logging, not cryptographic security.

### 14.2 Token Limits

**Protection:** Check (input_tokens + output_tokens) < model_limit before execution

**Risk:** Buffer overflow (context size attack)

**Mitigation:** Hard limit enforced. Oversized queries are blocked.

### 14.3 Model Isolation

**Protection:** Only authorized providers (OpenAI, Anthropic)

**Risk:** Attacker specifies unauthorized model

**Mitigation:** Enum validation in types.py. Only "openai" or "anthropic" accepted.

### 14.4 Cost Tracking

**Protection:** Estimate cost before LLM call

**Risk:** Cost explosion from runaway tokens

**Mitigation:** Token overflow check prevents extreme cases. Cost estimate is visible to user.

---

## 15. Design Review Checklist

The system follows these production-grade principles:

```
✓ Layered architecture (API, orchestration, components, infrastructure)
✓ Clear separation of concerns (routing, confidence, refusal are independent)
✓ Explicit state transitions (each step produces clear output)
✓ Fail-closed on errors (never silently degrades)
✓ Observable (logs all critical decisions)
✓ Testable (components can be tested independently)
✓ Scalable (stateless, can add instances)
✓ Documented (code is clear, self-documenting)
✓ Trade-offs acknowledged (post-call validation, lexical confidence, etc.)
✓ Performance budgeted (20ms governance overhead acceptable)
✓ Cost-aware (routing saves money, logging is fast)
✓ Security-conscious (query privacy, token limits, model isolation)
```

---

## 16. Future Design Improvements

If this system were to evolve, these design changes would be candidates:

### 16.1 Pre-Call Complexity Detection

**Problem:** Current system calls LLM then refuses if confidence is low.

**Design change:** Detect query complexity before LLM call. Route simple → cheap, complex → premium upfront.

**Benefit:** Avoid wasted LLM calls on obviously unanswerable questions.

### 16.2 Semantic Confidence

**Problem:** Lexical overlap doesn't detect semantic errors.

**Design change:** Add embedding-based semantic similarity. Compare answer embeddings to context embeddings.

**Benefit:** Catch hallucinations that reuse context tokens but are semantically wrong.

### 16.3 Adaptive Thresholds

**Problem:** Static threshold (0.55) doesn't fit all use cases.

**Design change:** Make confidence threshold configurable per request. Different domains have different risk tolerances.

**Benefit:** Conservative use cases (medical, legal) can use 0.9 threshold. Conversational use cases can use 0.4.

### 16.4 Multi-Provider Failover

**Problem:** No failover if OpenAI is down.

**Design change:** Implement retry logic. Try OpenAI, fallback to Anthropic on error.

**Benefit:** Better resilience to provider outages.

### 16.5 Async Logging

**Problem:** PostgreSQL writes add latency.

**Design change:** Queue logs to message broker (Redis/Kafka), write asynchronously.

**Benefit:** Logging no longer blocks request path.

### 16.6 Learning Feedback Loop

**Problem:** System doesn't learn which refusals were correct.

**Design change:** Add feedback collection. Was the refusal justified? Track accuracy over time.

**Benefit:** Can automatically adjust thresholds based on real-world feedback.

---

## 17. Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────┐
│                     Application                              │
│                   POST /govern                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (routes.py)                     │
│         Validation | Serialization | Error Handling         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestration Layer (policy_engine.py)          │
│                   10-Step Pipeline                           │
│                                                               │
│ 1. Est. Tokens ──┐                                           │
│ 2. Route Model ──┼─→ 3. Est. Output ──┐                     │
│ 4. Check Overflow┤                    │                      │
│ 5. Est. Cost ────┘                    ├─→ 6. LLM Call       │
│                                       │                      │
│ 7. Score Confidence ──┐               │                      │
│ 8. Refusal Decision ──┼─→ 9. Calc. Cost ──→ 10. Log        │
│ (Both depend on LLM answer)           │                      │
│                                       ▼                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ router.py   │ │confidence.py│ │ refusal.py   │ │cost_est.py   │
│ (Routing)   │ │(Grounding)  │ │ (Safety)     │ │ (Budget)     │
└─────────────┘ └─────────────┘ └──────────────┘ └──────────────┘
        │              │              │              │
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│           Infrastructure Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ llm_client.py    │  │ logger.py        │                  │
│  │ (Provider API)   │  │ (PostgreSQL)     │                  │
│  └─────────┬────────┘  └────────┬─────────┘                  │
│            │                    │                             │
│            ▼                    ▼                             │
│  [OpenAI / Anthropic]  [PostgreSQL sentinel_logs]           │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   Response       │
              │ (answer, cost,   │
              │  confidence,     │
              │  latency, etc.)  │
              └──────────────────┘
```

---

## 18. Implementation Notes

### 18.1 Why FastAPI?

- Async-ready (future-proof)
- Built-in validation (Pydantic)
- Auto-generated docs (Swagger)
- Excellent error handling
- Type hints throughout

### 18.2 Why PostgreSQL?

- ACID guarantees (audit integrity)
- Full transaction support
- Scalable (can partition by date)
- Good Python support (psycopg2)
- Cloud-friendly (managed services available)

### 18.3 Why tiktoken?

- Official OpenAI tokenizer
- Accurate token counts
- Cached encoders (fast)
- Handles special tokens correctly

### 18.4 Why SHA256 for query hashing?

- One-way (can't recover query)
- Fast (hardware acceleration)
- Standard (widely implemented)
- Collision-resistant

---

## 19. Conclusion

Sentinel Engine is designed as a production-grade governance layer with:

- **Clear architecture** (layered, orchestrated, abstracted)
- **Explicit safety** (fail-closed, confidence gates, overflow checks)
- **Full observability** (11 metrics per request)
- **Cost efficiency** (50% savings through routing)
- **Operational maturity** (extensible, testable, scalable)

The design acknowledges trade-offs (post-call validation, lexical confidence) and documents them. The system is not perfect but is fit for production use with the stated limitations understood.

Design quality: **Production-grade, not research-grade.**

---

**End of Design Document**
