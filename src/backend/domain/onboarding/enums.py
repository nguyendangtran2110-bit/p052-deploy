from enum import StrEnum


class OnboardingCategory(StrEnum):
    HANDOVER = "handover"
    UTILITIES = "utilities"
    GUIDANCE = "guidance"


class OnboardingItemType(StrEnum):
    TASK = "task"
    INFORMATION = "information"


class OnboardingItemStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"
    UNREAD = "unread"
    READ = "read"
