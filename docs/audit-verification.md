# Audit verification output

Python tools use `python -m` to avoid Windows launcher DLL failures.

## Second evaluation candidate checks

- Ruff C901 passed at the default threshold. Geocoding went from 24 to 7, errands from 15 to 10, routine optimization from 15 to 7, cache coalescing from 14 to 7, and confidence scoring from 12 to 6.
- AQI and exposure coverage was 95.29%, with every module at 90% or higher. OpenAPI and TypeScript regeneration produced no diff. Prettier passed on the edited frontend files.
- Chromium passed the four light/dark and 390/1440 px combinations, the FastAPI recorded-provider errand and room flows, and the expected provider-outage state. There were zero axe violations, CSP violations, or uncaught page errors. The outage produced its expected HTTP 503.
- Lighthouse accessibility scored 100 for both landing configurations. The recorded-provider workspace scored 100 at light/390 px and 96 at dark/1440 px.
- `pip-audit` and `npm audit --audit-level=high` found no known vulnerabilities. Gitleaks reported no leaks in the scanned history.
- The initial client bundle is 110.06 kB gzip compared with 109.59 kB at baseline. The lazy commute chart stayed at 1.04 kB gzip. Two warm-cache runs of 50 daily-plan requests had median/p95 latencies of 3.05/4.89 ms and 3.38/5.24 ms, versus 4.41/5.73 ms and 3.89/5.53 ms at baseline. These timings use recorded CAMS data and disabled model generation.


## Backend: ruff check .

```text
All checks passed!

Exit code: 0
```


## Backend: mypy --strict app

```text
Success: no issues found in 33 source files

Exit code: 0
```


## Backend: pytest --cov=app --cov-report=term-missing

```text
........................................................................ [ 51%]
....................................................................     [100%]
============================== warnings summary ===============================
tests\test_api_failures.py:7
  C:\PROMPTWARS\Urbero\backend\tests\test_api_failures.py:7: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.9-final-0 _______________

Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
app\__init__.py                   0      0   100%
app\api\__init__.py               0      0   100%
app\api\daily_plan.py            61      5    92%   41-43, 66-67
app\api\locations.py             19      1    95%   31
app\api\routes.py               121      7    94%   67, 145, 199-200, 222-224
app\api\security.py              78      2    97%   69, 87
app\aqi\__init__.py               0      0   100%
app\aqi\confidence.py            54      0   100%
app\aqi\cpcb.py                  76      3    96%   49, 77, 94
app\aqi\diurnal.py               58      1    98%   97
app\config\__init__.py            0      0   100%
app\config\constants.py          29      0   100%
app\exposure\__init__.py          0      0   100%
app\exposure\cadr.py             47      2    96%   55, 57
app\exposure\commute.py          46      1    98%   98
app\exposure\dose.py             32      1    97%   53
app\exposure\errands.py          93      6    94%   78, 92, 112, 114, 116, 118
app\exposure\optimizer.py       121      7    94%   38, 100-102, 106, 176, 178
app\exposure\transit.py           4      0   100%
app\planner\__init__.py           0      0   100%
app\planner\fallback.py          54      9    83%   51-64, 135-140
app\planner\gemini.py            36      2    94%   31, 37
app\planner\grok.py             130     22    83%   131, 170, 186, 221-246, 271, 352, 372
app\planner\schemas.py          153      0   100%
app\planner\vision.py            45      4    91%   51, 108-110
app\providers\__init__.py         0      0   100%
app\providers\base.py            49      3    94%   35, 38, 40
app\providers\cache.py          148     11    93%   58, 72-73, 151, 165-167, 184, 196-197, 217
app\providers\geocoding.py      184     16    91%   137, 161, 177, 250-252, 282, 287, 318-325, 388
app\providers\openmeteo.py      102      8    92%   46-47, 66-67, 86, 107, 114, 173
app\providers\pipeline.py        24      1    96%   45
app\providers\resilience.py      27      2    93%   26, 36
app\providers\waqi.py            61      7    89%   42, 63-64, 74, 82, 95, 116
-----------------------------------------------------------
TOTAL                          1852    121    93%
140 passed, 1 warning in 13.01s

Exit code: 0
```


## Frontend: npm run typecheck

```text

> urbero-frontend@0.1.0 typecheck
> tsc --noEmit


Exit code: 0
```


## Frontend: npm run lint

```text

> urbero-frontend@0.1.0 lint
> eslint . --max-warnings 0


Exit code: 0
```


## Frontend: npm test

```text

> urbero-frontend@0.1.0 test
> vitest run


 RUN  v5.1.1 C:/PROMPTWARS/Urbero/frontend


 Test Files  9 passed (9)
      Tests  51 passed (51)
   Start at  23:52:36
   Duration  21.27s (environment 32%, import 29%, tests 20%, setup 16%, transform 2%, worker 1%)

Error: Not implemented: window.scrollTo
    at module.exports (C:\PROMPTWARS\Urbero\frontend\node_modules\jsdom\lib\jsdom\browser\not-implemented.js:9:17)
    at C:\PROMPTWARS\Urbero\frontend\node_modules\jsdom\lib\jsdom\browser\Window.js:960:7
    at file:///C:/PROMPTWARS/Urbero/frontend/node_modules/motion-dom/dist/es/animation/keyframes/KeyframesResolver.mjs:56:24
    at Array.forEach (<anonymous>)
    at measureAllKeyframes (file:///C:/PROMPTWARS/Urbero/frontend/node_modules/motion-dom/dist/es/animation/keyframes/KeyframesResolver.mjs:54:28)
    at triggerCallback (file:///C:/PROMPTWARS/Urbero/frontend/node_modules/motion-dom/dist/es/frameloop/render-step.mjs:36:29)
    at Set.forEach (<anonymous>)
    at Object.process (file:///C:/PROMPTWARS/Urbero/frontend/node_modules/motion-dom/dist/es/frameloop/render-step.mjs:85:23)
    at processBatch (file:///C:/PROMPTWARS/Urbero/frontend/node_modules/motion-dom/dist/es/frameloop/batcher.mjs:35:26)
    at invokeTheCallbackFunction (C:\PROMPTWARS\Urbero\frontend\node_modules\jsdom\lib\jsdom\living\generated\Function.js:19:26) undefined

Exit code: 0
```


## Frontend: npm run build

```text

> urbero-frontend@0.1.0 build
> tsc && vite build

vite v6.4.6 building for production...
transforming...
✓ 2593 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.65 kB │ gzip:   0.38 kB
dist/assets/index-R0fhdGn4.css        47.98 kB │ gzip:   9.27 kB
dist/assets/CommuteBars-BEbGX2Vw.js    3.07 kB │ gzip:   1.04 kB
dist/assets/index-BWgzaHbL.js        352.36 kB │ gzip: 110.06 kB
✓ built in 7.03s

Exit code: 0
```
