import json
import os
from typing import Dict, Optional
from core.litellm_hander.schema import ClothesImageAnalysis
from core.litellm_hander.process import LiteLLMHandler
from PIL import Image as PILImage
from core.vto_service.gemini_handler import GeminiProcesser
from prompts.vto_model_prompts import assemble_model_prompt
from prompts.prod_image_prompts import product_image_prompt


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
    together_front_image_path: Optional[str] = None,
    together_back_image_path: Optional[str] = None,
    temperature: float = 1.0,
    image_count: int = 1,
    model_folder: str = "default",
    top_p: float = 0.95
) -> Dict:
    """
    Virtual Try-On: 앞면/뒷면 이미지와 프롬프트로 가상 착장 생성
    
    Args:
        front_image_path: 앞면 의류 이미지 경로 (Optional)
        back_image_path: 뒷면 의류 이미지 경로 (Optional)
        prompt: VTO 프롬프트
        together_front_image_path: 함께 입을 옷 앞면 이미지 경로 (Optional)
        together_back_image_path: 함께 입을 옷 뒷면 이미지 경로 (Optional)
        temperature: 결과의 다양성 (기본값: 1.0)
        image_count: 생성할 이미지 개수 (기본값: 1)
        model_folder: 사용할 모델 폴더 (기본값: "default")
        top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
    
    Returns:
        Dict: 응답 결과 (앞면/뒷면 이미지 리스트 및 비용 정보)
    """
    # 입력 검증
    if not front_image_path and not back_image_path:
        raise ValueError("최소 1개의 이미지(앞면 또는 뒷면)를 제공해야 합니다.")
    
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
    
    # GeminiProcesser 인스턴스 생성
    gemini_processer = GeminiProcesser()
    
    # 의류 이미지 로드
    front_clothes_img, back_clothes_img = await gemini_processer.load_clothes_images(front_image_path, back_image_path)
    together_front_clothes_img, together_back_clothes_img = await gemini_processer.load_clothes_images(together_front_image_path, together_back_image_path)
    
    # contents_list 구성: 각 조합에 대해 image_count만큼 생성
    contents_list = []
    
    # 정면 뷰: model_front + front_clothes (앞면 의류가 있으면)
    if front_clothes_img:
        for _ in range(image_count):
            content = [prompt, model_front_img, front_clothes_img]
            # 함께 입을 옷 추가
            if together_front_clothes_img:
                content.append(together_front_clothes_img)
            elif together_back_clothes_img:
                content.append(together_back_clothes_img)
            contents_list.append(content)
    
    # 뒷면 뷰: model_back + back_clothes (뒷면 의류가 있으면)
    if back_clothes_img:
        for _ in range(image_count):
            content = [prompt, model_back_img, back_clothes_img]
            # 함께 입을 옷 추가
            if together_back_clothes_img:
                content.append(together_back_clothes_img)
            elif together_front_clothes_img:
                content.append(together_front_clothes_img)
            contents_list.append(content)
    
    # 공통 추론 로직 실행
    return await gemini_processer.execute_vto_inference(
        contents_list=contents_list,
        front_has_images=front_clothes_img is not None,
        back_has_images=back_clothes_img is not None,
        image_count=image_count,
        temperature=temperature,
        include_side=False,
        top_p=top_p
    )

