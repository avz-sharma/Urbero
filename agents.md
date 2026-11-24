# AGENTS.md — Urban Air Quality Assistant (Challenge 6)

> **Purpose:** Operating manual for coding agents building **Challenge 6: Urban Air Quality Assistant** for Indian cities (Delhi, Noida, Mumbai, Kolkata). Every architectural rule, domain constraint, and phase gate below is mandatory.

## 1. Mission & Evaluation Criteria

Build a production-grade GenAI assistant that helps Indian families and communities navigate severe urban air pollution (going beyond raw AQI display) across three pillars:

1. **Low-emission daily routines** (safer commutes, trip consolidation, time-of-day plans).

2. **Indoor air quality guidance** (actionable CADR/purifier, sealing, ventilation, and footnote plant guidance).

3. **Sustainable alternatives & impact justification** (transparent math explaining *why* and quantifying impact).

Submissions are **AI-evaluated first** on 6 equally critical parameters, then tested live by human reviewers:

* **Code Quality** · **Security** · **Efficiency** · **Testing** · **Accessibility** · **Problem Statement Alignment**

## 2. Tech Stack, Repo Layout & Schema Single Source of Truth

### Stack

* **Backend:** Python 3.11+, FastAPI, Pydantic v2, `mypy --strict`, `ruff`, `pytest`, `Hypothesis`, `slowapi`.

* **Frontend:** React, Vite, TypeScript (`strict: true`, ESLint `@typescript-eslint/no-explicit-any: error`, Prettier), Testing Library, `jest-axe`.

* **Cache & Hosting:** In-process TTL cache (L1) + Supabase shared cache table (L2); deployed on Google Cloud Run (`min-instances=1` during judging; **zero login, zero judge-supplied API keys**).

### Mandatory Directory Structure

```
backend/
  app/
    config/constants.py       # Verified, cited scientific & AQI constants
    providers/
      base.py                 # Provider interface & reading contract
      openaq.py               # OpenAQ v3 client + retry/backoff/circuit breaker
      cache.py                # L1 in-process + L2 Supabase shared cache
      openmeteo.py            # [Phase 6 Optional] Labelled modelled forecasts
    aqi/
      cpcb.py                 # Pure CPCB National AQI calculator
      confidence.py           # Data Confidence badge scorer (High/Medium/Low)
      diurnal.py              # Station-history (24-72h) diurnal profiler
    exposure/
      dose.py                 # Pure inhaled PM2.5 dose + Berkeley Earth heuristic
      cadr.py                 # Pure room CADR & indoor action engine
      optimizer.py            # Pure schedule re-optimizer & Smog Episode trigger
      errands.py              # Pure brute-force errand merger (<=4 stops)
      commute.py              # Pure Planet vs. Lungs commute comparator
    planner/
      schemas.py              # SINGLE SOURCE OF TRUTH (Pydantic v2 models)
      grok.py                 # Grok structured output client (JSON mode)
      fallback.py             # Deterministic template plan fallback
      vision.py               # [Phase 6 Optional] Room photo pre-fill
    api/
      routes.py               # FastAPI endpoints
      security.py             # Rate limits, CORS, security headers, sanitization
  tests/
    fixtures/                 # Recorded API fixtures (ONLY place mocks live)
frontend/
  src/
    api/generated.ts          # Auto-generated via openapi-typescript
    LowEmissionRoutine/
    IndoorAirGuide/
    ImpactJustification/
    HouseholdProfile/
docs/
  adr/0001-deterministic-core-llm-edge.md

```

### Single Source of Truth Rule

Pydantic models in `backend/app/planner/schemas.py` drive:

1. FastAPI OpenAPI schema,

2. Grok structured output JSON format, and

3. Frontend TypeScript types via `openapi-typescript`.

**Never** hand-duplicate API interfaces in TypeScript.

## 3. Recommended Agent Tooling & MCP Loadout

Keep context lean by activating **only** these 8 curated skills/MCP servers—do not stack redundant plugins:

### Backend & System Architecture (5 Tools)

