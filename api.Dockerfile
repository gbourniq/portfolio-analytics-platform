FROM ghcr.io/gbourniq/portfolio_analytics/python-base:3.12-slim

# Add labels
LABEL description="Portfolio Analytics API"

# Install dependencies
COPY pyproject.toml ./pyproject.toml
RUN poetry install --only main,api

# Copy source code to the container
COPY portfolio_analytics/common/utils portfolio_analytics/common/utils
COPY portfolio_analytics/api portfolio_analytics/api

# Set ownership and switch to non-root user
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
