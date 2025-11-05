import json
from typing import Dict, List
from core.litellm_hander.schema import ClothesImageAnalysis
from core.litellm_hander.process import LiteLLMHandler
from core.vto_service.gemini_handler import GeminiProcesser


async def analyze_clothes_image(image_path: str) -> ClothesImageAnalysis:
    llm_handler = LiteLLMHandler()
    image_content = await llm_handler.convert_litellm_image_object(image_path)
    response = await llm_handler.analyze_clothes_image(image_content)
    contents = json.loads(response.choices[0].message.content)
    clothes_image_analysis = ClothesImageAnalysis(**contents)
    return clothes_image_analysis

async def image_inference_with_prompt(
    prompt: str,
    image_paths : List[str],
    temperature: float = 1.0,
    image_count: int = 1,
    top_p: float = 0.95,
    aspect_ratio: str = "1:1"
) -> Dict:
    """
    Single Image Inference: 주어진 이미지(단일 또는 여러 개)에 대해 추론 실행
    
    Args:
        prompt: 프롬프트
        image_paths: 이미지 경로(단일 또는 여러 개)
        temperature: 결과의 다양성 (기본값: 1.0)
        image_count: 생성할 이미지 개수 (기본값: 1)
        top_p: Top-p (nucleus) 샘플링 값 (기본값: 0.95)
    
    Returns:
        Dict: 응답 결과 (이미지 리스트 및 비용 정보)
    """
    gemini_processer = GeminiProcesser()
    image_contents = []
    
    for image_path in image_paths:
        image_contents.append(await gemini_processer.load_clothes_images(image_path))
    
    print(f"\n{'='*50}")
    print(f"이미지 생성 호출 내용")
    print(f"프롬프트: {prompt}")
    print(f"입력 이미지 개수: {len(image_paths)}")
    print(f"생성 이미지 개수: {image_count}")
    print(f"Temperature: {temperature}")
    print(f"Top-p (Nucleus Sampling): {top_p}")
    print(f"Aspect Ratio: {aspect_ratio}")
    print(f"{'='*50}\n")
    
    return await gemini_processer.execute_image_inference(
        contents_list=[prompt] + image_contents,
        image_count=image_count,
        temperature=temperature,
        top_p=top_p,
        aspect_ratio=aspect_ratio
    )
