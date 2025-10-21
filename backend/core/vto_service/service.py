import json
import asyncio
from typing import Dict, Optional, List
from core.litellm_hander.schema import ClothesImageAnalysis, LiteLLMUsageData
from core.litellm_hander.process import LiteLLMHandler
import os
from PIL import Image as PILImage
from core.vto_service.gemini_handler import GeminiProcesser
from prompts.vto_model_prompts import assemble_model_prompt


async def analyze_clothes_image(image_path: str) -> ClothesImageAnalysis:
    llm_handler = LiteLLMHandler()
    image_content = await llm_handler.convert_litellm_image_object(image_path)
    response = await llm_handler.analyze_clothes_image(image_content)
    contents = json.loads(response.choices[0].message.content)
    clothes_image_analysis = ClothesImageAnalysis(**contents)
    return clothes_image_analysis

async def virtual_tryon(
    front_image_path: Optional[str], 
    back_image_path: Optional[str], 
    prompt: str, 
    temperature: float = 1.0,
    image_count: int = 1,
    model_folder: str = "default"
) -> Dict:
    """
    Virtual Try-On: 앞면/뒷면 이미지와 프롬프트로 가상 착장 생성
    
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
    
    # GeminiProcesser 인스턴스 생성
    gemini_processer = GeminiProcesser()
    
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
    
    # 모든 조합에 대해 병렬 호출
    tasks = [gemini_processer.virtual_tryon_inference(contents, temperature) for contents in contents_list]
    responses = await asyncio.gather(*tasks)
    
    # 결과 분리
    result_image_list, usage_data_list = zip(*responses) if responses else ([], [])
    
    # None이 아닌 usage_data만 필터링
    usage_data_list = [usage for usage in usage_data_list if usage is not None]
    
    # 비용 정보 합산
    if usage_data_list:
        total_usage = await gemini_processer.sum_usage_data(usage_data_list)
    else:
        total_usage = await gemini_processer.calculate_vto_cost(None)
    
    # 결과 이미지를 뷰별로 분리
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

async def virtual_model_tryon(
    front_image_path: Optional[str], 
    back_image_path: Optional[str], 
    temperature: float = 1.0,
    image_count: int = 1,
    model_folder: str = "default"
) -> Dict:
    """
    Virtual Try-On: 앞면/뒷면 이미지와 프롬프트로 가상 모델 착장 생성
    
    Args:
        front_image_path: 앞면 의류 이미지 경로 (Optional)
        back_image_path: 뒷면 의류 이미지 경로 (Optional)
        temperature: 결과의 다양성 (기본값: 1.0)
        image_count: 생성할 이미지 개수 (기본값: 1)
        model_folder: 사용할 모델 폴더 (기본값: "default")
    
    Returns:
        Dict: 응답 결과 (앞면/뒷면 이미지 리스트 및 비용 정보)
    """
    # 입력 검증 - 최소 1개 이미지 필요
    if not front_image_path and not back_image_path:
        raise ValueError("최소 1개의 이미지(앞면 또는 뒷면)를 제공해야 합니다.")
    
    # GeminiProcesser 인스턴스 생성
    gemini_processer = GeminiProcesser()
    
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
    print(f"========================\n")
    
    # contents_list 구성: 각 조합에 대해 image_count만큼 생성
    contents_list = []
    
    # 정면 뷰: model_front + front_clothes (앞면 의류가 있으면)
    if front_clothes_img:
        for _ in range(image_count):
            contents_list.append([assemble_model_prompt(type="front"), front_clothes_img])
    
    # 뒷면 뷰: model_back + back_clothes (뒷면 의류가 있으면)
    if back_clothes_img:
        for _ in range(image_count):
            contents_list.append([assemble_model_prompt(type="back"), back_clothes_img])
    
    # 측면 뷰: model_side + front_clothes (앞면 의류가 있으면)
    # if front_clothes_img:
    #     for _ in range(image_count):
    #         contents_list.append([prompt, model_side_img, front_clothes_img])
    
    print(f"총 생성할 이미지 수: {len(contents_list)}")
    
    # 모든 조합에 대해 병렬 호출
    tasks = [gemini_processer.virtual_tryon_inference(contents, temperature) for contents in contents_list]
    responses = await asyncio.gather(*tasks)
    
    # 결과 분리
    result_image_list, usage_data_list = zip(*responses) if responses else ([], [])
    
    # None이 아닌 usage_data만 필터링
    usage_data_list = [usage for usage in usage_data_list if usage is not None]
    
    # 비용 정보 합산
    if usage_data_list:
        total_usage = await gemini_processer.sum_usage_data(usage_data_list)
    else:
        total_usage = await gemini_processer.calculate_vto_cost(None)
    
    # 결과 이미지를 뷰별로 분리
    front_image_list = []
    back_image_list = []
    
    idx = 0
    # 정면 의류가 있으면 정면 결과가 먼저 생성됨
    if front_clothes_img:
        front_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
        idx += image_count
    
    # 뒷면 의류가 있으면 뒷면 결과가 생성됨
    if back_clothes_img:
        back_image_list = [img for img in result_image_list[idx:idx+image_count] if img is not None]
        idx += image_count
    
    # 모든 이미지를 하나의 리스트로 합침
    all_images = front_image_list + back_image_list
    
    print(f"\n=== Virtual Try-On 완료 ===")
    print(f"정면 이미지: {len(front_image_list)}개")
    print(f"뒷면 이미지: {len(back_image_list)}개")
    print(f"총 생성된 이미지: {len(all_images)}개")
    print(f"========================\n")
    
    return {
        "response": all_images,  # 모든 이미지 리스트 반환
        "front_images": front_image_list,
        "back_images": back_image_list,
        "usage": total_usage,
        "debug_info": {
            "front_count": len(front_image_list),
            "back_count": len(back_image_list),
            "total_count": len(all_images),
            "requested_count_per_view": image_count,
            "model_name": "gemini-2.5-flash-image",
        }
    }