| Tool / Repo | Role in This Build | Active Phases | 
| ----- | ----- | ----- | 
| **Context7** (`upstash/context7`) | Fetches live, version-specific documentation for FastAPI, Pydantic v2, OpenAQ v3, and the Google GenAI SDK so deprecated APIs or `responseSchema` syntax are never hallucinated. | Phases 0, 2, 4, 6 | 
| **Superpowers** (`obra/superpowers`) | Enforces strict `RED -> GREEN -> REFACTOR` TDD loops and blocks phase sign-off without verified command output. | Phases 1–6 | 
| **Planning-with-files** (`OthmanAdi/planning-with-files`) | Maintains persistent Markdown state (`task_plan.md`, `findings.md`, `progress.md`) across sessions to track `# VERIFY_BEFORE_PROD` constants and prevent scope drift. | All Phases | 
| **Serena** (`oraios/serena`) | Provides LSP-backed symbol navigation (`find_symbol`, `find_referencing_symbols`) to verify `aqi/` and `exposure/` remain pure (zero I/O imports) and schema changes propagate cleanly. | Phases 1–6 | 
| **Rtk** (`rtk-ai/rtk`) | Compresses verbose CLI outputs (`pytest`, `mypy --strict`, `ruff`, `git diff`) by 60–90% to preserve context window quality across gate runs. | All Phases | 

### Frontend & Accessibility (3 Tools)

| Tool / Repo | Role in This Build | Active Phases | 
| ----- | ----- | ----- | 
| **Playwright-MCP** (`microsoft/playwright-mcp`) | Inspects the live rendered app via accessibility trees to verify WCAG 2.2 AA contrast, keyboard tab order, skip links, focus management, `aria-live="polite"` transitions, and all 3 Indian household presets. | Phases 5, 7 | 
| **ui-ux-pro-max** (`nextlevelbuilder/ui-ux-pro-max-skill`) | Enforces cohesive design tokens, typography hierarchy, and WCAG contrast alongside text+icon AQI indicators across the four pillar directories. | Phase 5 | 
| **Mattpocock** (`mattpocock/skills`) | Enforces strict TypeScript discipline (zero `any`, clean prop narrowing over `openapi-typescript` generated types). | Phases 0, 5, 6 | 

## 4. Core Architecture & Scope Lock

### Pattern: Deterministic Core, LLM at the Edge

* **Pure Engines (`aqi/`, `exposure/`):** Pure functions with **zero network, DB, or LLM I/O**. Every single number (CPCB AQI, inhaled $\mu\text{g}$ $\text{PM}_{2.5}$, cigarette equivalence, CADR, diurnal curve, errand permutations, $\text{CO}_2$ avoided, Planet vs. Lungs trade-offs, Data Confidence score) is computed deterministically in Python.

* **GenAI Edge (`planner/grok.py`):** Grok strictly personalizes narratives, explains `why`, drafts English/Hinglish WhatsApp family & RWA/school community briefings, and (Phase 6) pre-fills room form fields from a photo.

* Document this architecture in `docs/adr/0001-deterministic-core-llm-edge.md`.

### Hard Scope Lock — DO NOT BUILD

* WAQI secondary provider (use OpenAQ v3 + stale-flagged cache instead).

* Custom ML AQI forecasting models (unverifiable; reads as fabricated-data risk).

* Chatbot sidebars, city heatmaps, voice interfaces, wearables.

* User authentication/login or judge-supplied API key prompts.

## 5. Anti-Hallucination & Integrity Rules (NON-NEGOTIABLE)

### 5.1 Mandatory Verification Gate

Before writing domain math or external API adapters, query **Context7** / official specs and pin these 7 items in `backend/app/config/constants.py` with inline authoritative citations. **Never guess from memory.** If an item cannot be verified in your current environment, mark it `# VERIFY_BEFORE_PROD` in both `constants.py` and `findings.md` with an explicit assumption note and report it at phase exit:

1. **CPCB National AQI specification:** Official Indian breakpoint tables (verify $\text{PM}_{2.5}$ boundaries such as $30/31$ and $60/61$), linear sub-index interpolation formula, and minimum valid pollutant rule (must include a PM pollutant). **Never use US EPA breakpoints.**

