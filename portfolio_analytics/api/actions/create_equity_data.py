"""FastAPI endpoints for managing equity market data.

Provides functionality to download and update equity price data
for various stock indices.
"""

import datetime as dtm
import os
from http import HTTPStatus
from typing import Annotated, Any, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from portfolio_analytics.api.common import ApiTag
from portfolio_analytics.api.market_data.equity import Equity
from portfolio_analytics.common.utils.instruments import StockIndex
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

router = APIRouter(prefix="/market_data", tags=[str(ApiTag.MARKET_DATA)])


class EquityUpdateRequest(BaseModel):
    instruments: Annotated[
        List[StockIndex],
        Field(
            description="List of stock indices to fetch equity data for",
            example=[StockIndex.SP500, StockIndex.FTSE100, StockIndex.EUROSTOXX50],
        ),
    ]
    start_date: Optional[dtm.date] = Field(
        None, description="Start date for equity data (optional)"
    )
    end_date: Optional[dtm.date] = Field(
        None, description="End date for equity data (optional)"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "EquityUpdateRequest":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("Start date must be before end date")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2018-01-01",
                "end_date": "2024-12-31",
                "instruments": [
                    StockIndex.SP500,  # type: ignore
                    StockIndex.FTSE100,  # type: ignore
                    StockIndex.EUROSTOXX50,  # type: ignore
                ],
            }
        }
    }


class EquityUpdateResponse(BaseModel):
    output_path: str = Field(..., description="Path where equity data was saved")
    file_stats: dict = Field(
        ..., description="Statistics about the created parquet file"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "output_path": "/path/to/equity_data.parquet",
                "file_stats": {
                    "row_count": 5000,
                    "actual_date_range": {"min": "2023-01-01", "max": "2023-12-31"},
                    "data_coverage": {
                        "SP500": ["AAPL", "MSFT", "AMZN"],
                        "FTSE100": ["HSBA", "BP", "SHEL"],
                        "EUROSTOXX50": ["SAN", "SAP", "LVMH"],
                    },
                    "file_size_mb": 5.2,
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
                        "value": {
                            "detail": "Failed to download equity data from source"
                        },
                    },
                    "processing_error": {
                        "summary": "Data processing error",
                        "value": {"detail": "Error processing equity data"},
                    },
                }
            }
        },
    }
}


@router.post(
    "/equity",
    response_model=EquityUpdateResponse,
    status_code=HTTPStatus.OK,
    responses=example_responses,
    openapi_extra={"responses": {422: None}},
)
async def update_equity_data(request: EquityUpdateRequest) -> EquityUpdateResponse:
    """Update equity market data for specified stock indices.

    Downloads and processes equity data for the specified stock indices.

    **Parameters:**
    * `instruments`: List of stock indices to fetch equity data for
    * `start_date`: Optional start date for the data range
    * `end_date`: Optional end date for the data range

    **Returns:**
    * `EquityUpdateResponse`: Object containing:
        * output path where data was saved
        * file statistics including row count, date range, and indices covered

    **Raises:**
    * `HTTPException`: If the equity data update fails
        * Data download error (500)
        * Data processing error (500)
    """
    try:
        # Update equity market data
        output_path = Equity.update_market_data(
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
            "data_coverage": (
                df.groupby("EquityIndex")["Ticker"].unique().apply(sorted).to_dict()
            ),
            "file_size_mb": round(os.path.getsize(output_path) / (1024 * 1024), 2),
        }

        log.info(
            "Successfully updated equity data for"
            f" {[i.value for i in request.instruments]}"
        )

        return EquityUpdateResponse(output_path=str(output_path), file_stats=file_stats)

    except Exception as e:
        log.error(f"Failed to update equity data: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail=f"Failed to update equity data: {str(e)}",
        )
