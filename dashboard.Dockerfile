FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/portfolio_analytics

# Add labels
LABEL maintainer="guillaume.bournique@gmail.com" \
version="1.0" \
description="Portfolio Analytics Dashboard"

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install dependencies
COPY portfolio_analytics/dashboard/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy source code to the container
COPY portfolio_analytics/common/utils portfolio_analytics/common/utils
COPY portfolio_analytics/dashboard portfolio_analytics/dashboard

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8050/ || exit 1

# Command for production server
CMD ["gunicorn", "portfolio_analytics.dashboard.dashboard_main:server", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "4", \
     "--log-level", "info"]
