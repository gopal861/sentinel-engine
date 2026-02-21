# Sentinel Engine

A governance layer that sits between your application and LLM providers. It enforces cost control, prevents out-of-context answers from reaching users, and logs everything.   

**Deployment:** : (https://sentinel-engine-amdw.onrender.com/)

## The Problem

When you call an LLM API directly, you get three problems:

1. **Hallucination exposure** — The model answers confidently even when context doesn't support the answer. You pay for the request and the user gets wrong information.

2. **Unbounded costs** — Every query costs money. If you have 1 million queries a day, costs scale linearly. No way to optimize.

3. **No audit trail** — You can't explain to compliance why a specific response was given. There's no record of what happened.

We tested a baseline LLM (gpt-4o-mini) on 240 queries where context was intentionally incomplete. Result: **66.67% of responses were hallucinations** — the model answered even though the information wasn't in the context.

That's unacceptable for production.

## The Solution

Sentinel Engine intercepts every request. For each query, it:

1. Estimates tokens and routes to the cheapest model that can handle it
2. Calls the LLM (via OpenAI or Anthropic)
3. Computes confidence based on how much of the answer comes from provided context
4. Refuses to return the answer if confidence is below threshold
5. Logs everything to PostgreSQL for audit trail

**Result on same 240 queries:** 0% hallucinations. 100% of out-of-context questions were refused.

## What You Get

### Cost Reduction
50% of queries route to gpt-4o-mini (cheaper). 50% route to gpt-4o (needed for complexity).

Cost per 100 queries: **$0.0303**

Without routing (all gpt-4o): would be ~$0.06. You save money while enforcing safety.

### Hallucination Containment
Out-of-context answers are refused before they reach users. If the context doesn't contain the answer, the user sees:

```
"Request refused due to low confidence in context grounding."
```

Not a hallucination. Not a wrong answer. A clear refusal.

### Complete Audit Trail
Every request logged to PostgreSQL with:
- What was asked (query hash, for privacy)
- Which model was used (gpt-4o-mini or gpt-4o?)
- How confident the system was (0.0 - 1.0)
- Was it refused? (yes/no)
- How much did it cost? (estimated vs actual)
- How long did it take? (latency in ms)
- Token usage (input and output)

You can answer questions like:
- "What was our LLM cost last week?"
- "How many queries got refused?"
- "Are we routing correctly (50/50 split)?"
- "What's our average latency?"

### Deterministic Routing
Routing decisions are fully deterministic. Same query always routes the same way. This means:
- Reproducible cost predictions
- Auditable routing decisions
- No randomness, no surprises

## How to Use It

### Endpoint

```
POST https://sentinel-engine-amdw.onrender.com/govern
```

### Request

```json
{
  "query": "Who created Python?",
  "context": "Python was created by Guido van Rossum and first released in 1991.",
  "provider": "openai"
}
```

**Fields:**
- `query` (required): The question to answer
- `context` (required): The information available to answer it
- `provider` (required): Either "openai" or "anthropic"

### Response

```json
{
  "answer": "Guido van Rossum",
  "refusal": false,
  "confidence_score": 0.7932,
  "model_used": "gpt-4o-mini",
  "estimated_cost": 0.000303,
  "input_tokens": 95,
  "output_tokens": 9,
  "latency_ms": 894,
  "provider": "openai"
}
```

**Fields:**
- `answer`: The response (or refusal message if refused)
- `refusal`: Was the answer refused? (boolean)
- `confidence_score`: How grounded is this answer? (0.0 = not grounded, 1.0 = fully grounded)
- `model_used`: Which model was selected?
- `estimated_cost`: What was the cost estimate before calling?
- `input_tokens`: How many tokens in the request?
- `output_tokens`: How many tokens in the response?
- `latency_ms`: End-to-end time in milliseconds
- `provider`: Which provider handled this?

### Example: Answerable Question

```
Input:
{
  "query": "When was Tesla founded?",
  "context": "Tesla was founded in 2003 as an electric vehicle company.",
  "provider": "openai"
}

Output:
{
  "answer": "Tesla was founded in 2003.",
  "refusal": false,
  "confidence_score": 0.88,
  "model_used": "gpt-4o-mini",
  "estimated_cost": 0.000303,
  "latency_ms": 734
}

Interpretation: The answer is grounded in context (0.88 confidence). 
System routed to cheap model. Responded in 734ms. Cost $0.0003.
```

### Example: Unanswerable Question

```
Input:
{
  "query": "What is Tesla's current stock price?",
  "context": "Tesla was founded in 2003 as an electric vehicle company.",
  "provider": "openai"
}

Output:
{
  "answer": "Request refused due to low confidence in context grounding.",
  "refusal": true,
  "confidence_score": 0.12,
  "model_used": "gpt-4o-mini",
  "estimated_cost": 0.000303,
  "latency_ms": 627
}

Interpretation: Stock price is not in context (0.12 confidence). 
System refused to answer. Still logged and cost tracked.
```

## How It Works Internally

The system executes a 10-step pipeline for every request:

1. **Token Estimation** — Count tokens in query + context
2. **Routing Decision** — If tokens < 500, use gpt-4o-mini. Else use gpt-4o.
3. **Output Token Estimation** — Assume max 500 token response
4. **Overflow Check** — Reject if total tokens exceed model limit
5. **Cost Estimation** — Calculate cost before calling LLM
6. **LLM Call** — Send to OpenAI or Anthropic with grounding prompt
7. **Confidence Scoring** — Measure how much of answer comes from context
8. **Refusal Decision** — If confidence < 0.55, refuse
9. **Actual Cost Calculation** — Calculate real cost from API response
10. **Audit Logging** — Record all metrics to PostgreSQL

**Key design principle:** Refusal happens after LLM call. This costs money for refused answers, but it's simpler than trying to predict whether an answer will be hallucinated before calling the model. Trade-off is acceptable because confidence is usually high on answerable questions.

## What Works Well

**Deterministic routing.** Token count → model choice. Same query always routes the same way. This is rare in AI systems. Enables cost prediction and auditing.

**Fail-closed logging.** If database goes down, the system fails completely. Doesn't silently skip logging. This guarantees audit integrity. Critical for compliance.

**Strong grounding prompt.** LLM sees explicit instructions: "Answer strictly using context. Do not fabricate." This is first line of defense.

**Cost governance.** Simple rule (token threshold = 500) saves ~50% on simple queries without increasing hallucination risk.

**Complete observability.** Log 11 metrics per request. Can answer any operational question from logs.

## What Doesn't Work (Honest Limitations)

**Lexical-only confidence.** System measures token overlap between answer and context. It doesn't check if the answer is semantically correct.

Example of what it misses:
```
Context: "Paris is the capital of France"
Query: "What is the capital of Italy?"
LLM answer: "Paris"  ← Uses context tokens "Paris"
Confidence: 0.85 (high token overlap)
Result: NOT REFUSED (hallucination passes through)
```

System detects low-overlap hallucinations (questions outside context) but misses semantic errors that reuse context tokens.

**Post-call refusal costs money.** System calls LLM, gets answer, checks confidence, then refuses. The API call already happened. If 10% of queries get refused, that's 10% wasted cost.

Better approach would be pre-filtering (check if query is answerable before calling LLM), but that's harder to implement.

**No multi-provider failover.** If OpenAI is down, the system is down. No fallback to Anthropic. No retry logic. Acceptable for now, but means provider outage = service outage.

**Heuristic Anthropic tokenization.** For OpenAI, we use official tiktoken (accurate). For Anthropic, we use `len(text) / 4` (approximation). Edge cases with special characters might route to wrong model.

**Static thresholds.** Confidence threshold = 0.55 (fixed). Token threshold = 500 (fixed). Can't tune per use case. Conservative medicine needs 0.9 threshold. Chatbots need 0.3 threshold. Current system serves middle ground.

**Small test set.** System validated on 240 synthetic queries (all company facts). Unknown behavior on:
- Technical documentation
- Medical/legal content
- Code snippets
- Multi-document contexts
- Production scale (100+ concurrent requests)

## Measured Results

### Fabrication Rate
- **Baseline LLM:** 66.67% of out-of-context questions answered (hallucinations)
- **Sentinel Engine:** 0.00% of out-of-context questions answered (all refused)

Test: 240 queries (80 answerable, 160 intentionally unanswerable)

### Latency
- **Baseline P95:** 1571.44 ms
- **Sentinel P95:** 1462.00 ms
- **Improvement:** -109 ms (7% faster)

Why faster? Routing to cheaper/faster gpt-4o-mini for 50% of queries. Governance overhead (~20ms) is negligible vs LLM call time (1000-2000ms).

### Cost
- **Cost per 100 queries:** $0.0303
- **Routing distribution:** 50% gpt-4o-mini, 50% gpt-4o
- **Savings vs all-premium:** ~50% on routed queries

### Routing Accuracy
- **Test dataset:** 100 routing decisions
- **Correct routing:** 100/100 (100%)
- **Pattern:** 50 cheap model queries, 50 premium model queries, perfect split

## Deployment

**Platform:** Render (serverless Python hosting)

**Runtime:** Python 3.14

**Framework:** FastAPI

**Database:** PostgreSQL (audit logs)

**API Keys Required:**
- OpenAI API key (if using OpenAI)
- Anthropic API key (if using Anthropic)
- PostgreSQL connection string

**Environment Variables:**
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:password@host/dbname
```

**Live Endpoint:**
```
https://sentinel-engine-amdw.onrender.com/govern
```

Fully production-deployed. Real requests, real database, real metrics.

## Monitoring

Check system health at:
```
GET https://sentinel-engine-amdw.onrender.com/health
```

Response:
```json
{"status": "ok"}
```

Monitor operational metrics from PostgreSQL sentinel_logs table:

```sql
-- Refusal rate
SELECT 
  COUNT(*) as total_queries,
  SUM(CASE WHEN refusal_flag = true THEN 1 ELSE 0 END) as refused,
  ROUND(100.0 * SUM(CASE WHEN refusal_flag = true THEN 1 ELSE 0 END) / COUNT(*), 2) as refusal_rate_percent
FROM sentinel_logs;

-- Routing distribution
SELECT 
  model_used,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM sentinel_logs
GROUP BY model_used;

-- Cost tracking
SELECT 
  DATE(timestamp) as date,
  SUM(actual_cost) as total_cost,
  ROUND(AVG(actual_cost), 8) as avg_cost_per_query
FROM sentinel_logs
GROUP BY DATE(timestamp)
ORDER BY DATE(timestamp) DESC;

-- Latency percentiles
SELECT 
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) as p50,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99
FROM sentinel_logs;
```

## Architecture

```
Application
    ↓
