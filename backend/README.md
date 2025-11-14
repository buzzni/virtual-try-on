# Virtual Try-On Backend

가상 피팅(Virtual Try-On) 서비스의 백엔드 애플리케이션입니다.

## 📁 프로젝트 구조 (레이어별)

```
backend/
├── fast_api.py                 # FastAPI 애플리케이션 진입점
├── configs.py                  # 설정 관리 (환경별 설정)
├── custom_logger.py            # 커스텀 로거
├── pyproject.toml              # 프로젝트 의존성 및 설정
├── uv.lock                     # uv 패키지 매니저 lock 파일
├── alembic.ini                 # Alembic 마이그레이션 설정
│
├── api/                        # API 라우터 레이어 (요청/응답)
│   └── v1/
│       ├── auth.py             # 인증 API
│       ├── users.py            # 사용자 API
│       ├── collections.py      # 컬렉션 API
│       ├── projects.py         # 프로젝트 API
│       └── organizations.py    # 조직 API
│
├── core/                       # 핵심 시스템 모듈
│   ├── deps.py                 # 의존성 주입 (DB, User 등)
│   ├── exceptions.py           # 커스텀 예외 클래스
│   ├── security.py             # JWT, OAuth 보안
│   ├── litellm_hander/         # LLM 핸들러
│   │   ├── process.py          # LLM 처리 로직
│   │   ├── schema.py           # Pydantic 스키마
│   │   └── utils.py            # 유틸리티 함수
│   ├── st_pretotype/           # Streamlit UI 컴포넌트
│   │   ├── component.py        # UI 컴포넌트
│   │   ├── analyze_component.py
│   │   ├── dashboard_component.py
│   │   ├── product_image_component.py
│   │   └── side_view_component.py
│   └── vto_service/            # VTO 서비스
│       ├── service.py          # 서비스 로직
│       └── gemini_handler.py   # Gemini API 핸들러
│
├── db/                         # 데이터베이스 세션 관리
│   └── session.py              # AsyncSession 설정
│
├── models/                     # SQLAlchemy 모델 (DB 스키마)
│   ├── user.py                 # 사용자 모델
│   ├── organization.py         # 조직 모델
│   ├── collection.py           # 컬렉션 모델
│   └── project.py              # 프로젝트 모델
│
├── schemas/                    # Pydantic 스키마 (Request/Response)
│   ├── auth.py                 # 인증 스키마
│   ├── user.py                 # 사용자 스키마
│   ├── organization.py         # 조직 스키마
│   ├── collection.py           # 컬렉션 스키마
│   └── project.py              # 프로젝트 스키마
│
├── services/                   # 비즈니스 로직 레이어
│   └── organization_service.py # 조직 서비스 로직
│
├── alembic/                    # 데이터베이스 마이그레이션
│   ├── env.py                  # Alembic 환경 설정
│   ├── README.md               # 마이그레이션 가이드
│   └── versions/               # 마이그레이션 버전 파일들
│
├── tests/                      # 테스트 코드
│   ├── test_auth.py            # 인증 테스트
│   ├── test_users.py           # 사용자 테스트
│   ├── test_collections.py     # 컬렉션 테스트
│   ├── test_projects.py        # 프로젝트 테스트
│   └── test_organizations.py   # 조직 테스트
│
├── prompts/                    # LLM 프롬프트 템플릿
│   ├── analyze_prompts.py      # 이미지 분석 프롬프트
│   ├── prod_image_prompts.py   # 상품 이미지 프롬프트
│   ├── side_view_prompts.py    # 사이드 뷰 프롬프트
│   ├── style_cut_prompts.py    # 스타일/컷 프롬프트
│   ├── vto_model_prompts.py    # VTO 모델 프롬프트
│   └── vto_prompts.py          # VTO 프롬프트
│
├── scripts/                    # 실행 스크립트
│   ├── vto_example.py          # VTO 예제
│   ├── vto_gradio.py           # Gradio 버전
│   └── vto_pretotype.py        # Streamlit 프로토타입
│
└── assets/                     # 리소스 파일
    ├── default_model/          # 기본 모델 이미지
    ├── mock_human_model/       # 목업 인간 모델
    └── test_images/            # 테스트 이미지
```

## 🚀 시작하기

### 1. uv 설치

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 의존성 설치

```bash
cd backend
uv sync
```

### 3. 데이터베이스 설정 (Docker)

로컬 개발 시 Docker를 사용하여 PostgreSQL 데이터베이스를 실행합니다:

```bash
# 프로젝트 루트에서 실행
docker-compose up -d postgres
```

데이터베이스 정보:
- **호스트**: `localhost`
- **포트**: `54322` (호스트) → `5432` (컨테이너)
- **사용자**: `vto_user`
- **비밀번호**: `vto_password`
- **데이터베이스**: `vto_db`

데이터베이스가 실행 중인지 확인:
```bash
docker ps | grep vto-postgres
```

### 4. 환경 변수 설정

`backend/.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:

```env
# 환경 설정
ENV=local

# 데이터베이스 설정 (Docker Compose와 동일하게 설정)
# 주의: 로컬 개발 시 포트는 54322 (Docker Compose에서 호스트 포트로 매핑됨)
DB_HOST=localhost
DB_PORT=5432
DB_USER=vto_user
DB_PASSWORD=vto_password
DB_NAME=vto_db


### 5. 데이터베이스 마이그레이션

```bash
cd backend
uv run alembic upgrade head
```

### 6. 애플리케이션 실행

#### FastAPI 서버 실행

**⚠️ 중요: `backend` 폴더에서 실행해야 합니다**

```bash
cd backend
uv run uvicorn fast_api:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- API 문서: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

#### Streamlit 프로토타입 실행 (선택사항)

```bash
cd backend
PYTHONPATH=. uv run streamlit run scripts/vto_pretotype.py
```
### 테스트 실행

```bash
cd backend
uv run pytest
```

특정 테스트 파일 실행:
```bash
cd backend
uv run pytest tests/test_organizations.py -v
```

## 🗄️ 데이터베이스 관리

### Docker Compose로 데이터베이스 실행

```bash
# 프로젝트 루트에서 실행
docker-compose up -d postgres
```

### 데이터베이스 중지

```bash
docker-compose stop postgres
```
