import os
import tempfile
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["KNOWLEDGE_STORAGE_DIR"] = tempfile.mkdtemp(prefix="onbxrd-handbooks-")
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-with-more-than-32-characters"
os.environ["JWT_ISSUER"] = "onbxrd-test-api"
os.environ["JWT_AUDIENCE"] = "onbxrd-test-clients"
os.environ["MANAGEMENT_BOOTSTRAP_TOKEN"] = "test-management-bootstrap-token"

from src.backend.infrastructure.db.models import Resident, ResidentUnit, Unit  # noqa: E402
from src.backend.infrastructure.db.session import SessionFactory, drop_db, init_db  # noqa: E402
from src.main import app


@pytest_asyncio.fixture(autouse=True)
async def reset_database():
    await drop_db()
    await init_db()
    yield


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_auth(client):
    response = await client.post(
        "/api/v1/auth/bootstrap-management",
        headers={"X-Bootstrap-Token": "test-management-bootstrap-token"},
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123!",
            "employee_code": "MGT-001",
            "full_name": "Building Administrator",
            "department": "Operations",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "account": data["account"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest_asyncio.fixture
async def resident_unit():
    async with SessionFactory() as session:
        resident = Resident(
            resident_code="RES-001",
            full_name="Nguyen Van An",
            email="an@example.com",
            phone="0900000001",
        )
        unit = Unit(
            project_code="ONB",
            building="A",
            floor="12",
            unit_number="A-1204",
        )
        session.add_all([resident, unit])
        await session.flush()
        session.add(
            ResidentUnit(
                resident_id=resident.id,
                unit_id=unit.id,
                role="owner",
                is_primary=True,
            )
        )
        await session.commit()
        return {"resident_id": resident.id, "unit_id": unit.id}


@pytest.fixture
def resident_headers(resident_unit):
    return {
        "X-Actor-Role": "resident",
        "X-Resident-Id": resident_unit["resident_id"],
    }


@pytest.fixture
def management_headers():
    return {
        "X-Actor-Role": "management",
        "X-Actor-Id": "manager-001",
    }


@pytest.fixture
def mock_llm():
    """Mock LLM to avoid calling OpenAI during tests.

    Usage in test:
        def test_something(mock_llm):
            # LLM calls will return mock response instead of hitting OpenAI
            ...
    """
    mock = AsyncMock()
    mock.ainvoke.return_value = AsyncMock(content="Mocked LLM response")
    return mock
