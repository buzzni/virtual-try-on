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
        
    @staticmethod
    def _pil_to_png_bytes(image: Image.Image) -> bytes:
        """PIL Image를 PNG bytes로 변환"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    @staticmethod
    def _extract_image_from_response(response) -> Optional[bytes]:
        """응답에서 이미지 데이터 추출"""
        try:
            return response.candidates[0].content.parts[0].inline_data.data
        except (AttributeError, IndexError):
            return None
    
    def _create_usage_data(self, total_token_count: int = 0, prompt_token_count: int = 0,
                        candidates_token_count: int = 0, cost_usd: float = 0.0,
                        cost_krw: float = 0.0) -> LiteLLMUsageData:
        """LiteLLMUsageData 생성"""
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
    
    @staticmethod
    def _extract_token_details(usage_metadata) -> Tuple[int, int]:
        """토큰 세부사항 추출 (텍스트/이미지)"""
        text_tokens = image_tokens = 0
        
        if hasattr(usage_metadata, 'prompt_tokens_details') and usage_metadata.prompt_tokens_details:
            for detail in usage_metadata.prompt_tokens_details:
                if 'TEXT' in str(detail.modality):
                    text_tokens = detail.token_count or 0
                elif 'IMAGE' in str(detail.modality):
                    image_tokens += detail.token_count or 0
        
        return text_tokens, image_tokens

    async def create_image_content(self, image: Union[Image.Image, bytes, str, np.ndarray], 
                                use_resize: bool = False) -> types.Part:
        """이미지를 Gemini API 형식으로 변환"""
        
        # 문자열 경로인 경우: 파일 읽기
        if isinstance(image, str):
            async with aiofiles.open(image, "rb") as f:
                image_bytes = await f.read()
            return types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        
        # bytes인 경우: 그대로 사용
        if isinstance(image, bytes):
            return types.Part.from_bytes(data=image, mime_type="image/png")
        
        # numpy array인 경우: PIL Image로 변환
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # PIL Image 처리 (resize 옵션 적용)
        if use_resize and (image.width > 1024 or image.height > 1024):
            image.thumbnail([1024, 1024], Image.Resampling.LANCZOS)
        
        return types.Part.from_bytes(
            data=self._pil_to_png_bytes(image),
            mime_type="image/png"
        )
    
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
        image_path: Optional[str],
    ) -> Optional[Image.Image]:
        """
        의류 이미지를 로드하는 헬퍼 함수
        
        Args:
            image_path: 의류 이미지 경로
        
        Returns:
            Optional[Image.Image]: 의류 이미지
        """
        clothes_img = Image.open(image_path) if image_path else None
        return clothes_img

    async def gemini_image_inference(self, contents, temperature: float = 1.0, top_p: float = 0.95, aspect_ratio: str = "1:1"):
        """
        단일 이미지 추론 (재시도 로직 포함)
        
        Args:
            contents: 입력 콘텐츠 리스트 (텍스트 + 이미지들)
            temperature: 결과의 다양성
            top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
        
        Returns:
            tuple: (이미지 바이너리 데이터, 비용 정보)
        """
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
                        image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
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
    
    async def _run_with_semaphore(self, semaphore: asyncio.Semaphore, contents, temperature: float, top_p: float, aspect_ratio: str):
        """세마포어를 사용하여 동시 요청 수를 제한하는 헬퍼 메소드"""
        async with semaphore:
            return await self.gemini_image_inference(contents, temperature, top_p, aspect_ratio)
        
    async def execute_image_inference(
        self,
        contents_list: List,
        image_count: int,
        temperature: float,
        top_p: float = 0.95,
        aspect_ratio: str = "1:1"
    ) -> Dict:
        """
        단일 이미지 추론을 실행하고 결과를 반환하는 공통 로직
        (동시 요청 수 제한 및 재시도 로직 포함)
        
        Args:
            contents_list: Gemini API에 전달할 콘텐츠 리스트
            temperature: 결과의 다양성
            top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
        
        Returns:
            Dict: 응답 결과 (이미지 리스트 및 비용 정보)
        """
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"📸 총 생성할 이미지 수: {image_count}")
            print(f"⚙️  동시 요청 제한: 최대 {self.MAX_CONCURRENT_REQUESTS}개")
            print(f"🔄 재시도 설정: 최대 {self.MAX_RETRIES}회, 초기 대기 {self.RETRY_DELAY}초")
            print(f"🔄 Top-p: {top_p}")
            print(f"🔄 Temperature: {temperature}")
            print(f"{'='*50}\n")
        
        # 세마포어를 사용하여 동시 요청 수 제한
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        
        recursive_contents_list = []
        for _ in range(image_count):
            recursive_contents_list.append(contents_list)
        
        # 모든 조합에 대해 병렬 호출 (동시 요청 수 제한)
        tasks = [self._run_with_semaphore(semaphore, contents, temperature, top_p, aspect_ratio) for contents in recursive_contents_list]
        responses = await asyncio.gather(*tasks)
        
        # 결과 분리
        result_image_list, usage_data_list = zip(*responses) if responses else ([], [])
        
        # None이 아닌 usage_data만 필터링하여 비용 합산
        valid_usage_data = [usage for usage in usage_data_list if usage is not None]
        total_usage = await self.sum_usage_data(valid_usage_data) if valid_usage_data else await self.calculate_vto_cost(None)
        
        all_images = result_image_list
        
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
            "usage": total_usage,
            "debug_info": {
                "total_count": len(all_images),
                "success_count": success_count,
                "fail_count": fail_count,
                "model_name": self.MODEL_NAME,
            }
        }