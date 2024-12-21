FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/portfolio_analytics

# Add labels
LABEL maintainer="guillaume.bournique@gmail.com" \
    description="Base Python image for Portfolio Analytics" \
    org.opencontainers.image.source="https://github.com/gbourniq/portfolio_analytics"

# Install common system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    htop \
    vim \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create user with explicit UID/GID
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install poetry
RUN python3.12 -m pip install poetry==1.8.5 && \
    poetry config virtualenvs.create false
