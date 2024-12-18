codebase ?= portfolio_analytics
tests_dir ?= tests
cache_dirs := .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache


# Development

install-poetry:
	python3.10 -m pip install poetry -U

generate-lockfiles:
	python3.10 -m poetry lock
	python3.10 -m poetry export --with=api,dashboard,dev -f requirements.txt --without-hashes -o requirements.txt
	python3.10 -m poetry export --with=api -f requirements.txt -o portfolio_analytics/api/requirements.txt
	python3.10 -m poetry export --with=dashboard -f requirements.txt -o portfolio_analytics/dashboard/requirements.txt

install-deps:
	python3.10 -m pip install -e . -r requirements.txt

fmt:
	python3.10 -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive $(codebase) $(tests_dir)
	python3.10 -m isort --profile black --line-length 89 $(codebase) $(tests_dir)
	python3.10 -m black --line-length 89 --preview --enable-unstable-feature=string_processing $(codebase) $(tests_dir)
	python3.10 -m ruff check --fix $(codebase) $(tests_dir)

lint:
	python3.10 -m autoflake --check --quiet --recursive $(codebase)
	python3.10 -m isort --profile black --line-length 89 --check-only $(codebase)
	python3.10 -m black --line-length 89 --check $(codebase)
	python3.10 -m ruff check $(codebase)
	python3.10 -m mypy $(codebase)
	python3.10 -m flake8 --max-line-length 89 --max-doc-length 89 $(codebase)
	python3.10 -m pylint --fail-under=9.9 $(codebase)

clean:
	find . -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name "coverage.xml" \) -delete
	rm -rf $(cache_dirs)


# Unit Testing

test:
	python3.10 -m pytest --cov=$(codebase) -m "not integration" --cov-report html --cov-report xml

test-coverage: test
	cd htmlcov && python3.10 -m http.server


# Docker

up:
	UID=$$(id -u) GID=$$(id -g) docker compose up -d --build
	@echo "Waiting for services to be healthy..."
	@end_time=$$(( $$(date +%s) + 60 )); \
	while [ $$(date +%s) -lt $$end_time ]; do \
		if curl -s http://localhost:8000/health > /dev/null; then \
			echo "Services are healthy!" && exit 0; \
		fi; \
		echo "Waiting for services to become healthy..."; \
		sleep 1; \
	done; \
	echo "ERROR: Services failed to become healthy after 60 seconds" && \
	docker compose logs && docker compose down && exit 1

down:
	docker compose down

build: up down


# Integration Testing

integration-test:
	@echo "Running quick integration tests..."
	pytest tests/integration -v -m integration
	@echo "Tests passed successfully"
