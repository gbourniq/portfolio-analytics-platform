"""FastAPI endpoints for managing FX market data.

Provides functionality to download and update foreign exchange
rate data for various currencies.
"""

import datetime as dtm
import os
from http import HTTPStatus
from typing import Annotated, Any, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from portfolio_analytics.api.common import ApiTag
from portfolio_analytics.api.market_data.fx import FX
from portfolio_analytics.common.utils.instruments import Currency
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

router = APIRouter(prefix="/market_data", tags=[str(ApiTag.MARKET_DATA)])


class FXUpdateRequest(BaseModel):
    """Request model for updating FX market data.

    Contains the list of instruments and optional date range parameters.
    """

    instruments: Annotated[
        List[Currency],
        Field(
            description="List of base currencies to fetch FX data for",
            example=[Currency.USD, Currency.EUR, Currency.GBP],
        ),
    ]
    start_date: Optional[dtm.date] = Field(
        None, description="Start date for FX data (optional)"
    )
    end_date: Optional[dtm.date] = Field(
        None, description="End date for FX data (optional)"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "FXUpdateRequest":
        """Validate that start_date is before end_date if both are provided."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("Start date must be before end date")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2018-01-01",
                "end_date": "2024-12-31",
                "instruments": ["USD", "EUR", "GBP"],
            }
        }
    }


class FXUpdateResponse(BaseModel):
    """Response model for FX market data updates.

    Contains the output path and file statistics.
    """

    output_path: str = Field(..., description="Path where FX data was saved")
    file_stats: dict = Field(
        ..., description="Statistics about the created parquet file"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "output_path": "/path/to/fx_data.parquet",
                "file_stats": {
                    "row_count": 1000,
                    "actual_date_range": {"min": "2023-01-01", "max": "2023-12-31"},
                    "currencies_covered": ["USDEUR=X", "EURUSD=X", "GBPUSD=X"],
                    "file_size_mb": 1.5,
                },
            }
        }
    }


example_responses: dict[int | str, dict[str, Any]] = {
    503: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "examples": {
                    "download_error": {
                        "summary": "Data download error",
                        "value": {"detail": "Failed to download FX data from source"},
                    },
                    "processing_error": {
                        "summary": "Data processing error",
                        "value": {"detail": "Error processing FX data"},
                    },
                }
            }
        },
    }
}


@router.post(
    "/fx",
    response_model=FXUpdateResponse,
    status_code=HTTPStatus.OK,
    responses=example_responses,
    openapi_extra={"responses": {422: None}},
)
async def update_fx_data(request: FXUpdateRequest) -> FXUpdateResponse:
    """Update FX market data for specified currencies.

    Downloads and processes FX data for the specified base
    currencies against all other currencies.

    **Parameters:**
    * `instruments`: List of base currencies to fetch FX data for
    * `start_date`: Optional start date for the data range
    * `end_date`: Optional end date for the data range

    **Returns:**
    * `FXUpdateResponse`: Object containing:
        * output path where data was saved
        * file statistics including row count, date range, and currencies covered

    **Raises:**
    * `HTTPException`: If the FX data update fails
        * Data download error (500)
        * Data processing error (500)
    """
    try:
        # Update FX market data
        output_path = FX.update_market_data(
            instruments=request.instruments,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        # Read the parquet file to get statistics
        df = pd.read_parquet(output_path).reset_index()

        # Calculate file statistics
        file_stats = {
            "row_count": len(df),
            "file_date_range": {
                "min": df.Date.min().isoformat(),
                "max": df.Date.max().isoformat(),
            },
            "columns": df.columns.tolist(),
            "currencies_covered": df.Ticker.unique().tolist(),
            "file_size_mb": round(os.path.getsize(output_path) / (1024 * 1024), 2),
        }

        log.info(
            "Successfully updated FX data for "
            f"{', '.join([i.value for i in request.instruments])}"
        )

        return FXUpdateResponse(output_path=str(output_path), file_stats=file_stats)

    except Exception as e:
        log.error(f"Failed to update FX data: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail=f"Failed to update FX data: {str(e)}",
        ) from e
