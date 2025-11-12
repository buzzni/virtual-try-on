"""
Points API 테스트
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
from models.point import Point


async def get_mock_db_points():
    """Mock DB session for Points"""
    mock_db = AsyncMock()
    
    # execute 기본 응답
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    
    # flush/refresh 시 기본값 설정
    def mock_refresh(obj):
        obj.user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        obj.credit = getattr(obj, 'credit', None) or 100
        obj.look_book_ticket = getattr(obj, 'look_book_ticket', None) or 5
        obj.video_ticket = getattr(obj, 'video_ticket', None) or 10
        obj.updated_at = datetime.utcnow()
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    
    def mock_flush():
        pass
    mock_db.flush = AsyncMock(side_effect=mock_flush)
    
    yield mock_db


def get_mock_user_points():
    """Mock current user for Points"""
    mock_user = User(
        id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        email="test@example.com",
        name="John",
        language="ko",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return mock_user


@pytest.fixture(autouse=True)
def setup_overrides():
    app.dependency_overrides[get_db] = get_mock_db_points
    app.dependency_overrides[get_current_user] = get_mock_user_points
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_get_points():
    """GET /api/v1/points - 포인트 조회"""
    response = client.get("/api/v1/points")
    
    assert response.status_code == 200
    assert "credit" in response.json()
    assert "look_book_ticket" in response.json()
    assert "video_ticket" in response.json()


def test_update_points():
    """POST /api/v1/points/update - 포인트 업데이트 (증감)"""
    response = client.post(
        "/api/v1/points/update",
        json={
            "credit": 1000,
            "look_book_ticket": 10,
            "video_ticket": 5,
            "usage_method": "manual",
            "reason": "test_charge"
        }
    )
    
    assert response.status_code == 200
    assert "credit" in response.json()
    assert "look_book_ticket" in response.json()
    assert "video_ticket" in response.json()


def test_get_point_usage():
    """GET /api/v1/points/usage - 포인트 사용 내역 조회"""
    response = client.get("/api/v1/points/usage?limit=10")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_points_user_use_without_project_id():
    """POST /api/v1/points/update - user_use인데 project_id 없으면 에러"""
    response = client.post(
        "/api/v1/points/update",
        json={
            "credit": -100,
            "usage_method": "user_use",
            "reason": "test_use"
        }
    )
    
    assert response.status_code == 400
    assert "project_id" in response.json()["detail"].lower()


def test_update_points_invalid_project_id():
    """POST /api/v1/points/update - 존재하지 않는 project_id면 404"""
    response = client.post(
        "/api/v1/points/update",
        json={
            "credit": -100,
            "usage_method": "user_use",
            "project_id": "00000000-0000-0000-0000-000000000000",
            "reason": "test_use"
        }
    )
    
    assert response.status_code == 404
