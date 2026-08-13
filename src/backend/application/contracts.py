"""Compatibility imports; use feature-specific application contracts in new code."""

from src.backend.application.chat.contracts import AgentRuntime, ChatCommand, ChatOutcome
from src.backend.application.residents.contracts import CreateResidentCommand, CreateUnitCommand
from src.backend.application.tickets.contracts import CreateTicketCommand

__all__ = [
    "AgentRuntime",
    "ChatCommand",
    "ChatOutcome",
    "CreateResidentCommand",
    "CreateTicketCommand",
    "CreateUnitCommand",
]