2. **data.gov.in CPCB API:** Verify with a live key whether an active endpoint exists before adding any secondary provider; otherwise use OpenAQ v3 + stale-flagged cache only.

3. **OpenAQ v3 schema & limits:** Confirm `locations -> sensors -> measurements` flow, free-tier limits ($60$ req/min, $2{,}000$ req/hr), and whether location metadata flags reference-grade vs. low-cost sensors.

4. **Physiological & emission constants:** Citable sources for age/activity breathing rates, indoor infiltration factors, commute-mode exposure factors, and tailpipe $\text{CO}_2$ emission factors (or expose clearly labeled adjustable assumptions in config & UI).

5. **Reference thresholds:** Verify WHO 2021 24-hour $\text{PM}_{2.5}$ guideline ($15\,\mu\text{g/m}^3$) and India NAAQS 24-hour $\text{PM}_{2.5}$ limit ($60\,\mu\text{g/m}^3$).

6. **Grok SDK & model config:** Verify current Grok model identifier and JSON mode API syntax; read model name strictly from environment config (never hardcode).

7. **Open-Meteo Air Quality (Phase 6 only):** Confirm terms and response fields before implementing modelled forecasts.

### 5.2 Zero Fabricated Data

* Never hardcode AQI readings, pollutant concentrations, or diurnal smog curves in production code.

* Reject negative or physically absurd sensor readings.

* On live provider failure: fall back to the nearest active station, then to the last-known-good Supabase-cached real reading flagged `status="stale"` with its original `observed_at` timestamp.

* Every reading carries:
  `{source, station, distance_km, observed_at, fetched_at, status: "live" | "stale", is_reference_grade: bool | null}`.

* If Phase 6 Open-Meteo is added, visually and structurally separate modelled forecasts from live station readings.

### 5.3 Zero Math in LLM Prompts

* Never ask Grok to compute AQI, dose, cigarette counts, percentages, CADR, or $\text{CO}_2$.

* Pass pre-computed deterministic JSON into prompts as immutable facts.

* Re-validate Grok's JSON output with Pydantic; retry once on validation error; if it still fails, serve `planner/fallback.py` (deterministic template plan).

### 5.4 Mandatory Honesty Labels

* **Cigarette equivalence:** Berkeley Earth benchmark ($\approx 22\,\mu\text{g/m}^3$ for $24\,\text{h} \approx 1$ cigarette) MUST be labeled a communication heuristic, not a clinical equivalent.

* **Exposure baselines:** WHO 2021 ($15\,\mu\text{g/m}^3$) and India NAAQS ($60\,\mu\text{g/m}^3$) MUST be labeled reference values, never a "personal safe budget."

* **Indoor plants:** Lead with sealing gaps, ventilation timing, and purifiers; demote NASA-cited plants (Areca Palm, Snake Plant, Peace Lily) to a low-impact footnote.

* **No medical claims:** In **Smog Episode Mode** (Very Poor / Severe AQI), output fitted N95/FFP2 mask guidance (explicitly ruling out cloth masks) and a "consult a doctor" advisory for sensitive groups—never medical diagnoses or prescriptions.

* **Clean-air days:** Handle Good/Satisfactory AQI gracefully without alarmism.

## 6. Domain & Feature Contracts (Zero Skipped Features)

