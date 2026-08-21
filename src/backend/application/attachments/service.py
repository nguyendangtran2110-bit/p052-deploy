from __future__ import annotations

from pathlib import PurePath
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.announcements.access import resident_visibility_filters
from src.backend.core.config import Settings
from src.backend.domain.announcements.enums import AnnouncementStatus
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.backend.domain.identity.enums import ActorRole, ManagementRole
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import AIWorkflow, Announcement, Message, Ticket, TicketAttachment
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
        announcement_id: str | None = None,
        workflow_id: str | None = None,
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
        normalized_announcement_id = str(announcement_id) if announcement_id else None
        normalized_workflow_id = str(workflow_id) if workflow_id else None
        if sum(value is not None for value in (normalized_ticket_id, normalized_announcement_id, normalized_workflow_id)) > 1:
            raise ValidationError("Attachment cannot be linked to more than one parent")
        if normalized_ticket_id:
            ticket = await self.session.get(Ticket, normalized_ticket_id)
            if ticket is None:
                raise NotFoundError("Ticket was not found")
            self._authorize_ticket(ticket, actor)
        if normalized_announcement_id:
            announcement = await self.session.get(Announcement, normalized_announcement_id)
            if announcement is None:
                raise NotFoundError("Announcement was not found")
            self._authorize_announcement(announcement, actor)
        if normalized_workflow_id:
            workflow = await self.session.get(AIWorkflow, normalized_workflow_id)
            if workflow is None:
                raise NotFoundError("AI workflow was not found")
            self._authorize_workflow(workflow, actor)

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
            announcement_id=normalized_announcement_id,
            workflow_id=normalized_workflow_id,
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
            if attachment.announcement_id is not None:
                raise ConflictError("Attachment is already linked to an announcement")
            attachment.ticket_id = ticket_id
            attachment.workflow_id = None

    async def attach_to_announcement(
        self,
        attachment_ids: list[str] | tuple[str, ...],
        announcement_id: str,
        actor: ActorContext,
    ) -> None:
        if not attachment_ids:
            return
        announcement = await self.session.get(Announcement, announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        self._authorize_announcement(announcement, actor)
        attachments = await self._get_many(attachment_ids)
        if len(attachments) != len(set(attachment_ids)):
            raise NotFoundError("One or more attachments were not found")
        for attachment in attachments:
            await self._authorize_attachment(attachment, actor)
            if attachment.announcement_id not in {None, announcement_id}:
                raise ConflictError("Attachment is already linked to another announcement")
            if attachment.ticket_id is not None:
                raise ConflictError("Attachment is already linked to another ticket")
            attachment.announcement_id = announcement_id
            attachment.workflow_id = None

    async def bind_to_workflow(
        self,
        attachment_ids: list[str] | tuple[str, ...],
        workflow_id: str,
        actor: ActorContext,
    ) -> None:
        if not attachment_ids:
            return
        workflow = await self.session.get(AIWorkflow, workflow_id)
        if workflow is None:
            raise NotFoundError("AI workflow was not found")
        self._authorize_workflow(workflow, actor)
        attachments = await self._get_many(attachment_ids)
        if len(attachments) != len(set(attachment_ids)):
            raise NotFoundError("One or more attachments were not found")
        for attachment in attachments:
            self._authorize_workflow_attachment(attachment, workflow, actor)
            if attachment.workflow_id not in {None, workflow_id}:
                raise ConflictError("Attachment is already linked to another workflow")
            if attachment.ticket_id is not None or attachment.announcement_id is not None:
                raise ConflictError("Attachment is already linked to a ticket or announcement")
            attachment.workflow_id = workflow_id

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
            if attachment.announcement_id is not None:
                raise ConflictError("Attachment is already linked to an announcement")
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
        if attachment.announcement_id and actor.role is ActorRole.RESIDENT and actor.resident_id:
            statement = select(Announcement.id).where(
                Announcement.id == attachment.announcement_id,
                *resident_visibility_filters(actor.resident_id, utc_now()),
            )
            if await self.session.scalar(statement) is not None:
                return
        if attachment.workflow_id:
            workflow = await self.session.get(AIWorkflow, attachment.workflow_id)
            if workflow:
                self._authorize_workflow(workflow, actor)
                return
        raise AuthorizationError("Actor cannot access this attachment")

    @staticmethod
    def _authorize_workflow(workflow: AIWorkflow, actor: ActorContext) -> None:
        if actor.is_management and (
            actor.management_role is ManagementRole.ADMIN or workflow.owner_actor_id == actor.actor_id
        ):
            return
        if actor.role is ActorRole.RESIDENT and workflow.owner_resident_id == actor.resident_id:
            return
        raise AuthorizationError("Actor cannot access this workflow attachment")

    @staticmethod
    def _authorize_workflow_attachment(attachment: TicketAttachment, workflow: AIWorkflow, actor: ActorContext) -> None:
        if attachment.workflow_id == workflow.id:
            return
        if actor.role is ActorRole.RESIDENT and attachment.uploader_id in {actor.actor_id, actor.resident_id}:
            return
        if actor.is_management and attachment.uploader_id == actor.actor_id:
            return
        raise AuthorizationError("Attachment does not belong to this workflow")

    @staticmethod
    def _authorize_announcement(announcement: Announcement, actor: ActorContext) -> None:
        if not actor.is_management or actor.management_role not in {ManagementRole.MANAGER, ManagementRole.ADMIN}:
            raise AuthorizationError("Manager or administrator permission is required for announcement attachments")
        if announcement.status != AnnouncementStatus.DRAFT.value:
            raise ConflictError("Only draft announcements can receive attachments")
        if actor.management_role is not ManagementRole.ADMIN and announcement.author_id != actor.actor_id:
            raise AuthorizationError("Manager can only modify announcements they created")

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
