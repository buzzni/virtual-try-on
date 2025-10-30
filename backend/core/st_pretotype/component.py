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
    length_options,
    skin_tone_options,
    ethnicity_options,
    hairstyle_options,
    age_options,
    hair_color_options
)
from core.vto_service.service import virtual_tryon, vto_model_tryon, single_image_inference
from prompts.vto_prompts import assemble_prompt
from prompts.side_view_prompts import side_view_prompt

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


def render_vto_results(result: Dict, image_count: int, source_mode: str, include_side: bool = True):
    """
    VTO 결과를 표시하고 측면 이미지 생성을 위한 이미지 선택 기능을 제공합니다.
    
    Args:
        result: VTO 결과 딕셔너리
        image_count: 생성한 이미지 개수
        source_mode: "vto" 또는 "vm" (이미지 선택 키 구분용)
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
            st.markdown(f"**총 {total_count}개의 이미지가 생성되었습니다. (측면 이미지로 사용할 이미지를 선택하세요)**")
            
            # 모든 이미지 수집 (선택 기능용)
            all_images = []
            for idx, img_bytes in enumerate(front_images):
                all_images.append(("정면", idx + 1, img_bytes))
            for idx, img_bytes in enumerate(back_images):
                all_images.append(("후면", idx + 1, img_bytes))
            
            # 선택된 이미지 인덱스 초기화
            selected_key = f"{source_mode}_selected_image_idx"
            if selected_key not in st.session_state:
                st.session_state[selected_key] = 0
            
            selected_idx = st.session_state[selected_key]
            
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
                            
                            # 선택 버튼 추가
                            global_idx = idx  # 정면 이미지의 글로벌 인덱스
                            button_type = "primary" if global_idx == selected_idx else "secondary"
                            button_label = "✓ 측면 생성용 선택됨" if global_idx == selected_idx else "측면 생성용 선택"
                            if st.button(button_label, key=f"{source_mode}_select_front_{idx}", use_container_width=True, type=button_type):
                                st.session_state[selected_key] = global_idx
                                st.rerun()
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
                            
                            # 선택 버튼 추가
                            global_idx = len(front_images) + idx  # 후면 이미지의 글로벌 인덱스
                            button_type = "primary" if global_idx == selected_idx else "secondary"
                            button_label = "✓ 측면 생성용 선택됨" if global_idx == selected_idx else "측면 생성용 선택"
                            if st.button(button_label, key=f"{source_mode}_select_back_{idx}", use_container_width=True, type=button_type):
                                st.session_state[selected_key] = global_idx
                                st.rerun()
                        else:
                            st.warning(f"⚠️ 후면 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
            
            # 선택된 이미지 정보 표시
            if all_images and selected_idx < len(all_images):
                st.success(f"✅ 측면 생성용으로 선택된 이미지: {all_images[selected_idx][0]} #{all_images[selected_idx][1]}")
            
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


def side_view_component(source_mode: str):
    """
    측면 이미지 생성 컴포넌트 (간소화 버전)
    
    Args:
        source_mode: "vto" (가상피팅모드) 또는 "vm" (가상모델피팅모드)
    """
    SIDE_VIEW_TEMPERATURE = 0.5
    st.divider()
    st.subheader("🔄 측면 이미지 생성")
    
    # 세션 상태에서 결과 및 선택된 이미지 가져오기
    source_result = None
    selected_image_bytes = None
    
    source_result = st.session_state.get("vm_result")
    
    if source_result:
        # 선택된 이미지 인덱스 가져오기
        selected_key = "vm_selected_image_idx"
        if selected_key in st.session_state:
            selected_idx = st.session_state[selected_key]
            
            # 모든 이미지 수집
            all_images = []
            front_images = source_result.get("front_images", [])
            back_images = source_result.get("back_images", [])
            
            for idx, img_bytes in enumerate(front_images):
                all_images.append(("정면", idx + 1, img_bytes))
            for idx, img_bytes in enumerate(back_images):
                all_images.append(("후면", idx + 1, img_bytes))
            
            if all_images and selected_idx < len(all_images):
                selected_image_bytes = all_images[selected_idx][2]
    else:
        st.warning("⚠️ 먼저 위에서 가상 피팅 또는 가상 모델 피팅을 실행해주세요.")
    
    st.divider()
    
    # 실행 섹션
    st.subheader("🚀 측면 이미지 생성 실행")
    
    # 세션 상태 초기화
    result_key = "vm_side_result"
    if result_key not in st.session_state:
        st.session_state[result_key] = None
    
    col1, col2 = st.columns(2)  
    with col1:
        image_count = st.slider(
            "생성할 이미지 개수",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            key="vm_side_count",
            help="동시에 생성할 이미지 개수입니다."
        )
    with col2:
        if st.button(
            "🚀 측면 이미지 생성 (좌측 + 우측)", 
            use_container_width=True,
            key="vm_side_btn"
        ):
            if selected_image_bytes is None:
                st.error("❌ 이미지를 선택하거나 업로드해주세요.")
            else:
                with st.spinner("측면 이미지를 생성 중입니다... (좌측 & 우측)"):
                    tmp_image_path = None
                    
                    try:
                        # 이미지를 임시 파일로 저장
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                            tmp_file.write(selected_image_bytes)
                            tmp_image_path = tmp_file.name
                        
                        # 좌측 측면 이미지 생성
                        left_result = asyncio.run(single_image_inference(
                            prompt=side_view_prompt("left"),
                            image_path=tmp_image_path,
                            temperature=SIDE_VIEW_TEMPERATURE,
                            image_count=image_count
                        ))
                        
                        # 우측 측면 이미지 생성
                        right_result = asyncio.run(single_image_inference(
                            prompt=side_view_prompt("right"),
                            image_path=tmp_image_path,
                            temperature=SIDE_VIEW_TEMPERATURE,
                            image_count=image_count
                        ))
                        
                        # 결과 합치기
                        combined_result = {
                            "left_images": left_result.get("front_images", []),
                            "right_images": right_result.get("front_images", []),
                            "left_usage": left_result.get("usage"),
                            "right_usage": right_result.get("usage"),
                            "debug_info": {
                                "left": left_result.get("debug_info", {}),
                                "right": right_result.get("debug_info", {})
                            }
                        }
                        
                        st.session_state[result_key] = combined_result
                        st.success("✅ 측면 이미지 생성 완료! (좌측 + 우측)")
                    except Exception as e:
                        st.error(f"❌ 측면 이미지 생성 중 오류 발생: {str(e)}")
                    finally:
                        # 임시 파일 삭제
                        if tmp_image_path and os.path.exists(tmp_image_path):
                            os.unlink(tmp_image_path)
    
    # 결과 표시
    if st.session_state.get(result_key):
        st.subheader("📊 측면 이미지 생성 결과")
        
        result = st.session_state[result_key]
        
        try:
            left_images = result.get("left_images", [])
            right_images = result.get("right_images", [])
            debug_info = result.get("debug_info", {})
            
            total_images = len(left_images) + len(right_images)
            
            if total_images == 0:
                st.error("❌ 생성된 이미지가 없습니다.")
                with st.expander("🔍 디버깅 정보"):
                    st.json(debug_info)
            else:
                st.markdown(f"**총 {total_images}개의 이미지가 생성되었습니다. (좌측: {len(left_images)}개, 우측: {len(right_images)}개)**")
                
                # 좌측 측면 이미지 표시
                if left_images:
                    st.markdown("### ⬅️ 좌측 측면")
                    num_cols = min(len(left_images), 5)
                    cols = st.columns(num_cols)
                    for idx, image_bytes in enumerate(left_images):
                        with cols[idx % num_cols]:
                            if isinstance(image_bytes, bytes):
                                image = Image.open(BytesIO(image_bytes))
                                st.image(image, caption=f"좌측 #{idx+1}", use_container_width=True)
                            else:
                                st.warning(f"⚠️ 좌측 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
                
                # 우측 측면 이미지 표시
                if right_images:
                    st.markdown("### ➡️ 우측 측면")
                    num_cols = min(len(right_images), 5)
                    cols = st.columns(num_cols)
                    for idx, image_bytes in enumerate(right_images):
                        with cols[idx % num_cols]:
                            if isinstance(image_bytes, bytes):
                                image = Image.open(BytesIO(image_bytes))
                                st.image(image, caption=f"우측 #{idx+1}", use_container_width=True)
                            else:
                                st.warning(f"⚠️ 우측 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
                
                # 사용량 정보 - 좌측과 우측 합산
                st.divider()
                st.markdown("**사용량 정보:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 좌측 측면")
                    left_usage = result.get("left_usage")
                    if left_usage:
                        subcol1, subcol2, subcol3 = st.columns(3)
                        with subcol1:
                            st.metric("총 토큰", left_usage.total_token_count)
                        with subcol2:
                            st.metric("비용 (USD)", f"${left_usage.cost_usd:.6f}")
                        with subcol3:
                            st.metric("비용 (KRW)", f"₩{left_usage.cost_krw:.2f}")
                
                with col2:
                    st.markdown("#### 우측 측면")
                    right_usage = result.get("right_usage")
                    if right_usage:
                        subcol1, subcol2, subcol3 = st.columns(3)
                        with subcol1:
                            st.metric("총 토큰", right_usage.total_token_count)
                        with subcol2:
                            st.metric("비용 (USD)", f"${right_usage.cost_usd:.6f}")
                        with subcol3:
                            st.metric("비용 (KRW)", f"₩{right_usage.cost_krw:.2f}")
                
                # 합산 정보
                if left_usage and right_usage:
                    st.markdown("#### 💰 합계")
                    total_col1, total_col2, total_col3 = st.columns(3)
                    with total_col1:
                        st.metric("총 토큰", left_usage.total_token_count + right_usage.total_token_count)
                    with total_col2:
                        st.metric("비용 (USD)", f"${left_usage.cost_usd + right_usage.cost_usd:.6f}")
                    with total_col3:
                        st.metric("비용 (KRW)", f"₩{left_usage.cost_krw + right_usage.cost_krw:.2f}")
                
                # 디버깅 정보
                with st.expander("🔍 생성 상세 정보"):
                    st.json(debug_info)
                    
        except Exception as e:
            st.error(f"❌ 이미지 표시 중 오류 발생: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# ============================================================================
# 메인 탭 함수들
# ============================================================================

def sidebar():
    st.markdown("### 🧑 모델 설정")
    
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
    
    # 나이
    age_opts = age_options()
    age_keys = list(age_opts.keys())
    age_names = [age_opts[key]["name"] for key in age_keys]
    
    selected_age_name = st.selectbox(
        "나이",
        age_names,
        index=0
    )
    age = age_keys[age_names.index(selected_age_name)]
    
    # 피부색
    skin_tone_opts = skin_tone_options()
    skin_tone_keys = list(skin_tone_opts.keys())
    skin_tone_names = [skin_tone_opts[key]["name"] for key in skin_tone_keys]
    
    selected_skin_tone_name = st.selectbox(
        "피부색",
        skin_tone_names,
        index=0
    )
    skin_tone = skin_tone_keys[skin_tone_names.index(selected_skin_tone_name)]
    
    # 인종
    ethnicity_opts = ethnicity_options()
    ethnicity_keys = list(ethnicity_opts.keys())
    ethnicity_names = [ethnicity_opts[key]["name"] for key in ethnicity_keys]
    
    selected_ethnicity_name = st.selectbox(
        "인종",
        ethnicity_names,
        index=0
    )
    ethnicity = ethnicity_keys[ethnicity_names.index(selected_ethnicity_name)]
    
    # 헤어스타일
    hairstyle_opts = hairstyle_options(gender=gender)
    hairstyle_keys = list(hairstyle_opts.keys())
    hairstyle_names = [hairstyle_opts[key]["name"] for key in hairstyle_keys]
    
    selected_hairstyle_name = st.selectbox(
        "헤어스타일",
        hairstyle_names,
        index=0
    )
    hairstyle = hairstyle_keys[hairstyle_names.index(selected_hairstyle_name)]
    
    # 머리색
    hair_color_opts = hair_color_options()
    hair_color_keys = list(hair_color_opts.keys())
    hair_color_names = [hair_color_opts[key]["name"] for key in hair_color_keys]
    
    selected_hair_color_name = st.selectbox(
        "머리색",
        hair_color_names,
        index=0
    )
    hair_color = hair_color_keys[hair_color_names.index(selected_hair_color_name)]

    st.divider()
    st.markdown("### 👕 의상 설정")
    
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

    return {
        "gender": gender,
        "fit": fit,
        "sleeve": sleeve,
        "length": length,
        "main_category": main_category,
        "sub_category": sub_category,
        "age": age,
        "skin_tone": skin_tone,
        "ethnicity": ethnicity,
        "hairstyle": hairstyle,
        "hair_color": hair_color,
    }

def virtual_model_tab(settings: Dict[str, str]):
    MODEL_TEMPERATURE = 1.5
    # 카테고리에 따른 업로드 수 결정
    num_uploads = 1 if settings["main_category"] == "dress" else 2

    # 이미지 업로드 섹션 (헬퍼 함수 사용)
    front_image_file, back_image_file, together_front_image_file, together_back_image_file = render_image_uploaders(
        key_prefix="vm",
        num_uploads=num_uploads
    )
    
    # 실행 버튼 섹션
    st.subheader("🚀 실행")
    
    # 세션 상태 초기화 (가상모델피팅모드 전용)
    if "vm_result" not in st.session_state:
        st.session_state.vm_result = None
    
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
                    
                    # 모델 옵션 구성
                    model_options = {
                        "gender": settings.get("gender"),
                        "age": settings.get("age"),
                        "skin_tone": settings.get("skin_tone"),
                        "ethnicity": settings.get("ethnicity"),
                        "hairstyle": settings.get("hairstyle"),
                        "hair_color": settings.get("hair_color"),
                    }
                    
                    # Virtual Try-On 실행
                    result = asyncio.run(vto_model_tryon(
                        front_image_path=tmp_front_path,
                        back_image_path=tmp_back_path,
                        together_front_image_path=tmp_together_front_path,
                        together_back_image_path=tmp_together_back_path,
                        model_options=model_options,
                        temperature=MODEL_TEMPERATURE,
                        image_count=image_count
                    ))
                    st.session_state.vm_result = result
                    st.success("✅ 가상 모델 피팅 완료!")
                except Exception as e:
                    st.error(f"❌ 가상 모델 피팅 중 오류 발생: {str(e)}")
                finally:
                    # 임시 파일 삭제
                    cleanup_temp_files(tmp_front_path, tmp_back_path, tmp_together_front_path, tmp_together_back_path)
    
    # VTO 결과 출력 (헬퍼 함수 사용)
    if st.session_state.vm_result:
        st.subheader("📊 가상 모델 피팅 결과")
        render_vto_results(st.session_state.vm_result, image_count, source_mode="vm", include_side=False)
        render_usage_info(st.session_state.vm_result["usage"])
    
    # 측면 이미지 생성 컴포넌트 추가
    side_view_component("vm")