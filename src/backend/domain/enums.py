"""Compatibility imports; use feature-specific domain packages in new code."""

from src.backend.domain.conversations.enums import ConversationStatus, MessageRole
from src.backend.domain.identity.enums import ActorRole
from src.backend.domain.knowledge.enums import KnowledgeDocumentStatus, KnowledgeDocumentType
from src.backend.domain.residents.enums import ResidentUnitRole
from src.backend.domain.tickets.enums import TicketPriority, TicketSource, TicketStatus

__all__ = [
    "ActorRole",
    "ConversationStatus",
    "KnowledgeDocumentStatus",
    "KnowledgeDocumentType",
    "MessageRole",
    "ResidentUnitRole",
    "TicketPriority",
    "TicketSource",
    "TicketStatus",
]
