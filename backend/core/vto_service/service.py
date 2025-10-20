import json
from typing import Dict
from core.litellm_hander.schema import ClothesImageAnalysis
from core.litellm_hander.process import LiteLLMHandler
from google import genai
from google.genai import types
from PIL import Image as PILImage
from configs import settings

async def analyze_clothes_image(image_path: str) -> ClothesImageAnalysis:
    llm_handler = LiteLLMHandler()
    image_content = await llm_handler.convert_litellm_image_object(image_path)
    response = await llm_handler.analyze_clothes_image(image_content)
    contents = json.loads(response.choices[0].message.content)
    clothes_image_analysis = ClothesImageAnalysis(**contents)
    return clothes_image_analysis


async def virtual_tryon(
    image_path_1: str, 
    image_path_2: str, 
    prompt: str, 
    temperature: float = 1.0
) -> Dict:
    """
    Virtual Try-On: 두 이미지와 프롬프트로 가상 착장 생성
    
    Args:
        image_path_1: 첫 번째 이미지 경로 (사람)
        image_path_2: 두 번째 이미지 경로 (의류)
        prompt: VTO 프롬프트
        temperature: 결과의 다양성 (기본값: 1.0)
    
    Returns:
        Dict: 응답 결과 (이미지 데이터 포함)
    """
    # Google Genai SDK를 직접 사용 (LiteLLM이 이미지 생성 모델의 특수 파라미터를 제대로 지원하지 않음)
    client = genai.Client(api_key=settings.gemini_api_key)
    
    # 이미지 로드
    image_1 = PILImage.open(image_path_1)
    image_2 = PILImage.open(image_path_2)
    
    # 모델명
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
    
    # Gemini API 호출 (이미지만 생성하도록 설정)
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=[prompt, image_1, image_2],
        config=types.GenerateContentConfig(
            response_modalities=[types.Modality.IMAGE],  # 이미지만 생성
            temperature=temperature,
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
            ),
            safety_settings=safety_settings
        )
    )
    
    # 비용 계산을 위한 usage 정보 생성
    llm_handler = LiteLLMHandler()
    usage_info = {
        "usage": {
            "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
            "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
            "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
        }
    }
    usage_data = llm_handler.calculate_cost(usage_info, f"gemini/{model_name}", "virtual_tryon")
    
    # 응답에서 이미지 데이터 추출 (Genai SDK 응답 구조)
    image_data = None
    
    # 디버깅: 응답 구조 출력
    print(f"Response type: {type(response)}")
    print(f"Response has candidates: {hasattr(response, 'candidates')}")
    
    if hasattr(response, 'candidates') and len(response.candidates) > 0:
        candidate = response.candidates[0]
        print(f"Candidate type: {type(candidate)}")
        print(f"Candidate has content: {hasattr(candidate, 'content')}")
        
        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
            parts = candidate.content.parts
            print(f"Number of parts: {len(parts)}")
            
            for i, part in enumerate(parts):
                print(f"Part {i} type: {type(part)}")
                
                # 텍스트가 있는지 확인
                if hasattr(part, 'text') and part.text:
                    print(f"Part {i} has text: {part.text[:100]}")
                
                # 이미지 데이터가 있는지 확인 (inline_data)
                if hasattr(part, 'inline_data') and part.inline_data:
                    print(f"Part {i} has inline_data")
                    if hasattr(part.inline_data, 'data'):
                        image_data = part.inline_data.data
                        print(f"Found image data (length: {len(image_data)})")
                        break
    
    if not image_data:
        print("WARNING: No image data found in response!")
        if hasattr(response, 'text'):
            print(f"Response text: {response.text}")
    
    return {
        "response": image_data,
        "raw_response": response,
        "usage": usage_data,
        "debug_info": {
            "response_type": str(type(response)),
            "has_image": image_data is not None,
            "has_candidates": hasattr(response, 'candidates'),
            "num_candidates": len(response.candidates) if hasattr(response, 'candidates') else 0,
        }
    }

