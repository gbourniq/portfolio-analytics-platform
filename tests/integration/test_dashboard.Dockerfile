FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages directly
RUN pip install --no-cache-dir \
    dash==2.11.0 \
    "dash[testing]" \
    pytest \
    selenium \
    dash-bootstrap-components \
    plotly \
    python-dateutil \
    pandas

# Copy files to container
COPY pyproject.toml ./pyproject.toml
COPY tests/integration/test_dashboard.py ./test_dashboard.py

# Set environment variables for Dash testing
ENV DASH_TESTING_ENV=CI
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONPATH=/app

# Run tests
CMD ["pytest", "--headless", "--disable-warnings", "test_dashboard.py", "-x", "-v"]
