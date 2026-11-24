.PHONY: all setup lint typecheck test verify generate-api
all: verify
setup:
	python -m pip install -e ".[dev]"
	cd frontend && npm ci
lint:
	python -m ruff check .
	cd frontend && npm run lint
typecheck:
	python -m mypy --strict backend/app
	cd frontend && npm run typecheck
test:
	cd backend && python -m pytest --cov=app
	cd frontend && npm test
verify:
	python scripts/verify.py
generate-api:
	cd frontend && npm run generate:api
