"""
Auth API 테스트
- Mocking을 사용한 I/O 중심 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from fast_api import app
from db.session import get_db


async def get_mock_db_auth():
    """Mock DB session for Auth"""
    mock_db = AsyncMock()
    
    # execute 기본 응답 설정
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # refresh 시 ID 설정
    def mock_refresh(obj):
        obj.id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    
    yield mock_db


# 각 테스트 전에 override 설정
@pytest.fixture(autouse=True)
def setup_overrides():
    app.dependency_overrides[get_db] = get_mock_db_auth
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_signup():
    """POST /api/v1/auth/signup - 회원가입"""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newtest@example.com",
            "password": "password123",
            "name": "John",
            "last_name": "Doe",
            "language": "ko"
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "user_id" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login():
    """POST /api/v1/auth/login - 로그인"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    # Mock에서는 유저가 없으므로 401
    assert response.status_code == 401
    assert "detail" in response.json()


def test_oauth_google():
    """POST /api/v1/auth/oauth/google - 구글 OAuth"""
    response = client.post(
        "/api/v1/auth/oauth/google",
        json={
            "provider": "google",
            "access_token": "invalid_token"
        }
    )
    
    # 잘못된 토큰이므로 401
    assert response.status_code == 401


def test_oauth_kakao():
    """POST /api/v1/auth/oauth/kakao - 카카오 OAuth"""
    response = client.post(
        "/api/v1/auth/oauth/kakao",
        json={
            "provider": "kakao",
            "access_token": "invalid_token"
        }
    )
    
    # 잘못된 토큰이므로 401
    assert response.status_code == 401
