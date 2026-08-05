"""Compatibility imports; use feature-specific domain packages in new code."""

from src.backend.domain.conversations.enums import ConversationStatus, MessageRole
from src.backend.domain.identity.enums import AccountStatus, ActorRole, ManagementRole, TokenType
from src.backend.domain.knowledge.enums import KnowledgeDocumentStatus, KnowledgeDocumentType
from src.backend.domain.residents.enums import ResidentUnitRole
from src.backend.domain.tickets.enums import TicketPriority, TicketSource, TicketStatus

__all__ = [
    "AccountStatus",
    "ActorRole",
    "ConversationStatus",
    "KnowledgeDocumentStatus",
    "KnowledgeDocumentType",
    "MessageRole",
    "ManagementRole",
    "ResidentUnitRole",
    "TicketPriority",
    "TicketSource",
    "TicketStatus",
    "TokenType",
]
