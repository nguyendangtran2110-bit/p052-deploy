"""Compatibility imports; use infrastructure.db.repositories in new code."""

from src.backend.infrastructure.db.repositories import (
    ConversationRepository,
    KnowledgeRepository,
    ResidentRepository,
    TicketRepository,
)

__all__ = ["ConversationRepository", "KnowledgeRepository", "ResidentRepository", "TicketRepository"]
