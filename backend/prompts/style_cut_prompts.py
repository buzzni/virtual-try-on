from typing import Optional
from core.litellm_hander.schema import StyleCutOptions, ModelOptions
from core.litellm_hander.utils import StyleCutOptions as StyleCutOptionsUtils

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
    shot_type = StyleCutOptionsUtils.shot_type_options(style_cut_options.shot_type) if style_cut_options.shot_type else None
    camera_angle = StyleCutOptionsUtils.camera_angle_options(style_cut_options.camera_angle) if style_cut_options.camera_angle else None
    pose = StyleCutOptionsUtils.pose_options(style_cut_options.pose) if style_cut_options.pose else None
    arms_pose = StyleCutOptionsUtils.arms_pose_options(style_cut_options.arms_pose) if style_cut_options.arms_pose else None
    gaze = StyleCutOptionsUtils.gaze_options(style_cut_options.gaze) if style_cut_options.gaze else None
    facial_expression = StyleCutOptionsUtils.facial_expression_options(style_cut_options.facial_expression) if style_cut_options.facial_expression else None
    background = StyleCutOptionsUtils.background_options(style_cut_options.background) if style_cut_options.background else None
    lighting_style = StyleCutOptionsUtils.lighting_style_options(style_cut_options.lighting_style) if style_cut_options.lighting_style else None
    color_tone = StyleCutOptionsUtils.color_tone_options(style_cut_options.color_tone) if style_cut_options.color_tone else None
    camera_specs = StyleCutOptionsUtils.camera_specs_options(style_cut_options.camera_specs) if style_cut_options.camera_specs else None
    post_processing_keywords = StyleCutOptionsUtils.post_processing_options(style_cut_options.post_processing_keywords) if style_cut_options.post_processing_keywords else None
    
        
    # 성별에 따른 설명 설정
    if gender == "man":
        if age == "kid" or age == "teen":
            person_desc = "boy"
        else:   
            person_desc = "man"
        pronoun = "his"
        pronoun_obj = "him"
        pronoun_subj = "He"
    else:  # woman
        if age == "kid" or age == "teen":
            person_desc = "girl"
        else:
            person_desc = "woman"
        pronoun = "her"
        pronoun_obj = "her"
        pronoun_subj = "She"
    
    # 샷 타입 설명
    if shot_type:
        image_desc = f"{shot_type} image"
    else:
        image_desc = "image"
    
    # 기본 프롬프트 시작
    if background == "custom":
        prompt = f"Generate a photorealistic {image_desc} of a {person_desc} from the first image. The image is taken on a place described in the second image."
    else:
        prompt = f"Generate a photorealistic {image_desc} of a {person_desc} from the image."
    
    # 자세와 표정 설명 추가
    if pose:
        prompt += f"\n{pronoun_subj} is {pose}"
        if arms_pose:
            prompt += f", while {pronoun} {arms_pose}"
        if gaze:
            prompt += f", {gaze}"
        if facial_expression:
            prompt += f" with {facial_expression}"
        prompt += "."
    elif arms_pose:
        prompt += f"\n{pronoun_subj} is keeping {pronoun} {arms_pose}"
        if gaze:
            prompt += f", {gaze}"
        if facial_expression:
            prompt += f" with {facial_expression}"
        prompt += "."
    elif gaze:
        prompt += f"\n{pronoun_subj} is {gaze}"
        if facial_expression:
            prompt += f" with {facial_expression}"
        prompt += "."
    elif facial_expression:
        prompt += f"\n{pronoun_subj} is making {facial_expression}."

    # 샷 타입 및 카메라 앵글 추가
    if shot_type and camera_angle:
        prompt += f"\nThe main shot is a {shot_type} from a {camera_angle}, capturing {pronoun_obj}."
    elif shot_type:
        prompt += f"\nThe main shot is a {shot_type}, capturing {pronoun_obj}."
    elif camera_angle:
        prompt += f"\nThe shot is from a {camera_angle}, capturing {pronoun_obj}."
    else:
        prompt += f"\nThe main shot is a full-body shot from a front-side angle, capturing {pronoun_obj}."
    
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