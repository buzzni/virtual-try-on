"""
Collections API 테스트
- Mocking을 사용한 I/O 중심 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from datetime import datetime
from fast_api import app
from db.session import get_db
from core.deps import get_current_user
from models.user import User
from models.collection import Collection


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
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MockResult())

    def mock_refresh(obj):
        obj.id = UUID("223e4567-e89b-12d3-a456-426614174000")
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()

    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    return mock_db


@pytest.fixture
def mock_user():
    return User(
        id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        email="test@example.com",
        name="John",
        language="ko",
        phone_number="01012345678",
        organization_name="Buzzni",
        terms_agreed=True,
        privacy_agreed=True,
        marketing_agreed=False,
        user_type="user",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture(autouse=True)
def setup_overrides(mock_db, mock_user):
    async def _get_db_override():
        yield mock_db

    def _get_user_override():
        return mock_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_user_override
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_create_collection():
    """POST /api/v1/collections - 컬렉션 생성"""
    response = client.post(
        "/api/v1/collections",
        json={"name": "My Collection"}
    )
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "My Collection"


def test_get_collections():
    """GET /api/v1/collections - 컬렉션 목록 조회"""
    response = client.get("/api/v1/collections")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_collection():
    """PATCH /api/v1/collections/{id} - 컬렉션 수정"""
    collection_id = "223e4567-e89b-12d3-a456-426614174000"
    
    response = client.patch(
        f"/api/v1/collections/{collection_id}",
        json={"name": "Updated Collection"}
    )
    
    # Mock에서 collection이 없으므로 404
    assert response.status_code == 404


def test_create_collection_duplicate_name(mock_db):
    """POST /api/v1/collections - 중복 이름이면 400"""
    existing = Collection(
        id=UUID("323e4567-e89b-12d3-a456-426614174222"),
        user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        name="My Collection",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_db.execute.return_value = MockResult(scalar=existing)

    response = client.post(
        "/api/v1/collections",
        json={"name": "My Collection"}
    )

    assert response.status_code == 400
