"""Secret and token leak scanner for Urbero workspace.

Scans backend and frontend source files against regex patterns for high-entropy tokens,
API keys, and private credentials.
"""

import re
import sys
from pathlib import Path

LEAK_PATTERNS = [
    re.compile(r"(?i)AIza[0-9A-Za-z-_]{35}"),  # Google API key
    re.compile(r"(?i)ghp_[0-9a-zA-Z]{36}"),  # GitHub personal token
    re.compile(r"(?i)sk-[a-zA-Z0-9]{20,48}"),  # OpenAI / generic secret key
    re.compile(r"(?i)sbp_[a-zA-Z0-9]{40}"),  # Supabase service role key
]

IGNORE_DIRS = {".git", "node_modules", "dist", ".system_generated", "fixtures"}
TARGET_EXTS = {".py", ".ts", ".tsx", ".js", ".json", ".env"}


def scan_workspace(root_dir: Path) -> list[str]:
    violations: list[str] = []

    for path in root_dir.rglob("*"):
        if path.is_file():
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if path.suffix not in TARGET_EXTS and path.name != ".env":
                continue
            if path.name == ".env.example":
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for line_no, line in enumerate(content.splitlines(), start=1):
                    for pattern in LEAK_PATTERNS:
                        if pattern.search(line):
                            violations.append(f"{path}:{line_no}: Potential secret match")
            except OSError as err:
                violations.append(f"Could not read {path}: {err}")

    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = scan_workspace(root)

    if violations:
        print("FAIL: Secrets or unmasked credentials detected:")
        for v in violations:
            print(f"  {v}")
        return 1

    print("PASS: Secret scan clean (0 leaks detected).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
