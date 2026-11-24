# ADR 0001: Deterministic Core, LLM at the Edge

## Status
Accepted

## Context
Challenge 6 requires building a production-grade Urban Air Quality Assistant for Indian families (covering Delhi, Noida, Mumbai, and Kolkata). The system must deliver:
1. Low-emission daily routines
2. Actionable indoor air quality guidance (CADR, sealing, ventilation)
3. Transparent sustainable alternatives and impact math (dose, CO2, cigarette equivalence)

Large Language Models (LLMs) are prone to hallucinations, non-deterministic arithmetic, floating-point drift, and inconsistency when computing domain metrics such as sub-index breakpoints, inhaled particulate mass ($\mu\text{g}$), CADR requirements, or brute-force errand permutations. Presenting hallucinated air quality numbers or inaccurate health guidance undermines public trust and violates evaluation criteria.

## Decision
We enforce a strict separation of concerns following the **Deterministic Core, LLM at the Edge** pattern:

1. **Deterministic Core (`backend/app/aqi/`, `backend/app/exposure/`):**
   - Implemented exclusively as pure Python functions with **zero I/O** (no network, no database, no LLM calls).
   - All numerical computations are performed with verified, cited mathematical models:
     - CPCB National AQI sub-index linear interpolation
     - Inhaled $\text{PM}_{2.5}$ dose ($\mu\text{g}$) based on activity breathing rates, duration, and microenvironments
     - Berkeley Earth cigarette equivalence heuristic
     - Room Clean Air Delivery Rate ($\text{CADR} = V_{\text{room}} \times \text{ACH}$)
     - Multi-stop errand route permutations and $\text{CO}_2$ avoidance
     - Planet vs. Lungs commute trade-offs
     - Data Confidence scoring based on distance, age, and completeness
   - 100% testable via unit tests, golden-value regression fixtures, and `Hypothesis` property-based tests.

2. **LLM at the Edge (`backend/app/planner/grok.py`):**
   - Grok (xAI) operates strictly as a narrative translation, personalization, and summarization layer.
   - All mathematical figures, pollutant levels, doses, and trade-offs are passed into prompts as pre-computed, immutable JSON facts.
   - Prompts strictly forbid the LLM from calculating or altering numerical metrics.
   - Outputs are strictly constrained by structured JSON schemas validated against Pydantic v2 models.
   - If the LLM generates invalid JSON or fails validation after one retry, the system seamlessly falls back to a deterministic template planner (`backend/app/planner/fallback.py`).

## Consequences

### Positive
- **Zero Math Hallucination:** Every number shown to the user or reviewer is mathematically reproducible and verifiable.
- **Auditability:** Complete traceability from user input $\to$ raw pollutant data $\to$ deterministic formula $\to$ output card.
- **Performance & Efficiency:** Pure math runs in sub-milliseconds without LLM latency or token costs.
- **Resilience:** Even if upstream LLM APIs experience downtime or quota limits, the core assistant continues delivering 100% accurate actionable plans via deterministic fallback templates.
- **Security:** Untrusted user input is isolated from system prompts via structural delimiters.

### Negative
- Requires maintaining dual templates (dynamic prompt for LLM + structured fallback template).
- Any new mathematical feature must be implemented and verified in the deterministic core before being exposed to the LLM layer.
