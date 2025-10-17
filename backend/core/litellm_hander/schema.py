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