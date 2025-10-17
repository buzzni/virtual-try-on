from typing import Dict, Optional
import os
import aiofiles
from litellm import Router
from litellm.router import RetryPolicy
from custom_logger import get_logger
from configs import settings
from prompts.analyze_prompts import (
    analyze_clothes_image_prompt, valid_generated_vto_prompt)
from core.litellm_hander.schema import (
    LiteLLMUsageData,
    TotalUsageData,
    ClothesImageAnalysis,
    ValidGeneratedVTO,
)
import base64

logger = get_logger(__name__)


class LiteLLMHandler:
    def __init__(self):
        self.router = self._create_model_router()
        self.usage_data = []

    def _model_format(
        self, model: str, reasoning_effort: str = None, budget: int = None
    ) -> dict:
        """모델 설정 포맷"""
        format = {
            "model_name": model,
            "litellm_params": {"model": model, "api_key": self._get_api_key(model)},
        }
        if reasoning_effort:
            format["litellm_params"]["reasoning_effort"] = reasoning_effort
        if budget:
            # Gemini 전용 budget 설정
            assert model.startswith(
                "gemini"
            ), "Budget is only supported for Gemini models"
            format["litellm_params"]["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }
            if reasoning_effort:
                del format["litellm_params"]["reasoning_effort"]
        return format

    def _get_api_key(self, model: str) -> str:
        """모델에 따른 API 키 반환"""
        openai_key: str = settings.openai_api_key
        gemini_api_key: str = settings.gemini_api_key
        xai_api_key: str = "None"
        if model.startswith("gemini"):
            return gemini_api_key
        elif model.startswith("openai"):
            return openai_key
        elif model.startswith("xai"):
            return xai_api_key
        else:
            raise ValueError(f"지원하지 않는 모델입니다: {model}")

    def _create_model_router(self) -> Router:
        """LiteLLM Router 생성"""

        retry_policy = RetryPolicy(  # run 0 retries for AuthenticationErrorRetries
            BadRequestErrorRetries=0,
            ContentPolicyViolationErrorRetries=1,
        )

        model_list = [
            self._model_format("gemini/gemini-2.5-flash", budget=1024),
            self._model_format("gemini/gemini-2.0-flash"),
            self._model_format("openai/gpt-4.1-mini"),
            self._model_format("xai/grok-3-mini", reasoning_effort="low"),
            self._model_format("gemini/gemini-2.5-pro", budget=1024),
            self._model_format("openai/gpt-5-mini"),
            self._model_format("gemini/gemini-2.5-flash-lite", budget=0),
        ]
        fallback_model = [
            {"gemini/gemini-2.0-flash": ["openai/gpt-4.1-mini"]},
            {"gemini/gemini-2.5-flash": ["openai/gpt-5-mini"]},
            {"gemini/gemini-2.5-flash-lite": ["gemini/gemini-2.0-flash"]},
            {"openai/gpt-5-mini": ["gemini/gemini-2.5-flash"]},
        ]
        router = Router(
            model_list=model_list,
            fallbacks=fallback_model,
            retry_policy=retry_policy,
            timeout=45,
        )
        return router

    def _get_model_pricing(self, model_name: str) -> Dict[str, float]:
        """
        모델별 토큰 가격 정보 반환 (USD per 1M tokens)
        """
        pricing = {
            "gemini/gemini-2.5-pro": {
                "input": 1.25,
                "output": 10,
            },
            "gemini/gemini-2.5-flash": {
                "input": 0.3,
                "output": 2.5,
            },
            "gemini/gemini-2.5-flash-lite": {
                "input": 0.1,
                "output": 0.4,
            },
            "gemini/gemini-2.0-flash": {"input": 0.1, "output": 0.4},
            "openai/gpt-4.1-mini": {"input": 0.4, "output": 1.6},
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
            "xai/grok-3-mini": {"input": 0.3, "output": 0.5},
            "openai/gpt-5-mini": {"input": 0.2, "output": 2},
        }

        # 모델명 정규화
        for key in pricing.keys():
            if key == model_name.lower():
                return pricing[key]

        raise ValueError(f"지원하지 않는 모델입니다: {model_name}")

    def calculate_cost(
        self, response: Dict, model_name: str, task_name: str
    ) -> LiteLLMUsageData:
        # response가 딕셔너리인 경우 usage 정보 추출
        if isinstance(response, dict):
            usage = response.get("usage", {})

            total_token_count = usage.get("total_tokens", 0)
            prompt_token_count = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            reasoning_tokens = 0

            # reasoning 토큰 확인
            if (
                "completion_tokens_details" in usage
                and usage["completion_tokens_details"]
            ):
                reasoning_tokens = usage["completion_tokens_details"].get(
                    "reasoning_tokens", 0
                )
        else:
            # response가 객체인 경우
            usage = response.usage
            total_token_count = usage.total_tokens
            prompt_token_count = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            reasoning_tokens = 0

            # reasoning 토큰 확인
            if (
                hasattr(usage, "completion_tokens_details")
                and usage.completion_tokens_details
            ):
                reasoning_tokens = getattr(
                    usage.completion_tokens_details, "reasoning_tokens", 0
                )
        # 모델별 비용 계산
        pricing = self._get_model_pricing(model_name)
        input_cost = (prompt_token_count / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        total_cost_usd = input_cost + output_cost
        total_cost_krw = total_cost_usd * 1300

        usage_data = LiteLLMUsageData(
            total_token_count=total_token_count,
            prompt_token_count=prompt_token_count,
            candidates_token_count=completion_tokens,
            output_token_count=completion_tokens,
            cached_content_token_count=0,  # LiteLLM에서는 별도 제공 안함
            thoughts_token_count=reasoning_tokens,
            model_name=model_name,
            cost_usd=round(total_cost_usd, 6),
            cost_krw=round(total_cost_krw, 2),
            task_name=task_name,
        )
        return usage_data

    async def calculate_total_cost(self) -> TotalUsageData:
        # 전체 합계 계산
        total_tokens = sum(u.total_token_count for u in self.usage_data)
        total_prompt_tokens = sum(u.prompt_token_count for u in self.usage_data)
        total_candidates_tokens = sum(u.candidates_token_count for u in self.usage_data)
        total_cached_tokens = sum(u.cached_content_token_count for u in self.usage_data)
        total_output_tokens = sum(u.output_token_count for u in self.usage_data)
        total_thoughts_tokens = sum(u.thoughts_token_count for u in self.usage_data)
        total_cost_usd = sum(u.cost_usd for u in self.usage_data)
        total_cost_krw = sum(u.cost_krw for u in self.usage_data)

        # 전체 합계 객체 생성
        total_usage = LiteLLMUsageData(
            total_token_count=total_tokens,
            prompt_token_count=total_prompt_tokens,
            candidates_token_count=total_candidates_tokens,
            cached_content_token_count=total_cached_tokens,
            output_token_count=total_output_tokens,
            thoughts_token_count=total_thoughts_tokens,
            model_name="total",
            cost_usd=round(total_cost_usd, 6),
            cost_krw=round(total_cost_krw, 2),
            task_name="total_cost",
        )

        return TotalUsageData(total=total_usage, details=self.usage_data)

    async def analyze_clothes_image(
        self, image_content: Dict[str, str]
    ) -> LiteLLMUsageData:
        """
        옷 이미지 분석
        """
        model_name = "gemini/gemini-2.5-flash"
        prompt_text = analyze_clothes_image_prompt()
        response = await self.router.acompletion(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt_text}, image_content],
                }
            ],
            response_format=ClothesImageAnalysis,
        )
        self.usage_data.append(
            self.calculate_cost(response, model_name, "analyze_clothes_image")
        )
        return response

    async def valid_generated_vto(
        self,
        original_image: Dict[str, str],
        generated_image: Dict[str, str],
    ) -> LiteLLMUsageData:
        """
        생성된 VTO 이미지 검수
        """
        model_name = "gemini/gemini-2.5-flash"
        model_name = "openai/gpt-5-mini"
        prompt_text = valid_generated_vto_prompt()
        response = await self.router.acompletion(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        original_image,
                        generated_image,
                    ],
                }
            ],
            response_format=ValidGeneratedVTO,
        )
        self.usage_data.append(
            self.calculate_cost(response, model_name, "valid_generated_vto")
        )
        return response

    async def convert_litellm_image_object(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        이미지를 Gemini API에서 사용할 수 있는 types.Part 객체로 변환

        Args:
            image_path: 로컬 이미지 파일 경로
            image_bytes: 이미지 바이트 데이터
            image_url: 이미지 URL

        Returns:
            types.Part: Gemini API에서 사용 가능한 이미지 Part 객체
        """
        mime_type = "image/jpeg"  # 기본값

        if image_path:
            # 로컬 파일에서 이미지 읽기
            async with aiofiles.open(image_path, "rb") as f:
                image_bytes = await f.read()

            # base64 인코딩
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            # 파일 확장자로 MIME 타입 결정
            _, ext = os.path.splitext(image_path)
            ext = ext.lower()
            mime_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }.get(ext, "image/jpeg")

            # OpenAI 스타일의 image_url 형식으로 반환
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
            }
            return image_content

        elif image_url:
            # URL 이미지는 직접 URL 사용
            image_content = {"type": "image_url", "image_url": {"url": f"{image_url}"}}
            return image_content

        elif image_bytes:
            # 바이트 데이터를 base64로 인코딩
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
            }
            return image_content

        else:
            raise ValueError(
                "image_url, image_path, image_bytes 중 하나를 입력해주세요."
            )
