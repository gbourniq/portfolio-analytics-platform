"""FastAPI endpoints for downloading portfolio files.

Provides functionality to download individual portfolio files or
bulk download as zip archives.
"""

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from portfolio_analytics.api.api_exceptions import ResourceNotFoundError
from portfolio_analytics.api.common import ApiTag
from portfolio_analytics.common.filesystem import (
    PORTFOLIO_SAMPLES_DIR,
    PORTFOLIO_UPLOADS_DIR,
)
from portfolio_analytics.common.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

router = APIRouter(prefix="", tags=[str(ApiTag.PORTFOLIO_MANAGEMENT)])


example_responses: dict[int | str, dict] = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "examples": {
                    "file_not_found": {
                        "summary": "File not found",
                        "value": {"detail": "The specified file does not exist"},
                    }
                }
            }
        },
    }
}


@router.get(
    "/portfolio/download",
    response_class=FileResponse,
    responses=example_responses,
    openapi_extra={"responses": {422: None}},
)
async def download_portfolios(
    samples_only: Annotated[
        bool,
        Query(
            description=(
                "If true, downloads only sample portfolios. If false, downloads all"
                " portfolios"
            )
        ),
    ] = False,
) -> FileResponse:
    """Download portfolio files as a zip archive.

    **Parameters:**
    * `samples_only`: If true, downloads only sample portfolios. If false,
    downloads all portfolios

    **Returns:**
    * A zip file containing the requested portfolio files

    **Raises:**
    * `HTTPException`: If there's an error accessing or compressing the files
    """
    # Create a temporary file for the zip archive
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
        with zipfile.ZipFile(tmp_file.name, "w", zipfile.ZIP_DEFLATED) as archive:
            # Add all portfolios (samples and uploads if requested)
            for file in PORTFOLIO_SAMPLES_DIR.glob("*"):
                if file.is_file():
                    archive.write(file, arcname=file.name)

            # Add uploaded portfolios if not samples_only
            if not samples_only:
                for file in PORTFOLIO_UPLOADS_DIR.glob("*"):
                    if file.is_file():
                        archive.write(file, arcname=file.name)

    # Determine filename based on what's included
    filename = "sample_portfolios.zip" if samples_only else "all_portfolios.zip"

    log.info(f"Created portfolio archive: {filename}")

    # Return the zip file
    return FileResponse(
        path=tmp_file.name,
        filename=filename,
        media_type="application/zip",
        # Clean up temp file
        background=BackgroundTask(lambda: os.unlink(tmp_file.name)),
    )


@router.get(
    "/portfolio/download/{filename}",
    response_class=FileResponse,
    responses=example_responses,
)
async def download_portfolio(
    filename: Annotated[str, Path(description="Name of the portfolio file to download")],
) -> FileResponse:
    """Download a specific portfolio file.

    **Parameters:**
    * `filename`: Name of the portfolio file to download

    **Returns:**
    * The requested file as a download

    **Raises:**
    * `HTTPException`: If the file doesn't exist or there's an error accessing it
    """
    file_path = PORTFOLIO_SAMPLES_DIR / filename
    if not (
        file_path.exists() or (file_path := PORTFOLIO_UPLOADS_DIR / filename).exists()
    ):
        raise ResourceNotFoundError("The specified file does not exist")

    log.info(f"Downloading portfolio file: {filename}")
    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )
