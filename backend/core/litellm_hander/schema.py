from typing import List, Optional
from pydantic import BaseModel, Field

class LiteLLMUsageData(BaseModel):
    total_token_count: int = Field(..., description="총 토큰 수")
    prompt_token_count: int = Field(..., description="프롬프트 토큰 수")
    candidates_token_count: int = Field(..., description="응답 토큰 수")
    output_token_count: int = Field(..., description="출력 토큰 수")
    cached_content_token_count: int = Field(0, description="캐시된 토큰 수")
    thoughts_token_count: int = Field(0, description="사고 토큰 수")
    model_name: str = Field(..., description="모델 이름")
    cost_usd: float = Field(..., description="USD 비용")
    cost_krw: float = Field(..., description="KRW 비용")
    task_name: Optional[str] = Field(None, description="작업 이름")

class TotalUsageData(BaseModel):
    total: LiteLLMUsageData = Field(..., description="전체 비용 합계")
    details: List[LiteLLMUsageData] = Field(..., description="개별 항목 리스트")

class ClothesImageAnalysis(BaseModel):
    clothes_type: str = Field(..., description="옷 유형")
    fit_desc: str = Field(..., description="핏 설명")
    design_desc: str = Field(..., description="디자인 설명")
    material_desc: str = Field(..., description="소재 설명")
    color_desc: str = Field(..., description="색상 설명")
    style_desc: str = Field(..., description="스타일 설명")
    overall_desc: str = Field(..., description="전체 설명")


class Detection(BaseModel):
    label: str = Field(..., description="불일치 항목 설명")
    box_2d: List[int] = Field(..., description="불일치 항목 박스 좌표")

class ValidGeneratedVTO(BaseModel):
    result: str = Field(..., description="결과")
    detections: List[Detection] = Field(..., description="불일치 항목 리스트")
    
class ModelOptions(BaseModel):
    gender: str = Field(..., description="성별")
    age: Optional[str] = Field(None, description="나이")
    skin_tone: Optional[str] = Field(None, description="피부색")
    ethnicity: Optional[str] = Field(None, description="인종")
    hairstyle: Optional[str] = Field(None, description="헤어스타일")
    hair_color: Optional[str] = Field(None, description="머리색")
    height: Optional[float] = Field(None, description="키(cm)")
    weight: Optional[float] = Field(None, description="몸무게(kg)")

class ClothesOptions(BaseModel):
    main_category: str = Field(..., description="메인 카테고리")
    sub_category: str = Field(..., description="서브 카테고리")
    replacement: Optional[str] = Field(None, description="대체할 의상 부위")
    image_count: Optional[int] = Field(None, description="입력 이미지 개수")
    how: Optional[str] = Field(None, description="입히는 방법")
    sleeve: Optional[str] = Field(None, description="소매 속성")
    length: Optional[str] = Field(None, description="기장 속성")
    fit: Optional[str] = Field(None, description="핏 속성")
    total_length: Optional[float] = Field(None, description="전체 기장(cm)")
    
class StyleCutOptions(BaseModel):
    shot_type: Optional[str] = Field(None, description="카메라 구도 및 프레임 구성")
    camera_angle: Optional[str] = Field(None, description="카메라 앵글")
    pose: Optional[str] = Field(None, description="인물의 자세")
    arms_pose: Optional[str] = Field(None, description="팔 포즈")
    gaze: Optional[str] = Field(None, description="시선")
    facial_expression: Optional[str] = Field(None, description="표정 또는 감정 분위기")
    background: Optional[str] = Field(None, description="배경 컨텍스트")
    lighting_style: Optional[str] = Field(None, description="조명 세팅")
    color_tone: Optional[str] = Field(None, description="색감")
    camera_specs: Optional[str] = Field(None, description="카메라 스펙")
    post_processing_keywords: Optional[str] = Field(None, description="질감 및 후보정")