def gender_options():
    return {
        "person": {
            "name": "공통",
            "desc": "성별 구분 없이 공통으로 적용"
        },
        "man": {
            "name": "남성",
            "desc": "남성 모델에 적용"
        },
        "woman": {
            "name": "여성",
            "desc": "여성 모델에 적용"
        }
    }

def fit_options():
    return {
        "none": {
            "name": "설정 안 함",
            "desc": "핏 설정을 지정하지 않음"
        },
        "regular": {
            "name": "레귤러",
            "desc": "일반적인 기본 핏"
        },
        "oversized": {
            "name": "오버사이즈",
            "desc": "여유있는 루즈한 핏"
        },
        "slim": {
            "name": "슬림핏",
            "desc": "몸에 맞는 타이트한 핏"
        }
    }

def sleeve_options():
    return {
        "none": {
            "name": "설정 안 함",
            "desc": "소매 길이를 지정하지 않음"
        },
        "short": {
            "name": "반팔",
            "desc": "짧은 소매 길이"
        },
        "long": {
            "name": "긴팔",
            "desc": "긴 소매 길이"
        },
        "sleeveless": {
            "name": "민소매",
            "desc": "소매가 없는 스타일"
        }
    }

def length_options():
    return {
        "none": {
            "name": "설정 안 함",
            "desc": "기장을 지정하지 않음"
        },
        "crop": {
            "name": "크롭",
            "desc": "배꼽 위로 짧은 기장"
        },
        "waist": {
            "name": "허리",
            "desc": "허리 라인 기장"
        },
        "hip": {
            "name": "엉덩이",
            "desc": "엉덩이를 덮는 기장"
        },
        "thigh": {
            "name": "허벅지",
            "desc": "허벅지 중간 기장"
        },
        "knee": {
            "name": "무릎",
            "desc": "무릎 라인 기장"
        },
        "calf": {
            "name": "종아리",
            "desc": "종아리 중간 기장"
        },
        "long": {
            "name": "긴 기장",
            "desc": "발목 근처까지 오는 긴 기장"
        },
        "floor": {
            "name": "바닥에 닿는 기장",
            "desc": "바닥까지 닿는 매우 긴 기장"
        }
    }

