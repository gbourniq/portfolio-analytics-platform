#!/bin/bash

# Shared volume to store data
docker volume create shared-data

echo "Deploying application version ${GIT_TAG:-latest}"

# Data service
docker run -d \
  --name data \
  --user appuser:appuser \
  -v shared-data:/data \
  ghcr.io/gbourniq/portfolio_analytics/data:${GIT_TAG:-latest}

# Dashboard service
docker run -d \
  --name api \
  --user appuser:appuser \
  -v shared-data:/app/data \
  -p 8000:8000 \
  ghcr.io/gbourniq/portfolio_analytics/api:${GIT_TAG:-latest}

# API service
docker run -d \
  --name dashboard \
  --user appuser:appuser \
  -v shared-data:/app/data \
  -p 8050:8050 \
  ghcr.io/gbourniq/portfolio_analytics/dashboard:${GIT_TAG:-latest}
