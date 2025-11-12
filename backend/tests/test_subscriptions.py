"""
Subscriptions API 테스트
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


async def get_mock_db_subscriptions():
    """Mock DB session for Subscriptions"""
    mock_db = AsyncMock()
    
    # execute 기본 응답
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    
    # refresh 시 기본값 설정
    def mock_refresh(obj):
        obj.id = UUID("423e4567-e89b-12d3-a456-426614174000")
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
        if hasattr(obj, 'status') and obj.status is None:
            obj.status = "active"
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    
    yield mock_db


def get_mock_user_subscriptions():
    """Mock current user for Subscriptions"""
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
    app.dependency_overrides[get_db] = get_mock_db_subscriptions
    app.dependency_overrides[get_current_user] = get_mock_user_subscriptions
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_create_subscription():
    """POST /api/v1/subscriptions - 구독하기"""
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "plan": "premium",
            "payments": {"method": "card", "amount": 29.99}
        }
    )
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["plan"] == "premium"
    assert response.json()["status"] == "active"


def test_cancel_subscription():
    """POST /api/v1/subscriptions/cancel - 구독 취소"""
    response = client.post(
        "/api/v1/subscriptions/cancel",
        json={
            "cancel_reason": "Too expensive"
        }
    )
    
    # Mock에서 active subscription이 없으므로 404
    assert response.status_code == 404


def test_change_plan():
    """PATCH /api/v1/subscriptions/plan - 플랜 변경"""
    response = client.patch(
        "/api/v1/subscriptions/plan",
        json={
            "new_plan": "enterprise",
            "payments": {"method": "card", "amount": 99.99}
        }
    )
    
    # Mock에서 active subscription이 없으므로 404
    assert response.status_code == 404


def test_get_subscription_history():
    """GET /api/v1/subscriptions/history - 구독 신청 내역"""
    response = client.get("/api/v1/subscriptions/history")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
