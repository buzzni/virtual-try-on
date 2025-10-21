import asyncio
import streamlit as st
from PIL import Image
import tempfile
import os
from core.vto_service.service import analyze_clothes_image


def analyze_page():
    """의류 이미지 분석 페이지"""
    st.subheader("📤 이미지 업로드")
    
    # 이미지 업로드
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "분석할 이미지 선택",
            type=["jpg", "jpeg", "png", "webp"],
            key="analyze_upload"
        )
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="업로드된 이미지", use_container_width=True)
    
    with col2:
        st.markdown("### 분석 정보")
        st.info("""
        이 도구는 의류 이미지를 분석하여 다음 정보를 추출합니다:
        
        - 의류 카테고리 (상의, 하의, 아우터, 원피스 등)
        - 색상 정보
        - 스타일 및 특징
        - 소재 및 패턴
        - 핏과 실루엣
        
        분석 결과는 JSON 형식으로 제공됩니다.
        """)
    
    st.divider()
    
    # 분석 버튼 섹션
    st.subheader("🔍 이미지 분석")
    
    # 세션 상태 초기화
    if "analyze_result" not in st.session_state:
        st.session_state.analyze_result = None
    
    if st.button("🔍 이미지 분석 실행", use_container_width=True, type="primary"):
        if uploaded_file is None:
            st.error("❌ 이미지를 업로드해주세요.")
        else:
            with st.spinner("이미지를 분석 중입니다..."):
                # 임시 파일로 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    uploaded_file.seek(0)
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name
                
                try:
                    # 비동기 함수 실행
                    result = asyncio.run(analyze_clothes_image(tmp_path))
                    st.session_state.analyze_result = result
                    st.success("✅ 분석 완료!")
                except Exception as e:
                    st.error(f"❌ 분석 중 오류 발생: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                finally:
                    # 임시 파일 삭제
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    # 분석 결과 출력
    if st.session_state.analyze_result:
        st.divider()
        st.subheader("📊 분석 결과")
        
        result = st.session_state.analyze_result
        
        # 주요 정보 카드 형식으로 표시
        col1, col2, col3 = st.columns(3)
        
        result_dict = result.model_dump()
        
        with col1:
            st.markdown("#### 🏷️ 카테고리")
            if "main_category" in result_dict:
                st.info(f"**메인:** {result_dict.get('main_category', 'N/A')}")
            if "sub_category" in result_dict:
                st.info(f"**서브:** {result_dict.get('sub_category', 'N/A')}")
        
        with col2:
            st.markdown("#### 🎨 색상/스타일")
            if "color" in result_dict:
                st.info(f"**색상:** {result_dict.get('color', 'N/A')}")
            if "style" in result_dict:
                st.info(f"**스타일:** {result_dict.get('style', 'N/A')}")
        
        with col3:
            st.markdown("#### 📏 특징")
            if "fit" in result_dict:
                st.info(f"**핏:** {result_dict.get('fit', 'N/A')}")
            if "length" in result_dict:
                st.info(f"**기장:** {result_dict.get('length', 'N/A')}")
        
        # 전체 결과 JSON
        with st.expander("🔍 전체 분석 결과 (JSON)", expanded=False):
            st.json(result_dict)
