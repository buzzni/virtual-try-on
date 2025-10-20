import asyncio
from typing import Dict
import streamlit as st
from PIL import Image
import tempfile
import os
from io import BytesIO
from core.litellm_hander.utils import (
    clothes_category,
    gender_options,
    fit_options,
    sleeve_options,
    length_options
)
from core.vto_service.service import analyze_clothes_image, virtual_tryon
from prompts.vto_prompts import assemble_prompt

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
                st.image(image, caption="업로드된 이미지", width='stretch')
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
                st.image(image_a, caption="이미지 A", width='stretch')
        
        with col2:
            st.markdown("**이미지 B**")
            uploaded_file_b = st.file_uploader(
                "이미지 B 선택",
                type=["jpg", "jpeg", "png"],
                key="upload_b"
            )
            if uploaded_file_b:
                image_b = Image.open(uploaded_file_b)
                st.image(image_b, caption="이미지 B", width='stretch')

    st.divider()

    # 분석 버튼 섹션
    st.subheader("🔍 의류 이미지 분석")
    
    # 세션 상태 초기화
    if "analys" not in st.session_state:
        st.session_state.analys = None
    
    if st.button("🔍 첫 번째 이미지 분석", width='stretch'):
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
    
    # 세션 상태 초기화
    if "vto_result" not in st.session_state:
        st.session_state.vto_result = None
    if "generated_prompt" not in st.session_state:
        st.session_state.generated_prompt = None
    if "prompt_version" not in st.session_state:
        st.session_state.prompt_version = 0
    
    # 프롬프트 생성 버튼
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        st.json(settings)
        if st.button("📝 프롬프트 생성", width='stretch'):
            # 프롬프트 생성
            prompt = assemble_prompt(
                category=settings["main_category"],
                target="garment",
                replacement="clothing",
                gender=settings["gender"],
                fit=settings["fit"] if settings["fit"] != "none" else None,
                sleeve=settings["sleeve"] if settings["sleeve"] != "none" else None,
                length=settings["length"] if settings["length"] != "none" else None,
            )
            st.session_state.generated_prompt = prompt
            # 버전 증가로 text_area 강제 재생성
            st.session_state.prompt_version += 1
            st.success("✅ 프롬프트가 생성되었습니다!")
    
    # 생성된 프롬프트 표시 및 수정
    if st.session_state.generated_prompt:
        st.markdown("**생성된 프롬프트 (수정 가능):**")
        # 버전을 key에 포함하여 프롬프트가 생성될 때마다 text_area 재생성
        st.text_area(
            "프롬프트",
            value=st.session_state.generated_prompt,
            height=200,
            key=f"prompt_editor_{st.session_state.prompt_version}",
            help="필요시 프롬프트를 수정할 수 있습니다."
        )
    
    with col_btn2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="결과의 다양성을 조절합니다. 높을수록 더 다양하고 창의적인 결과가 나옵니다."
        )
        
    vto_button_disabled = st.session_state.generated_prompt is None
    if st.button(
        "🚀 Virtual Try-On 실행", 
        width='stretch',
        disabled=vto_button_disabled,
        help="먼저 프롬프트를 생성해주세요." if vto_button_disabled else None
    ):
        # 이미지 가져오기
        if num_uploads == 1:
            st.warning("⚠️ Virtual Try-On은 2개의 이미지가 필요합니다.")
        else:
            if uploaded_file_a is None or uploaded_file_b is None:
                st.error("❌ 두 개의 이미지를 모두 업로드해주세요.")
            else:
                with st.spinner("Virtual Try-On을 실행 중입니다..."):
                    # 임시 파일로 저장
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file_1:
                        uploaded_file_a.seek(0)
                        tmp_file_1.write(uploaded_file_a.read())
                        tmp_path_1 = tmp_file_1.name
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file_2:
                        uploaded_file_b.seek(0)
                        tmp_file_2.write(uploaded_file_b.read())
                        tmp_path_2 = tmp_file_2.name
                    
                    try:
                        # text_area에서 현재 프롬프트 가져오기 (사용자가 수정했을 수 있음)
                        prompt_key = f"prompt_editor_{st.session_state.prompt_version}"
                        prompt = st.session_state.get(prompt_key, st.session_state.generated_prompt)
                        
                        # Virtual Try-On 실행 (slider에서 선택한 temperature 사용)
                        result = asyncio.run(virtual_tryon(
                            tmp_path_1, 
                            tmp_path_2, 
                            prompt,
                            temperature=temperature
                        ))
                        st.session_state.vto_result = result
                        st.success("✅ Virtual Try-On 완료!")
                    except Exception as e:
                        st.error(f"❌ Virtual Try-On 중 오류 발생: {str(e)}")
                    finally:
                        # 임시 파일 삭제
                        if os.path.exists(tmp_path_1):
                            os.unlink(tmp_path_1)
                        if os.path.exists(tmp_path_2):
                            os.unlink(tmp_path_2)
    
    # VTO 결과 출력
    if st.session_state.vto_result:
        st.subheader("📊 Virtual Try-On 결과")
        st.markdown("**생성된 이미지:**")
        
        # 디버깅 옵션
        with st.expander("🔍 디버깅 정보 (응답 구조 확인)"):
            if "debug_info" in st.session_state.vto_result:
                st.json(st.session_state.vto_result["debug_info"])
            
            response_data = st.session_state.vto_result["response"]
            st.write("응답 타입:", type(response_data).__name__)
            st.write("응답이 None인가?", response_data is None)
            
            if response_data is not None:
                if isinstance(response_data, str):
                    st.write("응답 길이:", len(response_data))
                    st.write("응답 시작 부분 (최대 200자):", response_data[:200])
                else:
                    st.write("응답 내용:", response_data)
        
        try:
            # 응답에서 이미지 추출 (vto_mino 방식 적용)
            response_data = st.session_state.vto_result["response"]
            
            if response_data is None:
                st.error("❌ 응답에 이미지 데이터가 없습니다. 디버깅 정보를 확인해주세요.")
            elif isinstance(response_data, bytes):
                # 바이너리 데이터를 PIL Image로 변환 (vto_mino 방식)
                image = Image.open(BytesIO(response_data))
                st.image(image, caption="가상 착장 결과", width='stretch')
            else:
                st.warning(f"⚠️ 예상하지 못한 응답 형식입니다: {type(response_data).__name__}")
                st.text_area("원본 응답 데이터 (최대 500자)", value=str(response_data)[:500], height=150, disabled=True)
                
        except Exception as e:
            st.error(f"❌ 이미지 표시 중 오류 발생: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
        
        st.divider()
        
        st.markdown("**사용량 정보:**")
        usage = st.session_state.vto_result["usage"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 토큰", usage.total_token_count)
        with col2:
            st.metric("비용 (USD)", f"${usage.cost_usd:.6f}")
        with col3:
            st.metric("비용 (KRW)", f"₩{usage.cost_krw:.2f}")