FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/portfolio_analytics

# Add labels
LABEL maintainer="guillaume.bournique@gmail.com" \
description="Portfolio Analytics API"

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./pyproject.toml
RUN python3.12 -m pip install poetry==1.8.5 && \
    poetry config virtualenvs.create false && \
    poetry install --only main,api

# Copy source code to the container
COPY portfolio_analytics/common/utils portfolio_analytics/common/utils
COPY portfolio_analytics/api portfolio_analytics/api

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/ || exit 1

# Command for production server
CMD ["uvicorn", "portfolio_analytics.api.api_main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--timeout-keep-alive", "120", \
     "--log-level", "info"]
