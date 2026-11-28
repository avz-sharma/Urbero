# Audit verification output

Python tools use `python -m` to avoid Windows launcher DLL failures.


## Backend: ruff check .

```text
All checks passed!

Exit code: 0
```


## Backend: mypy --strict app

```text
Success: no issues found in 32 source files

Exit code: 0
```


## Backend: pytest --cov=app --cov-report=term-missing

```text
........................................................................ [ 50%]
.......................................................................  [100%]
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
app\api\routes.py               124      7    94%   67, 148, 197-198, 220-222
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
app\exposure\dose.py             32      0   100%
app\exposure\errands.py          95      6    94%   81, 95, 115, 117, 119, 121
app\exposure\optimizer.py       121      7    94%   38, 100-102, 106, 176, 178
app\exposure\transit.py           4      0   100%
app\planner\__init__.py           0      0   100%
app\planner\fallback.py          53      8    85%   52-64, 134-139
app\planner\grok.py             122      8    93%   127-128, 172, 186, 342-349
app\planner\schemas.py          156      0   100%
app\planner\vision.py            42      3    93%   102-104
app\providers\__init__.py         0      0   100%
app\providers\base.py            49      3    94%   35, 38, 40
app\providers\cache.py          148     11    93%   58, 72-73, 151, 165-167, 184, 196-197, 217
app\providers\geocoding.py      176     16    91%   125, 149, 165, 238-240, 270, 275, 306-313, 376
app\providers\openmeteo.py      106      7    93%   74-75, 95, 101, 117, 124, 183
app\providers\pipeline.py        24      1    96%   45
app\providers\resilience.py      41      2    95%   48, 58
app\providers\waqi.py            61      7    89%   42, 63-64, 74, 82, 95, 116
-----------------------------------------------------------
TOTAL                          1822    101    94%
143 passed, 1 warning in 10.76s

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
      Tests  56 passed (56)
   Start at  11:57:15
   Duration  20.91s (environment 32%, import 28%, tests 24%, setup 15%, transform 1%)

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
dist/index.html                        0.71 kB │ gzip:   0.42 kB
dist/assets/index-R0fhdGn4.css        47.98 kB │ gzip:   9.27 kB
dist/assets/CommuteBars-CHz8Msno.js    2.89 kB │ gzip:   1.00 kB
dist/assets/index-G2DP5XPS.js        351.66 kB │ gzip: 109.45 kB
✓ built in 7.97s

Exit code: 0
```
