backend AGENTS.md


📌 VTO (Virtual Try-On) Backend PRD

AI 패션 모델 이미지/영상 생성 서비스 백엔드 설계 문서
FastAPI + 포인트/구독 기반 작업 생성 및 자원 차감 시스템

⸻
테스트 코드 작성
tests/ 폴더아래 test code 작성 
api_endpoint 하나당 test_{router_name}.py 로 작성
mocking을 하고 I/O 위주의 테스트로 
⸻


작업 지침 방법론
1. task 범위설정
2. test code 작성
3. 코드 작성
4. test code test
5. 작업 완료 
6. 사용자에게 확인 

패키지 설치
uv add {}


작업상태 json
backend/task.json
{
  "1": {
    "task": "데이터 전처리 자동화",
    "status": "✅ 완료"
  },
  "2": {
    "task": "임베딩 벡터 저장 설계",
    "status": "🚧 진행중"
  },
}

⸻

1. 프로젝트 개요

항목	내용
목적	제품 + 모델 + 포즈 + 배경 조합을 활용한 가상 착장 이미지/영상 생성
핵심 기능	프로젝트/컬렉션 관리, VTO 생성 Jobs, 포인트&구독 기반 과금, 생성 결과 갤러리
타겟 유저	커머스 셀러, 브랜드 마케터, 패션 플랫폼 운영자
과금 모델	구독(무제한 or 일일 quota) + LookBook/Video Ticket + Credit

DB 생성시 db_agent 참고 backend/alembic/db_Agents.md
db 및 alembic 내용은 @backend/alembic/README.md  여기 읽고 업데이트 하면서 진행할것
⸻

2. 주요 요구사항 (Functional Requirements)

🔐 인증/사용자
	•	이메일/소셜(구글, 카카오) 로그인 
	•	다국어(language) 프로필 저장
	•	Soft delete 지원

🧾 구독 & 포인트 정책

타입	차감 방식
구독 사용중	VTO 생성 비용 차감 없음
LookBook Ticket	이미지 1회 생성 시 -1
Video Ticket	비디오 1회 생성 시 -1
Credit	이미지/비디오 생성시 cost만큼 차감
차감 우선순위	Subscription → LookBook Ticket → Video Ticket → Credit

	•	모든 차감/복구는 point_usage 테이블에 기록 (회계 장부 역할)
	•	SELECT FOR UPDATE로 동시 요청 중복 차감 방지

📁 컬렉션 & 프로젝트
	•	Collection > Project 계층
	•	Project는 제품, 생성 이미지/비디오, 마케팅 카피를 포함
	•	프로젝트 공유(shard_user_list), 이미지 개수 통계 저장

🛍 제품(Product)
	•	상의/하의/원피스/아우터 전면·후면 저장
	•	생성된 이미지/비디오 key 저장

✨ VTO 생성
	•	Job 생성 시 포인트/구독을 체크 및 차감 예약
	•	비동기 Queue에서 실행 (Worker)
	•	결과는 Project 기반 이미지 / 비디오 테이블에 저장
	•	실패시 자동 복구(refund) 가능해야 함

⸻

3. Non-Functional Requirements

항목	요구
동시성	동일 유저 동시 요청시 중복 차감 불가 (DB Lock 필수)
정합성	모든 사용 로그는 point_usage에 남김
확장성	향후 새로운 Ticket 추가 가능 구조
성능	entitlement 조회는 단일 row lock으로 처리


⸻

4. API 요구 사항 (MVP 범위)

Auth

Method	Endpoint
POST	/auth/login
POST	/auth/oauth/{provider}

User

| GET | /users/me |
| PATCH | /users/me |

Collection

| POST | /collections |
| GET | /collections |
| PATCH | /collections/{id} |

Project

| POST | /projects |
| GET | /projects/{id} |
| GET | /projects?collection_id |

VTO

| POST | /vto/jobs |
| GET  | /vto/jobs/{job_id} |
| GET  | /vto/projects/{id}/results |

Point

| GET  | /points |
| POST | /points/refund (Admin) |

⸻

5. 포인트 차감 트랜잭션 (Pseudo Flow)

BEGIN
SELECT points WHERE user_id = ? FOR UPDATE

IF subscription_active -> pass
ELSE IF look_book_ticket > 0 -> look_book_ticket -= 1
ELSE IF video_ticket > 0 -> video_ticket -= 1
ELSE IF credit >= cost -> credit -= cost
ELSE -> reject

INSERT INTO point_usage(...)
INSERT INTO vto_job(...)
COMMIT


⸻

6. FastAPI Layer 구조

app/
│
├── api/                        # API 라우터 (요청/응답 레이어)
│   └── v1/
│       ├── auth.py
│       ├── users.py
│       ├── collections.py
│       ├── projects.py
│       ├── points.py
│       └── vto.py              # VTO job 생성, 결과 조회
│
├── core/                       # 시스템 핵심 모듈
│   ├── config.py               # 환경/config
│   ├── security.py             # JWT, OAuth
│   ├── deps.py                 # Depends 주입 모음(DB, user 등)
│   └── exceptions.py
│
├── db/                         # DB 엔진/세션/마이그레이션
│   ├── session.py
│   └── migrations/ (alembic)
│
├── models/                     # SQLAlchemy 모델(테이블)
│   ├── user.py
│   ├── subscription.py
│   ├── point.py
│   ├── collection.py
│   ├── project.py
│   ├── product.py
│   ├── generate.py
│   ├── marketing.py
│   └── vto.py
│
├── schemas/                    # Pydantic Request/Response
│   ├── user.py
│   ├── project.py
│   ├── vto.py
│   └── point.py
│
├── services/                   # 비즈니스 로직 레이어
│   ├── point_service.py        # 포인트 차감/복구, lock 제어
│   ├── vto_service.py          # job 생성 & 벨리데이션
│   ├── project_service.py      
│   └── subscription_service.py
│
├── workers/                    # 비동기 작업 수행 (VTO 생성)
│   └── vto_worker.py
│
└── main.py                     # FastAPI App 진입점


⸻

7. Layer별 책임

Layer	역할
api	요청 검증, 응답 포맷, HTTP
service	트랜잭션, 비즈니스 규칙(포인트 차감, job 생성)
models	DB 스키마 및 관계
workers	실제 VTO 생성 실행 (Queue consumer)
core	인증, 설정, 공통 예외


⸻

8. MVP 성공 지표

지표	기준
생성 성공률	95% 이상
중복 차감 발생	0건
실패 후 자동 복구	100%
응답 latency (job 생성)	500ms 이하
포인트 정합성 오류	0건


