FROM python:3.12-slim

WORKDIR /app

# Install Python packages
RUN pip install --no-cache-dir pytest requests

# Copy test files
COPY tests/integration/test_api.py ./test_api.py

# Set Python path
ENV PYTHONPATH=/app

# Run tests
CMD ["pytest", "test_api.py", "-v", "-m", "api_integration"]
