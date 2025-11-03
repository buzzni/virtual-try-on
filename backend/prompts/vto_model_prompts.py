from typing import Optional
from core.litellm_hander.utils import skin_tone_options, ethnicity_options, hairstyle_options, age_options, hair_color_options
from core.litellm_hander.utils import clothes_category
from core.litellm_hander.utils import sleeve_options, length_options, fit_options
from core.litellm_hander.schema import ModelOptions, ClothesOptions

def assemble_model_prompt(
    type: str,
    model_options: Optional[ModelOptions] = None,
    clothes_options: Optional[ClothesOptions] = None,
    wear_together: Optional[str] = None
):
    """
    가상 모델 생성 프롬프트
    
    Args:
        type: "front" 또는 "back"
        model_options: 모델 옵션 (ModelOptions Pydantic 모델)
        clothes_options: 의상 옵션 (ClothesOptions Pydantic 모델)
        wear_together: 함께 입을 옷 설명 (Optional)
    """
    # 기본값 설정
    if model_options is None:
        model_options = ModelOptions(gender="woman")
    
    # ModelOptions에서 값 추출
    gender = model_options.gender
    age = model_options.age
    skin_tone = model_options.skin_tone
    ethnicity = model_options.ethnicity
    hairstyle = model_options.hairstyle
    hair_color = model_options.hair_color
    height = model_options.height
    weight = model_options.weight
    
    # ClothesOptions에서 값 추출 (있는 경우)
    main_category = clothes_options.main_category if clothes_options else None
    sub_category = clothes_options.sub_category if clothes_options else None
    sleeve = clothes_options.sleeve if clothes_options else None
    length = clothes_options.length if clothes_options else None
    fit = clothes_options.fit if clothes_options else None
    total_length = clothes_options.total_length if clothes_options else None
    
    # 성별에 따른 설명 설정
    if gender == "man":
        if age == "kid" or age == "teen":
            person_desc = "boy"
        else:   
            person_desc = "man"
        pronoun = "his"
        pronoun_obj = "him"
        pronoun_subj = "he"
        default_hair = "a neat hairstyle"
        makeup_desc = ""
    else:  # woman
        if age == "kid" or age == "teen":
            person_desc = "girl"
        else:
            person_desc = "woman"
        pronoun = "her"
        pronoun_obj = "her"
        pronoun_subj = "she"
        default_hair = "a loose updo hairstyle and soft bangs"
        makeup_desc = ", natural makeup"
    
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
    
    if age == "kid":
        if gender == "man":
            person_desc_2 = person_desc.replace("boy", "kid")
        else:
            person_desc_2 = person_desc.replace("girl", "kid")
    else:
        person_desc_2 = person_desc
        
    # 특성 설명 조합
    model_characteristics = f"{person_desc} with {hair_desc}"
    if characteristics:
        model_characteristics += f", {', '.join(characteristics)}"
    if makeup_desc and age != "kid":
        model_characteristics += makeup_desc

    if height:
        model_characteristics += f", {int(height)}cm tall"
    if weight:
        model_characteristics += f", {int(weight)}kg"
    # 의류 설명 조합
    if main_category == None:
        base_outfit = "outfit"
    else:
        base_outfit = clothes_category(main_category=main_category, sub_category=sub_category)
    
    # 옵션들을 앞에 붙이기 위해 수집
    modifiers = []
    if length and length != "none":
        modifiers.append(length_options(length))
    if fit and fit != "none":
        modifiers.append(fit_options(fit))
    if sleeve and sleeve != "none":
        modifiers.append(sleeve_options(sleeve))
    
    # outfit_desc 구성
    if modifiers:
        outfit_desc = f"the {', '.join(modifiers)} {base_outfit}"
    else:
        outfit_desc = f"the {base_outfit}"
    
    if wear_together:
        wear_together_desc = f", paired with {wear_together}"
    else:
        wear_together_desc = ""
    
    # front_prompt 구성
    front_prompt_parts = [
        f"Generate a photorealistic full-body studio image of {model_characteristics}.",
        f"{pronoun_subj.capitalize()} is wearing {outfit_desc} exactly as shown in the provided Source Image{wear_together_desc}."
    ]
    
    # total_length가 있으면 비율 조정 문장 추가
    if total_length:
        front_prompt_parts.append(f"Adjust the overall proportions based on the {base_outfit} length of {total_length} cm to maintain realistic body-to-clothing ratio.")
    
    front_prompt_parts.extend([
        f"Show {pronoun_obj} entire body clearly from head to shoes — nothing cropped or out of frame.",
        "Maintain realistic body proportions, gentle facial expression, and soft, even lighting that matches the clothing's visual tone.",
        "Replicate the outfit's design, color, fabric texture, and fit perfectly with natural folds and soft contact shadows.",
        "Use soft, even studio lighting on a plain light gray background with no props or patterns.",
        "The final image should look like a high-resolution professional studio photo, not an AI-generated image.",
        "Output a single high-resolution, full-body image in neutral, editorial style."
    ])
    
    front_prompt = "\n".join(front_prompt_parts) + "\n"
    
    # 뒷면 프롬프트용 특성 설명
    back_model_desc = f"{person_desc_2} with {hair_desc} visible from behind"
    if characteristics:
        back_model_desc += f", {', '.join(characteristics)}"
    if makeup_desc:
        back_model_desc += makeup_desc.replace(', ', ' (') + ' - not visible in this view)'
    
    back_prompt = f"""Generate a photorealistic image of {person_desc} wearing {outfit_desc} exactly as shown in the provided Source Image{wear_together_desc}.
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


# v 1.0.0
#     front_prompt = f"""Generate a photorealistic full-body image of {person_desc} wearing {outfit_desc} exactly as shown in the provided Source Image{wear_together_desc}
# **The model's head and shoes must both be fully visible in the image, with nothing cropped.**
# The entire clothing provided in the Source Image must be fully visible within the frame. No part of the clothing should be cropped, cut off, or out of view.
# The clothing's design, pattern, color, fabric texture, and fit must be perfectly replicated with no alteration.
# Create a model who matches this description: {model_characteristics}.
# Maintain realistic body proportions, gentle facial expression, and soft, even lighting that matches the clothing's visual tone.
# Place {pronoun_obj} in a minimalist, plain light gray background with no props, patterns, or textures.
# Lighting should be even and diffused, matching the direction implied by the outfit photo.
# Ensure the clothing drapes naturally on the model's body with realistic folds and contact shadows.
# Preserve accurate color balance and texture detail; avoid seams, blur, or artificial effects.
# Output a single high-resolution, full-body image in neutral, editorial style.
# """