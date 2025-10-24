from typing import Optional
from core.litellm_hander.utils import skin_tone_options, ethnicity_options, hairstyle_options, age_options, hair_color_options

def assemble_model_prompt(
    *, 
    type: str, 
    gender: str = "woman",
    age: Optional[str] = None,
    skin_tone: Optional[str] = None,
    ethnicity: Optional[str] = None,
    hairstyle: Optional[str] = None,
    hair_color: Optional[str] = None
):
    """
    가상 모델 생성 프롬프트
    
    Args:
        type: "front" 또는 "back"
        gender: "man" 또는 "woman" (기본값: "woman")
        age: 나이 옵션 키 (예: "young", "middle_aged", "senior")
        skin_tone: 피부색 옵션 키 (예: "fair", "medium", "dark")
        ethnicity: 인종 옵션 키 (예: "east_asian", "caucasian")
        hairstyle: 헤어스타일 옵션 키 (예: "long", "short", "updo")
        hair_color: 머리색 옵션 키 (예: "black", "brown", "blonde")
    """
    # 성별에 따른 설명 설정
    if gender == "man":
        person_desc = "man"
        pronoun = "his"
        pronoun_obj = "him"
        default_hair = "a neat hairstyle"
        makeup_desc = ""
    else:  # woman
        person_desc = "woman"
        pronoun = "her"
        pronoun_obj = "her"
        default_hair = "a loose updo hairstyle and soft bangs"
        makeup_desc = ", natural makeup with soft pink lips"
    
    # 옵션에 따른 특성 빌드
    characteristics = []
    
    # 나이 설정
    if age and age != "none":
        age_text = age_options(age)
        if age_text != "none":
            age_prefix = age_text
        else:
            age_prefix = "young"
    else:
        age_prefix = "young"
    
    # 인종 추가
    if ethnicity and ethnicity != "none":
        ethnicity_text = ethnicity_options(ethnicity)
        if ethnicity_text != "none":
            person_desc = f"a {age_prefix} {ethnicity_text} {person_desc}"
        else:
            person_desc = f"a {age_prefix} {person_desc}"
    else:
        person_desc = f"a {age_prefix} {person_desc}"
    
    # 피부색 추가
    if skin_tone and skin_tone != "none":
        skin_text = skin_tone_options(skin_tone)
        if skin_text != "none":
            characteristics.append(skin_text)
    
    # 헤어스타일과 머리색 조합
    # 먼저 헤어스타일 결정 (지정되지 않으면 기본값 사용)
    if hairstyle and hairstyle != "none":
        style_text = hairstyle_options(hairstyle, gender)
        if style_text != "none":
            base_hair = style_text
        else:
            base_hair = default_hair
    else:
        base_hair = default_hair
    
    # 머리색이 지정되면 앞에 추가
    if hair_color and hair_color != "none":
        color_text = hair_color_options(hair_color)
        if color_text != "none":
            # "black hair" 형태로 오므로 "hair" 제거하고 색상만 추출
            color_only = color_text.replace(" hair", "")
            hair_desc = f"{color_only} {base_hair}"
        else:
            hair_desc = base_hair
    else:
        hair_desc = base_hair
    
    # 특성 설명 조합
    model_characteristics = f"{person_desc} with {hair_desc}"
    if characteristics:
        model_characteristics += f", {', '.join(characteristics)}"
    if makeup_desc:
        model_characteristics += makeup_desc
    
    front_prompt = f"""Generate a photorealistic full-body image of {person_desc} wearing the outfit exactly as shown in the provided Source Image.
**The model's head and shoes must both be fully visible in the image, with nothing cropped.**
The entire clothing provided in the Source Image must be fully visible within the frame. No part of the clothing should be cropped, cut off, or out of view.
The clothing's design, pattern, color, fabric texture, and fit must be perfectly replicated with no alteration.
Create a model who matches this description: {model_characteristics}.
Maintain realistic body proportions, gentle facial expression, and soft, even lighting that matches the clothing's visual tone.
Place {pronoun_obj} in a minimalist, plain light gray background with no props, patterns, or textures.
Lighting should be even and diffused, matching the direction implied by the outfit photo.
Ensure the clothing drapes naturally on the model's body with realistic folds and contact shadows.
Preserve accurate color balance and texture detail; avoid seams, blur, or artificial effects.
Output a single high-resolution, full-body image in neutral, editorial style.
"""
    
    # 뒷면 프롬프트용 특성 설명
    back_model_desc = f"{person_desc} with {hair_desc} visible from behind"
    if characteristics:
        back_model_desc += f", {', '.join(characteristics)}"
    if makeup_desc:
        back_model_desc += makeup_desc.replace(', ', ' (') + ' - not visible in this view)'
    
    back_prompt = f"""Generate a photorealistic image of {person_desc} wearing the outfit exactly as shown in the provided Source Image.
**The model's head and shoes must both be fully visible in the image, with nothing cropped.**
The clothing's design, pattern, color, fabric texture, and fit must be perfectly replicated with no alteration.
The model must be shown from behind.
Do **not** show {pronoun} face, eyes, or any part of the front of {pronoun} body.
This image must be a **true back view** with the model completely turned away from the viewer, as if walking or standing with {pronoun} back to the camera.
A side or front angle is strictly prohibited.
Create a model who matches this description: {back_model_desc}.
Maintain realistic body proportions, soft posture, and even lighting that matches the outfit's visual tone.
Ensure that the lighting direction is consistent with the Source Image and that shadows, folds, and fabric contact points look natural on the body.
The background should be plain, minimalist, and light gray with no textures or props.
The final image must be high-resolution and editorial in tone, with no artificial artifacts, blur, or face visible.
"""

    if type == "front":
        return front_prompt
    elif type == "back":
        return back_prompt
    else:
        raise ValueError(f"Invalid type: {type}")
    
    
# Include subtle natural imperfections such as slight skin texture, soft shadow gradients, and natural garment creases to avoid an overly airbrushed look.