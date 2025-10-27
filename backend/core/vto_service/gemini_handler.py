from typing import Union, Optional, Tuple, Dict, List
import aiofiles
import asyncio
import io
from google import genai
from google.genai import types
from PIL import Image
import numpy as np
from configs import settings
from core.litellm_hander.schema import LiteLLMUsageData


class GeminiProcesser:
    """Gemini API를 사용한 Virtual Try-On 처리 클래스"""
    
    # 클래스 레벨 상수
    MODEL_NAME = "gemini-2.5-flash-image"
    TASK_NAME = "virtual_tryon"
    
    # 가격 정보 (USD)
    INPUT_PRICE_PER_1M_TOKENS = 0.35
    OUTPUT_PRICE_PER_1M_TOKENS = 30.00
    USD_TO_KRW_RATE = 1380
    
    # 재시도 설정
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # 초
    RETRY_BACKOFF_MULTIPLIER = 2.0
    
    # 배치 처리 설정
    MAX_CONCURRENT_REQUESTS = 10  # 동시 요청 최대 개수
    
    # Safety settings (클래스 레벨에서 한 번만 생성)
    SAFETY_SETTINGS = [
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
    
    def __init__(self, verbose: bool = True):
        """
        Args:
            verbose: 로깅 출력 여부 (기본값: True)
        """
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.aio_client = self.client.aio
        self.verbose = verbose
        
    def _extract_image_from_response(self, response) -> Optional[bytes]:
        """응답에서 이미지 데이터를 추출하는 헬퍼 메소드"""
        if not hasattr(response, 'candidates') or not response.candidates:
            return None
        
        candidate = response.candidates[0]
        if not hasattr(candidate, 'content') or not hasattr(candidate.content, 'parts'):
            return None
        
        for part in candidate.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                if hasattr(part.inline_data, 'data'):
                    return part.inline_data.data
        
        return None
        
    def _create_usage_data(
        self,
        total_token_count: int = 0,
        prompt_token_count: int = 0,
        candidates_token_count: int = 0,
        cost_usd: float = 0.0,
        cost_krw: float = 0.0
    ) -> LiteLLMUsageData:
        """LiteLLMUsageData 생성 헬퍼 메소드"""
        return LiteLLMUsageData(
            total_token_count=total_token_count,
            prompt_token_count=prompt_token_count,
            candidates_token_count=candidates_token_count,
            output_token_count=candidates_token_count,
            cached_content_token_count=0,
            thoughts_token_count=0,
            model_name=self.MODEL_NAME,
            cost_usd=round(cost_usd, 6),
            cost_krw=round(cost_krw, 2),
            task_name=self.TASK_NAME
        )
    
    def _extract_token_details(self, usage_metadata) -> Tuple[int, int]:
        """토큰 세부사항을 추출하는 헬퍼 메소드 (텍스트/이미지 분리)"""
        prompt_text_tokens = 0
        prompt_image_tokens = 0
        
        if hasattr(usage_metadata, 'prompt_tokens_details') and usage_metadata.prompt_tokens_details:
            for detail in usage_metadata.prompt_tokens_details:
                modality_str = str(detail.modality)
                if 'TEXT' in modality_str:
                    prompt_text_tokens = detail.token_count or 0
                elif 'IMAGE' in modality_str:
                    prompt_image_tokens += detail.token_count or 0
        
        return prompt_text_tokens, prompt_image_tokens
    
    def _split_images_by_view(
        self,
        result_image_list: List,
        front_has_images: bool,
        back_has_images: bool,
        image_count: int,
        include_side: bool
    ) -> Tuple[List, List, List]:
        """결과 이미지를 뷰별로 분리하는 헬퍼 메소드"""
        front_images, back_images, side_images = [], [], []
        idx = 0
        
        if front_has_images:
            front_images = [img for img in result_image_list[idx:idx+image_count] if img is not None]
            idx += image_count
        
        if back_has_images:
            back_images = [img for img in result_image_list[idx:idx+image_count] if img is not None]
            idx += image_count
        
        if include_side and front_has_images:
            side_images = [img for img in result_image_list[idx:idx+image_count] if img is not None]
        
        return front_images, back_images, side_images


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
            # PIL Image를 PNG bytes로 변환
            buffer = io.BytesIO()
            data.save(buffer, format='PNG')
            buffer.seek(0)
            data = types.Part.from_bytes(
                data=buffer.getvalue(),
                mime_type="image/png",
            )            
        elif isinstance(image, bytes):
            data = types.Part.from_bytes(
                data=image,
                mime_type="image/png",
            )
        elif isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
            if pil_image.width > 1024 or pil_image.height > 1024:
                pil_image.thumbnail([1024, 1024], Image.Resampling.LANCZOS)
            # PIL Image를 PNG bytes로 변환
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            buffer.seek(0)
            data = types.Part.from_bytes(
                data=buffer.getvalue(),
                mime_type="image/png",
            )
        else:
            # PIL Image를 PNG bytes로 변환
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            data = types.Part.from_bytes(
                data=buffer.getvalue(),
                mime_type="image/png",
            )
        return data

    async def virtual_tryon_inference(self, contents, temperature: float = 1.0, top_p: float = 0.95):
        """
        단일 Virtual Try-On 추론 (재시도 로직 포함)
        
        Args:
            contents: 입력 콘텐츠 리스트 (텍스트 + 이미지들)
            temperature: 결과의 다양성
            top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
        
        Returns:
            tuple: (이미지 바이너리 데이터, 비용 정보)
        """
        last_exception = None
        delay = self.RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Gemini API 호출 (이미지만 생성하도록 설정)
                response = await self.aio_client.models.generate_content(
                    model=self.MODEL_NAME,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=[types.Modality.IMAGE],
                        temperature=temperature,
                        top_p=top_p,
                        image_config=types.ImageConfig(aspect_ratio="1:1"),
                        safety_settings=self.SAFETY_SETTINGS
                    )
                )
                
                # 비용 계산
                usage_data = await self.calculate_vto_cost(
                    response.usage_metadata if hasattr(response, 'usage_metadata') else None
                )
                
                # 응답에서 이미지 데이터 추출
                image_data = self._extract_image_from_response(response)
                return image_data, usage_data
                
            except Exception as e:
                last_exception = e
                error_str = str(e)
                
                # 502, 503, 429 등 재시도 가능한 에러인지 확인
                is_retryable = any(code in error_str for code in ['502', '503', '429', 'Bad Gateway', 'Service Unavailable', 'Too Many Requests'])
                
                if is_retryable and attempt < self.MAX_RETRIES - 1:
                    if self.verbose:
                        print(f"⚠️  재시도 가능한 에러 발생 (시도 {attempt + 1}/{self.MAX_RETRIES}): {error_str[:100]}")
                        print(f"   {delay}초 후 재시도...")
                    
                    await asyncio.sleep(delay)
                    delay *= self.RETRY_BACKOFF_MULTIPLIER
                else:
                    if self.verbose:
                        print(f"❌ Inference Error (시도 {attempt + 1}/{self.MAX_RETRIES}): {error_str[:200]}")
                    break
        
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
            return self._create_usage_data()
        
        # None 값 방어 처리
        prompt_token_count = usage_metadata.prompt_token_count or 0
        candidates_token_count = usage_metadata.candidates_token_count or 0
        total_token_count = usage_metadata.total_token_count or 0
        
        # 비용 계산
        input_cost = (prompt_token_count / 1_000_000) * self.INPUT_PRICE_PER_1M_TOKENS
        output_cost = (candidates_token_count / 1_000_000) * self.OUTPUT_PRICE_PER_1M_TOKENS
        total_cost = input_cost + output_cost
        total_cost_krw = total_cost * self.USD_TO_KRW_RATE
        
        # 디버깅 로그 (verbose 모드일 때만)
        if self.verbose:
            prompt_text_tokens, prompt_image_tokens = self._extract_token_details(usage_metadata)
            print(f"\n=== 토큰 사용량 상세 ===")
            print(f"입력 토큰: {prompt_token_count} (텍스트: {prompt_text_tokens}, 이미지: {prompt_image_tokens})")
            print(f"출력 토큰: {candidates_token_count}")
            print(f"총 토큰: {total_token_count}")
            print(f"입력 비용: ${input_cost:.6f}")
            print(f"출력 비용: ${output_cost:.6f}")
            print(f"총 비용: ${total_cost:.6f} (약 {total_cost_krw:,.2f}원)")
            print(f"======================\n")
        
        return self._create_usage_data(
            total_token_count=total_token_count,
            prompt_token_count=prompt_token_count,
            candidates_token_count=candidates_token_count,
            cost_usd=total_cost,
            cost_krw=total_cost_krw
        )
        
    async def sum_usage_data(self, usage_data_list: List[LiteLLMUsageData]) -> LiteLLMUsageData:
        """
        여러 LiteLLMUsageData를 합산
        
        Args:
            usage_data_list: LiteLLMUsageData 리스트
        
        Returns:
            LiteLLMUsageData: 합산된 비용 정보
        """
        return self._create_usage_data(
            total_token_count=sum(u.total_token_count for u in usage_data_list),
            prompt_token_count=sum(u.prompt_token_count for u in usage_data_list),
            candidates_token_count=sum(u.candidates_token_count for u in usage_data_list),
            cost_usd=sum(u.cost_usd for u in usage_data_list),
            cost_krw=sum(u.cost_krw for u in usage_data_list)
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

    async def _run_with_semaphore(self, semaphore: asyncio.Semaphore, contents, temperature: float, top_p: float):
        """세마포어를 사용하여 동시 요청 수를 제한하는 헬퍼 메소드"""
        async with semaphore:
            return await self.virtual_tryon_inference(contents, temperature, top_p)
    
    async def execute_vto_inference(
        self,
        contents_list: List,
        front_has_images: bool,
        back_has_images: bool,
        image_count: int,
        temperature: float,
        include_side: bool = False,
        top_p: float = 0.95
    ) -> Dict:
        """
        Virtual Try-On 추론을 실행하고 결과를 반환하는 공통 로직
        (동시 요청 수 제한 및 재시도 로직 포함)
        
        Args:
            contents_list: Gemini API에 전달할 콘텐츠 리스트
            front_has_images: 앞면 이미지 존재 여부
            back_has_images: 뒷면 이미지 존재 여부
            image_count: 생성할 이미지 개수
            temperature: 결과의 다양성
            include_side: 측면 이미지 포함 여부
            top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
        
        Returns:
            Dict: 응답 결과 (앞면/뒷면/측면 이미지 리스트 및 비용 정보)
        """
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"📸 총 생성할 이미지 수: {len(contents_list)}")
            print(f"⚙️  동시 요청 제한: 최대 {self.MAX_CONCURRENT_REQUESTS}개")
            print(f"🔄 재시도 설정: 최대 {self.MAX_RETRIES}회, 초기 대기 {self.RETRY_DELAY}초")
            print(f"🔄 Top-p: {top_p}")
            print(f"🔄 Temperature: {temperature}")
            print(f"{'='*50}\n")
        
        # 세마포어를 사용하여 동시 요청 수 제한
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        
        # 모든 조합에 대해 병렬 호출 (동시 요청 수 제한)
        tasks = [self._run_with_semaphore(semaphore, contents, temperature, top_p) for contents in contents_list]
        responses = await asyncio.gather(*tasks)
        
        # 결과 분리
        result_image_list, usage_data_list = zip(*responses) if responses else ([], [])
        
        # None이 아닌 usage_data만 필터링하여 비용 합산
        valid_usage_data = [usage for usage in usage_data_list if usage is not None]
        total_usage = await self.sum_usage_data(valid_usage_data) if valid_usage_data else await self.calculate_vto_cost(None)
        
        # 결과 이미지를 뷰별로 분리
        front_images, back_images, side_images = self._split_images_by_view(
            result_image_list, front_has_images, back_has_images, image_count, include_side
        )
        
        # 모든 이미지를 하나의 리스트로 합침
        all_images = front_images + back_images + (side_images if include_side else [])
        
        # 성공/실패 통계
        success_count = len([img for img in result_image_list if img is not None])
        fail_count = len(result_image_list) - success_count
        
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"✅ 성공: {success_count}개")
            if fail_count > 0:
                print(f"❌ 실패: {fail_count}개")
            print(f"{'='*50}\n")
        
        return {
            "response": all_images,
            "front_images": front_images,
            "back_images": back_images,
            "side_images": side_images if include_side else [],
            "usage": total_usage,
            "debug_info": {
                "front_count": len(front_images),
                "back_count": len(back_images),
                "side_count": len(side_images) if include_side else 0,
                "total_count": len(all_images),
                "requested_count_per_view": image_count,
                "success_count": success_count,
                "fail_count": fail_count,
                "model_name": self.MODEL_NAME,
            }
        }