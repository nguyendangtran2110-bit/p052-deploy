from enum import StrEnum


class AIWorkflowType(StrEnum):
    RESIDENT_TICKET = "resident_ticket"
    MANAGER_ANNOUNCEMENT = "manager_announcement"


class AIWorkflowState(StrEnum):
    COLLECTING = "collecting"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    EXECUTING = "executing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    AWAITING_PUBLISH_CONFIRMATION = "awaiting_publish_confirmation"
    PUBLISHING = "publishing"
    PUBLISHED = "published"


class AIWorkflowActionStatus(StrEnum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"
    CANCELLED = "cancelled"
