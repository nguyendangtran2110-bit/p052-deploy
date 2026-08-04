"""Compatibility imports; use application.tickets in new code."""

from src.backend.application.tickets.service import ALLOWED_TRANSITIONS, TicketService

__all__ = ["ALLOWED_TRANSITIONS", "TicketService"]
