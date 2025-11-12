"""
Users API 테스트
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


async def get_mock_db():
    """Mock DB session"""
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.execute = AsyncMock()
    yield mock_db


def get_mock_user():
    """Mock current user"""
    mock_user = User(
        id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        email="test@example.com",
        name="John",
        last_name="Doe",
        language="ko",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return mock_user


# 각 테스트 전에 override 설정
@pytest.fixture(autouse=True)
def setup_overrides():
    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_user] = get_mock_user
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_get_me():
    """GET /api/v1/users/me - 내 정보 조회"""
    response = client.get("/api/v1/users/me")
    
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["name"] == "John"
    assert "id" in response.json()


def test_update_me():
    """PATCH /api/v1/users/me - 내 정보 수정"""
    response = client.patch(
        "/api/v1/users/me",
        json={
            "name": "Jane",
            "last_name": "Smith",
            "language": "en"
        }
    )
    
    assert response.status_code == 200
    assert "id" in response.json()


def test_delete_me():
    """DELETE /api/v1/users/me - 계정 삭제 (Hard Delete)"""
    response = client.delete("/api/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User deleted successfully"
