"""
Gemini API 클라이언트 모듈
Virtual Try-On을 위한 AI 이미지 생성 기능

이 모듈은 3가지 모드의 가상 착용 기능을 제공합니다:
1. Single Mode: 상품 이미지 생성 (1개 이미지)
2. Dual Mode: 사람 + 옷 이미지 (2개 이미지)  
3. Triple Mode: 사람 + 옷1 + 옷2 이미지 (3개 이미지)

주요 기능:
- 통합된 API 호출 함수 (virtual_tryon_unified)
- 토큰 사용량 및 비용 계산
- 에러 처리 및 로깅
"""

from google import genai
from google.genai import types
import asyncio
from PIL import Image
from io import BytesIO
from typing import List

# ==================================================================================
# 1. API 클라이언트 설정
# ==================================================================================

# API 키 설정
PRODUCT_ATTRIBUTE_GEMINI_API_KEY = "AIzaSyCN2e9RKYUMONd7Qvol2bXiYUcBQUh_gOM"

# ==================================================================================
# 2. Virtual Try-On 통합 함수
# ==================================================================================

async def virtual_tryon_unified(images, text_input, mode="single", image_count=1, temperature=1.0) -> tuple[List[Image.Image] | None, str]:
    """
    통합된 가상 착용 함수 - 모든 모드를 지원
    
    Args:
        images: 이미지 리스트 (numpy 배열들의 리스트)
            - Single Mode: [input_image]
            - Dual Mode: [person_image, clothes_image]
            - Triple Mode: [person_image, clothes1_image, clothes2_image]
        text_input: 사용자가 입력한 프롬프트
        mode: "single", "dual", "triple"
        image_count: 생성할 결과 이미지 개수 (기본값: 1)
        temperature: 생성 옵션 (기본값: 1.0)
    
    Returns:
        tuple: (결과이미지 리스트, 정보텍스트)
    """
    client = genai.Client(api_key=PRODUCT_ATTRIBUTE_GEMINI_API_KEY)
    aio_client = client.aio
    
    # 입력 검증
    if not images or len(images) == 0:
        return None, "이미지를 업로드해주세요."
    
    # 모드별 이미지 개수 검증
    expected_counts = {"single": 1, "dual": 2, "triple": 3}
    if len(images) != expected_counts.get(mode, 1):
        return None, f"{mode} 모드에서는 {expected_counts.get(mode, 1)}개의 이미지가 필요합니다."
    
    # 각 이미지가 None인지 검증
    for i, img in enumerate(images):
        if img is None:
            image_names = ["입력 이미지", "사람 이미지", "옷 이미지", "옷1 이미지", "옷2 이미지"]
            return None, f"{image_names[i]}을(를) 업로드해주세요."
    
    try:
        # 이미지 처리 및 contents 구성
        pil_images = [Image.fromarray(img) for img in images]
        contents = [text_input] + pil_images
        
        # 로깅
        mode_texts = {
            "single": "상품 이미지 생성",
            "dual": "사람 + 옷 이미지",
            "triple": "사람 + 옷1 + 옷2 이미지"
        }
        print(f"이미지 입력 모드: {mode_texts.get(mode, mode)}")
        print(f"입력 이미지 개수: {len(images)}")
        print(f"생성할 이미지 개수: {image_count}")
        print(f"Temperature: {temperature}")
        print(f"프롬프트: {text_input}")
        
        # 동일한 contents로 image_count 만큼 병렬 호출
        tasks = [virtual_tryon_inference(aio_client, contents, temperature) for _ in range(image_count)]
        
        responses = await asyncio.gather(*tasks)
        
        result_image_list, info_dict_list = zip(*responses)
        
        # None이 아닌 이미지만 필터링
        result_image_list = [img for img in result_image_list if img is not None]
        
        # 비용 정보 합산
        info_text = calculate_cost_info_multi(info_dict_list)
        
        return result_image_list, info_text
            
    except Exception as e:
        print(f"Error: {e}")
        return None, f"이미지 생성 중 오류가 발생했습니다: {str(e)}"

