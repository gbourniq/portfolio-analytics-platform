FROM ghcr.io/gbourniq/portfolio_analytics/python-base:3.12-slim

# Add labels
LABEL description="Portfolio Analytics Dashboard"

# Install dependencies
COPY pyproject.toml ./pyproject.toml
RUN poetry install --only main,dashboard

# Copy source code to the container
COPY portfolio_analytics/common portfolio_analytics/common
COPY portfolio_analytics/dashboard portfolio_analytics/dashboard

# Set ownership and switch to non-root user
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
     "--workers", "2", \
     "--threads", "4", \
     "--worker-class", "gthread", \
     "--worker-tmp-dir", "/dev/shm", \
     "--log-level", "info"]
