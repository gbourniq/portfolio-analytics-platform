codebase ?= portfolio_analytics
tests_dir ?= tests
cache_dirs := .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache
DOCKER_COMPOSE := $(shell which docker-compose > /dev/null 2>&1 && echo docker-compose || echo docker compose)


# Development

fmt:
	python3.12 -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive $(codebase) $(tests_dir)
	python3.12 -m isort --profile black --line-length 89 $(codebase) $(tests_dir)
	python3.12 -m black --line-length 89 --preview --enable-unstable-feature=string_processing $(codebase) $(tests_dir)
	python3.12 -m ruff check --fix $(codebase) $(tests_dir)

lint:
	python3.12 -m autoflake --check --quiet --recursive $(codebase)
	python3.12 -m isort --profile black --line-length 89 --check-only $(codebase)
	python3.12 -m black --line-length 89 --check $(codebase)
	python3.12 -m ruff check $(codebase)
	python3.12 -m mypy $(codebase)
	python3.12 -m flake8 --max-line-length 89 --max-doc-length 89 $(codebase)
	python3.12 -m pylint --fail-under=9.9 $(codebase)

clean:
	find . -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name "coverage.xml" \) -delete
	rm -rf $(cache_dirs)


# Unit Testing

test:
	python3.12 -m pytest --cov=$(codebase) -m "not integration" --cov-report html --cov-report xml

test-coverage: test
	cd htmlcov && python3.12 -m http.server


# Docker build

up:
	UID=$$(id -u) GID=$$(id -g) $(DOCKER_COMPOSE) up -d --build
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
	$(DOCKER_COMPOSE) logs && $(DOCKER_COMPOSE) down && exit 1

down:
	$(DOCKER_COMPOSE) down

build: up down


# Integration Testing

test-dashboard:
	docker build -t dash-app-tests . -f tests/integration/test_dashboard.Dockerfile
	docker run --rm dash-app-tests

test-api:
	make up
	pytest tests/integration -v -m api_integration
	make down