async def virtual_tryon_inference(client, contents, temperature) -> tuple[Image.Image | None, dict]:
    """
    가상 착용 추론 함수
    
    Args:
        client: Gemini API 클라이언트
        contents: 입력 콘텐츠 리스트 (텍스트 + 이미지들)
        temperature: 생성 옵션
    
    Returns:
        tuple: (결과 이미지, 비용 정보 딕셔너리)
    """
    # info_dict 초기화
    info_dict = {}
    
    try:
        # Gemini API 호출
        response = await client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.IMAGE],
                temperature=temperature,    # 결과의 다양성 (높을수록 무작위)
                image_config=types.ImageConfig(
                    aspect_ratio="1:1",
                ),
                safety_settings=[
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
            )
        )
        
        # 토큰 사용량 및 비용 계산
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            info_dict = calculate_cost_info_dict(response.usage_metadata)
        
        # 응답에서 이미지 추출
        image_parts = [
            part.inline_data.data
            for part in response.candidates[0].content.parts
            if part.inline_data
        ]
        
        # 응답 parts 개별 처리로 경고 방지
        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if text_parts:
            print("AI 응답 텍스트:", " ".join(text_parts))
        
        if image_parts:
            result_image = Image.open(BytesIO(image_parts[0]))
            return result_image, info_dict
        else:
            return None, info_dict
    
    except Exception as e:
        print(f"Inference Error: {e}")
        return None, info_dict

def calculate_cost_info_dict(usage_metadata) -> dict:
    """
    토큰 사용량을 기반으로 비용 정보 딕셔너리 생성
    
    Args:
        usage_metadata: Gemini API 응답의 사용량 메타데이터
    
    Returns:
        dict: 비용 정보 딕셔너리
    """
    # None 값 방어 처리
    prompt_token_count = usage_metadata.prompt_token_count or 0
    candidates_token_count = usage_metadata.candidates_token_count or 0
    total_token_count = usage_metadata.total_token_count or 0

    # 토큰 세부사항 추출 (None 값 방어)
    prompt_text_tokens = 0
    prompt_image_tokens = 0
    if usage_metadata.prompt_tokens_details:
        for detail in usage_metadata.prompt_tokens_details:
            if 'TEXT' in str(detail.modality):
                prompt_text_tokens = detail.token_count or 0
            elif 'IMAGE' in str(detail.modality):
                prompt_image_tokens += detail.token_count or 0

    output_image_tokens = 0
    if usage_metadata.candidates_tokens_details:
        for detail in usage_metadata.candidates_tokens_details:
            if 'IMAGE' in str(detail.modality):
                output_image_tokens += detail.token_count or 0

    # 가격 정보 (Gemini 2.5 Flash Image)
    INPUT_PRICE_PER_1M_TOKENS = 0.35    # USD
    OUTPUT_PRICE_PER_1M_TOKENS = 30.00  # USD
    USD_TO_KRW_RATE = 1420

    # 비용 계산
    input_cost = (prompt_token_count / 1_000_000) * INPUT_PRICE_PER_1M_TOKENS
    output_cost = (candidates_token_count / 1_000_000) * OUTPUT_PRICE_PER_1M_TOKENS
    total_cost = input_cost + output_cost

    input_cost_krw = input_cost * USD_TO_KRW_RATE
    output_cost_krw = output_cost * USD_TO_KRW_RATE
    total_cost_krw = total_cost * USD_TO_KRW_RATE
    
    cost_dict = {
        "prompt_token_count": prompt_token_count,
        "prompt_text_tokens": prompt_text_tokens,
        "prompt_image_tokens": prompt_image_tokens,
        "candidates_token_count": candidates_token_count,
        "output_image_tokens": output_image_tokens,
        "total_token_count": total_token_count,
        "input_cost": input_cost,
        "input_cost_krw": input_cost_krw,
        "output_cost": output_cost,
        "output_cost_krw": output_cost_krw,
        "total_cost": total_cost,
        "total_cost_krw": total_cost_krw,
    }

    return cost_dict