| Module / Feature | Required Behavior | 
| ----- | ----- | 
| **CPCB AQI (`aqi/cpcb.py`)** | Sub-index per pollutant ($\text{PM}_{2.5}, \text{PM}_{10}, \text{NO}_2, \text{CO}$, etc.) via CPCB breakpoint interpolation; overall AQI $= \max(\text{sub-indices})$; enforce minimum valid pollutant count including PM. | 
| **Inhaled Dose (`exposure/dose.py`)** | Combine outdoor $\text{PM}_{2.5}$, indoor infiltration factor, purifier effect, age/activity breathing rates, and duration to compute inhaled $\mu\text{g}$ $\text{PM}_{2.5}$, Berkeley Earth cigarette heuristic, and WHO/NAAQS reference lines. | 
| **Room CADR (`exposure/cadr.py`)** | Deterministic $\text{CADR} = V_{\text{room}} \times \text{ACH}_{\text{target}}$ driven by room form (dimensions, windows, kitchen chimney yes/no, incense/agarbatti use, unsealed balcony/door gaps). Sealing/ventilation/purifiers first; plants as footnote. | 
| **Data Confidence (`aqi/confidence.py`)** | Score `High` / `Medium` / `Low` + plain-language reason from `distance_km`, reading age (`fetched_at - observed_at`), and pollutant completeness. | 
| **Diurnal Profile (`aqi/diurnal.py`)** | Derived strictly from the station's last $24\text{--}72\,\text{h}$ OpenAQ measurements. | 
| **Routine Optimizer (`exposure/optimizer.py`)** | Enumerate station diurnal slots to optimize household schedules, quantify before/after dose reduction, handle clean-air days, and activate **Smog Episode Mode** at Very Poor/Severe AQI. | 
| **Errand Merger (`exposure/errands.py`)** | Brute-force permutations for $\le 4$ errands (groceries, pharmacy, bank, school pickup) respecting fixed time windows (shop hours, school pickup); output merged loop in cleanest window, tailpipe $\text{CO}_2$ avoided, and $\text{PM}_{2.5}$ dose reduced. | 
| **Planet vs. Lungs (`exposure/commute.py`)** | Side-by-side commute mode comparison (e.g., cycling, walking, car, Metro) showing both tailpipe $\text{CO}_2$ avoided and personal inhaled $\text{PM}_{2.5}$ dose (highlighting when cycling increases inhaled dose during severe smog). | 
| **Structured Cards & Briefings (`planner/`)** | Every recommendation card requires non-empty `why`, `quantified_impact`, `math_breakdown` (inputs, formula, source, station, timestamp), and live metadata. Generate copy-ready **WhatsApp Family Card** (English or Hinglish) AND **Community Brief** (RWA/school outdoor-activity & high-AQI advisory). | 
| **Presets & UI (`frontend/src/`)** | 3 one-click presets: *South Delhi Joint Family* (asthmatic grandfather, 8yo schoolkid, Gurgaon commuter), *Andheri Mumbai Working Couple*, *Salt Lake Kolkata Senior Couple*. Expandable **"Show the Math" drawer** on every card. Visible Live Source, Station Distance, Timestamp, and Data Confidence badge on every card. | 
| **Vision Pre-fill (`planner/vision.py`) \[Phase 6\]** | Optional photo upload that pre-fills the Room Form with confidence scores for user confirmation. Reject non-room images; strip EXIF; zero disk storage; treat image text as untrusted (prompt-injection defense). | 

## 7. Engineering Baselines (AI Grader Maximizers)

* **Code Quality:** Zero `any` in TS; `mypy --strict`; `ruff`; Prettier; pure domain modules; README with architecture diagram, citations, coverage badge, and Requirement $\to$ File $\to$ Test traceability table.

* **Security:**

  * All Grok & OpenAQ calls strictly server-side.

  * Use enums & bounded Pydantic fields (minimize free text); wrap untrusted user/OCR text in explicit delimiters (`<untrusted_input>...</untrusted_input>`).

  * `slowapi` rate limiting, strict CORS allow-list, security response headers, zero PII in logs.

  * Upload MIME + size validation + EXIF strip + in-memory only (Phase 6).

  * Commit `.env.example` only; Secrets via GCP Secret Manager; `gitleaks` pre-commit hook (clean git history); `pip-audit` & `npm audit` in CI.

* **Efficiency:**

  * 15–30 min per-station TTL cache (L1 in-process + L2 Supabase) to protect OpenAQ's $60$ req/min limit.

  * Normalize Grok cache keys (bucket AQI bands + round pollutants).

  * HTTP timeouts, exponential backoff retries, circuit breaker; debounced city search; lazy-loaded charts; Cloud Run `min-instances=1`.

