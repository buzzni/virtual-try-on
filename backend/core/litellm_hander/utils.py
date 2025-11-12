"""
옵션 관련 유틸리티 함수들을 클래스로 구조화
- ModelOptions: 모델 관련 옵션 (성별, 피부색, 인종, 나이, 헤어스타일, 머리색)
- ClothesOptions: 의상 관련 옵션 (핏, 소매, 기장, 의류 카테고리)
- StyleCutOptions: 스타일 컷 관련 옵션 (샷 타입, 카메라 앵글, 포즈, 표정, 조명, 색감, 카메라 스펙, 후보정, 배경)
"""


class ModelOptions:
    """모델 관련 옵션 유틸리티"""
    
    @staticmethod
    def gender_options():
        return {
            # "person": {
            #     "name": "공통",
            #     "desc": "성별 구분 없이 공통으로 적용"
            # },
            "woman": {
                "name": "여성",
                "desc": "여성 모델에 적용"
            },
            "man": {
                "name": "남성",
                "desc": "남성 모델에 적용"
            }
        }
    
    @staticmethod
    def skin_tone_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "피부색을 지정하지 않음",
                "prompt": "none"
            },
            "fair": {
                "name": "밝은 피부",
                "desc": "밝은 피부톤",
                "prompt": "fair skin"
            },
            "light": {
                "name": "연한 피부",
                "desc": "연한 피부톤",
                "prompt": "light skin"
            },
            "medium": {
                "name": "중간 피부",
                "desc": "중간 피부톤",
                "prompt": "medium skin"
            },
            "brown": {
                "name": "갈색 피부",
                "desc": "갈색 피부톤",
                "prompt": "brown skin"
            },
            "dark": {
                "name": "어두운 피부",
                "desc": "어두운 피부톤",
                "prompt": "dark skin"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def ethnicity_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "인종을 지정하지 않음",
                "prompt": "none"
            },
            "asian": {
                "name": "아시아인",
                "desc": "한국, 중국, 일본 등",
                "prompt": "East Asian"
            },
            "caucasian": {
                "name": "백인",
                "desc": "유럽계 백인",
                "prompt": "Caucasian"
            },
            "african": {
                "name": "아프리카계",
                "desc": "아프리카계",
                "prompt": "African"
            },
            "latino": {
                "name": "라틴계",
                "desc": "라틴 아메리카계",
                "prompt": "Latino"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def age_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "나이를 지정하지 않음",
                "prompt": "none"
            },
            "kid": {
                "name": "어린이",
                "desc": "10대 이하",
                "prompt": "young"
            },
            "teen": {
                "name": "10대",
                "desc": "10대 청소년",
                "prompt": "teenage"
            },
            "young": {
                "name": "청년 (기본값)",
                "desc": "20대~30대 초반",
                "prompt": "young"
            },
            "middle_aged": {
                "name": "중년",
                "desc": "40대~50대",
                "prompt": "middle-aged"
            },
            "mature": {
                "name": "장년",
                "desc": "50대~60대",
                "prompt": "mature"
            },
            "senior": {
                "name": "노년",
                "desc": "60대 이상",
                "prompt": "senior"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def hair_color_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "머리색을 지정하지 않음",
                "prompt": "none"
            },
            "black": {
                "name": "검정색",
                "desc": "검은색 머리",
                "prompt": "black hair"
            },
            "dark_brown": {
                "name": "진한 갈색",
                "desc": "진한 갈색 머리",
                "prompt": "dark brown hair"
            },
            "brown": {
                "name": "갈색",
                "desc": "갈색 머리",
                "prompt": "brown hair"
            },
            "light_brown": {
                "name": "밝은 갈색",
                "desc": "밝은 갈색 머리",
                "prompt": "light brown hair"
            },
            "light_brown_tint": {
                "name": "밝은 갈색 (염색)",
                "desc": "밝은 갈색 머리 (염색)",
                "prompt": "light brown tinted hair"
            },
            "blonde": {
                "name": "금발",
                "desc": "금발 머리",
                "prompt": "blonde hair"
            },
            "blonde_tint": {
                "name": "금발 (염색)",
                "desc": "금발 머리 (염색)",
                "prompt": "bleached light hair"
            },
            "platinum": {
                "name": "플래티넘",
                "desc": "백금색 머리",
                "prompt": "platinum blonde hair"
            },
            "red": {
                "name": "빨간색",
                "desc": "빨간색 머리",
                "prompt": "red hair"
            },
            "auburn": {
                "name": "적갈색",
                "desc": "적갈색 머리",
                "prompt": "auburn hair"
            },
            "gray": {
                "name": "회색",
                "desc": "회색 머리",
                "prompt": "gray hair"
            },
            "silver": {
                "name": "은색",
                "desc": "은색 머리",
                "prompt": "silver hair"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def hairstyle_options(key=None, gender="woman"):
        """
        헤어스타일 옵션
        gender에 따라 일부 옵션의 설명이 달라질 수 있음
        """
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "헤어스타일을 지정하지 않음",
                "prompt": "none"
            },
            "short": {
                "name": "짧은 머리 (공통)",
                "desc": "짧은 헤어스타일",
                "prompt": "short hair"
            },
            "medium": {
                "name": "중간 길이 (공통)",
                "desc": "어깨 정도 길이의 머리",
                "prompt": "medium-length hair"
            },
            "long": {
                "name": "긴 머리 (공통)",
                "desc": "긴 헤어스타일",
                "prompt": "long hair"
            },
            "bob": {
                "name": "단발머리 (여)",
                "desc": "턱 라인의 단발 헤어",
                "prompt": "bob haircut"
            },
            "pixie": {
                "name": "픽시컷 (여)",
                "desc": "매우 짧은 여성 헤어",
                "prompt": "pixie cut"
            },
            "wavy": {
                "name": "웨이브 (공통)",
                "desc": "웨이브가 있는 머리",
                "prompt": "wavy hair"
            },
            "curly": {
                "name": "곱슬머리 (공통)",
                "desc": "곱슬한 헤어스타일",
                "prompt": "curly hair"
            },
            "straight": {
                "name": "생머리 (공통)",
                "desc": "똑바른 머리",
                "prompt": "straight hair"
            },
            "updo": {
                "name": "업스타일 (여)",
                "desc": "머리를 올린 스타일",
                "prompt": "updo hairstyle"
            },
            "ponytail": {
                "name": "포니테일 (여)",
                "desc": "묶은 머리",
                "prompt": "ponytail"
            },
            "braided": {
                "name": "땋은 머리 (여)",
                "desc": "땋은 헤어스타일",
                "prompt": "braided hair"
            },
            "bun": {
                "name": "올림머리/번 (여) - 여성 기본값",
                "desc": "머리를 뒤로 묶어 올린 스타일",
                "prompt": "loose updo hairstyle and soft bangs"
            },
            "slicked_back": {
                "name": "올백 (공통)",
                "desc": "뒤로 넘긴 헤어",
                "prompt": "slicked-back hair"
            },
            "undercut": {
                "name": "언더컷 (공통)",
                "desc": "옆과 뒤를 짧게 자른 스타일",
                "prompt": "undercut"
            },
            "crew_cut": {
                "name": "크루컷 (남)",
                "desc": "매우 짧은 남성 헤어",
                "prompt": "crew cut"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options


class ClothesOptions:
    """의상 관련 옵션 유틸리티"""
    
    @staticmethod
    def fit_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "핏 설정을 지정하지 않음",
                "prompt": "none"
            },
            "regular": {
                "name": "레귤러",
                "desc": "일반적인 기본 핏",
                "prompt": "regular fit"
            },
            "oversized": {
                "name": "오버사이즈",
                "desc": "여유있는 루즈한 핏",
                "prompt": "oversized fit"
            },
            "slim": {
                "name": "슬림핏",
                "desc": "몸에 맞는 타이트한 핏",
                "prompt": "slim fit"
            }
        }
        
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def sleeve_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "소매 길이를 지정하지 않음",
                "prompt": "none"
            },
            "short": {
                "name": "반팔",
                "desc": "짧은 소매 길이",
                "prompt": "short-sleeve"
            },
            "long": {
                "name": "긴팔",
                "desc": "긴 소매 길이",
                "prompt": "long-sleeve"
            },
            "sleeveless": {
                "name": "민소매",
                "desc": "소매가 없는 스타일",
                "prompt": "sleeveless"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def length_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "기장을 지정하지 않음",
                "prompt": "none"
            },
            "crop": {
                "name": "크롭",
                "desc": "배꼽 위로 짧은 기장",
                "prompt": "cropped"
            },
            "waist": {
                "name": "허리",
                "desc": "허리 라인 기장",
                "prompt": "waist-length"
            },
            "hip": {
                "name": "엉덩이",
                "desc": "엉덩이를 덮는 기장",
                "prompt": "hip-length"
            },
            "thigh": {
                "name": "허벅지",
                "desc": "허벅지 중간 기장",
                "prompt": "thigh-length"
            },
            "knee": {
                "name": "무릎",
                "desc": "무릎 라인 기장",
                "prompt": "knee-length"
            },
            "calf": {
                "name": "종아리",
                "desc": "종아리 중간 기장",
                "prompt": "mid-calf-length"
            },
            "long": {
                "name": "긴 기장",
                "desc": "발목 근처까지 오는 긴 기장",
                "prompt": "full-length"
            },
            "floor": {
                "name": "바닥에 닿는 기장",
                "desc": "바닥까지 닿는 매우 긴 기장",
                "prompt": "floor-length"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def clothes_category(main_category=None, sub_category=None):
        catalog = {
            "none": {
                "name": "설정 안 함",
                "desc": "기본 의류",
                "prompt": "outfit",
                "children": {
                    "none": {
                        "name": "설정 안 함",
                        "desc": "의류 종류 전체",
                        "prompt": "outfit"
                    },
                }
            },
            "tops": {
                "name": "상의",
                "desc": "상반신 기본 의류. 계절·활동·핏에 따라 선택.",
                "prompt": "top",
                "children": {
                    "none": {
                        "name": "전체",
                        "desc": "상의 종류 전체",
                        "prompt": "top"
                    },
                    "sweatshirt": {
                        "name": "맨투맨/스웨트",
                        "desc": "도톰한 저지/기모 소재의 캐주얼 스웨트 셔츠.",
                        "prompt": "sweatshirt"
                    },
                    "hoodie": {
                        "name": "후드 티셔츠",
                        "desc": "후드와 캥거루 포켓이 특징인 캐주얼 톱.",
                        "prompt": "hoodie"
                    },
                    "shirt_blouse": {
                        "name": "셔츠/블라우스",
                        "desc": "칼라와 버튼 여밈의 포멀·세미포멀 상의.",
                        "prompt": "shirt"
                    },
                    "longsleeve_tshirt": {
                        "name": "긴소매 티셔츠",
                        "desc": "롱슬리브 저지 톱, 이너/단품용.",
                        "prompt": "long-sleeve t-shirt"
                    },
                    "shortsleeve_tshirt": {
                        "name": "반소매 티셔츠",
                        "desc": "하프슬리브 기본 티, 로고/프린트 다양.",
                        "prompt": "short-sleeve t-shirt"
                    },
                    "polo": {
                        "name": "피케/카라 티셔츠",
                        "desc": "카라와 버튼 플래킷의 니트 저지 톱.",
                        "prompt": "polo shirt"
                    },
                    "knit_sweater": {
                        "name": "니트/스웨터",
                        "desc": "편직 소재의 보온성 상의 (라운드·브이넥 등).",
                        "prompt": "knit sweater"
                    },
                    "sleeveless": {
                        "name": "민소매 티셔츠",
                        "desc": "슬리브리스 톱, 여름용 혹은 레이어링용.",
                        "prompt": "tank top"
                    },
                    "tops_etc": {
                        "name": "기타 상의",
                        "desc": "위 분류에 속하지 않는 상의 전반.",
                        "prompt": "top"
                    },
                },
            },
            "outer": {
                "name": "아우터",
                "desc": "기온·날씨 대응 및 스타일 포인트용 겉옷.",
                "prompt": "outerwear",
                "children": {
                    "none": {
                        "name": "전체",
                        "desc": "아우터 종류 전체",
                        "prompt": "outerwear"
                    },
                    "zipup_hoodie": {
                        "name": "후드 집업",
                        "desc": "지퍼 여밈 후디, 가벼운 레이어링용.",
                        "prompt": "zip-up hoodie"
                    },
                    "ma1": {
                        "name": "블루종/MA-1",
                        "desc": "허리·소매 시보리의 항공 재킷.",
                        "prompt": "bomber jacket"
                    },
                    "leather_riders": {
                        "name": "레더/라이더스 재킷",
                        "desc": "가죽 소재의 하드한 무드 재킷.",
                        "prompt": "leather jacket"
                    },
                    "cardigan": {
                        "name": "카디건",
                        "desc": "앞여밈 니트 아우터, 이너 위에 가볍게 착용.",
                        "prompt": "cardigan"
                    },
                    "trucker": {
                        "name": "트러커 재킷",
                        "desc": "데님/코튼 트윌의 박시 숏 재킷.",
                        "prompt": "trucker jacket"
                    },
                    "blazer": {
                        "name": "슈트/블레이저 재킷",
                        "desc": "테일러드 라펠의 포멀 재킷.",
                        "prompt": "blazer"
                    },
                    "varsity": {
                        "name": "스타디움 재킷",
                        "desc": "배색·스냅 여밈의 바시티 스타일 재킷.",
                        "prompt": "varsity jacket"
                    },
                    "coach": {
                        "name": "나일론/코치 재킷",
                        "desc": "경량 우븐, 생활 방풍/발수 기능.",
                        "prompt": "coach jacket"
                    },
                    "anorak": {
                        "name": "아노락 재킷",
                        "desc": "하프집·후드의 풀오버 윈드브레이커.",
                        "prompt": "anorak"
                    },
                    "training_jacket": {
                        "name": "트레이닝 재킷",
                        "desc": "저지/트랙 소재의 스포츠 아우터.",
                        "prompt": "track jacket"
                    },
                    "midseason_coat": {
                        "name": "환절기 코트",
                        "desc": "간절기용 경량 코트.",
                        "prompt": "light coat"
                    },
                    "safari": {
                        "name": "사파리/헌팅 재킷",
                        "desc": "포켓 많은 실용적 미들 재킷.",
                        "prompt": "safari jacket"
                    },
                    "vest": {
                        "name": "베스트",
                        "desc": "소매 없는 경량 레이어 아이템.",
                        "prompt": "vest"
                    },
                    "short_padding": {
                        "name": "숏패딩/헤비 아우터",
                        "desc": "두터운 충전재의 보온 숏 재킷.",
                        "prompt": "puffer jacket"
                    },
                    "mustang_fur": {
                        "name": "무스탕/퍼",
                        "desc": "셰어링/퍼 안감의 보온 아우터.",
                        "prompt": "shearling jacket"
                    },
                    "fleece": {
                        "name": "플리스/뽀글이",
                        "desc": "폴라 플리스 소재의 경량 보온 아우터.",
                        "prompt": "fleece jacket"
                    },
                    "single_coat": {
                        "name": "겨울 싱글 코트",
                        "desc": "싱글 브레스티드 클래식 겨울 코트.",
                        "prompt": "single-breasted coat"
                    },
                    "double_coat": {
                        "name": "겨울 더블 코트",
                        "desc": "더블 브레스티드 구조적 실루엣 코트.",
                        "prompt": "double-breasted coat"
                    },
                    "winter_coat_etc": {
                        "name": "겨울 기타 코트",
                        "desc": "체스터필드 등 기타 겨울 코트.",
                        "prompt": "winter coat"
                    },
                    "long_padding": {
                        "name": "롱패딩/헤비 아우터",
                        "desc": "무릎 이상 길이의 최고 보온 아우터.",
                        "prompt": "long puffer coat"
                    },
                    "padding_vest": {
                        "name": "패딩 베스트",
                        "desc": "충전재 베스트, 코어 보온용.",
                        "prompt": "puffer vest"
                    },
                    "outer_etc": {
                        "name": "기타 아우터",
                        "desc": "상기 외 아우터 전반.",
                        "prompt": "outerwear"
                    },
                },
            },
            "bottoms": {
                "name": "바지",
                "desc": "하반신 의류. 핏·소재·활동성 중심 선택.",
                "prompt": "pants",
                "children": {
                    "none": {
                        "name": "전체",
                        "desc": "바지 종류 전체",
                        "prompt": "pants"
                    },
                    "denim_pants": {
                        "name": "데님 팬츠",
                        "desc": "데님 소재의 5포켓/와이드/슬림 등.",
                        "prompt": "jeans"
                    },
                    "jogger_pants": {
                        "name": "트레이닝/조거 팬츠",
                        "desc": "저지·밴딩·밑단 시보리의 이지웨어.",
                        "prompt": "jogger pants"
                    },
                    "cotton_pants": {
                        "name": "코튼 팬츠",
                        "desc": "치노/트윌 등 캐주얼 코튼 바지.",
                        "prompt": "chino pants"
                    },
                    "slacks": {
                        "name": "슈트 팬츠/슬랙스",
                        "desc": "테일러드 라인의 포멀 팬츠.",
                        "prompt": "dress pants"
                    },
                    "short_pants": {
                        "name": "숏 팬츠",
                        "desc": "허벅지 길이의 경량 반바지.",
                        "prompt": "shorts"
                    },
                    "leggings": {
                        "name": "레깅스",
                        "desc": "신축성 높은 바디핏 팬츠.",
                        "prompt": "leggings"
                    },
                    "jumpsuit": {
                        "name": "점프 슈트/오버올",
                        "desc": "상·하의 일체형 작업복 실루엣.",
                        "prompt": "jumpsuit"
                    },
                    "bottoms_etc": {
                        "name": "기타 하의",
                        "desc": "상기 외 하의 전반.",
                        "prompt": "pants"
                    },
                },
            },
            "dress": {
                "name": "원피스",
                "desc": "한 벌로 스타일 완성. 길이·실루엣 다양.",
                "prompt": "dress",
                "children": {
                    "none": {
                        "name": "전체",
                        "desc": "원피스 종류 전체",
                        "prompt": "dress"
                    },
                    "mini_dress": {
                        "name": "미니원피스",
                        "desc": "허벅지 길이의 경쾌한 원피스.",
                        "prompt": "mini dress"
                    },
                    "midi_dress": {
                        "name": "미디원피스",
                        "desc": "무릎 전후의 균형감 있는 원피스.",
                        "prompt": "midi dress"
                    },
                    "maxi_dress": {
                        "name": "맥시원피스",
                        "desc": "발목까지 흐르는 롱 실루엣.",
                        "prompt": "maxi dress"
                    },
                },
            },
            "skirt": {
                "name": "치마",
                "desc": "길이·실루엣 다양.",
                "prompt": "skirt",
                "children": {
                    "none": {
                        "name": "전체",
                        "desc": "치마 종류 전체",
                        "prompt": "skirt"
                    },
                    "mini_skirt": {
                        "name": "미니스커트",
                        "desc": "짧은 길이의 스커트.",
                        "prompt": "mini skirt"
                    },
                    "midi_skirt": {
                        "name": "미디스커트",
                        "desc": "무릎 전후 길이의 스커트.",
                        "prompt": "midi skirt"
                    },
                    "long_skirt": {
                        "name": "롱스커트",
                        "desc": "발목까지 길게 떨어지는 스커트.",
                        "prompt": "long skirt"
                    },
                },
            },
        }
        if main_category and main_category in catalog.keys():
            main_category_dict = catalog[main_category]
            if sub_category and sub_category in main_category_dict["children"].keys():
                return main_category_dict["children"][sub_category]["prompt"]
            else:
                return main_category_dict["prompt"]
        elif main_category == "default":
            return "garment"
        else:
            return catalog


class StyleCutOptions:
    """스타일 컷 관련 옵션 유틸리티"""
    
    @staticmethod
    def shot_type_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "샷 타입을 지정하지 않음",
                "prompt": "none"
            },
            "full_body": {
                "name": "전신",
                "desc": "전신이 나오는 구도",
                "prompt": "full body shot"
            },
            "upper_body": {
                "name": "상반신",
                "desc": "상반신이 나오는 구도",
                "prompt": "upper body shot"
            },
            "lower_body": {
                "name": "하반신",
                "desc": "하반신이 나오는 구도",
                "prompt": "lower body shot"
            },
            "close_up": {
                "name": "클로즈업",
                "desc": "가까이서 찍은 구도",
                "prompt": "close-up shot"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def camera_angle_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "카메라 각도를 지정하지 않음",
                "prompt": "none"
            },
            "front": {
                "name": "정면",
                "desc": "정면에서 촬영",
                "prompt": "front"
            },
            "side": {
                "name": "측면",
                "desc": "측면에서 촬영",
                "prompt": "side"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def pose_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "포즈를 지정하지 않음",
                "prompt": "none"
            },
            "sitting_on_chair": {
                "name": "의자에 앉아있기",
                "desc": "의자에 앉아있는 자세",
                "prompt": "sitting on a chair"
            },
            "sitting_on_floor": {
                "name": "바닥에 앉아있기",
                "desc": "바닥에 앉아있는 자세",
                "prompt": "sitting on the floor"
            },
            "standing_hands_together": {
                "name": "서있기",
                "desc": "서있는 자세",
                "prompt": "standing"
            },
            "leaning_wall": {
                "name": "벽에 기대기",
                "desc": "벽에 기대어 있는 자세",
                "prompt": "leaning slightly forward near the wall"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def arms_pose_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "팔 포즈를 지정하지 않음",
                "prompt": "none"
            },
            "hands_together": {
                "name": "손을 모으고 있기",
                "desc": "손을 모으고 있는 자세",
                "prompt": "hands gently clapsed in front"
            },
            "hands_on_waist": {
                "name": "허리에 손을 얹고 있기",
                "desc": "허리에 손을 얹고 있는 자세",
                "prompt": "hands gently resting on waist"
            },
            "cheek_resting_on_hand": {
                "name": "턱을 괴고 있는 자세",
                "desc": "턱을 괴고 있는 자세",
                "prompt": "cheek resting gently on one hand in a thoughtful pose, the other hand relaxed by their side"
            },
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
        
    @staticmethod
    def gaze_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "시선을 지정하지 않음",
                "prompt": "none"
            },
            "looking_camera": {
                "name": "카메라를 보고 있는 자세",
                "desc": "카메라를 보고 있는 자세",
                "prompt": "looking at the camera"
            },
            "looking_light": {
                "name": "빛을 보고 있는 자세",
                "desc": "빛을 보고 있는 자세",
                "prompt": "looking towrad the light"
            },
            "closed_eyes": {
                "name": "눈을 감고 있는 자세",
                "desc": "눈을 감고 있는 자세",
                "prompt": "keeping eyes closed"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def facial_expression_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "표정을 지정하지 않음",
                "prompt": "none"
            },
            "neutral": {
                "name": "중립/평온",
                "desc": "중립적이고 평온하며 생각하는 표정",
                "prompt": "a calm, thoughtful expression"
            },
            "smile": {
                "name": "미소",
                "desc": "미소 짓는 표정",
                "prompt": "a smile"
            },
            "confident": {
                "name": "자신감 있는",
                "desc": "자신감 있는 표정",
                "prompt": "a confident smirk"
            },
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def lighting_style_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "조명 스타일을 지정하지 않음",
                "prompt": "none"
            },
            "direct_sunlight": {
                "name": "강한 직사광선",
                "desc": "오후의 햇빛, 직사광선",
                "prompt": "Strong afternoon sunlight streams on the objects, creating clear, bright highlights and defined shadows"
            },
            "natural_indoor": {
                "name": "자연스러운 조명",
                "desc": "자연스러운 조명",
                "prompt": "Neutral yet diffused lighting casts soft shadows"
            },
            "backlit": {
                "name": "역광",
                "desc": "역광 조명",
                "prompt": "The lighting creates a soft glow around the person"
            },
            "studio_high_contrast": {
                "name": "스튜디오 조명 (주황/파랑)",
                "desc": "대비가 큰 스튜디오 조명",
                "prompt": "Dramatic dual-tone cinematic lighting 一 warm orange glow on one side, cool blue rim highlights on the other, creating striking contrast and mood"
            },
            "night_flash": {
                "name": "야간 플래시",
                "desc": "야간 플래시 조명",
                "prompt": "Night flash makes intense, sharp highlights and shadows"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def color_tone_options(key=None):
        options = {
            "none": {
                "name": "중립",
                "desc": "색감을 지정하지 않음",
                "prompt": "none"
            },
            "warm": {
                "name": "따뜻하게",
                "desc": "따릗한 색감",
                "prompt": "warm color tone"
            },
            "cool": {
                "name": "차갑게",
                "desc": "차가운 색감",
                "prompt": "cool color tone"
            },
            "black_white": {
                "name": "흑백",
                "desc": "흑백 색감",
                "prompt": "black and white"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def camera_specs_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "카메라 스펙을 지정하지 않음",
                "prompt": "none"
            },
            "high_end": {
                "name": "고성능 카메라",
                "desc": "고성능 카메라로 촬영",
                "prompt": "high-end camera"
            },
            "smartphone": {
                "name": "휴대폰 카메라",
                "desc": "휴대폰 카메라로 촬영",
                "prompt": "smartphone camera"
            },
            "polaroid": {
                "name": "폴라로이드",
                "desc": "폴라로이드 카메라로 촬영",
                "prompt": "polaroid camera"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def post_processing_options(key=None):
        options = {
            "none": {
                "name": "설정 안 함",
                "desc": "후보정 스타일을 지정하지 않음",
                "prompt": "none"
            },
            "stylish_modern": {
                "name": "스타일리쉬 앤 모던",
                "desc": "스타일리쉬하고 모던한 느낌",
                "prompt": "stylish and modern"
            },
            "analog_nostalgic": {
                "name": "아날로그 느낌",
                "desc": "아날로그 느낌, 그레인, 노스탤직",
                "prompt": "analog feel, grainy, nostalgic"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
    
    @staticmethod
    def background_options(key=None):
        options = {
            "custom": {
                "name": "사용자 지정",
                "desc": "사용자가 지정한 배경",
                "prompt": "custom"
            },
            "dummy": {
                "name": "더미 배경",
                "desc": "더미 배경",
                "prompt": "dummy"
            }
        }
        if key in options.keys():
            return options[key]["prompt"]
        else:
            return options