def calculate_cost_info_multi(dict_list) -> str:
    """
    여러 비용 정보 딕셔너리를 합산하여 포맷된 문자열 반환
    
    Args:
        dict_list: 비용 정보 딕셔너리 리스트
    
    Returns:
        str: 포맷된 비용 정보 문자열
    """
    prompt_token_count = 0
    prompt_text_tokens = 0
    prompt_image_tokens = 0
    candidates_token_count = 0
    output_image_tokens = 0
    total_token_count = 0
    input_cost = 0
    input_cost_krw = 0
    output_cost = 0
    output_cost_krw = 0
    total_cost = 0
    total_cost_krw = 0

    for cost_dict in dict_list:
        prompt_token_count += cost_dict["prompt_token_count"]
        prompt_text_tokens += cost_dict["prompt_text_tokens"]
        prompt_image_tokens += cost_dict["prompt_image_tokens"]
        candidates_token_count += cost_dict["candidates_token_count"]
        output_image_tokens += cost_dict["output_image_tokens"]
        total_token_count += cost_dict["total_token_count"]
        input_cost += cost_dict["input_cost"]
        input_cost_krw += cost_dict["input_cost_krw"]
        output_cost += cost_dict["output_cost"]
        output_cost_krw += cost_dict["output_cost_krw"]
        total_cost += cost_dict["total_cost"]
        total_cost_krw += cost_dict["total_cost_krw"]

    return f"""
**토큰 사용량:**
- **입력 토큰:** {prompt_token_count}
  - 텍스트: {prompt_text_tokens}
  - 이미지: {prompt_image_tokens}
- **출력 토큰:** {candidates_token_count}
  - 이미지: {output_image_tokens}
- **총 토큰:** {total_token_count} 

**예상 비용:**
- **입력 비용:** ${input_cost:.6f} (약 {input_cost_krw:,.2f}원)
- **출력 비용:** ${output_cost:.6f} (약 {output_cost_krw:,.2f}원)
- **총 비용:** ${total_cost:.6f} (약 {total_cost_krw:,.2f}원)
"""  

