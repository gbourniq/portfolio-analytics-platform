import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

from portfolio_analytics.api.actions import (
    create_equity_data,
    create_fx_data,
    create_portfolio,
    delete_portfolios,
    download_portfolios,
    list_portfolios,
)
from portfolio_analytics.api.api_exceptions import (
    PortfolioAnalyticsError,
    portfolio_analytics_exception_handler,
)
from portfolio_analytics.api.common import CORS_ORIGIN_DOMAINS, URL_PREFIX, ApiTag
from portfolio_analytics.common.utils.filesystem import get_version
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

API_DESCRIPTION = """
API for portfolio analytics operations.

Visit the [Portfolio Analytics Dashboard](https://dashboard.portfolio-analytics.click)
 for a visual interface of the portfolios performance.
"""


# Create FastAPI app
app = FastAPI(
    title="Portfolio Analytics API",
    description=API_DESCRIPTION,
    version=get_version(),
    docs_url=f"{URL_PREFIX}/docs",
    openapi_url=f"{URL_PREFIX}/openapi.json",
    openapi_tags=ApiTag.get_openapi_tags(),
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},  # remove 'Schemas' section
)

# Register the exception handler
app.add_exception_handler(
    PortfolioAnalyticsError,
    portfolio_analytics_exception_handler,  # type: ignore
)


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """
    This should be placed BEFORE the CORS middleware.
    https://github.com/tiangolo/fastapi/issues/775#issuecomment-592946834
    """
    try:
        return await call_next(request)
    except Exception as e:  # pylint: disable=broad-except
        log.exception(f"[500 INTERNAL SERVER ERROR] {e}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error."}
        )


# Add CORS middleware
app.add_middleware(  # type: ignore
    CORSMiddleware,  # type: ignore
    allow_origins=CORS_ORIGIN_DOMAINS.split(", "),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers

# Portfolio
app.include_router(create_portfolio.router)
app.include_router(list_portfolios.router)
app.include_router(delete_portfolios.router)
app.include_router(download_portfolios.router)

# Market data
app.include_router(create_fx_data.router)
app.include_router(create_equity_data.router)

# Swagger docs formatting
# (remove endpoint description inferred from function name)
for route in app.routes:
    assert isinstance(route, Route)
    route.name = ""


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root endpoint to API documentation."""
    return RedirectResponse(url=f"{URL_PREFIX}/docs")


def _run_dev_server():
    uvicorn.run(
        "portfolio_analytics.api.api_main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )


if __name__ == "__main__":
    _run_dev_server()
