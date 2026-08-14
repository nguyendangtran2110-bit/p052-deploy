from datetime import datetime

from sqlalchemy import and_, exists, or_, select

from src.backend.infrastructure.db.models import Announcement, AnnouncementRead, AnnouncementScope, ResidentUnit, Unit


def resident_audience_match(resident_id: str):
    project_match = exists(
        select(1)
        .select_from(ResidentUnit)
        .join(Unit, Unit.id == ResidentUnit.unit_id)
        .where(
            ResidentUnit.resident_id == resident_id,
            Unit.is_active.is_(True),
            Unit.project_code == AnnouncementScope.project_code,
        )
    )
    building_match = exists(
        select(1)
        .select_from(ResidentUnit)
        .join(Unit, Unit.id == ResidentUnit.unit_id)
        .where(
            ResidentUnit.resident_id == resident_id,
            Unit.is_active.is_(True),
            Unit.building == AnnouncementScope.building,
            or_(
                AnnouncementScope.project_code.is_(None),
                Unit.project_code == AnnouncementScope.project_code,
            ),
        )
    )
    unit_match = exists(
        select(1)
        .select_from(ResidentUnit)
        .join(Unit, Unit.id == ResidentUnit.unit_id)
        .where(
            ResidentUnit.resident_id == resident_id,
            Unit.is_active.is_(True),
            ResidentUnit.unit_id == AnnouncementScope.unit_id,
        )
    )
    return exists(
        select(1)
        .select_from(AnnouncementScope)
        .where(
            AnnouncementScope.announcement_id == Announcement.id,
            or_(
                AnnouncementScope.scope_type == "all_residents",
                and_(AnnouncementScope.scope_type == "project", project_match),
                and_(AnnouncementScope.scope_type == "building", building_match),
                and_(AnnouncementScope.scope_type == "unit", unit_match),
            ),
        )
    )


def resident_visibility_filters(resident_id: str, now: datetime):
    return (
        Announcement.status == "published",
        Announcement.published_at.is_not(None),
        Announcement.published_at <= now,
        or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
        resident_audience_match(resident_id),
    )


def resident_unread_filter(resident_id: str):
    return ~exists(
        select(1).where(
            AnnouncementRead.announcement_id == Announcement.id,
            AnnouncementRead.resident_id == resident_id,
        )
    )
