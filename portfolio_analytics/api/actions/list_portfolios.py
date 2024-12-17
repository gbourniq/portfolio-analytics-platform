"""FastAPI endpoints for listing available portfolio files.

Provides functionality to retrieve metadata about available portfolio files.
"""

from http import HTTPStatus
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from portfolio_analytics.api.common import ApiTag
from portfolio_analytics.common.utils.filesystem import get_portfolio_files
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

router = APIRouter(prefix="", tags=[str(ApiTag.PORTFOLIO_MANAGEMENT)])


class PortfolioFile(BaseModel):
    """Model representing a portfolio file's metadata.

    Contains basic file information like name and size.
    """

    filename: str = Field(..., description="Name of the portfolio file")
    size: int = Field(..., description="Size of the file in bytes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "my_portfolio.csv",
                "size": 1024,
            }
        }
    }


class PortfolioListResponse(BaseModel):
    """Response model for listing portfolio files.

    Contains a list of portfolio file metadata.
    """

    portfolios: list[PortfolioFile] = Field(
        ..., description="List of available portfolio files"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "portfolios": [
                    {
                        "filename": "portfolio1.csv",
                        "size": 1024,
                    },
                    {
                        "filename": "portfolio2.xlsx",
                        "size": 2048,
                    },
                ]
            }
        }
    }


example_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "portfolios": [
                        {
                            "filename": "portfolio1.csv",
                            "size": 1024,
                        },
                        {
                            "filename": "portfolio2.xlsx",
                            "size": 2048,
                        },
                    ]
                }
            }
        },
    }
}


def create_portfolio_file_response(file_path: Path) -> PortfolioFile:
    """Create a PortfolioFile response object from a file path.

    Args:
        file_path: Path to the portfolio file

    Returns:
        PortfolioFile: Object containing file metadata
    """
    return PortfolioFile(
        filename=file_path.name,
        size=file_path.stat().st_size,
    )


@router.get(
    "/portfolio",
    response_model=PortfolioListResponse,
    status_code=HTTPStatus.OK,
    responses=example_responses,
)
async def list_portfolios() -> PortfolioListResponse:
    """List all available portfolio files.

    Retrieves a list of all portfolio files.

    **Returns:**
    * `PortfolioListResponse`: Object containing:
        * List of portfolio files, each with:
            * filename
            * file size
    """
    portfolio_files = get_portfolio_files()

    log.info(f"Found {len(portfolio_files)} portfolio files")

    return PortfolioListResponse(
        portfolios=[
            create_portfolio_file_response(file_path) for file_path in portfolio_files
        ]
    )
