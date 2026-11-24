"""Run the seven requested gates and retain complete, reviewable command output."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_coverage_badge(output: str) -> None:
    total = re.search(r"^TOTAL\s+\d+\s+\d+\s+(\d+%)", output, re.MULTILINE)
    if total is None:
        return
    coverage = total[1]
    color = "#176b47" if int(coverage[:-1]) >= 90 else "#a32020"
    (ROOT / "docs" / "coverage.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="150" height="22" role="img" '
        f'aria-label="Backend coverage: {coverage}">\n'
        '<rect width="150" height="22" rx="4" fill="#263238"/>\n'
        f'<rect x="104" width="46" height="22" rx="4" fill="{color}"/>\n'
        '<g fill="white" font-family="sans-serif" font-size="11" text-anchor="middle">\n'
        '<text x="52" y="15">backend coverage</text>\n'
        f'<text x="127" y="15">{coverage}</text>\n'
        '</g>\n</svg>\n',
        encoding="utf-8",
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    commands = [
        ("Backend: ruff check .", ROOT / "backend", [sys.executable, "-m", "ruff", "check", "."]),
        (
            "Backend: mypy --strict app",
            ROOT / "backend",
            [sys.executable, "-m", "mypy", "--strict", "app"],
        ),
        (
            "Backend: pytest --cov=app --cov-report=term-missing",
            ROOT / "backend",
            [sys.executable, "-m", "pytest", "--cov=app", "--cov-report=term-missing"],
        ),
    ]
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    commands.extend(
        (f"Frontend: npm {action}", ROOT / "frontend", [npm, *action.split()])
        for action in ("run typecheck", "run lint", "test", "run build")
    )
    log = [
        "# Audit verification output\n",
        "Python tools use `python -m` to avoid Windows launcher DLL failures.\n",
    ]
    failed = False
    for label, cwd, args in commands:
        print(f"\n{label}", flush=True)
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        output = result.stdout + result.stderr
        print(output, flush=True)
        print(f"Exit code: {result.returncode}", flush=True)
        log.append(f"\n## {label}\n\n```text\n{output}\nExit code: {result.returncode}\n```\n")
        if "-m" in args and "pytest" in args:
            write_coverage_badge(output)
        failed |= result.returncode != 0
    (ROOT / "docs" / "audit-verification.md").write_text("\n".join(log), encoding="utf-8")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
