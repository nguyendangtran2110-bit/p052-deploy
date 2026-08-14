from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.application.announcements.access import resident_unread_filter, resident_visibility_filters
from src.backend.application.announcements.contracts import (
    AnnouncementScopeCommand,
    CreateAnnouncementCommand,
    UpdateAnnouncementCommand,
)
from src.backend.application.attachments.service import AttachmentService
from src.backend.application.realtime import publish_announcement_event
from src.backend.domain.announcements.enums import (
    AnnouncementPriority,
    AnnouncementScopeType,
    AnnouncementStatus,
    AnnouncementType,
)
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
)
from src.backend.domain.identity.enums import ActorRole, ManagementRole
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import (
    Announcement,
    AnnouncementEvent,
    AnnouncementRead,
    AnnouncementScope,
    Resident,
    ResidentUnit,
    Unit,
)


class AnnouncementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.attachments = AttachmentService(session)

    async def create(self, command: CreateAnnouncementCommand, actor: ActorContext) -> Announcement:
        self._require_editor(actor)
        if not actor.actor_id:
            raise AuthenticationError("Management account identity is required")
        scopes = await self._build_scopes(command.scopes)
        expires_at = self._normalize_datetime(command.expires_at)
        announcement = Announcement(
            announcement_code=self._new_code(),
            title=command.title,
            content=command.content,
            type=command.announcement_type.value,
            priority=command.priority.value,
            status=AnnouncementStatus.DRAFT.value,
            author_id=actor.actor_id,
            expires_at=expires_at,
            version=0,
            scopes=scopes,
        )
        announcement.events.append(
            AnnouncementEvent(
                event_type="created",
                actor_type=actor.role.value,
                actor_id=actor.actor_id,
                to_status=AnnouncementStatus.DRAFT.value,
                payload={"scope_count": len(scopes)},
                created_at=utc_now(),
            )
        )
        self.session.add(announcement)
        await self.session.flush()
        await self.attachments.attach_to_announcement(command.attachment_ids, announcement.id, actor)
        await self.session.commit()
        created = await self._get_management(announcement.id)
        if created is None:
            raise NotFoundError("Created announcement could not be reloaded")
        publish_announcement_event(
            "announcement.updated",
            created,
            include_management=True,
            data={"change": "created", "published_at": None},
        )
        return created

    async def list_management(
        self,
        actor: ActorContext,
        *,
        status: AnnouncementStatus | None = None,
        announcement_type: AnnouncementType | None = None,
        priority: AnnouncementPriority | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Announcement], int]:
        self._require_editor(actor)
        filters = []
        if status:
            filters.append(Announcement.status == status.value)
        if announcement_type:
            filters.append(Announcement.type == announcement_type.value)
        if priority:
            filters.append(Announcement.priority == priority.value)
        statement = (
            select(Announcement)
            .options(selectinload(Announcement.scopes), selectinload(Announcement.attachments))
            .where(*filters)
            .order_by(Announcement.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(Announcement.id)).where(*filters)
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total

    async def get_management(self, announcement_id: str, actor: ActorContext) -> Announcement:
        self._require_editor(actor)
        announcement = await self._get_management(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        self._authorize_mutation(announcement, actor)
        return announcement

    async def update(
        self,
        announcement_id: str,
        command: UpdateAnnouncementCommand,
        actor: ActorContext,
    ) -> Announcement:
        self._require_editor(actor)
        announcement = await self._get_management(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        self._authorize_mutation(announcement, actor)
        if announcement.status != AnnouncementStatus.DRAFT.value:
            raise InvalidTransitionError("Only draft announcements can be edited")
        if announcement.version != command.version:
            raise ConflictError("Announcement has changed; reload it before updating")
        if not command.changed_fields - {"version"}:
            raise ValidationError("At least one announcement field must be updated")

        values: dict[str, object] = {}
        if "title" in command.changed_fields:
            if not command.title:
                raise ValidationError("Announcement title is required")
            values["title"] = command.title
        if "content" in command.changed_fields:
            if not command.content:
                raise ValidationError("Announcement content is required")
            values["content"] = command.content
        if "type" in command.changed_fields and command.announcement_type is not None:
            values["type"] = command.announcement_type.value
        if "priority" in command.changed_fields and command.priority is not None:
            values["priority"] = command.priority.value
        if "expires_at" in command.changed_fields:
            values["expires_at"] = self._normalize_datetime(command.expires_at)

        new_scopes: list[AnnouncementScope] | None = None
        if "scopes" in command.changed_fields:
            new_scopes = await self._build_scopes(command.scopes or ())
        attachment_ids = command.attachment_ids if "attachment_ids" in command.changed_fields else None
        if not values and new_scopes is None and attachment_ids is None:
            raise ValidationError("At least one announcement field must be updated")

        now = utc_now()
        result = await self.session.execute(
            update(Announcement)
            .where(Announcement.id == announcement_id, Announcement.version == command.version)
            .values(**values, version=Announcement.version + 1, updated_at=now)
        )
        if result.rowcount != 1:
            raise ConflictError("Announcement has changed; reload it before updating")

        if new_scopes is not None:
            await self.session.execute(delete(AnnouncementScope).where(AnnouncementScope.announcement_id == announcement_id))
            self.session.add_all(
                [
                    AnnouncementScope(
                        announcement_id=announcement_id,
                        scope_type=scope.scope_type.value,
                        project_code=scope.project_code,
                        building=scope.building,
                        unit_id=scope.unit_id,
                    )
                    for scope in command.scopes or ()
                ]
            )
        if attachment_ids is not None:
            await self.attachments.attach_to_announcement(attachment_ids, announcement_id, actor)
        self.session.add(
            AnnouncementEvent(
                announcement_id=announcement_id,
                event_type="updated",
                actor_type=actor.role.value,
                actor_id=actor.actor_id,
                from_status=AnnouncementStatus.DRAFT.value,
                to_status=AnnouncementStatus.DRAFT.value,
                payload={"changed_fields": sorted(command.changed_fields - {"version"})},
                created_at=utc_now(),
            )
        )
        await self.session.commit()
        updated = await self._get_management(announcement_id)
        if updated is None:
            raise NotFoundError("Updated announcement could not be reloaded")
        publish_announcement_event(
            "announcement.updated",
            updated,
            include_management=True,
            data={"published_at": None},
        )
        return updated

    async def publish(self, announcement_id: str, version: int, actor: ActorContext) -> Announcement:
        self._require_editor(actor)
        announcement = await self._get_management(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        self._authorize_mutation(announcement, actor)
        if announcement.status != AnnouncementStatus.DRAFT.value:
            raise InvalidTransitionError("Only draft announcements can be published")
        if announcement.version != version:
            raise ConflictError("Announcement has changed; reload it before publishing")
        if not announcement.scopes:
            raise ValidationError("At least one audience scope is required before publishing")
        now = utc_now()
        expires_at = self._normalize_datetime(announcement.expires_at)
        if expires_at is not None and expires_at <= now:
            raise ValidationError("Announcement expiry must be in the future")

        result = await self.session.execute(
            update(Announcement)
            .where(
                Announcement.id == announcement_id,
                Announcement.version == version,
                Announcement.status == AnnouncementStatus.DRAFT.value,
            )
            .values(
                status=AnnouncementStatus.PUBLISHED.value,
                published_at=now,
                version=Announcement.version + 1,
                updated_at=now,
            )
        )
        if result.rowcount != 1:
            raise ConflictError("Announcement has changed; reload it before publishing")
        self.session.add(
            AnnouncementEvent(
                announcement_id=announcement_id,
                event_type="published",
                actor_type=actor.role.value,
                actor_id=actor.actor_id,
                from_status=AnnouncementStatus.DRAFT.value,
                to_status=AnnouncementStatus.PUBLISHED.value,
                payload={},
                created_at=utc_now(),
            )
        )
        await self.session.commit()
        published = await self._get_management(announcement_id)
        if published is None:
            raise NotFoundError("Published announcement could not be reloaded")
        resident_ids = await self._resident_ids_for_announcement(published)
        publish_announcement_event(
            "announcement.published",
            published,
            resident_ids=resident_ids,
            include_management=True,
            data={"published_at": published.published_at.isoformat() if published.published_at else None},
        )
        return published

    async def archive(self, announcement_id: str, version: int, actor: ActorContext) -> Announcement:
        self._require_editor(actor)
        announcement = await self._get_management(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        self._authorize_mutation(announcement, actor)
        if announcement.status != AnnouncementStatus.PUBLISHED.value:
            raise InvalidTransitionError("Only published announcements can be archived")
        if announcement.version != version:
            raise ConflictError("Announcement has changed; reload it before archiving")
        resident_ids = await self._resident_ids_for_announcement(announcement)
        now = utc_now()
        result = await self.session.execute(
            update(Announcement)
            .where(
                Announcement.id == announcement_id,
                Announcement.version == version,
                Announcement.status == AnnouncementStatus.PUBLISHED.value,
            )
            .values(status=AnnouncementStatus.ARCHIVED.value, version=Announcement.version + 1, updated_at=now)
        )
        if result.rowcount != 1:
            raise ConflictError("Announcement has changed; reload it before archiving")
        self.session.add(
            AnnouncementEvent(
                announcement_id=announcement_id,
                event_type="archived",
                actor_type=actor.role.value,
                actor_id=actor.actor_id,
                from_status=AnnouncementStatus.PUBLISHED.value,
                to_status=AnnouncementStatus.ARCHIVED.value,
                payload={},
                created_at=utc_now(),
            )
        )
        await self.session.commit()
        archived = await self._get_management(announcement_id)
        if archived is None:
            raise NotFoundError("Archived announcement could not be reloaded")
        publish_announcement_event(
            "announcement.archived",
            archived,
            resident_ids=resident_ids,
            include_management=True,
            data={"published_at": archived.published_at.isoformat() if archived.published_at else None},
        )
        return archived

    async def delete_draft(self, announcement_id: str, actor: ActorContext) -> None:
        self._require_editor(actor)
        announcement = await self._get_management(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        self._authorize_mutation(announcement, actor)
        if announcement.status != AnnouncementStatus.DRAFT.value:
            raise ConflictError("Only draft announcements can be deleted")
        await self.session.delete(announcement)
        await self.session.commit()

    async def list_resident(
        self,
        actor: ActorContext,
        *,
        unread_only: bool = False,
        announcement_type: AnnouncementType | None = None,
        priority: AnnouncementPriority | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[Announcement, bool]], int]:
        resident_id = self._require_resident(actor)
        await self._ensure_active_resident(resident_id)
        filters = list(resident_visibility_filters(resident_id, utc_now()))
        if unread_only:
            filters.append(resident_unread_filter(resident_id))
        if announcement_type:
            filters.append(Announcement.type == announcement_type.value)
        if priority:
            filters.append(Announcement.priority == priority.value)
        statement = (
            select(Announcement)
            .options(selectinload(Announcement.scopes), selectinload(Announcement.attachments))
            .where(*filters)
            .order_by(Announcement.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(Announcement.id)).where(*filters)
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        read_ids = await self._read_ids(resident_id, [item.id for item in items])
        return [(item, item.id in read_ids) for item in items], total

    async def get_resident(self, announcement_id: str, actor: ActorContext) -> tuple[Announcement, bool]:
        resident_id = self._require_resident(actor)
        await self._ensure_active_resident(resident_id)
        statement = (
            select(Announcement)
            .options(selectinload(Announcement.scopes), selectinload(Announcement.attachments))
            .where(Announcement.id == announcement_id, *resident_visibility_filters(resident_id, utc_now()))
        )
        announcement = await self.session.scalar(statement)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        read, created = await self._record_read(announcement.id, resident_id)
        if created:
            await self.session.commit()
            publish_announcement_event(
                "announcement.read",
                announcement,
                resident_ids=(),
                include_management=True,
                data={"resident_id": resident_id, "read_at": read.read_at.isoformat()},
            )
        return announcement, True

    async def mark_read(self, announcement_id: str, actor: ActorContext) -> AnnouncementRead:
        resident_id = self._require_resident(actor)
        await self._ensure_active_resident(resident_id)
        statement = select(Announcement.id).where(
            Announcement.id == announcement_id,
            *resident_visibility_filters(resident_id, utc_now()),
        )
        if await self.session.scalar(statement) is None:
            raise NotFoundError("Announcement was not found")
        read, created = await self._record_read(announcement_id, resident_id)
        if created:
            await self.session.commit()
            announcement = await self._get_management(announcement_id)
            if announcement:
                publish_announcement_event(
                    "announcement.read",
                    announcement,
                    resident_ids=(),
                    include_management=True,
                    data={"resident_id": resident_id, "read_at": read.read_at.isoformat()},
                )
        return read

    async def unread_count(self, actor: ActorContext) -> int:
        resident_id = self._require_resident(actor)
        await self._ensure_active_resident(resident_id)
        statement = select(func.count(Announcement.id)).where(
            *resident_visibility_filters(resident_id, utc_now()),
            resident_unread_filter(resident_id),
        )
        return int((await self.session.scalar(statement)) or 0)

    async def statistics(self, announcement_id: str, actor: ActorContext) -> dict[str, int | str]:
        self._require_editor(actor)
        announcement = await self._get_management(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement was not found")
        self._authorize_mutation(announcement, actor)
        eligible_ids = await self._resident_ids_for_announcement(announcement)
        read_count = int(
            (
                await self.session.scalar(
                    select(func.count(AnnouncementRead.id)).where(AnnouncementRead.announcement_id == announcement_id)
                )
            )
            or 0
        )
        return {
            "announcement_id": announcement_id,
            "eligible_resident_count": len(eligible_ids),
            "read_count": read_count,
            "unread_count": max(len(eligible_ids) - read_count, 0),
        }

    async def _get_management(self, announcement_id: str) -> Announcement | None:
        return await self.session.scalar(
            select(Announcement)
            .options(
                selectinload(Announcement.scopes),
                selectinload(Announcement.attachments),
                selectinload(Announcement.events),
            )
            .execution_options(populate_existing=True)
            .where(Announcement.id == announcement_id)
        )

    async def _build_scopes(self, scopes: tuple[AnnouncementScopeCommand, ...]) -> list[AnnouncementScope]:
        result: list[AnnouncementScope] = []
        for scope in scopes:
            if scope.scope_type is AnnouncementScopeType.ALL_RESIDENTS:
                if scope.project_code or scope.building or scope.unit_id:
                    raise ValidationError("all_residents scope cannot include a target")
            elif scope.scope_type is AnnouncementScopeType.PROJECT:
                if not scope.project_code or scope.building or scope.unit_id:
                    raise ValidationError("project scope requires project_code only")
            elif scope.scope_type is AnnouncementScopeType.BUILDING:
                if not scope.building or scope.unit_id:
                    raise ValidationError("building scope requires building")
            elif scope.scope_type is AnnouncementScopeType.UNIT:
                if not scope.unit_id:
                    raise ValidationError("unit scope requires unit_id")
                unit = await self.session.get(Unit, scope.unit_id)
                if unit is None or not unit.is_active:
                    raise NotFoundError("Announcement target unit was not found or is inactive")
                if scope.project_code and scope.project_code != unit.project_code:
                    raise ValidationError("Unit does not belong to the selected project")
                if scope.building and scope.building != unit.building:
                    raise ValidationError("Unit does not belong to the selected building")
            result.append(
                AnnouncementScope(
                    scope_type=scope.scope_type.value,
                    project_code=scope.project_code,
                    building=scope.building,
                    unit_id=scope.unit_id,
                )
            )
        return result

    async def _resident_ids_for_announcement(self, announcement: Announcement) -> list[str]:
        if any(scope.scope_type == AnnouncementScopeType.ALL_RESIDENTS.value for scope in announcement.scopes):
            return list(
                (
                    await self.session.scalars(select(Resident.id).where(Resident.is_active.is_(True)))
                ).all()
            )
        conditions = []
        for scope in announcement.scopes:
            if scope.scope_type == AnnouncementScopeType.PROJECT.value and scope.project_code:
                conditions.append(Unit.project_code == scope.project_code)
            elif scope.scope_type == AnnouncementScopeType.BUILDING.value and scope.building:
                conditions.append(
                    (Unit.building == scope.building)
                    & (
                        or_(scope.project_code is None, Unit.project_code == scope.project_code)
                    )
                )
            elif scope.scope_type == AnnouncementScopeType.UNIT.value and scope.unit_id:
                conditions.append(Unit.id == scope.unit_id)
        if not conditions:
            return []
        statement = (
            select(Resident.id)
            .join(ResidentUnit, ResidentUnit.resident_id == Resident.id)
            .join(Unit, Unit.id == ResidentUnit.unit_id)
            .where(Resident.is_active.is_(True), Unit.is_active.is_(True), or_(*conditions))
            .distinct()
        )
        return list((await self.session.scalars(statement)).all())

    async def _read_ids(self, resident_id: str, announcement_ids: list[str]) -> set[str]:
        if not announcement_ids:
            return set()
        rows = await self.session.scalars(
            select(AnnouncementRead.announcement_id).where(
                AnnouncementRead.resident_id == resident_id,
                AnnouncementRead.announcement_id.in_(announcement_ids),
            )
        )
        return set(rows.all())

    async def _record_read(self, announcement_id: str, resident_id: str) -> tuple[AnnouncementRead, bool]:
        existing = await self.session.scalar(
            select(AnnouncementRead).where(
                AnnouncementRead.announcement_id == announcement_id,
                AnnouncementRead.resident_id == resident_id,
            )
        )
        if existing is not None:
            return existing, False
        read = AnnouncementRead(announcement_id=announcement_id, resident_id=resident_id)
        self.session.add(read)
        await self.session.flush()
        return read, True

    async def _ensure_active_resident(self, resident_id: str) -> None:
        resident = await self.session.get(Resident, resident_id)
        if resident is None or not resident.is_active:
            raise NotFoundError("Resident was not found or is inactive")

    @staticmethod
    def _require_resident(actor: ActorContext) -> str:
        if actor.role is not ActorRole.RESIDENT or not actor.resident_id:
            raise AuthenticationError("Resident authentication is required for announcements")
        return actor.resident_id

    @staticmethod
    def _require_editor(actor: ActorContext) -> None:
        if not actor.is_management or actor.management_role not in {
            ManagementRole.ADMIN,
            ManagementRole.MANAGER,
        }:
            raise AuthorizationError("Manager or administrator permission is required for announcements")

    @staticmethod
    def _authorize_mutation(announcement: Announcement, actor: ActorContext) -> None:
        if actor.management_role is ManagementRole.ADMIN:
            return
        if announcement.author_id != actor.actor_id:
            raise AuthorizationError("Manager can only modify announcements they created")

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _new_code() -> str:
        return f"ANN-{datetime.now(UTC).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
