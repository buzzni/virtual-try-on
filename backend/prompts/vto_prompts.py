from typing import Optional
"""
Virtual Try-On 프롬프트 모음
"""


def assemble_prompt(
    *, 
    category: str,
    target: str, 
    replacement: str,
    image_count: int = 2,
    gender: Optional[str] = None,
    how: Optional[str] = None,
    sleeve: Optional[str] = None,
    length: Optional[str] = None,
    fit: Optional[str] = None,
    button: Optional[str] = None,
    tuck: Optional[str] = None,
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
    detailed_target = target
    modifiers = []
    
    if length:
        modifiers.append(length)
    if fit:
        modifiers.append(fit)
    if sleeve:
        modifiers.append(sleeve)
    
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

    # 단추/지퍼 열기 닫기 처리
    if button == "open":
        action += f", while keeping the buttons of the new {target} opened."
    elif button == "close":
        action += f", while keeping the buttons of the new {target} closed."
    else:
        action += "."
    
    # action += f"\nDo not change {his_her} body pose and posture from the first image."
    
    if category == "상의" or category == "아우터" or category == "원피스":
        action += f"\nEnsure the details such as the number of buttons, pocket position, and stripe count of the {target} from the second image completely unchanged."
    else:
        action += f"\nEnsure the details of the {target} from the second image completely unchanged."
    
    # 넣입/빼입 처리
    if category == "상의":    
        if tuck == "in":
            action += f" Put the new {target} into {his_her} pants."
        elif tuck == "out":
            action += f" Do not put the new {target} into {his_her} pants."
    
    elif category == "하의":
        if tuck == "in":
            action += f" Put {his_her} shirt into the new {target}."
        elif tuck == "out":
            action += f" Do not put {his_her} shirt into the new {target}."
    
    return f"{objective}\n{action}\n{output}"
    # return f"{objective}\n{action}"
    # 입힌 것과 옷을 한번 다시 비교해서 디테일 맞추는 것은 어떨까?
    
    # 측면 사진 추출 프롬프트
    """
    Rotate the person in the image approximately 45 degrees to the left, as if the camera is viewing her from a front-side angle.
Keep her body shape, hairstyle, facial features, posture, and clothing consistent with the original.
The new image should show her from a slightly turned angle, with natural lighting and realistic perspective.
"""

# 3단계 카테고리별 구조화된 딕셔너리 (프롬프트 + 폴더 매핑 통합)
CLOTHING_CATEGORIES = {
    "기본": {
        "folder": None,  # 카테고리 기본 폴더
        "items": {
            "기본": {
                "folder": None,  # 아이템 폴더 (카테고리와 동일하면 생략 가능)
                "subcategories": {
                    "기본": {
                        "var": {
                            "target": "garment",
                            "replacement": "garment"
                        },
                        "folder": None  # 세부 폴더 없음 (상위 폴더 사용)
                    }
                }
            }
        }
    },
    "상의": {
        "folder": "top",
        "items": {
            "상의 전체": {
                "folder": None,
                "subcategories": {
                    "상의 전체": {
                        "var": {
                            "target": "top",
                            "replacement": "tops"
                        },
                        "folder": None
                    }
                }
            },
            "셔츠": {
                "folder": "top/shirts",
                "subcategories": {
                    "전체": {
                        "var": {
                            "target": "shirt",
                            "replacement": "tops"
                        },
                        "folder": None
                    }
                }
            },
            "블라우스": {
                "folder": "top/blouses",
                "subcategories": {
                    "전체": {
                        "var": {
                            "target": "blouse",
                            "replacement": "tops"
                        },
                        "folder": None
                    }
                }
            },
            "티셔츠": {
                "folder": "top/tshirts",
                "subcategories": {
                    "전체": {
                        "var": {
                            "target": "tshirt",
                            "replacement": "tops"
                        },
                        "folder": None
                    },
                    "티셔츠": {
                        "var": {
                            "target": "tshirt",
                            "replacement": "tops"
                        },
                        "folder": "top/tshirts"
                    },
                    "카라티": {
                        "var": {
                            "target": "polo shirt",
                            "replacement": "tops"
                        },
                        "folder": "top/tshirts/polo"
                    }
                }
            }
        }
    },
    "아우터": {
        "folder": "outer",
        "items": {
            "아우터 전체": {
                "folder": None,
                "subcategories": {
                    "아우터 전체": {
                        "var": {
                            "target": "outerwear",
                            "replacement": "clothings",
                            "how": "over"
                        },
                        "folder": None
                    }
                }
            },
            "코트": {
                "folder": "outer/coats",
                "subcategories": {
                    "전체": {
                        "var": {
                            "target": "coat",
                            "replacement": "clothings",
                            "how": "over"
                        },
                        "folder": None
                    }
                }
            },
            "자켓": {
                "folder": "outer/jackets",
                "subcategories": {
                    "자켓 전체": {
                        "var": {
                            "target": "jacket",
                            "replacement": "clothings",
                            "how": "over"
                        },
                        "folder": None
                    }
                }
            },
            "패딩": {
                "folder": "outer/padding",
                "subcategories": {
                    "패딩 전체": {
                        "var": {
                            "target": "padding",
                            "replacement": "clothings",
                            "how": "over"
                        },
                        "folder": None
                    }
                }
            }
        }
    },
    "하의": {
        "folder": "bottoms",
        "items": {
            "하의 전체": {
                "folder": None,
                "subcategories": {
                    "하의 전체": {
                        "var": {
                            "target": "bottom",
                            "replacement": "bottoms"
                        },
                        "folder": None
                    }
                }
            },
            "바지": {
                "folder": "bottoms/pants",
                "subcategories": {
                    "바지 전체": {
                        "var": {
                            "target": "pants",
                            "replacement": "bottoms"
                        },
                        "folder": None
                    }
                }
            },
            "스커트": {
                "folder": "bottoms/skirt",
                "subcategories": {
                    "스커트 전체": {
                        "var": {
                            "target": "skirt",
                            "replacement": "bottoms"
                        },
                        "folder": None
                    }
                }
            }
        }
    },
    "원피스": {
        "folder": "onepiece",
        "items": {
            "원피스 드레스": {
                "folder": "onepiece/dresses",
                "subcategories": {
                    "원피스 드레스 전체": {
                        "var": {
                            "target": "one-piece dress",
                            "replacement": "clothings"
                        },
                        "folder": None
                    }
                }
            }
        }
    },
    "스포츠/레저": {
        "folder": "sports",
        "items": {
            "수영복": {
                "folder": "sports/swimwear",
                "subcategories": {
                    "전체": {
                        "var": {
                            "target": "swimwear",
                            "replacement": "clothings",
                            "how": "remove"
                        },
                        "folder": None
                    },
                }
            }
        }
    }
}

# 카테고리 리스트
CATEGORY_TYPES = list(CLOTHING_CATEGORIES.keys())


# 성별 리스트
GENDER_DICT = {
    "공통(person)": "person",
    "남성(man)": "man",
    "여성(woman)": "woman"
}
GENDER_TYPES = list(GENDER_DICT.keys())

# 핏 리스트
FIT_DICT = {
    "설정 안 함": "none",
    "레귤러": "regular fit",
    "오버사이즈": "over-sized",
    "슬림핏": "slim fit"
}
FIT_TYPES = list(FIT_DICT.keys())

# 소매 리스트
SLEEVE_DICT = {
    "설정 안 함": "none",
    "반팔": "short-sleeve",
    "긴팔": "long-sleeve",
    "민소매": "sleeveless"
}
SLEEVE_TYPES = list(SLEEVE_DICT.keys())

# 기장 리스트
LENGTH_DICT = {
    "설정 안 함": "none",
    "크롭": "cropped",
    "허리": "waist-length",
    "엉덩이": "hip-length",
    "허벅지": "thigh-length",
    "무릎": "knee-length",
    "종아리": "mid-calf-length",
    "긴 기장": "full-length",
    "바닥에 닿는 기장": "floor-length"
}
LENGTH_TYPES = list(LENGTH_DICT.keys())

# 단추/지퍼 열기 닫기
BUTTON_DICT = {
    "설정 안 함": "none",
    "열기": "open",
    "닫기": "close"
}
BUTTON_TYPES = list(BUTTON_DICT.keys())

TUCK_DICT = {
    "설정 안 함": "none",
    "넣입": "in",
    "빼입": "out"
}
TUCK_TYPES = list(TUCK_DICT.keys())

# ==================================================================================
# 동적 속성 관리 시스템
# ==================================================================================

# 속성별 설정 딕셔너리 (새로운 속성 추가 시 여기에만 추가하면 됨)
ATTRIBUTE_CONFIG = {
    "gender": {
        "types": GENDER_TYPES,
        "default": GENDER_TYPES[0],
        "label": "성별을 선택하세요",
        "affects_prompt_only": False,  # 갤러리도 영향
        "affects_gallery": True
    },
    "fit": {
        "types": FIT_TYPES,
        "default": FIT_TYPES[0],
        "label": "핏을 선택하세요",
        "affects_prompt_only": True,  # 프롬프트만 영향
        "affects_gallery": False
    },
    "sleeve": {
        "types": SLEEVE_TYPES,
        "default": SLEEVE_TYPES[0],
        "label": "소매를 선택하세요",
        "affects_prompt_only": True,
        "affects_gallery": False
    },
    "length": {
        "types": LENGTH_TYPES,
        "default": LENGTH_TYPES[0],
        "label": "기장을 선택하세요",
        "affects_prompt_only": True,
        "affects_gallery": False
    },
    "button": {
        "types": BUTTON_TYPES,
        "default": BUTTON_TYPES[0],
        "label": "단추/지퍼 열기 닫기를 선택하세요",
        "affects_prompt_only": True,
        "affects_gallery": False
    },
    "tuck": {
        "types": TUCK_TYPES,
        "default": TUCK_TYPES[0],
        "label": "넣입/빼입을 선택하세요",
        "affects_prompt_only": True,
        "affects_gallery": False
    }
}


def get_items_by_category(*, category):
    """카테고리에 속한 아이템 리스트 반환"""
    if category in CLOTHING_CATEGORIES and "items" in CLOTHING_CATEGORIES[category]:
        return list(CLOTHING_CATEGORIES[category]["items"].keys())
    return []

def get_subcategories_by_item(*, category, item):
    """카테고리와 아이템에 속한 세부 카테고리 리스트 반환"""
    if (category in CLOTHING_CATEGORIES and 
        "items" in CLOTHING_CATEGORIES[category] and
        item in CLOTHING_CATEGORIES[category]["items"] and
        "subcategories" in CLOTHING_CATEGORIES[category]["items"][item]):
        return list(CLOTHING_CATEGORIES[category]["items"][item]["subcategories"].keys())
    return []

def build_prompt(
    *,
    category,
    item,
    subcategory,
    image_count=2,
    **attribute_types
):
    """단일 진입점 프롬프트 빌더 (경로 기반 + 동적 속성)

    Args:
        category, item, subcategory: 의상 경로 (필수)
        image_count: 입력 이미지 개수 (2: dual mode, 3: triple mode)
        **attribute_types: 동적 속성들 (gender_type, fit_type, sleeve_type, length_type 등)

    Returns:
        str | None: 생성된 프롬프트 (경로 미존재 시 None)
    """
    # 경로에서 var_data 추출
    if (
        category in CLOTHING_CATEGORIES and
        "items" in CLOTHING_CATEGORIES[category] and
        item in CLOTHING_CATEGORIES[category]["items"] and
        "subcategories" in CLOTHING_CATEGORIES[category]["items"][item] and
        subcategory in CLOTHING_CATEGORIES[category]["items"][item]["subcategories"]
    ):
        var_data = CLOTHING_CATEGORIES[category]["items"][item]["subcategories"][subcategory]["var"]
    else:
        return None

    # var_data를 복사해서 속성 추가
    prompt_vars = var_data.copy()
    
    prompt_vars["category"] = category

    # 동적으로 속성 처리
    for attr_name, config in ATTRIBUTE_CONFIG.items():
        attr_type_key = f"{attr_name}_type"
        attr_value = attribute_types.get(attr_type_key, config["default"])
        
        # 속성 딕셔너리 가져오기
        attr_dict_name = f"{attr_name.upper()}_DICT"
        attr_dict = globals().get(attr_dict_name)
        
        if attr_dict:
            # gender는 항상 추가 (기본값이어도)
            if attr_name == "gender":
                prompt_vars[attr_name] = attr_dict[attr_value]
            # 다른 속성들은 기본값이 아닌 경우만 추가
            elif attr_value != config["default"]:
                prompt_vars[attr_name] = attr_dict[attr_value]

    # 이미지 개수 추가
    prompt_vars["image_count"] = image_count

    # 프롬프트 생성
    return assemble_prompt(**prompt_vars)

def get_prompt_by_full_path(*, category, item, subcategory, image_count=2, **attribute_types):
    """하위호환: 경로 기반 프롬프트 빌드 (build_prompt 위임)
    
    Args:
        category, item, subcategory: 의상 경로 (필수)
        image_count: 입력 이미지 개수 (2: dual mode, 3: triple mode)
        **attribute_types: 동적 속성들 (gender_type, fit_type, sleeve_type, length_type 등)
    
    Returns:
        str | None: 생성된 프롬프트
    """
    return build_prompt(
        category=category,
        item=item,
        subcategory=subcategory,
        image_count=image_count,
        **attribute_types
    )
    
def get_folder_by_full_path(*, category, item, subcategory):
    """카테고리, 아이템, 세부 카테고리로 폴더 경로 반환"""
    if (category in CLOTHING_CATEGORIES and 
        "items" in CLOTHING_CATEGORIES[category] and
        item in CLOTHING_CATEGORIES[category]["items"] and
        "subcategories" in CLOTHING_CATEGORIES[category]["items"][item] and
        subcategory in CLOTHING_CATEGORIES[category]["items"][item]["subcategories"]):
        
        # 세부 카테고리 폴더가 있으면 사용
        subfolder = CLOTHING_CATEGORIES[category]["items"][item]["subcategories"][subcategory]["folder"]
        if subfolder:
            return subfolder
        
        # 없으면 아이템 폴더 사용
        item_folder = CLOTHING_CATEGORIES[category]["items"][item].get("folder")
        if item_folder:
            return item_folder
        
        # 없으면 카테고리 폴더 사용
        category_folder = CLOTHING_CATEGORIES[category].get("folder", "clothes")
        return category_folder
    
    return "clothes"  # 기본 폴더

# ==================================================================================
# 기본값 설정 (중앙 집중 관리)
# ==================================================================================

# UI에서 사용할 기본값들 (함수 정의 후에 설정)
CATEGORY_DEFAULT_VALUE = "기본"
ITEM_DEFAULT_VALUE = get_items_by_category(category=CATEGORY_DEFAULT_VALUE)[0] if get_items_by_category(category=CATEGORY_DEFAULT_VALUE) else None
SUBCATEGORY_DEFAULT_VALUE = get_subcategories_by_item(category=CATEGORY_DEFAULT_VALUE, item=ITEM_DEFAULT_VALUE)[0] if ITEM_DEFAULT_VALUE and get_subcategories_by_item(category=CATEGORY_DEFAULT_VALUE, item=ITEM_DEFAULT_VALUE) else None