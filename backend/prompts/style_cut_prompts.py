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
        style_cut_options: 스타일 컷 옵션 (StyleCutOptions Pydantic 모델)
    """
    # 기본값 설정
    if model_options is None:
        model_options = ModelOptions(gender="woman")
    
    if style_cut_options is None:
        style_cut_options = StyleCutOptions()
    
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
    
    # 인물 설명 생성
    person_desc = ""
    if age:
        person_desc += f"a {age} {gender}"
    else:
        person_desc += f"a {gender}"

    # 기본 프롬프트 시작
    if background == "custom":
        prompt = "Generate an photorealistic image of a person from the first image in a place from the second image."
    else:
        prompt = "Generate an photorealistic image of a person from the image."
    
    # 자세 설명 추가
    if pose:
        prompt += f"\nThe person is {pose}"
        
        if facial_expression:
            prompt += f", with {facial_expression} expression."
        else:
            prompt += "."
    else:
        if facial_expression:
            prompt += f"\nThe person has {facial_expression} expression."
        else:
            prompt += "\nThe person is standing, looking toward the light with a calm and thoughtful expression."
    
    # 샷 타입 및 카메라 앵글 추가
    if shot_type and camera_angle:
        prompt += f"\nThe main shot is a {shot_type} from a {camera_angle}, capturing the person."
    elif shot_type:
        prompt += f"\nThe main shot is a {shot_type}, capturing the person."
    elif camera_angle:
        prompt += f"\nThe shot is from a {camera_angle}, capturing the person."
    else:
        prompt += "\nThe main shot is a full-body shot from a front-side angle, capturing the person."
    
    # 조명 및 색감 추가
    if lighting_style and color_tone:
        prompt += f"\nUse {lighting_style} to illuminate the scene, ensuring {color_tone} color palette."
    elif lighting_style:
        prompt += f"\nUse {lighting_style} to illuminate the scene."
    elif color_tone:
        prompt += f"\nEnsure {color_tone} color palette."
    else:
        prompt += "\nUse natural lighting to illuminate the scene, ensuring a natural and realistic look."
    
    # 카메라 스펙 및 후보정 추가
    if camera_specs and post_processing_keywords:
        prompt += f"\nThis should be captured as if using an {camera_specs} setup to achieve {post_processing_keywords}."
    elif camera_specs:
        prompt += f"\nThis should be captured as if using an {camera_specs} setup."
    elif post_processing_keywords:
        prompt += f"\nApply {post_processing_keywords}."
    else:
        prompt += "\nThis should be captured as if using an high-end editorial fashion photography setup."
    
    return prompt