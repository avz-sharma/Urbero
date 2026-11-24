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
........................................................................ [ 62%]
...........................................                              [100%]
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
app\api\locations.py             19      1    95%   31
app\api\routes.py               154      6    96%   162, 283-284, 361-363
app\api\security.py              69      2    97%   61, 79
app\aqi\__init__.py               0      0   100%
app\aqi\confidence.py            57      0   100%
app\aqi\cpcb.py                  76      3    96%   49, 77, 94
app\aqi\diurnal.py               58      1    98%   97
app\config\__init__.py            0      0   100%
app\config\constants.py          29      0   100%
app\exposure\__init__.py          0      0   100%
app\exposure\cadr.py             44      2    95%   52, 54
app\exposure\commute.py          46      1    98%   98
app\exposure\dose.py             32      1    97%   53
app\exposure\errands.py          85      5    94%   70, 72, 74, 76, 107
app\exposure\optimizer.py       118      8    93%   38, 93, 95, 114-116, 120, 171
app\exposure\transit.py           4      0   100%
app\planner\__init__.py           0      0   100%
app\planner\fallback.py          52      9    83%   51-64, 135-140
app\planner\gemini.py            34      3    91%   22, 28, 47
app\planner\grok.py             101     20    80%   144, 160, 195-220, 245, 284
app\planner\schemas.py          132      0   100%
app\planner\vision.py            45      4    91%   51, 108-110
app\providers\__init__.py         0      0   100%
app\providers\base.py            49      3    94%   35, 38, 40
app\providers\cache.py          151     17    89%   57-58, 72-73, 151, 165-167, 193, 213, 230-233, 239-241
app\providers\geocoding.py      172     14    92%   161-162, 178, 220, 263, 285, 290, 321-328
app\providers\openmeteo.py      102      8    92%   46-47, 66-67, 86, 107, 114, 173
app\providers\pipeline.py        24      1    96%   45
app\providers\resilience.py      27      2    93%   26, 36
app\providers\waqi.py            61      7    89%   42, 63-64, 74, 82, 95, 116
-----------------------------------------------------------
TOTAL                          1741    118    93%
115 passed, 1 warning in 11.15s

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
      Tests  49 passed (49)
   Start at  22:25:36
   Duration  15.40s (import 34%, environment 27%, tests 23%, setup 15%, transform 1%)


Exit code: 0
```


## Frontend: npm run build

```text

> urbero-frontend@0.1.0 build
> tsc && vite build

vite v6.4.6 building for production...
transforming...
✓ 2591 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.94 kB │ gzip:   0.51 kB
dist/assets/index-DZDUG0RS.css        48.70 kB │ gzip:   9.40 kB
dist/assets/CommuteBars-D4UfjfNc.js    3.07 kB │ gzip:   1.04 kB
dist/assets/index-CAjl9X8B.js        355.33 kB │ gzip: 109.59 kB
✓ built in 7.69s

Exit code: 0
```
