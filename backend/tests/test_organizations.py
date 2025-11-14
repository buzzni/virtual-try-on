"""
Organization API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from datetime import datetime
from fast_api import app
from db.session import get_db
from core.deps import get_current_user
from models.organization import Organization


class MockResult:
    def __init__(self, scalar=None, items=None):
        self._scalar = scalar
        self._items = items or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=self._items)
        return mock_scalars


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


def mock_user():
    user = MagicMock()
    user.id = UUID("123e4567-e89b-12d3-a456-426614174000")
    return user


@pytest.fixture(autouse=True)
def setup_overrides(mock_db):
    async def _get_db_override():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = mock_user
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_create_organization(mock_db):
    """POST /api/v1/organizations - 조직 생성"""
    # 중복 체크 시 기존 조직이 없음 (None 반환)
    mock_db.execute.return_value = MockResult(scalar=None)

    def refresh_side_effect(obj):
        obj.id = UUID("123e4567-e89b-12d3-a456-426614174111")
        obj.name = "Buzzni"
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()

    mock_db.refresh.side_effect = refresh_side_effect

    response = client.post("/api/v1/organizations", json={"name": "Buzzni"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Buzzni"
    assert "id" in data


def test_list_organizations(mock_db):
    """GET /api/v1/organizations - 조직 목록"""
    organization = Organization(
        id=UUID("123e4567-e89b-12d3-a456-426614174111"),
        name="Buzzni",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_db.execute.return_value = MockResult(items=[organization])

    response = client.get("/api/v1/organizations")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Buzzni"


def test_get_organization(mock_db):
    """GET /api/v1/organizations/{id} - 조직 단건 조회"""
    organization = Organization(
        id=UUID("123e4567-e89b-12d3-a456-426614174111"),
        name="Buzzni",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_db.execute.return_value = MockResult(scalar=organization)

    response = client.get("/api/v1/organizations/123e4567-e89b-12d3-a456-426614174111")

    assert response.status_code == 200
    assert response.json()["name"] == "Buzzni"


def test_update_organization(mock_db):
    """PATCH /api/v1/organizations/{id} - 조직 수정"""
    organization = Organization(
        id=UUID("123e4567-e89b-12d3-a456-426614174111"),
        name="Buzzni",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_db.execute.return_value = MockResult(scalar=organization)

    response = client.patch(
        "/api/v1/organizations/123e4567-e89b-12d3-a456-426614174111",
        json={"name": "Buzzni Updated"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Buzzni Updated"


def test_create_organization_duplicate_name(mock_db):
    """POST /api/v1/organizations - 중복 이름이면 400"""
    existing = Organization(
        id=UUID("223e4567-e89b-12d3-a456-426614174222"),
        name="Buzzni",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_db.execute.return_value = MockResult(scalar=existing)

    response = client.post("/api/v1/organizations", json={"name": "Buzzni"})

    assert response.status_code == 400


def test_delete_organization(mock_db):
    """DELETE /api/v1/organizations/{id} - 조직 삭제"""
    organization = Organization(
        id=UUID("123e4567-e89b-12d3-a456-426614174111"),
        name="Buzzni",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_db.execute.return_value = MockResult(scalar=organization)

    response = client.delete(
        "/api/v1/organizations/123e4567-e89b-12d3-a456-426614174111"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Organization deleted"
