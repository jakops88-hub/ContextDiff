"""
ContextDiff API - Semantic Text Difference Analysis.

This is the main FastAPI application providing endpoints for
semantic comparison of text using LLM-powered analysis.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import CompareRequest, DiffResponse, HealthResponse
from app.services.diff_engine import DiffEngine, get_diff_engine, LLMAPIError, LLMResponseError
from app.middleware import RateLimitMiddleware
from app.monitoring import init_sentry
from app.utils.text_processing import TextSanitizer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def verify_api_access(request: Request) -> None:
    """
    Security dependency to verify API access.
    
    Allows access if:
    1. X-API-SECRET header matches API_SECRET env var (for RapidAPI), OR
    2. Request origin is in ALLOWED_ORIGINS (for trusted frontends)
    
    Args:
        request: FastAPI Request object
        
    Raises:
        HTTPException: 403 Forbidden if authentication fails
    """
    # If no API_SECRET is configured, allow all access (local dev)
    if not settings.API_SECRET:
        return
    
    # Check 1: Verify X-API-SECRET header (RapidAPI)
    api_secret = request.headers.get("X-API-SECRET")
    if api_secret == settings.API_SECRET:
        logger.info("Access granted via X-API-SECRET header")
        return
    
    # Check 2: Verify Origin header (Trusted frontends)
    origin = request.headers.get("origin") or request.headers.get("referer", "")
    if origin:
        # Extract base origin (remove path)
        base_origin = origin.split("//")[-1].split("/")[0]
        
        # Check against allowed origins
        for allowed in settings.ALLOW_ORIGINS:
            if allowed == "*":
                logger.info(f"Access granted via wildcard origin: {origin}")
                return
            # Remove protocol from allowed origin for comparison
            allowed_base = allowed.replace("https://", "").replace("http://", "").split("/")[0]
            if base_origin == allowed_base or allowed_base in base_origin:
                logger.info(f"Access granted via allowed origin: {origin}")
                return
    
    # Access denied
    logger.warning(
        f"Access denied - No valid authentication. "
        f"API Secret: {'Present' if api_secret else 'Missing'}, "
        f"Origin: {origin or 'Missing'}"
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. Valid X-API-SECRET header or trusted origin required."
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting ContextDiff API...")
    
    # Initialize monitoring
    init_sentry()
    
    # Validate settings
    try:
        settings.validate_settings()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    logger.info(f"Using OpenAI model: {settings.OPENAI_MODEL}")
    logger.info(f"API version: {settings.API_VERSION}")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ContextDiff API...")


# Initialize FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    burst_size=settings.RATE_LIMIT_BURST
)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """
    Root endpoint - redirects to API documentation.
    
    Returns:
        Redirect to /docs.
    """
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Health Check",
    description="Check if the API is running and accessible."
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        Service status and version information.
    """
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION
    )


