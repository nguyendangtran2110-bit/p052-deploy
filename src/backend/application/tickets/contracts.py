from dataclasses import dataclass

from src.backend.domain.tickets.enums import TicketPriority, TicketSource


@dataclass(frozen=True, slots=True)
class CreateTicketCommand:
    resident_id: str
    unit_id: str
    category: str
    priority: TicketPriority
    title: str
    description: str
    location: str
    source: TicketSource
    conversation_id: str | None = None
    idempotency_key: str | None = None
