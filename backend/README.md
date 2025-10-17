# Virtual Try-On Backend

가상 피팅(Virtual Try-On) 서비스의 백엔드 애플리케이션입니다.

## 📁 프로젝트 구조

```
backend/
├── .env                        # 환경 변수 설정 파일
├── .python-version             # Python 버전 지정
├── pyproject.toml              # 프로젝트 의존성 및 설정
├── uv.lock                     # uv 패키지 매니저 lock 파일
├── configs.py                  # 설정 관리
├── custom_logger.py            # 커스텀 로거
├── fast_api.py                 # FastAPI 애플리케이션
├── README.md                   # 프로젝트 문서
│
├── core/                       # 핵심 비즈니스 로직
│   ├── database/               # 데이터베이스 관련
│   ├── litellm_hander/         # LLM 핸들러
│   │   ├── process.py          # LLM 처리 로직
│   │   ├── schema.py           # Pydantic 스키마
│   │   └── utils.py            # 유틸리티 함수
│   ├── st_pretotype/           # Streamlit UI 컴포넌트
│   │   └── component.py        # UI 컴포넌트
│   └── vto_service/            # VTO 서비스
│       └── service.py          # 서비스 로직
│
├── prompts/                    # LLM 프롬프트 템플릿
│   └── analyze_prompts.py      # 이미지 분석 프롬프트
│
├── scripts/                    # 실행 스크립트
│   ├── vto_example.py          # VTO 예제
│   ├── vto_mino.py             # VTO 미노 버전
│   └── vto_pretotype.py        # Streamlit 프로토타입
│
└── assets/                     # 리소스 파일
    ├── test_images/            # 테스트 이미지
    └── mock_human_model/       # 목업 인간 모델
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

### 3. 환경 변수 설정

`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:

### 4. 애플리케이션 실행

#### Streamlit 프로토타입 실행

```bash
PYTHONPATH=. uv run streamlit run scripts/vto_pretotype.py
```

#### FastAPI 서버 실행 (개발중)

```bash
uv run uvicorn fast_api:app --reload
```

## 📦 주요 의존성

- **FastAPI**: 웹 API 프레임워크
- **Streamlit**: 프로토타입 UI
- **LiteLLM**: LLM 통합
- **Pillow**: 이미지 처리
- **Rembg**: 배경 제거
- **SQLAlchemy**: 데이터베이스 ORM

## 🛠️ 개발

### 패키지 추가

```bash
uv add package-name
```

### 패키지 제거

```bash
uv remove package-name
```

### Python 버전 변경

```bash
uv python pin 3.12
```


## 🎨 Streamlit 프로토타입

프로토타입은 두 가지 모드를 제공합니다:

1. **가상 피팅 모드**: 의류 이미지를 모델에 가상으로 입혀보기
2. **상품 이미지 생성 모드**: 상품 이미지 자동 생성

### 주요 기능

- 카테고리별 의류 분류 (상의, 하의, 아우터, 원피스)
- 의류 속성 설정 (성별, 핏, 소매, 기장)
- 이미지 분석 AI
- 실시간 프리뷰

