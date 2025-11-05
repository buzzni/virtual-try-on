import asyncio
import tempfile
import streamlit as st
from PIL import Image
from io import BytesIO
from typing import Optional
from core.litellm_hander.schema import ModelOptions
from core.vto_service.service import image_inference_with_prompt
from prompts.side_view_prompts import side_view_prompt


def cleanup_temp_files(*file_paths):
    """임시 파일들을 삭제합니다."""
    import os
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)


def side_view_component(model_options: ModelOptions, front_image_file=None):
    """
    측면 이미지 생성 컴포넌트 (간소화 버전)
    
    Args:
        model_options: 모델 옵션
        front_image_file: 원본 앞면 의상 이미지 파일 (Optional)
    """
    SIDE_VIEW_TEMPERATURE = 0.5
    st.divider()
    st.subheader("🔄 측면 이미지 생성")
    
    # selected_image_bytes 초기화
    selected_image_bytes = None
    
    # 세션 상태에서 결과 및 선택된 이미지 가져오기
    source_result = st.session_state.get("vm_result")
    
    if source_result:
        # 선택된 이미지 인덱스 가져오기
        selected_key = "vm_selected_image_idx"
        if selected_key in st.session_state:
            selected_idx = st.session_state[selected_key]
            
            # 모든 이미지 수집 (결과 키가 "response"로 변경됨)
            all_images = []
            front_images = source_result.get("response", [])
            
            for idx, img_bytes in enumerate(front_images):
                all_images.append(("정면", idx + 1, img_bytes))
            
            if all_images and selected_idx < len(all_images):
                selected_image_bytes = all_images[selected_idx][2]
                # 미리보기 표시
                st.info(f"선택된 이미지: {all_images[selected_idx][0]} #{all_images[selected_idx][1]}")
                preview_image = Image.open(BytesIO(selected_image_bytes))
                st.image(preview_image, caption="측면 생성에 사용될 이미지", width=300)
    else:
        st.warning("⚠️ 먼저 위에서 가상 모델 피팅을 실행해주세요.")
    
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
            width='stretch',
            key="vm_side_btn"
        ):
            if selected_image_bytes is None:
                st.error("❌ 이미지를 선택하거나 업로드해주세요.")
            else:
                with st.spinner("측면 이미지를 생성 중입니다... (좌측 & 우측)"):
                    tmp_paths = []
                    
                    try:
                        # 선택된 이미지를 임시 파일로 저장
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                            tmp_file.write(selected_image_bytes)
                            tmp_paths.append(tmp_file.name)
                        
                        # 원본 이미지 사용
                        if front_image_file is not None:
                            front_image_file.seek(0)
                            original_bytes = front_image_file.read()
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                                tmp_file.write(original_bytes)
                                tmp_paths.append(tmp_file.name)
                        
                        # 좌측/우측 측면 이미지를 동시에 생성
                        async def generate_side_views():
                            left_task = image_inference_with_prompt(
                                prompt=side_view_prompt("left", model_options.gender),
                                image_paths=tmp_paths,
                                temperature=SIDE_VIEW_TEMPERATURE,
                                image_count=image_count
                            )
                            right_task = image_inference_with_prompt(
                                prompt=side_view_prompt("right", model_options.gender),
                                image_paths=tmp_paths,
                                temperature=SIDE_VIEW_TEMPERATURE,
                                image_count=image_count
                            )
                            left_result, right_result = await asyncio.gather(left_task, right_task)
                            return left_result, right_result
                        
                        left_result, right_result = asyncio.run(generate_side_views())
                        
                        # 결과 합치기
                        combined_result = {
                            "left_images": left_result.get("response", []),
                            "right_images": right_result.get("response", []),
                            "left_usage": left_result.get("usage"),
                            "right_usage": right_result.get("usage"),
                            "debug_info": {
                                "left": left_result.get("debug_info", {}),
                                "right": right_result.get("debug_info", {}),
                                "image_count": len(tmp_paths)
                            }
                        }
                        
                        st.session_state[result_key] = combined_result
                        st.success("✅ 측면 이미지 생성 완료! (좌측 + 우측)")
                    except Exception as e:
                        st.error(f"❌ 측면 이미지 생성 중 오류 발생: {str(e)}")
                    finally:
                        # 모든 임시 파일 삭제
                        cleanup_temp_files(*tmp_paths)
    
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
                                st.image(image, caption=f"좌측 #{idx+1}", width='stretch')
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
                                st.image(image, caption=f"우측 #{idx+1}", width='stretch')
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