def clothes_category():
    catalog = {
        "tops": {
            "name": "상의",
            "desc": "상반신 기본 의류. 계절·활동·핏에 따라 선택.",
            "children": {
                "sweatshirt": {
                    "name": "맨투맨/스웨트",
                    "desc": "도톰한 저지/기모 소재의 캐주얼 스웨트 셔츠.",
                },
                "hoodie": {
                    "name": "후드 티셔츠",
                    "desc": "후드와 캥거루 포켓이 특징인 캐주얼 톱.",
                },
                "shirt_blouse": {
                    "name": "셔츠/블라우스",
                    "desc": "칼라와 버튼 여밈의 포멀·세미포멀 상의.",
                },
                "longsleeve_tshirt": {
                    "name": "긴소매 티셔츠",
                    "desc": "롱슬리브 저지 톱, 이너/단품용.",
                },
                "shortsleeve_tshirt": {
                    "name": "반소매 티셔츠",
                    "desc": "하프슬리브 기본 티, 로고/프린트 다양.",
                },
                "polo": {
                    "name": "피케/카라 티셔츠",
                    "desc": "카라와 버튼 플래킷의 니트 저지 톱.",
                },
                "knit_sweater": {
                    "name": "니트/스웨터",
                    "desc": "편직 소재의 보온성 상의 (라운드·브이넥 등).",
                },
                "sleeveless": {
                    "name": "민소매 티셔츠",
                    "desc": "슬리브리스 톱, 여름용 혹은 레이어링용.",
                },
                "tops_etc": {
                    "name": "기타 상의",
                    "desc": "위 분류에 속하지 않는 상의 전반.",
                },
            },
        },
        "outer": {
            "name": "아우터",
            "desc": "기온·날씨 대응 및 스타일 포인트용 겉옷.",
            "children": {
                "zipup_hoodie": {
                    "name": "후드 집업",
                    "desc": "지퍼 여밈 후디, 가벼운 레이어링용.",
                },
                "ma1": {
                    "name": "블루종/MA-1",
                    "desc": "허리·소매 시보리의 항공 재킷.",
                },
                "leather_riders": {
                    "name": "레더/라이더스 재킷",
                    "desc": "가죽 소재의 하드한 무드 재킷.",
                },
                "cardigan": {
                    "name": "카디건",
                    "desc": "앞여밈 니트 아우터, 이너 위에 가볍게 착용.",
                },
                "trucker": {
                    "name": "트러커 재킷",
                    "desc": "데님/코튼 트윌의 박시 숏 재킷.",
                },
                "blazer": {
                    "name": "슈트/블레이저 재킷",
                    "desc": "테일러드 라펠의 포멀 재킷.",
                },
                "varsity": {
                    "name": "스타디움 재킷",
                    "desc": "배색·스냅 여밈의 바시티 스타일 재킷.",
                },
                "coach": {
                    "name": "나일론/코치 재킷",
                    "desc": "경량 우븐, 생활 방풍/발수 기능.",
                },
                "anorak": {
                    "name": "아노락 재킷",
                    "desc": "하프집·후드의 풀오버 윈드브레이커.",
                },
                "training_jacket": {
                    "name": "트레이닝 재킷",
                    "desc": "저지/트랙 소재의 스포츠 아우터.",
                },
                "midseason_coat": {
                    "name": "환절기 코트",
                    "desc": "간절기용 경량 코트.",
                },
                "safari": {
                    "name": "사파리/헌팅 재킷",
                    "desc": "포켓 많은 실용적 미들 재킷.",
                },
                "vest": {
                    "name": "베스트",
                    "desc": "소매 없는 경량 레이어 아이템.",
                },
                "short_padding": {
                    "name": "숏패딩/헤비 아우터",
                    "desc": "두터운 충전재의 보온 숏 재킷.",
                },
                "mustang_fur": {
                    "name": "무스탕/퍼",
                    "desc": "셰어링/퍼 안감의 보온 아우터.",
                },
                "fleece": {
                    "name": "플리스/뽀글이",
                    "desc": "폴라 플리스 소재의 경량 보온 아우터.",
                },
                "single_coat": {
                    "name": "겨울 싱글 코트",
                    "desc": "싱글 브레스티드 클래식 겨울 코트.",
                },
                "double_coat": {
                    "name": "겨울 더블 코트",
                    "desc": "더블 브레스티드 구조적 실루엣 코트.",
                },
                "winter_coat_etc": {
                    "name": "겨울 기타 코트",
                    "desc": "체스터필드 등 기타 겨울 코트.",
                },
                "long_padding": {
                    "name": "롱패딩/헤비 아우터",
                    "desc": "무릎 이상 길이의 최고 보온 아우터.",
                },
                "padding_vest": {
                    "name": "패딩 베스트",
                    "desc": "충전재 베스트, 코어 보온용.",
                },
                "outer_etc": {
                    "name": "기타 아우터",
                    "desc": "상기 외 아우터 전반.",
                },
            },
        },
        "bottoms": {
            "name": "바지",
            "desc": "하반신 의류. 핏·소재·활동성 중심 선택.",
            "children": {
                "denim_pants": {
                    "name": "데님 팬츠",
                    "desc": "데님 소재의 5포켓/와이드/슬림 등.",
                },
                "jogger_pants": {
                    "name": "트레이닝/조거 팬츠",
                    "desc": "저지·밴딩·밑단 시보리의 이지웨어.",
                },
                "cotton_pants": {
                    "name": "코튼 팬츠",
                    "desc": "치노/트윌 등 캐주얼 코튼 바지.",
                },
                "slacks": {
                    "name": "슈트 팬츠/슬랙스",
                    "desc": "테일러드 라인의 포멀 팬츠.",
                },
                "short_pants": {
                    "name": "숏 팬츠",
                    "desc": "허벅지 길이의 경량 반바지.",
                },
                "leggings": {
                    "name": "레깅스",
                    "desc": "신축성 높은 바디핏 팬츠.",
                },
                "jumpsuit": {
                    "name": "점프 슈트/오버올",
                    "desc": "상·하의 일체형 작업복 실루엣.",
                },
                "bottoms_etc": {
                    "name": "기타 하의",
                    "desc": "상기 외 하의 전반.",
                },
            },
        },
        "dress": {
            "name": "원피스",
            "desc": "한 벌로 스타일 완성. 길이·실루엣 다양.",
            "children": {
                "mini_dress": {
                    "name": "미니원피스",
                    "desc": "허벅지 길이의 경쾌한 원피스.",
                },
                "midi_dress": {
                    "name": "미디원피스",
                    "desc": "무릎 전후의 균형감 있는 원피스.",
                },
                "maxi_dress": {
                    "name": "맥시원피스",
                    "desc": "발목까지 흐르는 롱 실루엣.",
                },
                "mini_skirt": {
                    "name": "미니스커트",
                    "desc": "짧은 길이의 스커트.",
                },
                "midi_skirt": {
                    "name": "미디스커트",
                    "desc": "무릎 전후 길이의 스커트.",
                },
                "long_skirt": {
                    "name": "롱스커트",
                    "desc": "발목까지 길게 떨어지는 스커트.",
                },
            },
        },
    }
    return catalog