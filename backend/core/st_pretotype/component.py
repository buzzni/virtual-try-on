import asyncio
from typing import Dict, Tuple, Optional, List, Tuple
import streamlit as st
from PIL import Image
import tempfile
import os
from io import BytesIO
from core.litellm_hander.utils import ModelOptions as ModelOptionsUtils, ClothesOptions as ClothesOptionsUtils
from core.litellm_hander.schema import ModelOptions, ClothesOptions
from core.vto_service.service import image_inference_with_prompt
from prompts.vto_model_prompts import assemble_model_prompt
from core.st_pretotype.side_view_component import side_view_component

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
        st.markdown("**앞면 이미지**")
        front_image_file = st.file_uploader(
            "앞면 이미지 선택",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"{key_prefix}_upload_a"
        )
        if front_image_file:
            image_a = Image.open(front_image_file)
            st.image(image_a, caption="앞면 이미지", width='stretch')
    with col2:
        # 함께 입을 옷 업로더 초기화
        together_front_image_file = None
        
        if num_uploads > 1:
            st.markdown("**함께 입을 옷 앞면 이미지**")
            together_front_image_file = st.file_uploader(
                "함께 입을 옷 앞면 이미지 선택",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"{key_prefix}_upload_together_a"
            )
            if together_front_image_file:
                image_together_a = Image.open(together_front_image_file)
                st.image(image_together_a, caption="함께 입을 옷 앞면 이미지", width='stretch')

    st.divider()
    
    return front_image_file, together_front_image_file


def save_images_to_temp_files(
    front_image, 
    together_front_image, 
) -> Tuple[Optional[str], Optional[str]]:
    """
    업로드된 이미지들을 임시 파일로 저장합니다.
    
    Returns:
        Tuple: (tmp_front_path, tmp_together_front_path)
    """
    tmp_front_path = None
    tmp_together_front_path = None
    
    # 앞면 이미지 저장
    if front_image is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            front_image.seek(0)
            tmp_file.write(front_image.read())
            tmp_front_path = tmp_file.name
    
    # 함께 입을 옷 앞면 이미지 저장
    if together_front_image is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            together_front_image.seek(0)
            tmp_file.write(together_front_image.read())
            tmp_together_front_path = tmp_file.name
    
    return tmp_front_path, tmp_together_front_path


def cleanup_temp_files(*file_paths):
    """임시 파일들을 삭제합니다."""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)


