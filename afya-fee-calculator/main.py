"""Afya Health Cross-Border Fee Calculator - FastAPI Application Entry Point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config_loader import FeeConfigLoader
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load fee configuration on startup."""
    loader = FeeConfigLoader()
    loader.load()
    countries = loader.get_available_countries()
    print(f"Fee Calculator started. Loaded config for {len(countries)} countries: {countries}")
    yield


app = FastAPI(
    title="Afya Health Fee Calculator",
    description=(
        "Cross-border payment fee calculation service for Afya Health. "
        "Supports multiple countries, payment methods, tiered pricing, "
        "cascading taxes, and currency conversion."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Custom handler for Pydantic validation errors to return structured error."""
    errors = exc.errors()
    messages = "; ".join(e["msg"] for e in errors)
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": messages,
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
