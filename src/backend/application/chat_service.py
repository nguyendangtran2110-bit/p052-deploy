"""Compatibility import; use application.chat.service in new code."""

from src.backend.application.chat.service import ChatService

__all__ = ["ChatService"]
