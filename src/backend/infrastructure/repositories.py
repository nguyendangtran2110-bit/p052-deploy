"""Compatibility imports; use infrastructure.db.repositories in new code."""

from src.backend.infrastructure.db.repositories import (
    AccountRepository,
    ConversationRepository,
    KnowledgeRepository,
    RefreshSessionRepository,
    ResidentRepository,
    TicketRepository,
)

__all__ = [
    "AccountRepository",
    "ConversationRepository",
    "KnowledgeRepository",
    "RefreshSessionRepository",
    "ResidentRepository",
    "TicketRepository",
]
