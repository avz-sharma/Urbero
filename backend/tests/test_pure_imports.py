"""Verification tests ensuring aqi/ and exposure/ remain completely pure (zero I/O)."""

import ast
from pathlib import Path

FORBIDDEN_MODULES = {
    "socket",
    "http",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "sqlite3",
    "psycopg2",
    "asyncpg",
    "sqlalchemy",
    "google",
    "openai",
    "anthropic",
    "supabase",
    "slowapi",
}


def test_pure_modules_have_zero_io_imports() -> None:
    """Check AST of all modules under aqi/ and exposure/ for I/O and network packages."""
    app_root = Path(__file__).resolve().parent.parent / "app"
    pure_dirs = [app_root / "aqi", app_root / "exposure"]

    for d in pure_dirs:
        for py_file in d.glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top_pkg = alias.name.split(".")[0]
                        assert top_pkg not in FORBIDDEN_MODULES, (
                            f"Pure module {py_file.name} imports forbidden I/O package: {alias.name}"
                        )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    top_pkg = node.module.split(".")[0]
                    assert top_pkg not in FORBIDDEN_MODULES, (
                        f"Pure module {py_file.name} imports forbidden I/O package: {node.module}"
                    )
