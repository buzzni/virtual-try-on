"""
Entitlements API 테스트
- Point와 Subscription 조합하여 실시간 조회
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
from models.subscription import Subscription


async def get_mock_db_entitlements():
    """Mock DB session for Entitlements"""
    mock_db = AsyncMock()
    
    # Mock Point
    mock_point = Point(
        user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        credit=1000,
        look_book_ticket=5,
        video_ticket=15
    )
    
    # Mock Subscription (active)
    mock_subscription = Subscription(
        id=UUID("423e4567-e89b-12d3-a456-426614174000"),
        user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        plan="pro",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # execute 응답 설정
    def execute_side_effect(query):
        result = AsyncMock()
        # Point 조회
        if "points" in str(query):
            result.scalar_one_or_none = MagicMock(return_value=mock_point)
        # Subscription 조회
        elif "subscriptions" in str(query):
            result.scalar_one_or_none = MagicMock(return_value=mock_subscription)
        else:
            result.scalar_one_or_none = MagicMock(return_value=None)
        return result
    
    mock_db.execute = AsyncMock(side_effect=execute_side_effect)
    
    yield mock_db


def get_mock_user_entitlements():
    """Mock current user for Entitlements"""
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
    app.dependency_overrides[get_db] = get_mock_db_entitlements
    app.dependency_overrides[get_current_user] = get_mock_user_entitlements
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_get_my_entitlement():
    """GET /api/v1/entitlements/me - Point와 Subscription 조합 조회"""
    response = client.get("/api/v1/entitlements/me")
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "subscription_active" in data
    assert "look_book_remaining" in data
    assert "video_remaining" in data
    assert "credit_cached" in data
    # 실시간 조회이므로 last_synced_at 없음
    assert "last_synced_at" not in data
