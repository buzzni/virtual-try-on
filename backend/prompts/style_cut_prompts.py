from typing import Optional
from core.litellm_hander.schema import StyleCutOptions, ModelOptions

def assemble_style_cut_prompt(
    model_options: Optional[ModelOptions] = None,
    style_cut_options: Optional[StyleCutOptions] = None
):
    """
    스타일 컷 프롬프트
    
    Args:
        model_options: 모델 옵션 (ModelOptions Pydantic 모델)
        clothes_options: 의상 옵션 (ClothesOptions Pydantic 모델)
        style_cut_options: 스타일 컷 옵션 (StyleCutOptions Pydantic 모델)
    """
    # 기본값 설정
    if model_options is None:
        model_options = ModelOptions(gender="woman")
    
    # ModelOptions에서 값 추출
    gender = model_options.gender
    age = model_options.age

    # StyleCutOptions에서 값 추출 (있는 경우)
    shot_type = style_cut_options.shot_type
    camera_angle = style_cut_options.camera_angle
    pose = style_cut_options.pose
    facial_expression = style_cut_options.facial_expression
    background = style_cut_options.background
    lighting_style = style_cut_options.lighting_style
    color_tone = style_cut_options.color_tone
    camera_specs = style_cut_options.camera_specs
    post_processing_keywords = style_cut_options.post_processing_keywords
    
    person_desc = ""
    if age:
        person_desc += f"a {age} {gender}"
    else:
        person_desc += f"a {gender}"

    if background == "custom":
        prompt = "Generate an photorealistic image of a person from the first image in a place from the second image."
    else:
        prompt = "Generate an photorealistic image of a person from the image."
    
    prompt += f"\nThe person is {pose}"
    
    if facial_expression:
        prompt += f", with {facial_expression} expression."
    else:
        prompt += f"."
        
    prompt += f"\nThe main shot is a {shot_type} from a {camera_angle}, capturing the person."
    prompt += f"\nUse {lighting_style} to illuminate the scene, ensuring {color_tone} color palette."
    prompt += f"\nThis should be captured as if using an {camera_specs} setup to achieve {post_processing_keywords}."
    
    return prompt