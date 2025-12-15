"""
Monitoring and error tracking integration.

Supports Sentry for error tracking and performance monitoring.
Configure via environment variables.
"""

import logging
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings


logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry SDK for error tracking and performance monitoring.
    
    Configuration via environment variables:
        - SENTRY_DSN: Sentry project DSN (required)
        - SENTRY_ENVIRONMENT: Environment name (e.g., production, staging)
        - SENTRY_TRACES_SAMPLE_RATE: Percentage of transactions to trace (0.0-1.0)
        - SENTRY_PROFILES_SAMPLE_RATE: Percentage of transactions to profile (0.0-1.0)
    
    Only initializes if SENTRY_DSN is configured.
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured. Skipping Sentry initialization.")
        return
    
    try:
        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",  # Group by endpoint name
                    failed_request_status_codes=[500, 599]  # Track server errors
                ),
                logging_integration
            ],
            # Performance monitoring
            enable_tracing=True,
            
            # Release tracking (useful for deployment correlation)
            release=settings.API_VERSION,
            
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII by default (GDPR compliance)
            
            # Custom tags
            _experiments={
                "profiles_sample_rate": settings.SENTRY_PROFILES_SAMPLE_RATE,
            }
        )
        
        # Set global tags
        sentry_sdk.set_tag("service", "contextdiff-api")
        sentry_sdk.set_tag("version", settings.API_VERSION)
        
        logger.info(
            f"Sentry initialized successfully. "
            f"Environment: {settings.SENTRY_ENVIRONMENT}, "
            f"Traces sample rate: {settings.SENTRY_TRACES_SAMPLE_RATE}"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        # Don't crash the app if Sentry fails to initialize


def capture_exception(error: Exception, context: Optional[dict] = None) -> None:
    """
    Manually capture an exception to Sentry.
    
    Args:
        error: The exception to capture.
        context: Additional context to attach to the event.
    
    Example:
        try:
            risky_operation()
        except ValueError as e:
            capture_exception(e, {"user_id": "123", "operation": "text_compare"})
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_exception(error)
    else:
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", context: Optional[dict] = None) -> None:
    """
    Send a message to Sentry (not an exception).
    
    Useful for tracking important events or anomalies.
    
    Args:
        message: The message to send.
        level: Severity level (debug, info, warning, error, fatal).
        context: Additional context to attach.
    
    Example:
        capture_message(
            "Unusual API usage pattern detected",
            level="warning",
            context={"ip": "1.2.3.4", "requests": 1000}
        )
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_message(message, level=level)
    else:
        sentry_sdk.capture_message(message, level=level)


def add_breadcrumb(message: str, category: str = "custom", level: str = "info", data: Optional[dict] = None) -> None:
    """
    Add a breadcrumb to track user actions or application state.
    
    Breadcrumbs provide context leading up to an error.
    
    Args:
        message: Breadcrumb message.
        category: Category for grouping (e.g., "api", "database", "validation").
        level: Severity level.
        data: Additional structured data.
    
    Example:
        add_breadcrumb(
            "Text comparison started",
            category="api",
            data={"sensitivity": "high", "text_length": 1500}
        )
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def set_user_context(user_id: str, email: Optional[str] = None, ip_address: Optional[str] = None) -> None:
    """
    Set user context for error tracking.
    
    Helps identify which users are affected by issues.
    
    Args:
        user_id: Unique user identifier.
        email: User email (optional).
        ip_address: User IP address (optional).
    
    Example:
        set_user_context(
            user_id="api_key_abc123",
            ip_address="192.168.1.1"
        )
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "ip_address": ip_address
    })


def clear_user_context() -> None:
    """Clear user context (e.g., after request completion)."""
    sentry_sdk.set_user(None)
