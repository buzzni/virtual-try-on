def assemble_model_prompt(*, type: str, gender: str = "woman"):
    """
    가상 모델 생성 프롬프트
    
    Args:
        type: "front" 또는 "back"
        gender: "man" 또는 "woman" (기본값: "woman")
    """
    # 성별에 따른 설명 설정
    if gender == "man":
        person_desc = "a young man"
        pronoun = "his"
        pronoun_obj = "him"
        hair_desc = "a neat hairstyle"
        makeup_desc = ""
    else:  # woman
        person_desc = "a young woman"
        pronoun = "her"
        pronoun_obj = "her"
        hair_desc = "a loose updo hairstyle and soft bangs"
        makeup_desc = ", natural makeup with soft pink lips"
    
    front_prompt = f"""Generate a photorealistic full-body image of {person_desc} wearing the outfit exactly as shown in the provided Source Image.
**The model's head and shoes must both be fully visible in the image, with nothing cropped.**
The entire clothing provided in the Source Image must be fully visible within the frame. No part of the clothing should be cropped, cut off, or out of view.
The clothing's design, pattern, color, fabric texture, and fit must be perfectly replicated with no alteration.
Create a model who matches this description: {person_desc} with {hair_desc}{makeup_desc}.
Maintain realistic body proportions, gentle facial expression, and soft, even lighting that matches the clothing's visual tone.
Place {pronoun_obj} in a minimalist, plain light gray background with no props, patterns, or textures.
Lighting should be even and diffused, matching the direction implied by the outfit photo.
Ensure the clothing drapes naturally on the model's body with realistic folds and contact shadows.
Preserve accurate color balance and texture detail; avoid seams, blur, or artificial effects.
Output a single high-resolution, full-body image in neutral, editorial style.
"""
    
    back_prompt = f"""Generate a photorealistic image of {person_desc} wearing the outfit exactly as shown in the provided Source Image.
**The model's head and shoes must both be fully visible in the image, with nothing cropped.**
The clothing's design, pattern, color, fabric texture, and fit must be perfectly replicated with no alteration.
The model must be shown from behind.
Do **not** show {pronoun} face, eyes, or any part of the front of {pronoun} body.
This image must be a **true back view** with the model completely turned away from the viewer, as if walking or standing with {pronoun} back to the camera.
A side or front angle is strictly prohibited.
Create a model who matches this description: {person_desc} with {hair_desc} visible from behind{makeup_desc.replace(', ', ' (') + ' - not visible in this view)' if makeup_desc else ''}.
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
    