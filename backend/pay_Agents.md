아래는 즉시 사용 가능한 PRD(Product Requirements Document) 형태로 정리한 문서입니다.
(서술 → 기능 → 정책 → DB → API → 시퀀스 → 예외 → 모니터링 → 레이어 구조 포함)

⸻

📌 VTO Credit & Subscription System PRD

1. 제품 개요

1.1 목적

VTO 이미지/컨텐츠 생성 서비스에서 포인트/티켓/구독 기반 권한 검증과 사용량 차감을 안정적으로 처리하고, 10초 내 요청 → 결과 반환이 가능한 동기 방식 생성 API를 제공한다.

1.2 핵심 원칙

항목	원칙
권한 체크	entitlement 정보 1회 조회로 모든 판단 완료
차감 방식	구독 → 티켓 → 크레딧 순서
생성 방식	요청 즉시 처리(10초 이내 응답), 별도 job queue 없음
기록 정책	요청 전에 사용 예약 기록, 완료 후(성공/실패) 상태 업데이트
데이터 정합성	entitlement는 캐시, point_usage는 원장(ledger)


⸻

2. 사용자 권한 & 차감 정책

2.1 기본 소비 정책

Action	일반 유저 소비	구독 유저 소비
main_model	171 credit	✅ 무제한
marketing_letter	114 credit	✅ 무제한
nuggi_cut	114 credit	✅ 무제한
look_book	look_book_ticket 1	구독 시 5개 제공
video	video_ticket 1	구독 시 15개 제공

2.2 차감 우선순위

subscription active ? 무제한 or 구독 티켓 차감 :
look_book/video ticket → credit → 부족 시 거부


⸻

3. 핵심 요구사항 (Functional Requirements)

3.1 VTO 생성 요청
	•	사용자는 action 타입을 기반으로 VTO 생성 요청 가능
	•	요청 즉시 entitlement 확인 → 예약 차감 → 생성 → 결과 반환 (10초 SLA)
	•	요청 전 record 생성, 생성 후 status 업데이트
	•	멱등성 지원 (Idempotency-Key)

3.2 차감 정책
	•	크레딧/티켓 차감은 예약(reserved) → 성공(used)/실패(refunded) 흐름을 따라야 함
	•	실패 시 자동 환불
	•	동시 요청 시 중복 차감 불가 (DB Lock)

3.3 데이터 정합성
	•	entitlement는 캐시(read model)
	•	실제 포인트/티켓 원장은 points, 변경로그는 point_usage

⸻

4. 비기능 요구사항 (NFR)

항목	요구
응답속도	10초 이하
장애 정책	실패 시 자동 환불 / 타임아웃도 환불
동시성	Negative balance 금지, race condition 방어
중복 요청	Idempotency Key로 1회 처리
감사(Audit)	모든 포인트 변화는 point_usage에 기록


⸻

5. 경우의 수 (Summary)

상태	동작
구독 O + 무제한 액션	허용(차감 없음)
구독 O + 티켓 액션	티켓 차감
구독 X + 티켓 보유	티켓 차감
구독 X + 티켓 없음 + 크레딧 충분	크레딧 차감
구독 X + 크레딧 부족	요청 거부
생성 실패/타임아웃	예약 취소 및 환불


⸻

6. API 정의

6.1 VTO 생성 요청 (Core)

POST /v1/vto/generate

Request:

{
  "action": "main_model",
  "project_id": "uuid",
  "params": {}
}

Response:

{
  "status": "success",
  "result_url": "https://...",
  "vto_record_id": "uuid"
}

6.2 권한 조회

GET /v1/entitlement

6.3 포인트/티켓 사용 기록

GET /v1/point_usage?user_id=&limit=

6.4 환불

POST /v1/points/refund

⸻

7. DB Schema

entitlement (권한 캐시)

Field	Desc
user_id (PK)	user
subscription_active	bool
look_book_remaining	int
video_remaining	int
credit_cached	int
last_synced_at	ts

points (잔고 원본)

| user_id(PK), credit, look_book_ticket, video_ticket |

point_usage (원장/차감로그)

| id | user_id | job_id | usage_type | amount | status(reserved/used/refunded) | created_at |

vto_record (생성 기록)

| id | user_id | action | used_amount | used_type | status(processing/success/failed) | result_url |

⸻

8. 요청 시퀀스

Client → Generate Request
  ↓
Read entitlement FOR UPDATE
  ↓
차감가능 검증 → 예약차감 + record 생성
  ↓
ML 실행 (10s)
  ↓
Success ? used : refund
  ↓
Response 반환


⸻

9. 예외 처리

케이스	처리
10초 초과	실패로 간주 → 환불
잔액 부족	402 반환
동시 요청	DB Lock으로 1건만 차감
중복 요청	Idempotency로 1회만 처리


⸻

10. 모니터링 지표

Metric	Target
VTO latency	P95 < 10s
Refund rate	< 1%
Negative balance	0
Error rate	< 0.3%





