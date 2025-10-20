import json
import asyncio
from typing import Dict, Optional, List
from core.litellm_hander.schema import ClothesImageAnalysis, LiteLLMUsageData
from core.litellm_hander.process import LiteLLMHandler
from google import genai
from google.genai import types
import os
from PIL import Image as PILImage
from configs import settings


def sum_usage_data(usage_data_list: List[LiteLLMUsageData]) -> LiteLLMUsageData:
    """
    여러 LiteLLMUsageData를 합산 (vto_mino의 calculate_cost_info_multi 방식)
    
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


async def analyze_clothes_image(image_path: str) -> ClothesImageAnalysis:
    llm_handler = LiteLLMHandler()
    image_content = await llm_handler.convert_litellm_image_object(image_path)
    response = await llm_handler.analyze_clothes_image(image_content)
    contents = json.loads(response.choices[0].message.content)
    clothes_image_analysis = ClothesImageAnalysis(**contents)
    return clothes_image_analysis

def calculate_vto_cost(usage_metadata) -> LiteLLMUsageData:
    """
    Gemini 2.5 Flash Image 모델의 토큰 사용량 및 비용 계산
    vto_mino.py의 calculate_cost_info_dict 방식 적용
    
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
    INPUT_PRICE_PER_1M_TOKENS = 0.35    # USD (vto_mino.py 기준)
    OUTPUT_PRICE_PER_1M_TOKENS = 30.00  # USD (이미지 생성이라서 높음)
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

