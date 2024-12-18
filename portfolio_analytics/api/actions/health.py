"""FastAPI endpoints for health checks.

Provides functionality to check the API's health status.
"""

from http import HTTPStatus
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from portfolio_analytics.api.common import ApiTag
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

router = APIRouter(prefix="", tags=[str(ApiTag.SYSTEM)])


class HealthResponse(BaseModel):
    """Response model for health check endpoint.

    Contains basic health status information.
    """

    status: str = Field(..., description="Health status of the API")
    version: str = Field(..., description="API version")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
            }
        }
    }


example_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "status": "healthy",
                    "version": "1.0.0",
                }
            }
        },
    }
}


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=HTTPStatus.OK,
    responses=example_responses,
)
async def health_check() -> HealthResponse:
    """Check the health status of the API.

    Returns basic health information about the API.

    **Returns:**
    * `HealthResponse`: Object containing:
        * status: Current health status
        * version: API version
    """
    log.debug("Health check requested")

    return HealthResponse(
        status="healthy",
        version="1.0.0",  # You might want to import this from a version.py file
    )
