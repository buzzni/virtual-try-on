from typing import Optional
from core.litellm_hander.utils import ClothesOptions as ClothesOptionsUtils

"""
Virtual Try-On 프롬프트 모음
"""

def assemble_prompt(
    *, 
    main_category: str,
    sub_category: str, 
    replacement: str,
    image_count: int = 2,
    gender: Optional[str] = None,
    how: Optional[str] = None,
    sleeve: Optional[str] = None,
    length: Optional[str] = None,
    fit: Optional[str] = None
):
    """
    프롬프트 조립 함수
    
    Args:
        category: 카테고리 (예: "상의", "하의", "원피스", "스포츠/레저")
        target: 대상 의상 (예: "shirt", "pants")
        replacement: 대체할 의상 부위 (예: "tops", "bottoms")
        image_count: 입력 이미지 개수 (2: dual mode, 3: triple mode)
        gender: 성별 ("person", "man", "woman")
        how: 입히는 방법 ("remove", "over", None)
        sleeve: 소매 속성
        length: 기장 속성
        fit: 핏 속성
        button: 단추/지퍼 열기 닫기 속성
        tuck: 넣입/빼입 속성
    Returns:
        str: 조립된 프롬프트
    """
    # 성별 처리 (기본값: "person")
    person_word = gender if gender else "person"
    
    if gender == "man":
        his_her = "his"
    elif gender == "woman":
        his_her = "her"
    else:
        his_her = "their"
        
    # target에 속성들을 붙여서 상세한 설명 생성
    target = ClothesOptionsUtils.clothes_category(main_category=main_category, sub_category=sub_category)
    detailed_target = target
    modifiers = []
    
    if length:
        modifiers.append(ClothesOptionsUtils.length_options(length))
    if fit:
        modifiers.append(ClothesOptionsUtils.fit_options(fit))
    if sleeve:
        modifiers.append(ClothesOptionsUtils.sleeve_options(sleeve))
    
    if modifiers:
        detailed_target = f"{', '.join(modifiers)} {target}"
    
    # 입히는 방법
    if how == 'remove':
        # 기존 착장 완전히 제거
        replace_method = f"removing every original {replacement}"
        result_description = f"with none of {his_her} original {replacement} remaining."
    elif how == 'over':
        # 기존 착장 위에 입히기
        replace_method = f"putting it naturally over {his_her} original clothing"
        result_description = f"with {his_her} original clothing."
    else:
        # 기존 착장 자연스럽게 대체
        replace_method = f"replacing it naturally in place of {his_her} original {replacement}"
        result_description = f"with none of {his_her} original {replacement} remaining."
    
    # objective = "Create a new image by combining the elements from the provided images."
    objective = "Create a professional e-commerce fashion photo."
    
    # 이미지 개수에 따라 프롬프트 조정 (추후 확장 가능)
    if image_count == 3:
        # Triple mode: 3개 이미지 (사람 + 옷1 + 옷2)
        action = f"Take the {person_word} from Image 1 and dress them in the new {detailed_target} using Image 2 (front view) and Image 3 (back view), {replace_method}"
        action += f"\nUse the front and back {target} images appropriately depending on the {person_word}'s visible pose and angle."
        output = f"The final image should be a photorealistic image of the {person_word} wearing the new {detailed_target} {result_description}"
    else:
        # Dual mode (기본): 2개 이미지 (사람 + 옷)
        # action = f"Take the {person_word} from Image 1 and dress them in the new {detailed_target} from Image 2, {replace_method}"
        action = f"Take the {detailed_target} from the second image and let the {person_word} from the first image wear it, {replace_method}"
        output = f"The final image should be a photorealistic image of the {person_word} wearing the new {detailed_target} {result_description}"

    action += "."
    # # 단추/지퍼 열기 닫기 처리
    # if button == "open":
    #     action += f", while keeping the buttons of the new {target} opened."
    # elif button == "close":
    #     action += f", while keeping the buttons of the new {target} closed."
    # else:
    #     action += "."
    
    # action += f"\nDo not change {his_her} body pose and posture from the first image."
    
    if main_category in ["tops", "outer", "dress"]:
        action += f"\nEnsure the details such as the number of buttons, pocket position, and stripe count of the {target} from the second image completely unchanged."
    else:
        action += f"\nEnsure the details of the {target} from the second image completely unchanged."
    
    # 넣입/빼입 처리
    # if category == "상의":    
    #     if tuck == "in":
    #         action += f" Put the new {target} into {his_her} pants."
    #     elif tuck == "out":
    #         action += f" Do not put the new {target} into {his_her} pants."
    
    # elif category == "하의":
    #     if tuck == "in":
    #         action += f" Put {his_her} shirt into the new {target}."
    #     elif tuck == "out":
    #         action += f" Do not put {his_her} shirt into the new {target}."
    
    return f"{objective}\n{action}\n{output}"
    # return f"{objective}\n{action}"
    # 입힌 것과 옷을 한번 다시 비교해서 디테일 맞추는 것은 어떨까?
    
    # 측면 사진 추출 프롬프트
    """
    Rotate the person in the image approximately 45 degrees to the left, as if the camera is viewing her from a front-side angle.
Keep her body shape, hairstyle, facial features, posture, and clothing consistent with the original.
The new image should show her from a slightly turned angle, with natural lighting and realistic perspective.
"""