* **Testing:**

  * CPCB boundary tests (e.g., $\text{PM}_{2.5}$ $30/31$, $60/61$) & minimum-pollutant rule tests.

  * `Hypothesis` property-based tests: higher $\text{PM}_{2.5}$ never lowers dose; higher activity never lowers dose.

  * Failover, stale cache, absurd/negative sensor rejection, malformed Grok $\to$ template fallback, and Smog Episode Mode (N95 + doctor line) tests.

  * Recorded API fixtures; frontend Testing Library + `jest-axe`; CI on every push with coverage threshold ($\ge 90\%$ on deterministic engines).

* **Accessibility (WCAG 2.2 AA, Lighthouse CI** $\ge 95$**):**

  * Semantic HTML5 landmarks, skip link, keyboard-navigable tabs, focus management on results render, `prefers-reduced-motion`, $44\,\text{px}$ touch targets, text+icon alongside color.

  * Accessible HTML data-table alternative for every chart.

  * `aria-live="polite"` triggered **only** when the AQI category changes.

  * Accurate `lang` attributes (including Hindi/Hinglish spans + optional Hindi toggle).

## 8. Phase-Wise Implementation Plan & Hard Exit Gates

Execute **one phase at a time**. Do not start Phase $N+1$ until every exit gate command in Phase $N$ passes.

| Phase | Priority | Deliverables | Hard Exit Gate | 
| ----- | ----- | ----- | ----- | 
| **0. Foundation & Spec Lock** | Must | Repo scaffold, linters, `gitleaks` pre-commit, CI workflow, `.env.example`, `docs/adr/0001-*.md`, verified `config/constants.py`, `task_plan.md` / `findings.md` / `progress.md`, single-command `Makefile`/scripts. | `ruff`, `mypy --strict`, `tsc --noEmit`, `eslint`, `gitleaks` pass. | 
| **1. Deterministic Core Engines** | Must | `aqi/cpcb.py`, `exposure/dose.py`, `exposure/cadr.py`, `aqi/confidence.py` + unit, golden-value, & `Hypothesis` property tests (via Superpowers TDD). | `pytest` passes with $\ge 90\%$ coverage; CPCB boundary, monotonicity, and Serena pure-import checks green. | 
| **2. Live Data & Diurnal Profile** | Must + Should | `providers/base.py`, `providers/openaq.py`, `providers/cache.py` (L1+Supabase, single-flight coalescing), `aqi/diurnal.py` + recorded-fixture tests. | Live fetch, unit normalization, nearest-station fallback, stale cache, and absurd-sensor rejection tests pass. | 
| **3. Optimization Engines** | Must + Should | `exposure/optimizer.py`, `exposure/errands.py`, `exposure/commute.py` + Smog Episode & clean-air tests. | Deterministic permutation, fixed-window, Planet vs. Lungs, and Smog Episode tests pass. | 
| **4. GenAI Edge & API Layer** | Must + Should | `planner/schemas.py`, `planner/grok.py`, `planner/fallback.py`, `api/routes.py`, `api/security.py`, WhatsApp + Community brief templates, E2E FastAPI smoke tests. | Malformed-JSON fallback, prompt-delimiter, Smog N95/doctor-line, E2E smoke tests, and OpenAPI schema export pass. | 
| **5. Accessible Pillar UI** | Must + Should | `openapi-typescript` gen, 4 pillar directories, 3 Indian presets, Room CADR form, "Show the Math" drawer, Data Confidence badge, chart+table pairs. | `tsc --noEmit`, `eslint`, Testing Library, `jest-axe` (0 violations), and Playwright-MCP WCAG checks pass. | 
| **6. Optional "Could" Extensions** | Could | `planner/vision.py` (Room photo pre-fill + user confirm) & `providers/openmeteo.py` (labelled modelled forecast). | MIME/size/EXIF/non-room tests pass; modelled data strictly separated from live data. | 
| **7. Evaluation Hardening** | Must | Lighthouse CI ($\ge 95$), `pip-audit`, `npm audit`, Cloud Run config (`min-instances=1`), Secret Manager wiring, final `README.md` w/ diagram & traceability table. | Full CI green, Lighthouse A11y $\ge 95$, zero high-severity CVEs, clean `gitleaks` history scan. | 

## 9. Agent Execution Protocol

For every phase requested by the user:

