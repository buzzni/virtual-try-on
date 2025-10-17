import asyncio
from typing import Dict
import streamlit as st
from PIL import Image
import tempfile
import os
from core.litellm_hander.utils import (
    clothes_category,
    gender_options,
    fit_options,
    sleeve_options,
    length_options
)
from core.vto_service.service import analyze_clothes_image

def sidebar():
    st.header("⚙️ 설정")
    
    # 성별
    gender_opts = gender_options()
    gender_keys = list(gender_opts.keys())
    gender_names = [gender_opts[key]["name"] for key in gender_keys]
    
    selected_gender_name = st.selectbox(
        "성별",
        gender_names,
        index=0
    )
    gender = gender_keys[gender_names.index(selected_gender_name)]
    
    # 핏
    fit_opts = fit_options()
    fit_keys = list(fit_opts.keys())
    fit_names = [fit_opts[key]["name"] for key in fit_keys]
    
    selected_fit_name = st.selectbox(
        "핏",
        fit_names,
        index=0
    )
    fit = fit_keys[fit_names.index(selected_fit_name)]
    
    # 소매
    sleeve_opts = sleeve_options()
    sleeve_keys = list(sleeve_opts.keys())
    sleeve_names = [sleeve_opts[key]["name"] for key in sleeve_keys]
    
    selected_sleeve_name = st.selectbox(
        "소매",
        sleeve_names,
        index=0
    )
    sleeve = sleeve_keys[sleeve_names.index(selected_sleeve_name)]
    
    # 기장
    length_opts = length_options()
    length_keys = list(length_opts.keys())
    length_names = [length_opts[key]["name"] for key in length_keys]
    
    selected_length_name = st.selectbox(
        "기장",
        length_names,
        index=0
    )
    length = length_keys[length_names.index(selected_length_name)]
    
    st.divider()
    
    # 카테고리 데이터 가져오기
    catalog = clothes_category()
    
    # 메인 카테고리 (영문 key -> 한글 name 매핑)
    main_cat_options = list(catalog.keys())
    main_cat_names = [catalog[key]["name"] for key in main_cat_options]
    
    selected_main_name = st.selectbox(
        "메인 카테고리",
        main_cat_names,
        index=0
    )
    
    # 선택된 name에서 key 찾기
    main_category = main_cat_options[main_cat_names.index(selected_main_name)]
    
    # 서브 카테고리 (선택된 메인 카테고리의 children)
    sub_cat_options = list(catalog[main_category]["children"].keys())
    sub_cat_names = [catalog[main_category]["children"][key]["name"] for key in sub_cat_options]
    
    selected_sub_name = st.selectbox(
        "서브 카테고리",
        sub_cat_names,
        index=0
    )
    
    # 선택된 name에서 key 찾기
    sub_category = sub_cat_options[sub_cat_names.index(selected_sub_name)]

    return {
        "gender": gender,
        "fit": fit,
        "sleeve": sleeve,
        "length": length,
        "main_category": main_category,
        "sub_category": sub_category,
    }

def vto_tab(settings: Dict[str, str]):
    st.text(f"settings: {settings}")
    # 카테고리에 따른 업로드 수 결정
    num_uploads = 1 if settings["main_category"] == "dress" else 2

    # 이미지 업로드 섹션
    st.subheader("📤 이미지 업로드")

    if num_uploads == 1:
        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "이미지 선택",
                type=["jpg", "jpeg", "png"],
                key="upload_1"
            )
        with col2:
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="업로드된 이미지", use_container_width=True)
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**이미지 A**")
            uploaded_file_a = st.file_uploader(
                "이미지 A 선택",
                type=["jpg", "jpeg", "png"],
                key="upload_a"
            )
            if uploaded_file_a:
                image_a = Image.open(uploaded_file_a)
                st.image(image_a, caption="이미지 A", use_container_width=True)
        
        with col2:
            st.markdown("**이미지 B**")
            uploaded_file_b = st.file_uploader(
                "이미지 B 선택",
                type=["jpg", "jpeg", "png"],
                key="upload_b"
            )
            if uploaded_file_b:
                image_b = Image.open(uploaded_file_b)
                st.image(image_b, caption="이미지 B", use_container_width=True)

    st.divider()

    # 분석 버튼 섹션
    st.subheader("🔍 의류 이미지 분석")
    
    # 세션 상태 초기화
    if "analys" not in st.session_state:
        st.session_state.analys = None
    
    if st.button("🔍 첫 번째 이미지 분석", use_container_width=True):
        # 첫 번째 이미지 가져오기
        first_image = uploaded_file if num_uploads == 1 else uploaded_file_a
        
        if first_image is None:
            st.error("❌ 첫 번째 이미지를 업로드해주세요.")
        else:
            with st.spinner("이미지를 분석 중입니다..."):
                # 임시 파일로 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    first_image.seek(0)
                    tmp_file.write(first_image.read())
                    tmp_path = tmp_file.name
                
                try:
                    # 비동기 함수 실행
                    result = asyncio.run(analyze_clothes_image(tmp_path))
                    st.session_state.analys = result
                    st.success("✅ 분석 완료!")
                except Exception as e:
                    st.error(f"❌ 분석 중 오류 발생: {str(e)}")
                finally:
                    # 임시 파일 삭제
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    # 분석 결과 출력
    if st.session_state.analys:
        st.subheader("📊 분석 결과")
        st.json(st.session_state.analys.model_dump())
    
    st.divider()

    # 실행 버튼 섹션
    st.subheader("🚀 실행")    