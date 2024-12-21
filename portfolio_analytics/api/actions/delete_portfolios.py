"""FastAPI endpoints for deleting portfolio files.

Provides functionality to delete uploaded portfolio files while
preserving sample portfolios.
"""

from http import HTTPStatus
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from portfolio_analytics.api.common import ApiTag
from portfolio_analytics.common.filesystem import (
    PORTFOLIO_UPLOADS_DIR,
    cleanup_cache,
    cleanup_portfolio_uploads,
    get_portfolio_files,
)
from portfolio_analytics.common.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

router = APIRouter(prefix="", tags=[str(ApiTag.PORTFOLIO_MANAGEMENT)])


class DeletePortfoliosResponse(BaseModel):
    """Response model for portfolio deletion operations.

    Contains a status message about the operation.
    """

    message: str = Field(..., description="Status message of the operation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Successfully deleted 5 portfolio files (except samples)"
            }
        }
    }


example_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "examples": {
                    "files_deleted": {
                        "value": {"message": "Successfully deleted 5 portfolio files"}
                    },
                    "no_files": {
                        "value": {"message": "No portfolio files found to delete"}
                    },
                }
            }
        },
    }
}


@router.delete(
    "/portfolio",
    response_model=DeletePortfoliosResponse,
    status_code=HTTPStatus.OK,
    responses=example_responses,
)
async def delete_portfolios() -> DeletePortfoliosResponse:
    """Delete all uploaded portfolio files.

    Deletes all portfolio files in the uploads directory,
    except for the sample files in the samples subdirectory.

    **Returns:**
    * `DeletePortfoliosResponse`: Object containing:
        * message: Status message confirming the operation with number of files deleted
    """
    # Get count of files before deletion
    num_files_deleted = len(
        [f for f in get_portfolio_files() if f.parent == PORTFOLIO_UPLOADS_DIR]
    )

    if num_files_deleted == 0:
        log.info("No portfolio files found to delete")
        return DeletePortfoliosResponse(message="No portfolio files found to delete")

    # Perform cleanup
    cleanup_portfolio_uploads()
    cleanup_cache()

    log.info(f"Deleted {num_files_deleted} portfolio files (except samples)")

    return DeletePortfoliosResponse(
        message=(
            f"Successfully deleted {num_files_deleted} portfolio files (except samples)"
        )
    )