async def vto_model_tryon(
    front_image_path: Optional[str], 
    back_image_path: Optional[str], 
    together_front_image_path: Optional[str],
    together_back_image_path: Optional[str],
    model_options: Optional[Dict[str, str]] = None,
    temperature: float = 1.0,
    image_count: int = 1,
    top_p: float = 0.95
) -> Dict:
    """
    Virtual Try-On: 앞면/뒷면 이미지와 프롬프트로 가상 모델 착장 생성
    
    Args:
        front_image_path: 앞면 의류 이미지 경로 (Optional)
        back_image_path: 뒷면 의류 이미지 경로 (Optional)
        together_front_image_path: 함께 입을 옷 앞면 이미지 경로 (Optional)
        together_back_image_path: 함께 입을 옷 뒷면 이미지 경로 (Optional)
        model_options: 모델 관련 옵션 딕셔너리 (Optional)
            - gender: 성별 (기본값: "woman")
            - age: 나이 옵션 (Optional)
            - skin_tone: 피부색 옵션 (Optional)
            - ethnicity: 인종 옵션 (Optional)
            - hairstyle: 헤어스타일 옵션 (Optional)
            - hair_color: 머리색 옵션 (Optional)
        temperature: 결과의 다양성 (기본값: 1.0)
        image_count: 생성할 이미지 개수 (기본값: 1)
        top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
    
    Returns:
        Dict: 응답 결과 (앞면/뒷면 이미지 리스트 및 비용 정보)
    """
    # 입력 검증
    if not front_image_path and not back_image_path:
        raise ValueError("최소 1개의 이미지(앞면 또는 뒷면)를 제공해야 합니다.")
    
    # 모델 옵션 기본값 설정
    if model_options is None:
        model_options = {}
    
    gender = model_options.get("gender", "woman")
    age = model_options.get("age")
    skin_tone = model_options.get("skin_tone")
    ethnicity = model_options.get("ethnicity")
    hairstyle = model_options.get("hairstyle")
    hair_color = model_options.get("hair_color")
    
    # GeminiProcesser 인스턴스 생성
    gemini_processer = GeminiProcesser()
    
    # 의류 이미지 로드
    front_clothes_img, back_clothes_img = await gemini_processer.load_clothes_images(front_image_path, back_image_path)
    together_front_clothes_img, together_back_clothes_img = await gemini_processer.load_clothes_images(together_front_image_path, together_back_image_path)
    
    # contents_list 구성: 각 조합에 대해 image_count만큼 생성
    contents_list = []
    
    # 정면 뷰: 정면 프롬프트 + front_clothes (앞면 의류가 있으면)
    if front_clothes_img:
        for _ in range(image_count):
            front_prompt = assemble_model_prompt(
                type="front",
                gender=gender,
                age=age if age != "none" else None,
                skin_tone=skin_tone if skin_tone != "none" else None,
                ethnicity=ethnicity if ethnicity != "none" else None,
                hairstyle=hairstyle if hairstyle != "none" else None,
                hair_color=hair_color if hair_color != "none" else None
            )
            if together_front_clothes_img:
                contents_list.append([front_prompt, front_clothes_img, together_front_clothes_img])
            elif together_back_clothes_img:
                contents_list.append([front_prompt, front_clothes_img, together_back_clothes_img])
            else:
                contents_list.append([front_prompt, front_clothes_img])
    
    # 뒷면 뷰: 뒷면 프롬프트 + back_clothes (뒷면 의류가 있으면)
    if back_clothes_img:
        for _ in range(image_count):
            back_prompt = assemble_model_prompt(
                type="back",
                gender=gender,
                age=age if age != "none" else None,
                skin_tone=skin_tone if skin_tone != "none" else None,
                ethnicity=ethnicity if ethnicity != "none" else None,
                hairstyle=hairstyle if hairstyle != "none" else None,
                hair_color=hair_color if hair_color != "none" else None
            )
            if together_back_clothes_img:
                contents_list.append([back_prompt, back_clothes_img, together_back_clothes_img])
            elif together_front_clothes_img:
                contents_list.append([back_prompt, back_clothes_img, together_front_clothes_img])
            else:
                contents_list.append([back_prompt, back_clothes_img])
    
    # 공통 추론 로직 실행
    return await gemini_processer.execute_vto_inference(
        contents_list=contents_list,
        front_has_images=front_clothes_img is not None,
        back_has_images=back_clothes_img is not None,
        image_count=image_count,
        temperature=temperature,
        include_side=False,
        top_p=top_p
    )
    
async def single_image_inference(
    prompt: str,
    image_path: str,
    temperature: float = 1.0,
    image_count: int = 1,
    top_p: float = 0.95
) -> Dict:
    """
    Single Image Inference: 주어진 이미지에 대해 추론 실행
    
    Args:
        prompt: 프롬프트
        image_path: 이미지 경로
        temperature: 결과의 다양성 (기본값: 1.0)
        image_count: 생성할 이미지 개수 (기본값: 1)
        top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
    
    Returns:
        Dict: 응답 결과 (이미지 리스트 및 비용 정보)
    """
    gemini_processer = GeminiProcesser()
    image_content, _ = await gemini_processer.load_clothes_images(image_path, None)
    contents_list = []
    for _ in range(image_count):
        contents_list.append([prompt, image_content])
    
    return await gemini_processer.execute_vto_inference(
        contents_list=contents_list,
        front_has_images=image_content is not None,
        back_has_images=False,
        image_count=image_count,
        temperature=temperature,
        include_side=False,
        top_p=top_p
    )
