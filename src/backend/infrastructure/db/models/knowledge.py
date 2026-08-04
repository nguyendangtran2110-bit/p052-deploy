from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.knowledge.enums import KnowledgeDocumentStatus, KnowledgeDocumentType
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, VectorType, utc_now


class KnowledgeDocument(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('handbook', 'regulation', 'amenity_guide', 'notice')",
            name="ck_knowledge_document_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'indexing', 'indexed', 'failed', 'archived')",
            name="ck_knowledge_document_status",
        ),
        Index("ix_knowledge_scope", "project_code", "building", "status"),
    )

    title: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(
        String(30), default=KnowledgeDocumentType.HANDBOOK.value, index=True, nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    project_code: Mapped[str | None] = mapped_column(String(50), index=True)
    building: Mapped[str | None] = mapped_column(String(100), index=True)
    source_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    checksum_sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=KnowledgeDocumentStatus.PENDING.value, index=True, nullable=False
    )
    effective_date: Mapped[date | None] = mapped_column(Date)
    document_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    chunks: Mapped[list[KnowledgeChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="KnowledgeChunk.chunk_index"
    )


class KnowledgeChunk(UuidPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
        Index("ix_chunk_document_section", "document_id", "section"),
    )

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(255))
    page_number: Mapped[int | None] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(VectorType(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")
