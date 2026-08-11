from __future__ import annotations

from pathlib import PurePath
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import Settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.backend.domain.identity.enums import ActorRole
from src.backend.infrastructure.db.models import Message, Ticket, TicketAttachment
from src.backend.infrastructure.storage import S3Storage


class AttachmentService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None):
        self.session = session
        self.settings = settings
        self.storage = S3Storage(settings) if settings else None

    async def create_upload(
        self,
        *,
        filename: str,
        mime_type: str,
        size_bytes: int,
        ticket_id: str | None,
        actor: ActorContext,
    ) -> tuple[TicketAttachment, str]:
        self._require_authenticated(actor)
        if self.settings is None or self.storage is None:
            raise ValidationError("Attachment storage is not configured")
        normalized_mime = mime_type.strip().lower()
        if normalized_mime not in self.settings.allowed_attachment_mime_types:
            raise ValidationError("Attachment MIME type is not allowed")
        if size_bytes <= 0 or size_bytes > self.settings.max_upload_bytes:
            raise ValidationError(f"Attachment size must be between 1 and {self.settings.max_upload_bytes} bytes")

        normalized_ticket_id = str(ticket_id) if ticket_id else None
        if normalized_ticket_id:
            ticket = await self.session.get(Ticket, normalized_ticket_id)
            if ticket is None:
                raise NotFoundError("Ticket was not found")
            self._authorize_ticket(ticket, actor)

        uploader_id = actor.actor_id or actor.resident_id
        if not uploader_id:
            raise AuthenticationError("Authenticated actor identity is required")
        safe_filename = PurePath(filename.strip()).name[:255]
        if not safe_filename or safe_filename in {".", ".."}:
            raise ValidationError("Attachment filename is required")
        object_key = f"attachments/{uploader_id}/{uuid4().hex}-{safe_filename}"
        attachment = TicketAttachment(
            uploader_id=uploader_id,
            ticket_id=normalized_ticket_id,
            filename=safe_filename,
            storage_path=object_key,
            mime_type=normalized_mime,
            size_bytes=size_bytes,
        )
        self.session.add(attachment)
        await self.session.flush()
        upload_url = await self.storage.create_presigned_upload(object_key, normalized_mime)
        await self.session.commit()
        return attachment, upload_url

    async def create_download(self, attachment_id: str, actor: ActorContext) -> tuple[TicketAttachment, str]:
        self._require_authenticated(actor)
        attachment = await self.session.get(TicketAttachment, attachment_id)
        if attachment is None:
            raise NotFoundError("Attachment was not found")
        await self._authorize_attachment(attachment, actor)
        if self.settings is None or self.storage is None:
            raise ValidationError("Attachment storage is not configured")
        return attachment, await self.storage.create_presigned_download(attachment.storage_path, attachment.filename)

    async def attach_to_ticket(self, attachment_ids: list[str] | tuple[str, ...], ticket_id: str, actor: ActorContext) -> None:
        if not attachment_ids:
            return
        ticket = await self.session.get(Ticket, ticket_id)
        if ticket is None:
            raise NotFoundError("Ticket was not found")
        self._authorize_ticket(ticket, actor)
        attachments = await self._get_many(attachment_ids)
        if len(attachments) != len(set(attachment_ids)):
            raise NotFoundError("One or more attachments were not found")
        for attachment in attachments:
            await self._authorize_attachment(attachment, actor)
            if attachment.ticket_id not in {None, ticket_id}:
                raise ConflictError("Attachment is already linked to another ticket")
            attachment.ticket_id = ticket_id

    async def attach_to_message(
        self,
        attachment_ids: list[str] | tuple[str, ...],
        message_id: str,
        *,
        ticket_id: str | None,
        actor: ActorContext,
    ) -> None:
        if not attachment_ids:
            return
        message = await self.session.get(Message, message_id)
        if message is None:
            raise NotFoundError("Message was not found")
        attachments = await self._get_many(attachment_ids)
        if len(attachments) != len(set(attachment_ids)):
            raise NotFoundError("One or more attachments were not found")
        for attachment in attachments:
            await self._authorize_attachment(attachment, actor)
            if attachment.message_id not in {None, message_id}:
                raise ConflictError("Attachment is already linked to another message")
            if ticket_id and attachment.ticket_id not in {None, ticket_id}:
                raise ConflictError("Attachment is already linked to another ticket")
            attachment.message_id = message_id
            if ticket_id:
                attachment.ticket_id = ticket_id

    async def _get_many(self, attachment_ids: list[str] | tuple[str, ...]) -> list[TicketAttachment]:
        normalized = list(dict.fromkeys(str(attachment_id) for attachment_id in attachment_ids))
        if not normalized:
            return []
        result = await self.session.scalars(select(TicketAttachment).where(TicketAttachment.id.in_(normalized)))
        return list(result.all())

    async def _authorize_attachment(self, attachment: TicketAttachment, actor: ActorContext) -> None:
        if actor.is_management:
            return
        identifiers = {value for value in (actor.actor_id, actor.resident_id) if value}
        if attachment.uploader_id in identifiers:
            return
        if attachment.ticket_id:
            ticket = await self.session.get(Ticket, attachment.ticket_id)
            if ticket and actor.role is ActorRole.RESIDENT and ticket.resident_id == actor.resident_id:
                return
        raise AuthorizationError("Actor cannot access this attachment")

    @staticmethod
    def _authorize_ticket(ticket: Ticket, actor: ActorContext) -> None:
        if actor.is_management:
            return
        if actor.role is ActorRole.RESIDENT and ticket.resident_id == actor.resident_id:
            return
        raise AuthorizationError("Actor cannot use attachments for this ticket")

    @staticmethod
    def _require_authenticated(actor: ActorContext) -> None:
        if not actor.is_authenticated:
            raise AuthenticationError("Authentication is required for attachments")
