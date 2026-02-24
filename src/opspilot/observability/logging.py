"""Structured JSON logging configuration using structlog."""

import logging
import os

import structlog


def configure_logging() -> None:
    """Set up structlog with JSON output and timestamping.

    Reads LOG_LEVEL from the environment (default: INFO).
    Call once at application startup.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(format="%(message)s", level=getattr(logging, log_level))
