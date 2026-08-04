"""Compatibility import; use application.knowledge.service in new code."""

from src.backend.application.knowledge.service import KnowledgeService

__all__ = ["KnowledgeService"]
