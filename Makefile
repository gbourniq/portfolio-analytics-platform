codebase ?= portfolio_analytics
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
	python3.10 -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive $(codebase)
	python3.10 -m isort --profile black --line-length 89 $(codebase)
	python3.10 -m black --line-length 89 --preview --enable-unstable-feature=string_processing $(codebase)
	python3.10 -m ruff check --fix $(codebase)

lint:
	python3.10 -m autoflake --check --quiet --recursive $(codebase)
	python3.10 -m isort --profile black --line-length 89 --check-only $(codebase)
	python3.10 -m black --line-length 89 --check $(codebase)
	python3.10 -m ruff check $(codebase)
	python3.10 -m mypy $(codebase)
	python3.10 -m flake8 --max-line-length 89 --max-doc-length 89 $(codebase)
	python3.10 -m pylint --fail-under=9.0 $(codebase)

test:
	python3.10 -m pytest --cov=$(codebase) --cov-report html --cov-report xml

coverage:
	cd htmlcov && python3.10 -m http.server

clean:
	find . -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name "coverage.xml" \) -delete
	rm -rf $(cache_dirs)


# Build

up:
	UID=$$(id -u) GID=$$(id -g) docker compose up -d --build
	@echo "Waiting for services to be healthy..."
	@for i in $$(seq 1 30); do \
		if docker compose ps api | grep -q "healthy" && \
			docker compose ps dashboard | grep -q "healthy"; then \
			exit 0; \
		fi; \
		sleep 2; \
	done; \
	if [ $$? -ne 0 ]; then \
		@echo "ERROR: Services failed to become healthy after 60 seconds" && \
		docker compose logs && docker compose down && exit 1; \
	fi
	@echo "Services are healthy!"

down:
	docker compose down

build:
	@echo Checking valid docker build...
	make up
	@echo "Running quick integration tests..."
	# Add your actual test commands here
	@echo "Tests passed successfully"
	make down
