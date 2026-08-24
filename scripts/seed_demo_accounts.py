"""Seed demo accounts for local development and testing.

Creates:
1. Admin Account: admin@onbxrd.local / Admin@123
2. Resident Account: resident@onbxrd.local / Resident@123 (Unit A-0801 at Phu Dong Sky Garden)
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import sys

# Ensure repository root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from src.backend.domain.identity.enums import AccountStatus, ManagementRole
from src.backend.domain.residents.enums import ResidentUnitRole
from src.backend.infrastructure.db.models import (
    ManagementProfile,
    Resident,
    ResidentUnit,
    Unit,
    UserAccount,
)
from src.backend.infrastructure.db.session import SessionFactory, init_db
from src.backend.infrastructure.security.passwords import hash_password


async def seed() -> None:
    await init_db()
    async with SessionFactory() as session:
        # 1. Create or get Unit
        unit_stmt = select(Unit).where(Unit.project_code == "PDSG", Unit.building == "A", Unit.unit_number == "A-0801")
        unit = await session.scalar(unit_stmt)
        if not unit:
            unit = Unit(
                project_code="PDSG",
                building="A",
                floor="8",
                unit_number="A-0801",
                is_active=True,
            )
            session.add(unit)
            await session.flush()
            print(f"[Seed] Created Unit: {unit.unit_number} (ID: {unit.id})")
        else:
            print(f"[Seed] Found existing Unit: {unit.unit_number}")

        # 2. Create or get Resident Profile
        res_stmt = select(Resident).where(Resident.resident_code == "RES-PDSG-001")
        resident = await session.scalar(res_stmt)
        if not resident:
            resident = Resident(
                resident_code="RES-PDSG-001",
                full_name="Nguyen Van Cu Dan",
                email="resident@onbxrd.vn",
                phone="0901234567",
                is_active=True,
            )
            session.add(resident)
            await session.flush()

            # Link resident to unit
            link = ResidentUnit(
                resident_id=resident.id,
                unit_id=unit.id,
                role=ResidentUnitRole.OWNER.value,
                is_primary=True,
            )
            session.add(link)
            print(f"[Seed] Created Resident Profile: {resident.full_name} ({resident.resident_code})")
        else:
            resident.email = "resident@onbxrd.vn"
            print(f"[Seed] Found and updated existing Resident Profile: {resident.full_name}")

        # 3. Create or update Resident UserAccount
        res_acc_stmt = select(UserAccount).where(
            (UserAccount.email == "resident@onbxrd.vn") | (UserAccount.resident_id == resident.id)
        )
        res_acc = await session.scalar(res_acc_stmt)
        now = datetime.now(UTC)
        if not res_acc:
            res_acc = UserAccount(
                email="resident@onbxrd.vn",
                password_hash=hash_password("Resident@123456"),
                role="resident",
                status=AccountStatus.ACTIVE.value,
                resident_id=resident.id,
                email_verified_at=now,
            )
            session.add(res_acc)
            print("[Seed] Created Resident UserAccount: resident@onbxrd.vn / Resident@123456")
        else:
            res_acc.email = "resident@onbxrd.vn"
            res_acc.password_hash = hash_password("Resident@123456")
            res_acc.resident_id = resident.id
            res_acc.status = AccountStatus.ACTIVE.value
            res_acc.email_verified_at = now
            print("[Seed] Updated Resident UserAccount: resident@onbxrd.vn / Resident@123456")

        # 4. Create or update Management UserAccount
        prof_stmt = select(ManagementProfile).where(ManagementProfile.employee_code == "MGT-001")
        existing_prof = await session.scalar(prof_stmt)

        admin_acc_stmt = select(UserAccount).where(
            (UserAccount.email == "admin@onbxrd.vn")
            | (UserAccount.id == (existing_prof.account_id if existing_prof else None))
        )
        admin_acc = await session.scalar(admin_acc_stmt)
        if not admin_acc:
            admin_acc = UserAccount(
                email="admin@onbxrd.vn",
                password_hash=hash_password("Admin@12345678"),
                role="management",
                status=AccountStatus.ACTIVE.value,
                email_verified_at=now,
            )
            session.add(admin_acc)
            await session.flush()
        else:
            admin_acc.email = "admin@onbxrd.vn"
            admin_acc.password_hash = hash_password("Admin@12345678")
            admin_acc.status = AccountStatus.ACTIVE.value
            admin_acc.email_verified_at = now

        if not existing_prof:
            profile = ManagementProfile(
                account_id=admin_acc.id,
                employee_code="MGT-001",
                full_name="Quan Ly Toa Nha",
                phone="0909999999",
                department="Ban Quan Ly",
                job_title="Truong Ban",
                management_role=ManagementRole.ADMIN.value,
                project_code="PDSG",
                building="A",
            )
            session.add(profile)
            print("[Seed] Created Management Admin: admin@onbxrd.vn / Admin@12345678")
        else:
            existing_prof.account_id = admin_acc.id
            print("[Seed] Updated Management Admin: admin@onbxrd.vn / Admin@12345678")

        await session.commit()
        print("\n[Seed] SUCCESS! Demo accounts are ready:")
        print("  - Resident Login   : resident@onbxrd.vn / Resident@123456")
        print("  - Management Login : admin@onbxrd.vn / Admin@12345678\n")


if __name__ == "__main__":
    asyncio.run(seed())
