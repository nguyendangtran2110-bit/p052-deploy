"""Compatibility imports; use domain.common.errors in new code."""

from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "DomainError",
    "InvalidTransitionError",
    "NotFoundError",
    "ValidationError",
]
