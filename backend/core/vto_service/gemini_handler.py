from typing import Union, Optional, Tuple, Dict
import aiofiles
import asyncio
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import numpy as np
from configs import settings
from typing import List
from core.litellm_hander.schema import LiteLLMUsageData


class GeminiProcesser:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.aio_client = self.client.aio

    async def create_image_content(self, image: Union[Image.Image, bytes, str], use_reize = False) -> str:
        if isinstance(image, str):
            async with aiofiles.open(image, "rb") as f:
                image_bytes = await f.read()
            data = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/png",
            )

        elif use_reize:
            data = Image.open(image)
            if data.width > 1024 or data.height > 1024:
                data.thumbnail([1024, 1024], Image.Resampling.LANCZOS)            
        elif isinstance(image, bytes):
            data = types.Part.from_bytes(
                data=image,
                mime_type="image/png",
            )
        elif isinstance(image, np.ndarray):
            data = Image.fromarray(image)
            data.thumbnail([1024, 1024], Image.Resampling.LANCZOS)
        else:
            data = image
        return data

    async def virtual_tryon_inference(self, contents, temperature: float = 1.0):
        """
        단일 Virtual Try-On 추론
        
        Args:
            client: Gemini API 클라이언트
            contents: 입력 콘텐츠 리스트 (텍스트 + 이미지들)
            temperature: 결과의 다양성
        
        Returns:
            tuple: (이미지 바이너리 데이터, 비용 정보)
        """
        model_name = "gemini-2.5-flash-image"
        
        # Safety settings (Genai SDK format)
        safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.OFF
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.OFF
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.OFF
            )
        ]
        
        try:
            # Gemini API 호출 (이미지만 생성하도록 설정)
            response = await self.aio_client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=[types.Modality.IMAGE],  # 이미지만 생성
                    temperature=temperature,
                    image_config=types.ImageConfig(
                        aspect_ratio="1:1",
                    ),
                    safety_settings=safety_settings
                )
            )
            
            # 비용 계산
            usage_data = await self.calculate_vto_cost(response.usage_metadata if hasattr(response, 'usage_metadata') else None)
            
            # 응답에서 이미지 데이터 추출
            if hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if hasattr(part.inline_data, 'data'):
                                return part.inline_data.data, usage_data
            
            return None, usage_data
            
        except Exception as e:
            print(f"Inference Error: {e}")
            return None, None
        
    async def calculate_vto_cost(self, usage_metadata) -> LiteLLMUsageData:
        """
        Gemini 2.5 Flash Image 모델의 토큰 사용량 및 비용 계산
        
        Args:
            usage_metadata: Gemini API 응답의 사용량 메타데이터
        
        Returns:
            LiteLLMUsageData: 토큰 및 비용 정보
        """
        if not usage_metadata:
            return LiteLLMUsageData(
                total_token_count=0,
                prompt_token_count=0,
                candidates_token_count=0,
                output_token_count=0,
                cached_content_token_count=0,
                thoughts_token_count=0,
                model_name="gemini-2.5-flash-image",
                cost_usd=0.0,
                cost_krw=0.0,
                task_name="virtual_tryon"
            )
        
        # None 값 방어 처리
        prompt_token_count = usage_metadata.prompt_token_count or 0
        candidates_token_count = usage_metadata.candidates_token_count or 0
        total_token_count = usage_metadata.total_token_count or 0
        
        # 토큰 세부사항 추출 (텍스트/이미지 분리)
        prompt_text_tokens = 0
        prompt_image_tokens = 0
        if hasattr(usage_metadata, 'prompt_tokens_details') and usage_metadata.prompt_tokens_details:
            for detail in usage_metadata.prompt_tokens_details:
                if 'TEXT' in str(detail.modality):
                    prompt_text_tokens = detail.token_count or 0
                elif 'IMAGE' in str(detail.modality):
                    prompt_image_tokens += detail.token_count or 0
        
        output_image_tokens = 0
        if hasattr(usage_metadata, 'candidates_tokens_details') and usage_metadata.candidates_tokens_details:
            for detail in usage_metadata.candidates_tokens_details:
                if 'IMAGE' in str(detail.modality):
                    output_image_tokens += detail.token_count or 0
        
        # Gemini 2.5 Flash Image 가격 정보
        INPUT_PRICE_PER_1M_TOKENS = 0.35
        OUTPUT_PRICE_PER_1M_TOKENS = 30.00  # USD
        USD_TO_KRW_RATE = 1380
        
        # 비용 계산
        input_cost = (prompt_token_count / 1_000_000) * INPUT_PRICE_PER_1M_TOKENS
        output_cost = (candidates_token_count / 1_000_000) * OUTPUT_PRICE_PER_1M_TOKENS
        total_cost = input_cost + output_cost
        
        total_cost_krw = total_cost * USD_TO_KRW_RATE
        
        # 디버깅 로그
        print(f"\n=== 토큰 사용량 상세 ===")
        print(f"입력 토큰: {prompt_token_count} (텍스트: {prompt_text_tokens}, 이미지: {prompt_image_tokens})")
        print(f"출력 토큰: {candidates_token_count} (이미지: {output_image_tokens})")
        print(f"총 토큰: {total_token_count}")
        print(f"입력 비용: ${input_cost:.6f}")
        print(f"출력 비용: ${output_cost:.6f}")
        print(f"총 비용: ${total_cost:.6f} (약 {total_cost_krw:,.2f}원)")
        print(f"======================\n")
        
        return LiteLLMUsageData(
            total_token_count=total_token_count,
            prompt_token_count=prompt_token_count,
            candidates_token_count=candidates_token_count,
            output_token_count=candidates_token_count,
            cached_content_token_count=0,
            thoughts_token_count=0,
            model_name="gemini-2.5-flash-image",
            cost_usd=round(total_cost, 6),
            cost_krw=round(total_cost_krw, 2),
            task_name="virtual_tryon"
        )
        
    async def sum_usage_data(self, usage_data_list: List[LiteLLMUsageData]) -> LiteLLMUsageData:
        """
        여러 LiteLLMUsageData를 합산
        
        Args:
            usage_data_list: LiteLLMUsageData 리스트
        
        Returns:
            LiteLLMUsageData: 합산된 비용 정보
        """
        total_token_count = sum(u.total_token_count for u in usage_data_list)
        prompt_token_count = sum(u.prompt_token_count for u in usage_data_list)
        candidates_token_count = sum(u.candidates_token_count for u in usage_data_list)
        output_token_count = sum(u.output_token_count for u in usage_data_list)
        cached_content_token_count = sum(u.cached_content_token_count for u in usage_data_list)
        thoughts_token_count = sum(u.thoughts_token_count for u in usage_data_list)
        cost_usd = sum(u.cost_usd for u in usage_data_list)
        cost_krw = sum(u.cost_krw for u in usage_data_list)
        
        return LiteLLMUsageData(
            total_token_count=total_token_count,
            prompt_token_count=prompt_token_count,
            candidates_token_count=candidates_token_count,
            output_token_count=output_token_count,
            cached_content_token_count=cached_content_token_count,
            thoughts_token_count=thoughts_token_count,
            model_name="gemini-2.5-flash-image",
            cost_usd=round(cost_usd, 6),
            cost_krw=round(cost_krw, 2),
            task_name="virtual_tryon"
        )
    
    async def load_clothes_images(
        self,
        front_image_path: Optional[str],
        back_image_path: Optional[str]
    ) -> Tuple[Optional[Image.Image], Optional[Image.Image]]:
        """
        의류 이미지를 로드하는 헬퍼 함수
        
        Args:
            front_image_path: 앞면 의류 이미지 경로
            back_image_path: 뒷면 의류 이미지 경로
        
        Returns:
            Tuple: (앞면 이미지, 뒷면 이미지)
        """
        front_clothes_img = Image.open(front_image_path) if front_image_path else None
        back_clothes_img = Image.open(back_image_path) if back_image_path else None
        return front_clothes_img, back_clothes_img
    
    async def execute_vto_inference(
        self,
        contents_list: List,
        front_has_images: bool,
        back_has_images: bool,
        image_count: int,
        temperature: float,
        include_side: bool = False
    ) -> Dict:
        """
        Virtual Try-On 추론을 실행하고 결과를 반환하는 공통 로직
        
        Args:
            contents_list: Gemini API에 전달할 콘텐츠 리스트
            front_has_images: 앞면 이미지 존재 여부
            back_has_images: 뒷면 이미지 존재 여부
            image_count: 생성할 이미지 개수
            temperature: 결과의 다양성
            include_side: 측면 이미지 포함 여부
        
        Returns:
            Dict: 응답 결과 (앞면/뒷면/측면 이미지 리스트 및 비용 정보)
        """
        print(f"총 생성할 이미지 수: {len(contents_list)}")
        
        # 모든 조합에 대해 병렬 호출
        tasks = [self.virtual_tryon_inference(contents, temperature) for contents in contents_list]
        responses = await asyncio.gather(*tasks)
        
        # 결과 분리
        result_image_list, usage_data_list = zip(*responses) if responses else ([], [])
        
        # None이 아닌 usage_data만 필터링
        usage_data_list = [usage for usage in usage_data_list if usage is not None]
        
        # 비용 정보 합산
        if usage_data_list:
            total_usage = await self.sum_usage_data(usage_data_list)
        else:
            total_usage = await self.calculate_vto_cost(None)
        
        # 결과 이미지를 뷰별로 분리
        front_image_list = []
        back_image_list = []
        side_image_list = []
        
        idx = 0
        # 정면 의류가 있으면 정면 결과가 먼저 생성됨
        if front_has_images:
            front_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
            idx += image_count
        
        # 뒷면 의류가 있으면 뒷면 결과가 생성됨
        if back_has_images:
            back_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
            idx += image_count
        
        # 측면 이미지가 포함되면 측면 결과가 마지막에 생성됨
        if include_side and front_has_images:
            side_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
        
        # 모든 이미지를 하나의 리스트로 합침
        all_images = front_image_list + back_image_list + (side_image_list if include_side else [])
        
        return {
            "response": all_images,
            "front_images": front_image_list,
            "back_images": back_image_list,
            "side_images": side_image_list if include_side else [],
            "usage": total_usage,
            "debug_info": {
                "front_count": len(front_image_list),
                "back_count": len(back_image_list),
                "side_count": len(side_image_list) if include_side else 0,
                "total_count": len(all_images),
                "requested_count_per_view": image_count,
                "model_name": "gemini-2.5-flash-image",
            }
        }