Sentinel Engine (/govern endpoint)
    ├─ Token Estimation
    ├─ Deterministic Routing (token count → model)
    ├─ Cost Estimation
    ├─ LLM Call (OpenAI or Anthropic)
    ├─ Confidence Scoring (lexical overlap)
    ├─ Refusal Gate (confidence < 0.55?)
    ├─ Audit Logging (PostgreSQL)
    └─ Response
    ↓
OpenAI / Anthropic API
    ↓
PostgreSQL (audit trail)
```

## Known Issues & Trade-offs

**Issue #1: Semantic hallucinations aren't caught**

Lexical confidence catches "answer outside context" but not "semantically wrong but uses context tokens."

Mitigation: Use as second layer, not sole validation. For high-stakes applications (medical, legal), add semantic validation layer.

**Issue #2: Cost on refused queries**

Refuses happen after LLM call. API charge is incurred even for refused responses.

Mitigation: In production, consider pre-filtering for obvious out-of-domain queries. Current design prioritizes simplicity over cost efficiency.

**Issue #3: No multi-provider failover**

OpenAI outage = service outage. No graceful degradation.

Mitigation: Monitor OpenAI status. Consider adding Anthropic fallback in future version.

**Issue #4: Only tested on synthetic data**

240 company fact questions. Real production traffic is more diverse.

Mitigation: Deploy with confidence_threshold = 0.65 (more conservative) until production metrics confirm safety.

## What's Next

If this system evolves, candidates for improvement:

1. **Pre-call complexity detection.** Avoid wasting LLM calls on obviously unanswerable questions.

2. **Semantic confidence scoring.** Add embedding-based similarity check (not just token overlap).

3. **Adaptive thresholds.** Different use cases need different sensitivity (medical needs 0.9, chatbots need 0.4).

4. **Multi-provider failover.** Retry with Anthropic if OpenAI fails.

5. **Learning feedback loop.** Track which refusals were correct/incorrect, adjust thresholds automatically.

6. **Async logging.** Queue logs instead of writing synchronously (reduce latency).

## Project Structure

```
sentinel/
  ├─ api/
  │  └─ routes.py           (HTTP endpoint)
  ├─ core/
  │  ├─ policy_engine.py    (10-step orchestration)
  │  ├─ router.py           (routing decision)
  │  ├─ confidence.py       (grounding validation)
  │  ├─ refusal.py          (safety gate)
  │  ├─ cost_estimator.py   (budget control)
  │  ├─ llm_client.py       (provider API)
  │  └─ logger.py           (PostgreSQL audit)
  ├─ prompts/
  │  └─ grounding_prompt.py (LLM instructions)
  ├─ config.py              (thresholds, prices, models)
  ├─ types.py               (Pydantic schemas)
  └─ main.py                (FastAPI app)