async def virtual_tryon_fixed(clothing_info, images, text_input, image_count=1, temperature=1.0) -> tuple[List[Image.Image] | None, str]:
    """
    멀티 이미지 가상 착용 함수
    
    Args:
        clothing_info: 의상 정보 딕셔너리
            - {"category": str, "item": str, "subcategory": str}
        images: 옷 이미지 딕셔너리 (numpy 배열)
            - {"front": front_image or None, "back": back_image or None}
        text_input: 사용자가 입력한 프롬프트
        image_count: 생성할 결과 이미지 개수 (기본값: 1)
        temperature: 생성 옵션 (기본값: 1.0)
    Returns:
        tuple: (결과이미지, 정보텍스트)
    """
    client = genai.Client(api_key=PRODUCT_ATTRIBUTE_GEMINI_API_KEY)
    
    # 의상 정보 추출
    category = clothing_info.get("category")
    item = clothing_info.get("item")
    subcategory = clothing_info.get("subcategory")
    
    print(f"의상 정보 - category: {category}, item: {item}, subcategory: {subcategory}")
    
    # 입력 검증 - 딕셔너리에서 None이 아닌 이미지만 추출
    front_img = images.get("front")
    back_img = images.get("back")
    
    # None이 아닌 이미지만 리스트로 변환
    clothes_images = []
    if front_img is not None:
        clothes_images.append(front_img)
    if back_img is not None:
        clothes_images.append(back_img)
    
    # 최소 1개 이미지 필요
    if len(clothes_images) == 0:
        return [], [], [], "최소 1개의 이미지를 업로드해주세요."
    
    # 로깅 - 어떤 이미지가 업로드되었는지 출력
    uploaded_types = []
    if front_img is not None:
        uploaded_types.append("Front")
    if back_img is not None:
        uploaded_types.append("Back")
    print(f"업로드된 이미지: {', '.join(uploaded_types)}")
    
    try:
        if category == "상의":
            model_folder = "top"
        elif category == "하의":
            model_folder = "bottom"
        elif category == "원피스" or category == "스포츠/레저":
            model_folder = "top_bottom"
        else:
            model_folder = "default"
            
        # 고정 사람 이미지 로드
        front_image_path = os.path.join("assets", "model", model_folder, "front.png")
        back_image_path = os.path.join("assets", "model", model_folder, "back.png")
        side_image_path = os.path.join("assets", "model", model_folder, "side.png")
        
        if not os.path.exists(front_image_path):
            return None, f"정면 이미지 파일을 찾을 수 없습니다: {front_image_path}"
        if not os.path.exists(back_image_path):
            return None, f"뒷면 이미지 파일을 찾을 수 없습니다: {back_image_path}"
        if not os.path.exists(side_image_path):
            return None, f"측면 이미지 파일을 찾을 수 없습니다: {side_image_path}"
        
        front_pil_image = Image.open(front_image_path)
        back_pil_image = Image.open(back_image_path)
        side_pil_image = Image.open(side_image_path)
        
        # 옷 이미지 처리 - front와 back을 각각 PIL 이미지로 변환
        front_clothes_pil = Image.fromarray(front_img) if front_img is not None else None
        back_clothes_pil = Image.fromarray(back_img) if back_img is not None else None
        
        # 로깅
        print(f"고정 사람 이미지: {front_image_path}, {back_image_path}, {side_image_path}")
        print(f"옷 이미지 개수: {len(clothes_images)}")
        print(f"Temperature: {temperature}")
        print(f"생성할 이미지 개수: {image_count}")
        print(f"프롬프트: {text_input}")      

        # contents 구성: 사람 이미지별로 매칭되는 옷 이미지만 결합
        contents_list = []
        
        # front_pil_image + front_clothes (있으면)
        if front_clothes_pil is not None:
            for _ in range(image_count):
                contents_list.append([text_input, front_pil_image, front_clothes_pil])
        
        # back_pil_image + back_clothes (있으면)
        if back_clothes_pil is not None:
            for _ in range(image_count):
                contents_list.append([text_input, back_pil_image, back_clothes_pil])
        
        # side_pil_image + front_clothes (있으면)
        if front_clothes_pil is not None:
            for _ in range(image_count):
                contents_list.append([text_input, side_pil_image, front_clothes_pil])
        
        tasks = [virtual_tryon_inference(client.aio, contents, temperature) for contents in contents_list]
        
        responses = await asyncio.gather(*tasks)
        
        result_image_list, info_dict_list = zip(*responses)
        
        info_text = calculate_cost_info_multi(info_dict_list)
        
        # 결과 이미지를 동적으로 분리 (어떤 이미지가 업로드되었는지에 따라)
        front_image_list = []
        back_image_list = []
        side_image_list = []
        
        idx = 0
        # front_clothes가 있으면 front 결과가 먼저 생성됨
        if front_clothes_pil is not None:
            front_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
            idx += image_count
        
        # back_clothes가 있으면 back 결과가 생성됨
        if back_clothes_pil is not None:
            back_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
            idx += image_count
        
        # front_clothes가 있으면 side 결과가 마지막에 생성됨
        if front_clothes_pil is not None:
            side_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
        
        return front_image_list, back_image_list, side_image_list, info_text
            
    except Exception as e:
        print(f"Error: {e}")
        return [], [], [], f"이미지 생성 중 오류가 발생했습니다: {str(e)}"