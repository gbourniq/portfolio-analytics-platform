# Portfolio Analytics Platform

[![CI/CD](https://github.com/gbourniq/portfolio-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/gbourniq/portfolio-analytics/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pylint Score](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/gbourniq/b149841cbef1088a8bf7671efee16734/raw/pylint.txt)](https://github.com/gbourniq/portfolio-analytics/actions)
[![Code Coverage](https://codecov.io/gh/gbourniq/portfolio-analytics/graph/badge.svg?token=O5LIL4YV9L)](https://codecov.io/gh/gbourniq/portfolio-analytics)

🌐 **Live Demo**: [dashboard.portfolio-analytics.click](https://dashboard.portfolio-analytics.click)

## Overview

A comprehensive portfolio management solution consisting of two main components:

### Interactive Dashboard

![Dashboard Interface](.github/images/dashboard.png)

- Real-time portfolio performance visualization
- Key metrics tracking (Sharpe ratio, drawdown, PnL)
- Currency conversion support
- Customizable time period analysis

### REST API

![API Documentation](.github/images/api.png)

- Portfolio management operations (create, list, delete)
- Market data integration for FX and Equity
- System health monitoring
- OpenAPI 3.1 compliant

### Expected input

The dashboard analyzes portfolio positions across multiple stock exchanges, accepting input data (csv, xlsx, parquet) in the following format:

| Date       | AAPL | ABBV | ... | SHEL.L | DHL.DE | BNP.PA |
| ---------- | ---- | ---- | --- | ------ | ------ | ------ |
| 2018-01-01 | 52   | 79   | ... | 104    | 165    | 90     |
| 2018-01-02 | 122  | 95   | ... | 100    | 6      | 93     |
| 2018-01-03 | 86   | 199  | ... | 152    | 90     | 159    |
| ...        | ...  | ...  | ... | ...    | ...    | ...    |
| 2024-12-19 | 133  | 105  | ... | 39     | 187    | 78     |

## Getting Started

### Quick Start with Docker

Run application locally for development/CI
```bash
docker-compose up -d --build
```

Run the app in production
```bash
GIT_TAG=v0.1.28 ./run.sh
```

### Local Development

1. Install dependencies:

```bash
python3.12 -m pip install poetry -U
poetry install --sync --no-interaction
```

2. Start services:

```bash
python portfolio_analytics/dashboard/dashboard_main.py
python portfolio_analytics/api/api_main.py
```

### CI

![CI](.github/images/ci.png)

## Future Improvements

### Data Pipeline

- Add historical index constituents tracking via a point-in-time security master database

### API Enhancements

- Implement asynchronous pipeline execution with DynamoDB tracking
- Add paginated portfolio listing endpoints

### Storage Optimization

- Migrate to S3 for blob storage
- Implement S3 pre-signed URLs for portfolio file operations

### Infrastructure

- Deploy containers to ECS or Kubernetes for improved scalability
- Implement automated pipeline scheduling system (Airflow). Currently relying on triggering the APIs manually.