scripts/
  ├─ baseline_evaluate.py   (reproduce baseline)
  ├─ evaluate.py            (reproduce sentinel)
  ├─ routing_analysis.py    (routing accuracy test)
  └─ [visualization scripts]

proof/
  ├─ baseline_results.csv   (240 baseline queries)
  ├─ evaluation_results.csv (240 sentinel queries)
  └─ routing_results.csv    (100 routing tests)
```

## Reproducibility

All results are reproducible. To regenerate evaluation data:

```bash
python baseline_evaluate.py
python evaluate.py
python routing_analysis.py
```

Results go to proof/ directory. Compare to what's committed.

System is production-deployed. You can also test live:

```bash
curl -X POST https://sentinel-engine-amdw.onrender.com/govern \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who created Python?",
    "context": "Python was created by Guido van Rossum.",
    "provider": "openai"
  }'
```

## Why This Design

Every design choice has a reason. Some are good reasons. Some are trade-offs.

**Why deterministic routing?** Makes cost predictable. Same query always costs the same. Enables auditing.

**Why fail-closed logging?** Audit integrity is non-negotiable. If logging fails, system fails. Never silently skip.

**Why post-call refusal?** Simpler than pre-call filtering. Pre-call would need to understand if a question is answerable (hard). Post-call is: call LLM, check confidence, refuse if needed.

**Why lexical confidence?** Fast and cheap. Semantic validation would require ML model or external API (slower, more expensive). Lexical works for context-grounding.

**Why static threshold (0.55)?** One threshold that works for most cases. Not optimal for all use cases (medical needs higher, chatbots need lower). Trade-off for simplicity.

## Supporting Documentation

- **DESIGN.md** — Complete system design (why architectural choices, trade-offs, patterns)
- **ARCHITECTURE.md** — Technical architecture details
- **VALIDATION_REPORT.md** — Evidence for all claims (CSVs, math, metrics)

## Author's Note

This system was built because hallucination risk in production LLM systems is real. Grounding your responses in provided context isn't perfect, but it's better than nothing.

The design acknowledges trade-offs honestly. It's not claiming to be perfect. It's claiming to solve specific problems (out-of-context hallucinations, cost control, audit trail) within known constraints (lexical validation, no semantic checking, single provider).

Use it where it's strong (cost governance, audit logging, context-grounding). Don't use it where it's weak (semantic validation, multi-provider failover).

For most production LLM applications, this is useful. Not a complete solution, but a solid governance layer.

---

**Live endpoint:** https://sentinel-engine-amdw.onrender.com/govern

**Metrics proven by:** 240 evaluation queries, 100 routing tests, actual PostgreSQL logs

**Production status:** Deployed and operating