async def virtual_tryon_inference(client, contents, temperature: float = 1.0):
    """
    단일 Virtual Try-On 추론 (vto_mino 방식)
    
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
        response = await client.models.generate_content(
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
        usage_data = calculate_vto_cost(response.usage_metadata if hasattr(response, 'usage_metadata') else None)
        
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


async def virtual_tryon(
    front_image_path: Optional[str], 
    back_image_path: Optional[str], 
    prompt: str, 
    temperature: float = 1.0,
    image_count: int = 1,
    model_folder: str = "default"
) -> Dict:
    """
    Virtual Try-On: 앞면/뒷면 이미지와 프롬프트로 가상 착장 생성 (vto_mino의 virtual_tryon_fixed 방식)
    
    Args:
        front_image_path: 앞면 의류 이미지 경로 (Optional)
        back_image_path: 뒷면 의류 이미지 경로 (Optional)
        prompt: VTO 프롬프트
        temperature: 결과의 다양성 (기본값: 1.0)
        image_count: 생성할 이미지 개수 (기본값: 1)
        model_folder: 사용할 모델 폴더 (기본값: "default")
    
    Returns:
        Dict: 응답 결과 (앞면/뒷면/측면 이미지 리스트 및 비용 정보)
    """
    # 입력 검증 - 최소 1개 이미지 필요
    if not front_image_path and not back_image_path:
        raise ValueError("최소 1개의 이미지(앞면 또는 뒷면)를 제공해야 합니다.")
    
    # Google Genai SDK를 직접 사용
    client = genai.Client(api_key=settings.gemini_api_key)
    aio_client = client.aio
    
    # 고정 사람 모델 이미지 로드
    model_front_path = os.path.join("assets", "default_model", model_folder, "front.png")
    model_back_path = os.path.join("assets", "default_model", model_folder, "back.png")
    model_side_path = os.path.join("assets", "default_model", model_folder, "side.png")
    
    # 파일 존재 확인
    if not os.path.exists(model_front_path):
        raise FileNotFoundError(f"정면 모델 이미지를 찾을 수 없습니다: {model_front_path}")
    if not os.path.exists(model_back_path):
        raise FileNotFoundError(f"뒷면 모델 이미지를 찾을 수 없습니다: {model_back_path}")
    if not os.path.exists(model_side_path):
        raise FileNotFoundError(f"측면 모델 이미지를 찾을 수 없습니다: {model_side_path}")
    
    model_front_img = PILImage.open(model_front_path)
    model_back_img = PILImage.open(model_back_path)
    model_side_img = PILImage.open(model_side_path)
    
    # 의류 이미지 로드
    front_clothes_img = PILImage.open(front_image_path) if front_image_path else None
    back_clothes_img = PILImage.open(back_image_path) if back_image_path else None
    
    # 로깅
    uploaded_types = []
    if front_clothes_img:
        uploaded_types.append("앞면")
    if back_clothes_img:
        uploaded_types.append("뒷면")
    
    print(f"\n=== Virtual Try-On 실행 ===")
    print(f"업로드된 의류 이미지: {', '.join(uploaded_types)}")
    print(f"생성할 이미지 개수 (각 뷰당): {image_count}")
    print(f"Temperature: {temperature}")
    print(f"모델 폴더: {model_folder}")
    print(f"프롬프트: {prompt[:100]}...")
    print(f"========================\n")
    
    # contents_list 구성: 각 조합에 대해 image_count만큼 생성
    contents_list = []
    
    # 정면 뷰: model_front + front_clothes (앞면 의류가 있으면)
    if front_clothes_img:
        for _ in range(image_count):
            contents_list.append([prompt, model_front_img, front_clothes_img])
    
    # 뒷면 뷰: model_back + back_clothes (뒷면 의류가 있으면)
    if back_clothes_img:
        for _ in range(image_count):
            contents_list.append([prompt, model_back_img, back_clothes_img])
    
    # 측면 뷰: model_side + front_clothes (앞면 의류가 있으면)
    # if front_clothes_img:
    #     for _ in range(image_count):
    #         contents_list.append([prompt, model_side_img, front_clothes_img])
    
    print(f"총 생성할 이미지 수: {len(contents_list)}")
    
    # 모든 조합에 대해 병렬 호출 (vto_mino 방식)
    tasks = [virtual_tryon_inference(aio_client, contents, temperature) for contents in contents_list]
    responses = await asyncio.gather(*tasks)
    
    # 결과 분리
    result_image_list, usage_data_list = zip(*responses) if responses else ([], [])
    
    # None이 아닌 usage_data만 필터링
    usage_data_list = [usage for usage in usage_data_list if usage is not None]
    
    # 비용 정보 합산
    if usage_data_list:
        total_usage = sum_usage_data(usage_data_list)
    else:
        total_usage = calculate_vto_cost(None)
    
    # 결과 이미지를 뷰별로 분리 (vto_mino의 virtual_tryon_fixed 방식)
    front_image_list = []
    back_image_list = []
    side_image_list = []
    
    idx = 0
    # 정면 의류가 있으면 정면 결과가 먼저 생성됨
    if front_clothes_img:
        front_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
        idx += image_count
    
    # 뒷면 의류가 있으면 뒷면 결과가 생성됨
    if back_clothes_img:
        back_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
        idx += image_count
    
    # 정면 의류가 있으면 측면 결과가 마지막에 생성됨
    if front_clothes_img:
        side_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
    
    # 모든 이미지를 하나의 리스트로 합침
    all_images = front_image_list + back_image_list # + side_image_list
    
    print(f"\n=== Virtual Try-On 완료 ===")
    print(f"정면 이미지: {len(front_image_list)}개")
    print(f"뒷면 이미지: {len(back_image_list)}개")
    # print(f"측면 이미지: {len(side_image_list)}개")
    print(f"총 생성된 이미지: {len(all_images)}개")
    print(f"========================\n")
    
    return {
        "response": all_images,  # 모든 이미지 리스트 반환
        "front_images": front_image_list,
        "back_images": back_image_list,
        # "side_images": side_image_list,
        "usage": total_usage,
        "debug_info": {
            "front_count": len(front_image_list),
            "back_count": len(back_image_list),
            # "side_count": len(side_image_list),
            "total_count": len(all_images),
            "requested_count_per_view": image_count,
            "model_name": "gemini-2.5-flash-image",
        }
    }