def render_vto_results(result: Dict, image_count: int):
    """
    VTO 결과를 표시하고 측면 이미지 생성을 위한 이미지 선택 기능을 제공합니다.
    
    Args:
        result: VTO 결과 딕셔너리
        image_count: 생성한 이미지 개수
    """
    try:
        # 앞면/뒷면/측면 이미지 개별 추출
        front_images = result.get("response", [])
        debug_info = result.get("debug_info", {})
        
        total_count = len(front_images)
        
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
            
            # 선택된 이미지 인덱스 초기화
            selected_key = "vm_selected_image_idx"
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
                            if st.button(button_label, key=f"vm_select_front_{idx}", width='stretch', type=button_type):
                                st.session_state[selected_key] = global_idx
                                st.rerun()
                        else:
                            st.warning(f"⚠️ 정면 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
            
            # 선택된 이미지 정보 표시
            if all_images and selected_idx < len(all_images):
                st.success(f"✅ 측면 생성용으로 선택된 이미지: {all_images[selected_idx][0]} #{all_images[selected_idx][1]}")
            
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

def sidebar() -> Tuple[ModelOptions, ClothesOptions]:
    """
    사이드바 UI를 렌더링하고 선택된 옵션을 반환합니다.
    
    Returns:
        Tuple[ModelOptions, ClothesOptions]: 선택된 모델 옵션과 의상 옵션
    """
    st.markdown("### 🧑 모델 설정")
    
    # 성별
    gender_opts = ModelOptionsUtils.gender_options()
    gender_keys = list(gender_opts.keys())
    gender_names = [gender_opts[key]["name"] for key in gender_keys]
    
    selected_gender_name = st.selectbox(
        "성별",
        gender_names,
        index=0
    )
    gender = gender_keys[gender_names.index(selected_gender_name)]
    
    # 나이
    age_opts = ModelOptionsUtils.age_options()
    age_keys = list(age_opts.keys())
    age_names = [age_opts[key]["name"] for key in age_keys]
    
    selected_age_name = st.selectbox(
        "나이",
        age_names,
        index=0
    )
    age = age_keys[age_names.index(selected_age_name)]
    
    # 피부색
    skin_tone_opts = ModelOptionsUtils.skin_tone_options()
    skin_tone_keys = list(skin_tone_opts.keys())
    skin_tone_names = [skin_tone_opts[key]["name"] for key in skin_tone_keys]
    
    selected_skin_tone_name = st.selectbox(
        "피부색",
        skin_tone_names,
        index=0
    )
    skin_tone = skin_tone_keys[skin_tone_names.index(selected_skin_tone_name)]
    
    # 인종
    ethnicity_opts = ModelOptionsUtils.ethnicity_options()
    ethnicity_keys = list(ethnicity_opts.keys())
    ethnicity_names = [ethnicity_opts[key]["name"] for key in ethnicity_keys]
    
    selected_ethnicity_name = st.selectbox(
        "인종",
        ethnicity_names,
        index=0
    )
    ethnicity = ethnicity_keys[ethnicity_names.index(selected_ethnicity_name)]
    
    # 헤어스타일
    hairstyle_opts = ModelOptionsUtils.hairstyle_options(gender=gender)
    hairstyle_keys = list(hairstyle_opts.keys())
    hairstyle_names = [hairstyle_opts[key]["name"] for key in hairstyle_keys]
    
    selected_hairstyle_name = st.selectbox(
        "헤어스타일",
        hairstyle_names,
        index=0
    )
    hairstyle = hairstyle_keys[hairstyle_names.index(selected_hairstyle_name)]
    
    # 머리색
    hair_color_opts = ModelOptionsUtils.hair_color_options()
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
    catalog = ClothesOptionsUtils.clothes_category()
    
    
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
    fit_opts = ClothesOptionsUtils.fit_options()
    fit_keys = list(fit_opts.keys())
    fit_names = [fit_opts[key]["name"] for key in fit_keys]
    
    selected_fit_name = st.selectbox(
        "핏",
        fit_names,
        index=0
    )
    fit = fit_keys[fit_names.index(selected_fit_name)]
    
    # 소매
    sleeve_opts = ClothesOptionsUtils.sleeve_options()
    sleeve_keys = list(sleeve_opts.keys())
    sleeve_names = [sleeve_opts[key]["name"] for key in sleeve_keys]
    
    selected_sleeve_name = st.selectbox(
        "소매",
        sleeve_names,
        index=0
    )
    sleeve = sleeve_keys[sleeve_names.index(selected_sleeve_name)]
    
    # 기장
    length_opts = ClothesOptionsUtils.length_options()
    length_keys = list(length_opts.keys())
    length_names = [length_opts[key]["name"] for key in length_keys]
    
    selected_length_name = st.selectbox(
        "기장",
        length_names,
        index=0
    )
    length = length_keys[length_names.index(selected_length_name)]

    # Pydantic 모델로 반환
    model_options = ModelOptions(
        gender=gender,
        age=age,
        skin_tone=skin_tone,
        ethnicity=ethnicity,
        hairstyle=hairstyle,
        hair_color=hair_color,
    )
    
    clothes_options = ClothesOptions(
        main_category=main_category,
        sub_category=sub_category,
        fit=fit,
        sleeve=sleeve,
        length=length,
    )
    
    return model_options, clothes_options

def virtual_model_tab(model_options: ModelOptions, clothes_options: ClothesOptions):
    """
    가상 모델 피팅 탭을 렌더링합니다.
    
    Args:
        model_options: 모델 옵션
        clothes_options: 의상 옵션
    """
    MODEL_TEMPERATURE = 0.5
    MODEL_TOP_P = 0.97
    # 카테고리에 따른 업로드 수 결정
    num_uploads = 1 if clothes_options.main_category == "dress" else 2

    # 이미지 업로드 섹션 (헬퍼 함수 사용)
    main_image_file, sub_image_file  = render_image_uploaders(
        key_prefix="vm",
        num_uploads=num_uploads
    )
    
    # 실행 버튼 섹션
    st.subheader("🚀 실행")
    
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
        if main_image_file is None:
            st.error("❌ 피팅할 옷 이미지를 업로드해주세요.")
        else:
            with st.spinner("가상 모델 피팅을 실행 중입니다..."):
                try:
                    # 이미지를 임시 파일로 저장
                    tmp_main_path, tmp_sub_path = save_images_to_temp_files(
                        main_image_file, sub_image_file
                    )
                    paths = [tmp_main_path, tmp_sub_path] if tmp_sub_path else [tmp_main_path]
                    
                    result = asyncio.run(image_inference_with_prompt(
                        prompt=assemble_model_prompt(
                            type="front",
                            model_options=model_options,
                            clothes_options=clothes_options
                        ),
                        image_paths=paths,
                        temperature=MODEL_TEMPERATURE,
                        image_count=image_count,
                        top_p=MODEL_TOP_P
                    ))
                    st.session_state.vm_result = result
                    st.success("✅ 가상 모델 피팅 완료!")
                except Exception as e:
                    st.error(f"❌ 가상 모델 피팅 중 오류 발생: {str(e)}")
                finally:
                    # 임시 파일 삭제
                    cleanup_temp_files(tmp_main_path, tmp_sub_path)
    
    # VTO 결과 출력 (헬퍼 함수 사용)
    if st.session_state.vm_result:
        st.subheader("📊 가상 모델 피팅 결과")
        render_vto_results(st.session_state.vm_result, image_count)
        render_usage_info(st.session_state.vm_result["usage"])
    
    # 측면 이미지 생성 컴포넌트 추가 (원본 앞면 이미지 전달)
    side_view_component(model_options, main_image_file)