from enum import StrEnum


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class ConversationHandoffStatus(StrEnum):
    BOT_ACTIVE = "bot_active"
    WAITING_MANAGEMENT = "waiting_management"
    MANAGEMENT_ACTIVE = "management_active"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    MANAGEMENT = "management"
    SYSTEM = "system"
