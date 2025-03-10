#!/bin/bash

# Shared volume to store data
docker volume create shared-data

echo "Deploying application version ${GIT_TAG:-latest}"

# Data service
docker run -d \
  --name data \
  --user 1000:1000 \
  -v shared-data:/data:rw \
  ghcr.io/gbourniq/portfolio_analytics/data:${GIT_TAG:-latest}

# Dashboard service
docker run -d \
  --name dashboard \
  --user 1000:1000 \
  --group-add 1000 \
  -p 8050:8050 \
  -v shared-data:/app/data:rw \
  ghcr.io/gbourniq/portfolio_analytics/dashboard:${GIT_TAG:-latest}

# API service
docker run -d \
  --name api \
  --user 1000:1000 \
  --group-add 1000 \
  -p 8000:8000 \
  -v shared-data:/app/data:rw \
  ghcr.io/gbourniq/portfolio_analytics/api:${GIT_TAG:-latest}
