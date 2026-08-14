"""Compatibility import; use application.residents.service in new code."""

from src.backend.application.residents.service import ResidentService

__all__ = ["ResidentService"]