@app.post(
    "/v1/compare",
    response_model=DiffResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
    summary="Compare Texts for Semantic Differences",
    description="""
    Analyze semantic differences between an original text and a generated text.
    
    This endpoint uses advanced LLM-powered analysis to detect:
    - Factual changes or inaccuracies
    - Tone and sentiment shifts
    - Content omissions or additions
    - Formatting changes that affect meaning
    
    The `sensitivity` parameter controls how strict the analysis is:
    - **low**: Only flag critical issues (factual errors, major omissions)
    - **medium**: Balanced analysis (default, recommended for most use cases)
    - **high**: Maximum scrutiny (catch all semantic variations)
    
    Returns a detailed report with:
    - Overall risk assessment (is_safe, risk_score, semantic_change_level)
    - List of specific changes with locations and reasoning
    """,
    responses={
        200: {
            "description": "Successful analysis",
            "content": {
                "application/json": {
                    "example": {
                        "summary": {
                            "is_safe": False,
                            "risk_score": 45,
                            "semantic_change_level": "MODERATE"
                        },
                        "changes": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "type": "FACTUAL",
                                "severity": "warning",
                                "description": "Certainty level changed",
                                "original_span": {
                                    "text": "will be available",
                                    "start": 12,
                                    "end": 28
                                },
                                "generated_span": {
                                    "text": "might be available",
                                    "start": 12,
                                    "end": 30
                                },
                                "reasoning": "Modal verb changed from definite to uncertain"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error or LLM API error"},
        503: {"description": "Service temporarily unavailable (rate limit, timeout)"}
    }
)
async def compare_texts(
    request_body: CompareRequest,
    diff_engine: DiffEngine = Depends(get_diff_engine),
    _: None = Depends(verify_api_access)
) -> DiffResponse:
    """
    Compare two texts for semantic differences.
    
    Args:
        request: CompareRequest with original_text, generated_text, and sensitivity.
        diff_engine: Injected DiffEngine instance.
        
    Returns:
        DiffResponse containing analysis results.
        
    Raises:
        HTTPException: If analysis fails due to API errors or validation issues.
    """
    start_time = time.time()
    
    logger.info(
        f"Received compare request: sensitivity={request_body.sensitivity.value}, "
        f"premium_mode={request_body.premium_mode}, "
        f"original_length={len(request_body.original_text)}, "
        f"generated_length={len(request_body.generated_text)}"
    )
    
    # Cost optimization: Enforce MAX_TOTAL_CHARS for free tier
    total_chars = len(request_body.original_text) + len(request_body.generated_text)
    if not request_body.premium_mode and total_chars > settings.MAX_TOTAL_CHARS:
        logger.warning(
            f"Free tier limit exceeded: {total_chars} chars (max {settings.MAX_TOTAL_CHARS}). "
            f"Use premium_mode=true for larger texts."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Text Too Long",
                "message": f"Free tier limit is {settings.MAX_TOTAL_CHARS} total characters. "
                          f"Your request has {total_chars} characters. "
                          f"Set premium_mode=true to process larger texts.",
                "total_chars": total_chars,
                "max_free_chars": settings.MAX_TOTAL_CHARS,
                "suggestion": "Use premium_mode=true for texts beyond 15k characters"
            }
        )
    
    # Validate individual text length (absolute maximum: 20,000 characters per text)
    MAX_TEXT_LENGTH = 20000
    
    for text_name, text_value in [("original_text", request_body.original_text), ("generated_text", request_body.generated_text)]:
        is_valid, error_msg = TextSanitizer.validate_length(text_value, MAX_TEXT_LENGTH)
        if not is_valid:
            logger.warning(f"Text length validation failed for {text_name}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Text Too Long",
                    "message": error_msg,
                    "field": text_name,
                    "max_length": MAX_TEXT_LENGTH
                }
            )
    
    # Sanitize texts to ensure consistent encoding and indexing
    original_sanitized = TextSanitizer.clean(request_body.original_text)
    generated_sanitized = TextSanitizer.clean(request_body.generated_text)
    
    logger.debug(
        f"Text sanitization complete: "
        f"original {len(request_body.original_text)} -> {len(original_sanitized)}, "
        f"generated {len(request_body.generated_text)} -> {len(generated_sanitized)}"
    )
    
    # Create new request with sanitized texts
    sanitized_request = CompareRequest(
        original_text=original_sanitized,
        generated_text=generated_sanitized,
        sensitivity=request_body.sensitivity,
        premium_mode=request_body.premium_mode
    )
    
    try:
        # Perform semantic analysis on sanitized texts
        result = await diff_engine.analyze_diff(sanitized_request)
        
        elapsed_time = time.time() - start_time
        
        logger.info(
            f"Analysis successful: risk_score={result.summary.risk_score}, "
            f"changes={len(result.changes)}, "
            f"processed in {elapsed_time:.2f}s"
        )
        
        return result
        
    except LLMAPIError as e:
        logger.error(f"LLM API error: {e}")
        
        # Determine appropriate status code
        error_message = str(e).lower()
        if "rate limit" in error_message:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif "timeout" in error_message:
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        else:
            status_code = status.HTTP_502_BAD_GATEWAY
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "LLM API Error",
                "message": str(e),
                "type": "llm_api_error"
            }
        )
    
    except LLMResponseError as e:
        logger.error(f"LLM response validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Response Validation Error",
                "message": "The LLM returned an invalid response. Please try again.",
                "type": "llm_response_error"
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in compare endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "type": "internal_error"
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler to catch any unhandled exceptions.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        JSONResponse with error details.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "type": "unhandled_exception"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
