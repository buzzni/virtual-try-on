import asyncio
from typing import Dict, Tuple, Optional, List
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
from core.vto_service.service import analyze_clothes_image, virtual_tryon, vto_model_tryon
from prompts.vto_prompts import assemble_prompt

# ============================================================================
# 헬퍼 함수들
# ============================================================================

def render_image_uploaders(key_prefix: str, num_uploads: int) -> Tuple[Optional[st.runtime.uploaded_file_manager.UploadedFile], ...]:
    """
    이미지 업로더 UI를 렌더링하고 업로드된 파일들을 반환합니다.
    
    Args:
        key_prefix: file_uploader의 key prefix (중복 방지)
        num_uploads: 업로드 개수 (1: dress, 2: top/bottom)
    
    Returns:
        Tuple: (front_image_file, back_image_file, together_front_image_file, together_back_image_file)
    """
    st.subheader("📤 이미지 업로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            st.markdown("**앞면 이미지**")
            front_image_file = st.file_uploader(
                "앞면 이미지 선택",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"{key_prefix}_upload_a"
            )
            if front_image_file:
                image_a = Image.open(front_image_file)
                st.image(image_a, caption="앞면 이미지", width='stretch')
    
        with col1_2:
            st.markdown("**뒷면 이미지**")
            back_image_file = st.file_uploader(
                "뒷면 이미지 선택",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"{key_prefix}_upload_b"
            )
            if back_image_file:
                image_b = Image.open(back_image_file)
                st.image(image_b, caption="뒷면 이미지", width='stretch')
    with col2:
        # 함께 입을 옷 업로더 초기화
        together_front_image_file = None
        together_back_image_file = None
        
        if num_uploads > 1:
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.markdown("**함께 입을 옷 앞면 이미지**")
                together_front_image_file = st.file_uploader(
                    "함께 입을 옷 앞면 이미지 선택",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"{key_prefix}_upload_together_a"
                )
                if together_front_image_file:
                    image_together_a = Image.open(together_front_image_file)
                    st.image(image_together_a, caption="함께 입을 옷 앞면 이미지", width='stretch')
            
            with col2_2:
                st.markdown("**함께 입을 옷 뒷면 이미지**")
                together_back_image_file = st.file_uploader(
                    "함께 입을 옷 뒷면 이미지 선택",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"{key_prefix}_upload_together_b"
                )
                if together_back_image_file:
                    image_together_b = Image.open(together_back_image_file)
                    st.image(image_together_b, caption="함께 입을 옷 뒷면 이미지", width='stretch')
    
    st.divider()
    
    return front_image_file, back_image_file, together_front_image_file, together_back_image_file


def save_images_to_temp_files(
    front_image, 
    back_image, 
    together_front_image, 
    together_back_image
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    업로드된 이미지들을 임시 파일로 저장합니다.
    
    Returns:
        Tuple: (tmp_front_path, tmp_back_path, tmp_together_front_path, tmp_together_back_path)
    """
    tmp_front_path = None
    tmp_back_path = None
    tmp_together_front_path = None
    tmp_together_back_path = None
    
    # 앞면 이미지 저장
    if front_image is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            front_image.seek(0)
            tmp_file.write(front_image.read())
            tmp_front_path = tmp_file.name
    
    # 뒷면 이미지 저장
    if back_image is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            back_image.seek(0)
            tmp_file.write(back_image.read())
            tmp_back_path = tmp_file.name
    
    # 함께 입을 옷 앞면 이미지 저장
    if together_front_image is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            together_front_image.seek(0)
            tmp_file.write(together_front_image.read())
            tmp_together_front_path = tmp_file.name
    
    # 함께 입을 옷 뒷면 이미지 저장
    if together_back_image is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            together_back_image.seek(0)
            tmp_file.write(together_back_image.read())
            tmp_together_back_path = tmp_file.name
    
    return tmp_front_path, tmp_back_path, tmp_together_front_path, tmp_together_back_path


def cleanup_temp_files(*file_paths):
    """임시 파일들을 삭제합니다."""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)


def render_vto_results(result: Dict, image_count: int, include_side: bool = True):
    """
    VTO 결과를 표시합니다.
    
    Args:
        result: VTO 결과 딕셔너리
        image_count: 생성한 이미지 개수
        include_side: 측면 이미지 포함 여부
    """
    try:
        # 앞면/뒷면/측면 이미지 개별 추출
        front_images = result.get("front_images", [])
        back_images = result.get("back_images", [])
        side_images = result.get("side_images", [])
        debug_info = result.get("debug_info", {})
        
        total_count = len(front_images) + len(back_images) + (len(side_images) if include_side else 0)
        
        if total_count == 0:
            st.error("❌ 생성된 이미지가 없습니다.")
            with st.expander("🔍 디버깅 정보"):
                st.json(debug_info)
        else:
            st.markdown(f"**총 {total_count}개의 이미지가 생성되었습니다.**")
            
            # 앞면 이미지 표시
            if front_images:
                st.markdown("### 🔵 정면 뷰")
                num_cols = image_count
                cols = st.columns(num_cols)
                for idx, image_bytes in enumerate(front_images):
                    with cols[idx % num_cols]:
                        if isinstance(image_bytes, bytes):
                            image = Image.open(BytesIO(image_bytes))
                            st.image(image, caption=f"정면 #{idx+1}", width='stretch')
                        else:
                            st.warning(f"⚠️ 정면 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
            
            # 뒷면 이미지 표시
            if back_images:
                st.markdown("### 🔴 후면 뷰")
                num_cols = image_count
                cols = st.columns(num_cols)
                for idx, image_bytes in enumerate(back_images):
                    with cols[idx % num_cols]:
                        if isinstance(image_bytes, bytes):
                            image = Image.open(BytesIO(image_bytes))
                            st.image(image, caption=f"후면 #{idx+1}", width='stretch')
                        else:
                            st.warning(f"⚠️ 후면 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
            
            # 측면 이미지 표시 (옵션)
            if include_side and side_images:
                st.markdown("### 🟢 측면 뷰")
                num_cols = min(len(side_images), 3)
                cols = st.columns(num_cols)
                for idx, image_bytes in enumerate(side_images):
                    with cols[idx % num_cols]:
                        if isinstance(image_bytes, bytes):
                            image = Image.open(BytesIO(image_bytes))
                            st.image(image, caption=f"측면 #{idx+1}", width='stretch')
                        else:
                            st.warning(f"⚠️ 측면 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
            
            # 디버깅 정보 (옵션)
            with st.expander("🔍 생성 상세 정보"):
                st.json(debug_info)
            
    except Exception as e:
        st.error(f"❌ 이미지 표시 중 오류 발생: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def render_usage_info(usage):
    """사용량 정보를 표시합니다."""
    st.divider()
    st.markdown("**사용량 정보:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 토큰", usage.total_token_count)
    with col2:
        st.metric("비용 (USD)", f"${usage.cost_usd:.6f}")
    with col3:
        st.metric("비용 (KRW)", f"₩{usage.cost_krw:.2f}")

# ============================================================================
# 메인 탭 함수들
# ============================================================================

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

    # 이미지 업로드 섹션 (헬퍼 함수 사용)
    front_image_file, back_image_file, together_front_image_file, together_back_image_file = render_image_uploaders(
        key_prefix="vto",
        num_uploads=num_uploads
    )

    # 분석 버튼 섹션
    st.subheader("🔍 의류 이미지 분석")
    
    # 세션 상태 초기화
    if "analys" not in st.session_state:
        st.session_state.analys = None
    
    if st.button("🔍 첫 번째 이미지 분석", width='stretch'):
        # 첫 번째 이미지 가져오기
        if front_image_file:
            image = front_image_file
        elif back_image_file:
            image = back_image_file
        else:
            st.error("❌ 최소 하나의 이미지를 업로드해주세요.")
            return
        
        with st.spinner("이미지를 분석 중입니다..."):
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                image.seek(0)
                tmp_file.write(image.read())
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
                main_category=settings["main_category"],
                sub_category=settings["sub_category"],
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
        
        image_count = st.slider(
            "생성할 이미지 개수",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="동시에 생성할 이미지 개수입니다. 여러 개를 생성하면 다양한 결과를 얻을 수 있습니다."
        )
        
    vto_button_disabled = st.session_state.generated_prompt is None
    if st.button(
        "🚀 Virtual Try-On 실행", 
        width='stretch',
        disabled=vto_button_disabled,
        help="먼저 프롬프트를 생성해주세요." if vto_button_disabled else None
    ):
        # 이미지 가져오기
        front_image = front_image_file
        back_image = back_image_file
        together_front_image = together_front_image_file
        together_back_image = together_back_image_file
        
        if front_image is None and back_image is None:
            st.error("❌ 최소 하나의 이미지를 업로드해주세요.")
        else:
            with st.spinner("Virtual Try-On을 실행 중입니다..."):
                try:
                    # 이미지를 임시 파일로 저장
                    tmp_front_path, tmp_back_path, tmp_together_front_path, tmp_together_back_path = save_images_to_temp_files(
                        front_image, back_image, together_front_image, together_back_image
                    )
                    
                    # text_area에서 현재 프롬프트 가져오기 (사용자가 수정했을 수 있음)
                    prompt_key = f"prompt_editor_{st.session_state.prompt_version}"
                    prompt = st.session_state.get(prompt_key, st.session_state.generated_prompt)
                    
                    # Virtual Try-On 실행
                    result = asyncio.run(virtual_tryon(
                        front_image_path=tmp_front_path,
                        back_image_path=tmp_back_path,
                        prompt=prompt,
                        together_front_image_path=tmp_together_front_path,
                        together_back_image_path=tmp_together_back_path,
                        temperature=temperature,
                        image_count=image_count
                    ))
                    st.session_state.vto_result = result
                    st.success("✅ Virtual Try-On 완료!")
                except Exception as e:
                    st.error(f"❌ Virtual Try-On 중 오류 발생: {str(e)}")
                finally:
                    # 임시 파일 삭제
                    cleanup_temp_files(tmp_front_path, tmp_back_path, tmp_together_front_path, tmp_together_back_path)
    
    # VTO 결과 출력 (헬퍼 함수 사용)
    if st.session_state.vto_result:
        st.subheader("📊 Virtual Try-On 결과")
        render_vto_results(st.session_state.vto_result, image_count, include_side=False)
        render_usage_info(st.session_state.vto_result["usage"])
            
            
def virtual_model_tab(settings: Dict[str, str]):
    # 카테고리에 따른 업로드 수 결정
    num_uploads = 1 if settings["main_category"] == "dress" else 2

    # 이미지 업로드 섹션 (헬퍼 함수 사용)
    front_image_file, back_image_file, together_front_image_file, together_back_image_file = render_image_uploaders(
        key_prefix="vm",
        num_uploads=num_uploads
    )
    
    # 실행 버튼 섹션
    st.subheader("🚀 실행")
    
    # 세션 상태 초기화
    if "vto_result" not in st.session_state:
        st.session_state.vto_result = None
    if "generated_prompt" not in st.session_state:
        st.session_state.generated_prompt = None
    if "prompt_version" not in st.session_state:
        st.session_state.prompt_version = 0
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="결과의 다양성을 조절합니다. 높을수록 더 다양하고 창의적인 결과가 나옵니다."
    )
    
    image_count = st.slider(
        "생성할 이미지 개수",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="동시에 생성할 이미지 개수입니다. 여러 개를 생성하면 다양한 결과를 얻을 수 있습니다."
    )
        
    if st.button(
        "🚀 가상 모델 피팅 실행", 
        width='stretch',
    ):
        # 이미지 가져오기
        front_image = front_image_file
        back_image = back_image_file
        together_front_image = together_front_image_file
        together_back_image = together_back_image_file
        
        if front_image is None and back_image is None:
            st.error("❌ 최소 하나의 이미지를 업로드해주세요.")
        else:
            with st.spinner("가상 모델 피팅을 실행 중입니다..."):
                try:
                    # 이미지를 임시 파일로 저장
                    tmp_front_path, tmp_back_path, tmp_together_front_path, tmp_together_back_path = save_images_to_temp_files(
                        front_image, back_image, together_front_image, together_back_image
                    )
                    
                    # Virtual Try-On 실행
                    result = asyncio.run(vto_model_tryon(
                        front_image_path=tmp_front_path,
                        back_image_path=tmp_back_path,
                        together_front_image_path=tmp_together_front_path,
                        together_back_image_path=tmp_together_back_path,
                        temperature=temperature,
                        image_count=image_count
                    ))
                    st.session_state.vto_result = result
                    st.success("✅ 가상 모델 피팅 완료!")
                except Exception as e:
                    st.error(f"❌ 가상 모델 피팅 중 오류 발생: {str(e)}")
                finally:
                    # 임시 파일 삭제
                    cleanup_temp_files(tmp_front_path, tmp_back_path, tmp_together_front_path, tmp_together_back_path)
    
    # VTO 결과 출력 (헬퍼 함수 사용)
    if st.session_state.vto_result:
        st.subheader("📊 가상 모델 피팅 결과")
        render_vto_results(st.session_state.vto_result, image_count, include_side=False)
        render_usage_info(st.session_state.vto_result["usage"])