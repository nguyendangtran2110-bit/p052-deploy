from enum import StrEnum


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
