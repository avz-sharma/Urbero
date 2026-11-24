"""Export FastAPI OpenAPI JSON schema to docs/openapi.json."""

import json
import sys
from pathlib import Path

# Ensure root directory is on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


def export_openapi() -> None:
    from backend.app.api.routes import app

    schema = app.openapi()
    out_dir = root_dir / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "openapi.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Exported OpenAPI schema to {out_file}")


if __name__ == "__main__":
    export_openapi()
