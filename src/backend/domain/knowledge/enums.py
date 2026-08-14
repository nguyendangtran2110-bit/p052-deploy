from enum import StrEnum


class KnowledgeDocumentStatus(StrEnum):
    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class KnowledgeDocumentType(StrEnum):
    HANDBOOK = "handbook"
    REGULATION = "regulation"
    AMENITY_GUIDE = "amenity_guide"
    NOTICE = "notice"
