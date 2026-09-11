.PHONY: help install dev run test lint docker-build docker-run report clean

help:
	@echo "install       Install runtime dependencies"
	@echo "dev           Install runtime + development dependencies"
	@echo "run           Start the API on http://localhost:7860"
	@echo "test          Run the test suite"
	@echo "lint          Run ruff"
	@echo "docker-build  Build the container image"
	@echo "docker-run    Run the container with .env"
	@echo "report        Regenerate the project report PDF"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

run:
	PYTHONPATH=src uvicorn finagent.app:app --host 0.0.0.0 --port 7860 --reload

test:
	PYTHONPATH=src pytest -q

lint:
	ruff check src tests

docker-build:
	docker build -t finagent:latest .

docker-run:
	docker run --rm -p 7860:7860 --env-file .env finagent:latest

report:
	python docs/report/build_report.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