1. **Plan & Sync State First:** Update `task_plan.md` (`Planning-with-files`), query **Context7** for any library/API docs needed in this phase, and output a concise 5–10 line **File & Verification Plan** before writing code.

2. **Implement Strictly in Scope:** Touch only files belonging to the active phase. Follow **Superpowers** `RED -> GREEN -> REFACTOR` TDD for all logic and use **Serena** to verify module isolation and symbol references.

3. **Run Real Verification:** Execute all gate commands for the phase (including **Playwright-MCP** accessibility checks in Phases 5 & 7) and paste exact pass/fail summaries (never claim tests pass without executing them).

4. **Phase Handoff Report:** Update `progress.md` and end with:

   * Files created/modified

   * Exact gate command results

   * Remaining `# VERIFY_BEFORE_PROD` items (if any)

   * Readiness check for the next phase

## 10. Operational Guardrails & Production Readiness

### 10.1 Code Quality & Tooling Guardrails

* **Single-command reproducible setup:** Provide and verify clean setup, lint, type-check, and test commands in one place (`Makefile` or unified `pyproject.toml` + `package.json` scripts) so automated graders can run the full verification suite without guessing flags.

* **No silent catches or mock fallbacks in production paths:** Never use `except Exception: pass` or silent zero/default returns in `aqi/`, `exposure/`, or `providers/`. Every fallback must explicitly propagate status (`live` | `stale` | `fallback_template`) and emit structured non-PII diagnostic logs.

* **Diff hygiene & surgical edits:** Keep every diff scoped to the active phase, avoid unrequested edits to unrelated files, and remove dead code or unused dependencies before phase sign-off.

### 10.2 Data, Unit & Math Integrity

* **Unit normalization before CPCB math:** OpenAQ sensors may report gases in different units (e.g., `ppm` vs. $\mu\text{g/m}^3$ or $\text{mg/m}^3$). Explicitly normalize and validate pollutant units *before* CPCB breakpoint interpolation (e.g., CPCB $\text{CO}$ breakpoints use $\text{mg/m}^3$).

* **CPCB averaging & pollutant clarity:** Clearly label whether station inputs represent spot/hourly readings or 24-hour / 8-hour windows alongside CPCB's multi-pollutant minimum rule (requiring at least one particulate parameter, $\text{PM}_{2.5}$ or $\text{PM}_{10}$).

* **Golden-value regression fixtures:** Lock in verified hand-calculated test cases (CPCB boundary edges such as $30/31$ and $60/61$, sub-index interpolation examples, and multi-stop errand ordering) so future refactors cannot silently shift numerical outputs.

### 10.3 Security & Cloud Run Readiness

* **Fail-closed configuration & safe error responses:** Validate required environment variables at startup (fail fast in non-test mode), enforce request body size limits on all POST/upload endpoints, and return generic, non-leaking HTTP error messages to clients.

* **Subprocess & path safety:** Forbid shell string interpolation (`shell=True`) in any helper or schema-generation scripts, and validate all file paths to prevent directory traversal outside the workspace.

### 10.4 Efficiency & Evaluation-Demo Stability

* **Single-flight / request coalescing:** Coalesce concurrent in-flight fetches for identical coordinates or household payloads so judging bursts do not stampede OpenAQ's $60$ req/min limit.

* **Strict outbound timeouts:** Enforce explicit connect and read timeouts on every OpenAQ, Supabase, and Grok HTTP call so a slow upstream dependency can never hang a worker or CI run.

### 10.5 End-to-End Smoke & Traceability Audit

* **API route smoke tests:** Alongside unit, `Hypothesis`, and `jest-axe` tests, run automated integration smoke tests against FastAPI routes using recorded OpenAQ/Grok fixtures to verify HTTP status codes, OpenAPI schema conformance, and fallback behavior.

* **Pre-submission traceability & honesty audit:** Before completing Phase 7, verify that every Challenge 6 requirement maps to a concrete module and test in `README.md`, and that all mandatory honesty caveats (Berkeley Earth heuristic, WHO/NAAQS reference lines, indoor plants footnote, fitted N95/FFP2 vs. cloth + doctor note in Very Poor/Severe AQI) appear in both backend schemas and rendered UI.