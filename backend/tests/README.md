# Backend Tests

API 엔드포인트 테스트 가이드

## 테스트 실행

```bash
# 전체 테스트 실행
uv run python -m pytest tests/ -v

# 특정 파일만
uv run python -m pytest tests/test_auth.py -v

# 특정 테스트만
uv run python -m pytest tests/test_auth.py::test_signup -v
```

## 테스트 작성 방침

### 1. 엔드포인트 == 테스트 함수 (1:1 매칭)
- 모든 API 엔드포인트는 최소 1개의 테스트 함수 필수
- 파일명: `test_{router_name}.py`
- 함수명: `test_{endpoint_name}`

### 2. Mocking 필수
- **실제 DB 연결 금지**
- `app.dependency_overrides[get_db]` 사용하여 mock DB 주입
- I/O 중심 테스트: 요청/응답 검증만 수행

### 3. 표준 패턴

```python
"""
Router API 테스트
- Mocking을 사용한 I/O 중심 테스트
"""
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from fast_api import app
from db.session import get_db


async def get_mock_db():
    """Mock DB session 생성"""
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


app.dependency_overrides[get_db] = get_mock_db
client = TestClient(app)


def test_endpoint_name():
    """POST /api/v1/endpoint - 설명"""
    response = client.post(
        "/api/v1/endpoint",
        json={"key": "value"}
    )
    
    assert response.status_code == 200
    assert "field" in response.json()
```

### 4. 체크리스트
- [ ] 엔드포인트당 최소 1개 테스트 함수
- [ ] dependency_overrides로 DB mocking
- [ ] 실제 DB 연결 없이 동작
- [ ] status code 및 response body 검증
- [ ] 모든 테스트 통과 확인: `uv run python -m pytest tests/ -v`

## 현재 테스트 현황

### test_auth.py ✅ 4/4 PASS

| 엔드포인트 | 테스트 함수 |
|-----------|-----------|
| POST /api/v1/auth/signup | `test_signup` |
| POST /api/v1/auth/login | `test_login` |
| POST /api/v1/auth/oauth/google | `test_oauth_google` |
| POST /api/v1/auth/oauth/kakao | `test_oauth_kakao` |

### test_users.py ✅ 2/2 PASS

| 엔드포인트 | 테스트 함수 |
|-----------|-----------|
| GET /api/v1/users/me | `test_get_me` |
| PATCH /api/v1/users/me | `test_update_me` |

### test_collections.py ✅ 3/3 PASS

| 엔드포인트 | 테스트 함수 |
|-----------|-----------|
| POST /api/v1/collections | `test_create_collection` |
| GET /api/v1/collections | `test_get_collections` |
| PATCH /api/v1/collections/{id} | `test_update_collection` |

### test_projects.py ✅ 4/4 PASS

| 엔드포인트 | 테스트 함수 |
|-----------|-----------|
| POST /api/v1/projects | `test_create_project` |
| GET /api/v1/projects/{id} | `test_get_project` |
| GET /api/v1/projects | `test_get_projects` |
| GET /api/v1/projects?collection_id | `test_get_projects_by_collection` |
