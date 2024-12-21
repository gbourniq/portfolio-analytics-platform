"""Exception handling module for the Portfolio Analytics API."""

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse

from portfolio_analytics.common.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)


class PortfolioAnalyticsError(Exception):
    """Base exception for all portfolio analytics errors."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# Data Related Errors
class DataNotFoundError(PortfolioAnalyticsError):
    """Raised when required data is not found."""

    status_code = HTTPStatus.NOT_FOUND


class DataValidationError(PortfolioAnalyticsError):
    """Raised when data validation fails."""

    status_code = HTTPStatus.BAD_REQUEST


# Market Data Errors
class MarketDataFetchError(PortfolioAnalyticsError):
    """Raised when failing to fetch market data."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE


class MarketDataProcessingError(PortfolioAnalyticsError):
    """Raised when failing to process market data."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


# Portfolio Errors
class PortfolioValidationError(PortfolioAnalyticsError):
    """Raised when portfolio validation fails."""

    status_code = HTTPStatus.BAD_REQUEST


class PortfolioProcessingError(PortfolioAnalyticsError):
    """Raised when portfolio processing fails."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


# API Errors
class RateLimitError(PortfolioAnalyticsError):
    """Raised when rate limit is exceeded."""

    status_code = HTTPStatus.TOO_MANY_REQUESTS


class ResourceNotFoundError(PortfolioAnalyticsError):
    """Raised when a resource is not found."""

    status_code = HTTPStatus.NOT_FOUND


class BadRequestError(PortfolioAnalyticsError):
    """Raised when user input is invalid."""

    status_code = HTTPStatus.BAD_REQUEST


async def portfolio_analytics_exception_handler(
    request: Request, exc: PortfolioAnalyticsError
) -> JSONResponse:
    """Central error handler for all portfolio analytics errors.

    Args:
        request: FastAPI request object containing the incoming request details.
        exc: Portfolio analytics exception that was raised.

    Returns:
        JSONResponse: Error response containing the error message and appropriate
            HTTP status code.
    """
    log.error(
        f"Error handling request: {exc.message}",
        extra={
            "error_type": exc.__class__.__name__,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})
