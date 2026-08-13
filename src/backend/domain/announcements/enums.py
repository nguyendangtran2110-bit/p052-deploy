from enum import StrEnum


class AnnouncementStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AnnouncementType(StrEnum):
    GENERAL = "general"
    MAINTENANCE = "maintenance"
    FACILITY = "facility"
    REGULATION_UPDATE = "regulation_update"
    EVENT = "event"
    EMERGENCY = "emergency"


class AnnouncementPriority(StrEnum):
    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"


class AnnouncementScopeType(StrEnum):
    ALL_RESIDENTS = "all_residents"
    PROJECT = "project"
    BUILDING = "building"
    UNIT = "unit"
