"""FastAPI endpoints for creating and uploading portfolio files.

Provides functionality to upload and validate new portfolio files in various formats.
"""

import datetime as dtm
import re
from http import HTTPStatus
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel, Field

from portfolio_analytics.api.api_exceptions import (
    BadRequestError,
    PortfolioProcessingError,
    PortfolioValidationError,
)
from portfolio_analytics.api.common import ApiTag
from portfolio_analytics.common.utils.filesystem import (
    PORTFOLIO_SAMPLES_DIR,
    PORTFOLIO_UPLOADS_DIR,
    read_portfolio_file,
)
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

# Constants
MAX_FILENAME_LENGTH = 255
ALLOWED_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".parquet"}

router = APIRouter(prefix="", tags=[str(ApiTag.PORTFOLIO_MANAGEMENT)])


class PortfolioUploadResponse(BaseModel):
    filename: str = Field(..., description="Name of the uploaded file")
    size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="Content type of the uploaded file")
    uploaded_at: dtm.datetime = Field(..., description="Timestamp of upload")

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "my_portfolio.csv",
                "size": 1024,
                "content_type": "text/csv",
                "uploaded_at": "2023-08-15T12:34:56Z",
            }
        }
    }


example_responses: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "examples": {
                    "invalid_extension": {
                        "summary": "Invalid file extension",
                        "value": {
                            "detail": (
                                f"Only {', '.join(ALLOWED_EXTENSIONS)} files are"
                                " supported"
                            )
                        },
                    },
                    "invalid_filename": {
                        "summary": "Invalid filename",
                        "value": {"detail": "Filename contains invalid characters"},
                    },
                    "file_exists": {
                        "summary": "File already exists",
                        "value": {"detail": "A file with this name already exists"},
                    },
                    "invalid_content": {
                        "summary": "Invalid file content",
                        "value": {
                            "detail": "Invalid file content: Unable to parse file"
                        },
                    },
                }
            }
        },
    }
}


# Define the file validator
def validate_file_metadata(file: UploadFile) -> None:
    """Validate file metadata including filename, extension, and existence.

    Args:
        file: The uploaded file to validate

    Raises:
        BadRequestException: If any validation fails
    """
    assert file.filename, "No filename provided"

    # Check filename length
    if len(file.filename) > MAX_FILENAME_LENGTH:
        raise BadRequestError(
            "Filename must be less than {MAX_FILENAME_LENGTH} characters"
        )

    # Check filename pattern
    if not ALLOWED_FILENAME_PATTERN.match(file.filename):
        raise BadRequestError("Filename contains invalid characters")

    # Check file extension
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise BadRequestError(
            f"Only {', '.join(ALLOWED_EXTENSIONS)} files are supported"
        )

    if (PORTFOLIO_UPLOADS_DIR / file.filename).exists() or (
        PORTFOLIO_SAMPLES_DIR / file.filename
    ).exists():
        raise BadRequestError("A file with this name already exists")


def validate_file_content(content: bytes, file_extension: str) -> None:
    """Validate that the file content can be loaded into a pandas
    DataFrame and meets the required format.

    Args:
        content: Raw file content in bytes
        file_extension: File extension (including the dot)

    Raises:
        HTTPException: If the file content cannot be loaded into a DataFrame
        or doesn't meet requirements
    """
    # Read the file into a DataFrame based on file extension
    try:
        df = read_portfolio_file(content, file_extension)
    except ValueError as e:
        raise PortfolioProcessingError(str(e))

    # Validate required "Date" column exists
    if "Date" not in df.columns:
        raise PortfolioValidationError('DataFrame must contain a "Date" column')

    # Validate Date column contains datetime values
    try:
        pd.to_datetime(df["Date"])
    except (ValueError, TypeError) as e:
        raise PortfolioValidationError(
            f'The "Date" column must contain valid date/datetime values: {str(e)}'
        )

    # Validate numeric columns (all columns except Date)
    numeric_columns = df.columns.drop("Date")
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise PortfolioValidationError(
                f'Column "{col}" must contain numeric values (found {df[col].dtype})'
            )


@router.post(
    "/portfolio",
    response_model=PortfolioUploadResponse,
    status_code=HTTPStatus.CREATED,
    responses=example_responses,
    openapi_extra={"responses": {422: None}},
)
async def upload_portfolio(
    file: Annotated[
        UploadFile,
        File(description="Portfolio file to upload (CSV, XLSX, or Parquet format)"),
    ],
) -> PortfolioUploadResponse:
    """Upload a portfolio file.

    Upload a portfolio file in CSV, XLSX, or Parquet format.

    **Parameters:**
    * `file`: The portfolio file to upload (CSV, XLSX, or Parquet)

    **Returns:**
    * `PortfolioUploadResponse`: Object containing:
        * filename
        * file size
        * content type
        * upload timestamp

    **Raises:**
    * `HTTPException`: If the file or filename validation fails
        * Invalid file extension (400)
        * Invalid filename format (400)
        * File already exists (400)
        * Invalid file content (400)
    """
    # Validate the file metadata
    validate_file_metadata(file)

    # Validate file content
    assert file.filename is not None
    content, output_path = await file.read(), PORTFOLIO_UPLOADS_DIR / file.filename
    validate_file_content(content, output_path.suffix)

    # Ensure uploads directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    output_path.write_bytes(content)

    log.info(f"Successfully uploaded file to {output_path}")

    return PortfolioUploadResponse(
        filename=output_path.name,
        size=len(content),
        content_type=file.content_type or "application/octet-stream",
        uploaded_at=dtm.datetime.now(),
    )
