from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import AuthorizationError, NotFoundError, ValidationError
from src.backend.domain.identity.enums import ActorRole
from src.backend.domain.onboarding.enums import OnboardingCategory, OnboardingItemStatus, OnboardingItemType
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import (
    OnboardingChecklistTemplate,
    OnboardingChecklistTemplateItem,
    Resident,
    ResidentOnboardingChecklist,
    ResidentOnboardingItem,
    ResidentUnit,
    Unit,
)

DEFAULT_TEMPLATE_CODE = "default-move-in-v1"

DEFAULT_TEMPLATE_ITEMS: tuple[dict[str, object], ...] = (
    {
        "code": "handover_condition",
        "category": OnboardingCategory.HANDOVER.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Xác nhận điều kiện bàn giao căn hộ",
        "summary": "Kiểm tra các hạng mục cơ bản và xác nhận căn hộ đã sẵn sàng tiếp nhận.",
        "handbook_reference": None,
    },
    {
        "code": "handover_keys_access",
        "category": OnboardingCategory.HANDOVER.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Nhận chìa khóa, thẻ và remote",
        "summary": "Xác nhận đã nhận các vật dụng truy cập căn hộ, thang máy và khu vực chung.",
        "handbook_reference": None,
    },
    {
        "code": "handover_meter_reading",
        "category": OnboardingCategory.HANDOVER.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Ghi nhận chỉ số điện nước",
        "summary": "Xác nhận chỉ số điện nước ban đầu đã được ghi nhận khi nhận căn hộ.",
        "handbook_reference": None,
    },
    {
        "code": "handover_condition_review",
        "category": OnboardingCategory.HANDOVER.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Kiểm tra hiện trạng căn hộ",
        "summary": "Kiểm tra nhanh hiện trạng căn hộ và ghi nhận các vấn đề cần hỗ trợ bằng ticket nếu có.",
        "handbook_reference": None,
    },
    {
        "code": "resident_profile",
        "category": OnboardingCategory.UTILITIES.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Hoàn tất hồ sơ cư dân",
        "summary": "Kiểm tra thông tin hồ sơ cư dân và thông tin căn hộ trong ứng dụng.",
        "handbook_reference": None,
    },
    {
        "code": "resident_card",
        "category": OnboardingCategory.UTILITIES.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Đăng ký thẻ cư dân",
        "summary": "Xác nhận đã biết quy trình đăng ký và sử dụng thẻ cư dân.",
        "handbook_reference": "quy trình đăng ký và sử dụng thẻ cư dân",
    },
    {
        "code": "vehicle_access",
        "category": OnboardingCategory.UTILITIES.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Đăng ký thẻ hoặc QR xe",
        "summary": "Xác nhận đã biết cách đăng ký phương tiện và sử dụng thẻ/QR khi ra vào.",
        "handbook_reference": "quy định đăng ký và sử dụng bãi đỗ xe",
    },
    {
        "code": "resident_app",
        "category": OnboardingCategory.UTILITIES.value,
        "item_type": OnboardingItemType.TASK.value,
        "title": "Kích hoạt ứng dụng cư dân",
        "summary": "Xác nhận đã đăng nhập và biết các chức năng chính của ứng dụng cư dân.",
        "handbook_reference": None,
    },
    {
        "code": "resident_rules",
        "category": OnboardingCategory.GUIDANCE.value,
        "item_type": OnboardingItemType.INFORMATION.value,
        "title": "Đọc nội quy cư dân",
        "summary": "Xem tóm tắt các quy định quan trọng trong handbook của dự án.",
        "handbook_reference": "nội quy cư dân",
    },
    {
        "code": "amenities",
        "category": OnboardingCategory.GUIDANCE.value,
        "item_type": OnboardingItemType.INFORMATION.value,
        "title": "Tìm hiểu tiện ích nội khu",
        "summary": "Xem giờ hoạt động, địa điểm và cách đăng ký hồ bơi, gym, BBQ hoặc phòng sinh hoạt.",
        "handbook_reference": "giờ hoạt động và quy định sử dụng tiện ích nội khu",
    },
    {
        "code": "services_and_fees",
        "category": OnboardingCategory.GUIDANCE.value,
        "item_type": OnboardingItemType.INFORMATION.value,
        "title": "Tìm hiểu dịch vụ và thanh toán phí",
        "summary": "Xem quy trình đăng ký dịch vụ và các khoản phí cần biết.",
        "handbook_reference": "quy trình đăng ký dịch vụ và thanh toán phí",
    },
    {
        "code": "guests_and_delivery",
        "category": OnboardingCategory.GUIDANCE.value,
        "item_type": OnboardingItemType.INFORMATION.value,
        "title": "Tìm hiểu quy định khách, shipper và đỗ xe",
        "summary": "Xem cách tiếp nhận khách/shipper và quy định đỗ xe trong khu dân cư.",
        "handbook_reference": "quy định khách, shipper và đỗ xe",
    },
    {
        "code": "fire_safety",
        "category": OnboardingCategory.GUIDANCE.value,
        "item_type": OnboardingItemType.INFORMATION.value,
        "title": "Xem hướng dẫn phòng cháy chữa cháy",
        "summary": "Tìm hiểu lối thoát hiểm, điểm tập kết và các quy tắc PCCC cơ bản.",
        "handbook_reference": "hướng dẫn phòng cháy chữa cháy và thoát hiểm",
    },
    {
        "code": "management_contact",
        "category": OnboardingCategory.GUIDANCE.value,
        "item_type": OnboardingItemType.INFORMATION.value,
        "title": "Lưu kênh liên hệ ban quản lý",
        "summary": "Biết cách liên hệ ban quản lý khi cần hỗ trợ hoặc muốn tạo ticket.",
        "handbook_reference": "kênh liên hệ ban quản lý",
    },
    {
        "code": "renovation_rules",
        "category": OnboardingCategory.GUIDANCE.value,
        "item_type": OnboardingItemType.INFORMATION.value,
        "title": "Xem quy định sửa chữa và cải tạo",
        "summary": "Tìm hiểu thời gian, thủ tục và giới hạn khi sửa chữa hoặc cải tạo căn hộ.",
        "handbook_reference": "quy định sửa chữa và cải tạo căn hộ",
    },
)


class OnboardingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_for_resident(self, resident_id: str) -> bool:
        links = await self._active_unit_links(resident_id)
        created = False
        for _, unit in links:
            created = await self.ensure_for_resident_unit(resident_id, unit) or created
        return created

    async def ensure_for_resident_unit(self, resident_id: str, unit: Unit | str) -> bool:
        unit_id = unit.id if isinstance(unit, Unit) else unit
        existing = await self.session.scalar(
            select(ResidentOnboardingChecklist).where(
                ResidentOnboardingChecklist.resident_id == resident_id,
                ResidentOnboardingChecklist.unit_id == unit_id,
            )
        )
        if existing is not None:
            return False

        resolved_unit = unit if isinstance(unit, Unit) else await self.session.get(Unit, unit_id)
        if resolved_unit is None:
            raise NotFoundError("Unit was not found")
        template = await self._find_template(resolved_unit)
        checklist = ResidentOnboardingChecklist(
            resident_id=resident_id,
            unit_id=resolved_unit.id,
            template_id=template.id,
        )
        checklist.items = [
            ResidentOnboardingItem(
                template_item_id=item.id,
                code=item.code,
                category=item.category,
                item_type=item.item_type,
                title=item.title,
                summary=item.summary,
                handbook_reference=item.handbook_reference,
                is_required=item.is_required,
                sort_order=item.sort_order,
                status=(
                    OnboardingItemStatus.PENDING.value
                    if item.item_type == OnboardingItemType.TASK.value
                    else OnboardingItemStatus.UNREAD.value
                ),
            )
            for item in template.items
        ]
        self.session.add(checklist)
        await self.session.flush()
        return True

    async def list_for_resident(self, actor: ActorContext, unit_id: str | None = None) -> list[ResidentOnboardingChecklist]:
        resident_id = self._resident_id(actor)
        created = await self.ensure_for_resident(resident_id)
        if created:
            await self.session.commit()

        statement = (
            select(ResidentOnboardingChecklist)
            .options(
                selectinload(ResidentOnboardingChecklist.items),
                selectinload(ResidentOnboardingChecklist.unit),
            )
            .where(ResidentOnboardingChecklist.resident_id == resident_id)
            .order_by(ResidentOnboardingChecklist.created_at)
        )
        if unit_id:
            if not any(checklist.unit_id == unit_id for checklist in await self._checklists_for_resident(resident_id)):
                raise AuthorizationError("Resident does not have access to the selected unit")
            statement = statement.where(ResidentOnboardingChecklist.unit_id == unit_id)
        return list((await self.session.scalars(statement)).all())

    async def update_item(
        self,
        item_id: str,
        status: OnboardingItemStatus,
        actor: ActorContext,
    ) -> ResidentOnboardingItem:
        resident_id = self._resident_id(actor)
        item = await self.session.scalar(
            select(ResidentOnboardingItem)
            .options(
                selectinload(ResidentOnboardingItem.checklist).selectinload(ResidentOnboardingChecklist.items),
            )
            .where(ResidentOnboardingItem.id == item_id)
        )
        if item is None:
            raise NotFoundError("Onboarding item was not found")
        if item.checklist.resident_id != resident_id:
            raise AuthorizationError("Resident cannot access this onboarding item")

        self._validate_status(item, status)
        now = utc_now()
        item.status = status.value
        item.acted_at = None if status in {OnboardingItemStatus.PENDING, OnboardingItemStatus.UNREAD} else now
        item.checklist.updated_at = now
        item.checklist.completed_at = self._completed_at(item.checklist.items, now)
        await self.session.commit()

        refreshed = await self.session.scalar(
            select(ResidentOnboardingItem)
            .options(selectinload(ResidentOnboardingItem.checklist))
            .where(ResidentOnboardingItem.id == item_id)
        )
        if refreshed is None:
            raise NotFoundError("Onboarding item was not found after update")
        return refreshed

    async def list_management(
        self,
        actor: ActorContext,
        *,
        search: str | None = None,
        project_code: str | None = None,
        building: str | None = None,
        is_completed: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ResidentOnboardingChecklist], int]:
        self._require_management(actor)
        await self._ensure_all_resident_units()
        filters = self._management_filters(search, project_code, building, is_completed)
        statement = (
            select(ResidentOnboardingChecklist)
            .options(
                selectinload(ResidentOnboardingChecklist.items),
                selectinload(ResidentOnboardingChecklist.resident),
                selectinload(ResidentOnboardingChecklist.unit),
            )
            .join(Resident, Resident.id == ResidentOnboardingChecklist.resident_id)
            .join(Unit, Unit.id == ResidentOnboardingChecklist.unit_id)
            .where(*filters)
            .order_by(Resident.full_name, Unit.project_code, Unit.building, Unit.unit_number)
            .offset(offset)
            .limit(limit)
        )
        count_statement = (
            select(func.count(ResidentOnboardingChecklist.id))
            .join(Resident, Resident.id == ResidentOnboardingChecklist.resident_id)
            .join(Unit, Unit.id == ResidentOnboardingChecklist.unit_id)
            .where(*filters)
        )
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total

    async def get_management_resident(
        self,
        resident_id: str,
        actor: ActorContext,
    ) -> list[ResidentOnboardingChecklist]:
        self._require_management(actor)
        resident = await self.session.get(Resident, resident_id)
        if resident is None:
            raise NotFoundError("Resident was not found")
        await self.ensure_for_resident(resident_id)
        await self.session.commit()
        statement = (
            select(ResidentOnboardingChecklist)
            .options(
                selectinload(ResidentOnboardingChecklist.items),
                selectinload(ResidentOnboardingChecklist.resident),
                selectinload(ResidentOnboardingChecklist.unit),
            )
            .where(ResidentOnboardingChecklist.resident_id == resident_id)
            .order_by(ResidentOnboardingChecklist.created_at)
        )
        return list((await self.session.scalars(statement)).all())

    async def _find_template(self, unit: Unit) -> OnboardingChecklistTemplate:
        statement = (
            select(OnboardingChecklistTemplate)
            .options(selectinload(OnboardingChecklistTemplate.items))
            .where(
                OnboardingChecklistTemplate.is_active.is_(True),
                or_(
                    OnboardingChecklistTemplate.unit_id == unit.id,
                    OnboardingChecklistTemplate.unit_id.is_(None),
                ),
                or_(
                    OnboardingChecklistTemplate.project_code == unit.project_code,
                    OnboardingChecklistTemplate.project_code.is_(None),
                ),
                or_(
                    OnboardingChecklistTemplate.building == unit.building,
                    OnboardingChecklistTemplate.building.is_(None),
                ),
            )
            .order_by(
                case((OnboardingChecklistTemplate.unit_id == unit.id, 4), else_=0).desc(),
                case((OnboardingChecklistTemplate.building == unit.building, 2), else_=0).desc(),
                case((OnboardingChecklistTemplate.project_code == unit.project_code, 1), else_=0).desc(),
                OnboardingChecklistTemplate.created_at.desc(),
            )
            .limit(1)
        )
        template = await self.session.scalar(statement)
        if template is not None:
            return template
        return await self._ensure_default_template()

    async def _ensure_default_template(self) -> OnboardingChecklistTemplate:
        statement = (
            select(OnboardingChecklistTemplate)
            .options(selectinload(OnboardingChecklistTemplate.items))
            .where(OnboardingChecklistTemplate.template_code == DEFAULT_TEMPLATE_CODE)
        )
        template = await self.session.scalar(statement)
        if template is not None:
            return template

        template = OnboardingChecklistTemplate(
            template_code=DEFAULT_TEMPLATE_CODE,
            name="Move-in checklist mặc định",
            description="Checklist resident tự theo dõi sau khi được gán căn hộ.",
            is_active=True,
            items=[
                OnboardingChecklistTemplateItem(
                    code=str(item["code"]),
                    category=str(item["category"]),
                    item_type=str(item["item_type"]),
                    title=str(item["title"]),
                    summary=str(item["summary"]),
                    handbook_reference=(
                        str(item["handbook_reference"]) if item["handbook_reference"] is not None else None
                    ),
                    is_required=True,
                    sort_order=index,
                )
                for index, item in enumerate(DEFAULT_TEMPLATE_ITEMS, start=1)
            ],
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def _active_unit_links(self, resident_id: str) -> list[tuple[ResidentUnit, Unit]]:
        today = date.today()
        statement = (
            select(ResidentUnit, Unit)
            .join(Unit, Unit.id == ResidentUnit.unit_id)
            .where(
                ResidentUnit.resident_id == resident_id,
                Unit.is_active.is_(True),
                or_(ResidentUnit.active_from.is_(None), ResidentUnit.active_from <= today),
                or_(ResidentUnit.active_to.is_(None), ResidentUnit.active_to >= today),
            )
            .order_by(ResidentUnit.is_primary.desc(), Unit.project_code, Unit.building, Unit.unit_number)
        )
        return list((await self.session.execute(statement)).all())

    async def _ensure_all_resident_units(self) -> None:
        statement = select(ResidentUnit.resident_id, ResidentUnit.unit_id).join(Unit, Unit.id == ResidentUnit.unit_id)
        rows = list((await self.session.execute(statement)).all())
        created = False
        for resident_id, unit_id in rows:
            created = await self.ensure_for_resident_unit(resident_id, unit_id) or created
        if created:
            await self.session.commit()

    @staticmethod
    def _management_filters(
        search: str | None,
        project_code: str | None,
        building: str | None,
        is_completed: bool | None,
    ) -> list:
        filters = []
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Resident.full_name.ilike(pattern),
                    Resident.resident_code.ilike(pattern),
                    Unit.unit_number.ilike(pattern),
                )
            )
        if project_code:
            filters.append(Unit.project_code == project_code)
        if building:
            filters.append(Unit.building == building)
        if is_completed is True:
            filters.append(ResidentOnboardingChecklist.completed_at.is_not(None))
        elif is_completed is False:
            filters.append(ResidentOnboardingChecklist.completed_at.is_(None))
        return filters

    @staticmethod
    def progress(checklist: ResidentOnboardingChecklist) -> dict[str, int]:
        required = [item for item in checklist.items if item.is_required]
        completed = sum(
            1
            for item in required
            if (
                item.status in {OnboardingItemStatus.COMPLETED.value, OnboardingItemStatus.NOT_APPLICABLE.value}
                if item.item_type == OnboardingItemType.TASK.value
                else item.status == OnboardingItemStatus.READ.value
            )
        )
        return {
            "required_item_count": len(required),
            "completed_item_count": completed,
            "progress_percent": round(completed * 100 / len(required)) if required else 100,
        }

    @staticmethod
    def _completed_at(items: list[ResidentOnboardingItem], now: datetime) -> datetime | None:
        required = [item for item in items if item.is_required]
        if not required:
            return now
        if all(
            (
                item.status in {OnboardingItemStatus.COMPLETED.value, OnboardingItemStatus.NOT_APPLICABLE.value}
                if item.item_type == OnboardingItemType.TASK.value
                else item.status == OnboardingItemStatus.READ.value
            )
            for item in required
        ):
            return now
        return None

    @staticmethod
    def _validate_status(item: ResidentOnboardingItem, status: OnboardingItemStatus) -> None:
        if item.item_type == OnboardingItemType.TASK.value:
            allowed = {
                OnboardingItemStatus.PENDING,
                OnboardingItemStatus.COMPLETED,
                OnboardingItemStatus.NOT_APPLICABLE,
            }
        else:
            allowed = {OnboardingItemStatus.UNREAD, OnboardingItemStatus.READ}
        if status not in allowed:
            raise ValidationError(f"Status {status.value} is not valid for this onboarding item")

    @staticmethod
    def _resident_id(actor: ActorContext) -> str:
        if actor.role is not ActorRole.RESIDENT or not actor.resident_id:
            raise AuthorizationError("Resident permission is required")
        return actor.resident_id

    @staticmethod
    def _require_management(actor: ActorContext) -> None:
        if not actor.is_management:
            raise AuthorizationError("Management permission is required")

    async def _checklists_for_resident(self, resident_id: str) -> list[ResidentOnboardingChecklist]:
        return list(
            (
                await self.session.scalars(
                    select(ResidentOnboardingChecklist).where(
                        ResidentOnboardingChecklist.resident_id == resident_id
                    )
                )
            ).all()
        )
