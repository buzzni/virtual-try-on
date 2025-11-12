"""
Projects API 테스트
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
from models.project import Project


async def get_mock_db_projects():
    """Mock DB session for Projects"""
    mock_db = AsyncMock()
    
    # execute 기본 응답
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # refresh 시 ID 및 기본값 설정
    def mock_refresh(obj):
        obj.id = UUID("323e4567-e89b-12d3-a456-426614174000")
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
        obj.selected_image_number = 0
        obj.total_image_number = 0
        obj.total_video_number = 0
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    
    yield mock_db


def get_mock_user_projects():
    """Mock current user for Projects"""
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
    app.dependency_overrides[get_db] = get_mock_db_projects
    app.dependency_overrides[get_current_user] = get_mock_user_projects
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_create_project():
    """POST /api/v1/projects - 프로젝트 생성"""
    response = client.post(
        "/api/v1/projects",
        json={
            "collection_id": "223e4567-e89b-12d3-a456-426614174000",
            "name": "My Project"
        }
    )
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "My Project"


def test_get_project():
    """GET /api/v1/projects/{id} - 프로젝트 조회"""
    project_id = "323e4567-e89b-12d3-a456-426614174000"
    
    response = client.get(f"/api/v1/projects/{project_id}")
    
    # Mock에서 project가 없으므로 404
    assert response.status_code == 404


def test_get_projects():
    """GET /api/v1/projects - 프로젝트 목록 조회"""
    response = client.get("/api/v1/projects")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_projects_by_collection():
    """GET /api/v1/projects?collection_id - 컬렉션별 프로젝트 조회"""
    collection_id = "223e4567-e89b-12d3-a456-426614174000"
    
    response = client.get(f"/api/v1/projects?collection_id={collection_id}")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
