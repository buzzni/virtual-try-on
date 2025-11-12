# virtual-try-on

Virtual Try-On 서비스 - AI 기반 가상 착용 시스템

## 프로젝트 구조

```
virtual-try-on/
├── backend/          # FastAPI 백엔드 서버
├── frontend/         # 프론트엔드 애플리케이션
└── docker-compose.yml
```

## 실행 방법

### 전체 실행
```bash
docker-compose up
```

### 백엔드만 실행
```bash
docker-compose up backend
```

### 프론트엔드만 실행
```bash
docker-compose up frontend
```

### 백그라운드 실행
```bash
docker-compose up -d
```

## 서비스 포트

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

## 개발 환경

### Backend
- Python 3.12
- FastAPI
- PostgreSQL 16
- uv (패키지 관리)

### Frontend
- Node.js 20
- TBD (프레임워크 미정)