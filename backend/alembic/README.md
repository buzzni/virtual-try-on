# Alembic Database Migrations

## 기본 명령어

```bash
# 마이그레이션 파일 자동 생성 (추천)
uv run alembic revision --autogenerate -m "create users table"

# 마이그레이션 파일 수동 생성
uv run alembic revision -m "create users table"

# 최신 버전으로 업그레이드
uv run alembic upgrade head

# 한 단계 롤백
uv run alembic downgrade -1

# 현재 버전 확인
uv run alembic current

# 마이그레이션 히스토리
uv run alembic history
```

## 사용 플로우

### 1. Local 환경 설정

```bash
# PostgreSQL 시작
docker-compose up -d

# 환경 변수 설정
export ENV=local
```

### 2. 마이그레이션 생성 및 적용

```bash
# 방법 1: 자동 생성 (모델 변경사항 자동 감지)
uv run alembic revision --autogenerate -m "initial migration"

# 방법 2: 수동 생성
uv run alembic revision -m "initial migration"
# versions/xxxxx_initial_migration.py 파일 편집
# upgrade(), downgrade() 함수에 스키마 변경 작성

# 마이그레이션 실행
uv run alembic upgrade head
```

### 3. 환경별 적용

```bash
# Dev
export ENV=dev
uv run alembic upgrade head

# Prod
export ENV=prod
uv run alembic upgrade head
```

## 현재 적용된 마이그레이션

- ✅ ecb9574aa6d8: create users table (User 모델)

## 환경별 DB 연결

- **local**: Docker PostgreSQL (localhost:5432)
- **dev**: AWS RDS (환경변수로 설정)
- **prod**: AWS RDS (환경변수로 설정)

환경은 `ENV` 환경변수로 제어되며, `configs.py`의 설정을 자동으로 사용합니다.
