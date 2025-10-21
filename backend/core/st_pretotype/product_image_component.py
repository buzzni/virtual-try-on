import asyncio
from typing import Dict
import streamlit as st
from PIL import Image
import tempfile
import os
from io import BytesIO
from core.vto_service.service import single_image_inference
from prompts.prod_image_prompts import product_image_prompt

def product_image_sidebar():
    mode_opts = {
        "default": {
            "name": "기본",
            "desc": "기본 모드"
        },
        "mannequin": {
            "name": "마네킹 제거",
            "desc": "마네킹 제거 모드"
        },
        "person": {
            "name": "사람 제거",
            "desc": "옷을 입고있는 사람 제거 모드"
        }
    }
    mode_keys = list(mode_opts.keys())
    mode_names = [mode_opts[key]["name"] for key in mode_keys]
    
    selected_mode_name = st.selectbox(
        "모드",
        mode_names,
        index=0
    )
    mode = mode_keys[mode_names.index(selected_mode_name)]
    return {"mode": mode}

def product_image_tab(settings: Dict[str, str]):
    # 이미지 업로드 섹션
    st.subheader("📤 이미지 업로드")

    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "이미지 선택",
            type=["jpg", "jpeg", "png", "webp"],
            key="upload_1"
        )
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="업로드된 이미지", width='stretch')
    with col2:
        # 실행 버튼 섹션
        st.subheader("🚀 실행")
        
        # 세션 상태 초기화
        if "product_image_result" not in st.session_state:
            st.session_state.product_image_result = None
        
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
            "🚀 상품 이미지 생성 실행", 
            width='stretch',
        ):
            # 이미지 가져오기
            uploaded_image = uploaded_file
            
            if uploaded_image is None:
                st.error("❌ 이미지를 업로드해주세요.")
            else:
                with st.spinner("상품 이미지 생성을 실행 중입니다..."):
                    tmp_image_path = None
                    
                    try:
                        if uploaded_image is not None:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                                uploaded_image.seek(0)
                                tmp_file.write(uploaded_image.read())
                                tmp_image_path = tmp_file.name
                        
                        # 상품 이미지 생성 실행
                        result = asyncio.run(single_image_inference(
                            prompt=product_image_prompt(type=settings["mode"]),
                            image_path=tmp_image_path,
                            temperature=temperature,
                            image_count=image_count
                        ))
                        st.session_state.product_image_result = result
                        st.success("✅ 상품 이미지 생성 완료!")
                    except Exception as e:
                        st.error(f"❌ 상품 이미지 생성 중 오류 발생: {str(e)}")
                    finally:
                        # 임시 파일 삭제
                        if tmp_image_path and os.path.exists(tmp_image_path):
                            os.unlink(tmp_image_path)
                            
        st.divider()
        if st.session_state.product_image_result:
            st.markdown("**사용량 정보:**")
            usage = st.session_state.product_image_result["usage"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 토큰", usage.total_token_count)
            with col2:
                st.metric("비용 (USD)", f"${usage.cost_usd:.6f}")
            with col3:
                st.metric("비용 (KRW)", f"₩{usage.cost_krw:.2f}")
            
    st.divider()
    
    # 상품 이미지 생성 결과 출력
    if st.session_state.product_image_result:
        st.subheader("📊 상품 이미지 생성 결과")
        
        try:
            # 상품 이미지 개별 추출
            product_images = st.session_state.product_image_result.get("front_images", [])
            debug_info = st.session_state.product_image_result.get("debug_info", {})
            
            if len(product_images) == 0:
                st.error("❌ 생성된 이미지가 없습니다.")
                with st.expander("🔍 디버깅 정보"):
                    st.json(debug_info)
            else:
                st.markdown(f"**총 {len(product_images)}개의 이미지가 생성되었습니다.**")
                
                # 상품 이미지 표시
                if product_images:
                    st.markdown("### 🔵 상품 이미지")
                    num_cols = image_count
                    cols = st.columns(num_cols)
                    for idx, image_bytes in enumerate(product_images):
                        with cols[idx % num_cols]:
                            if isinstance(image_bytes, bytes):
                                image = Image.open(BytesIO(image_bytes))
                                st.image(image, caption=f"이미지 #{idx+1}", width='stretch')
                            else:
                                st.warning(f"⚠️ 상품 이미지 #{idx+1}의 형식이 올바르지 않습니다.")
                # 디버깅 정보 (옵션)
                with st.expander("🔍 생성 상세 정보"):
                    st.json(debug_info)
                
        except Exception as e:
            st.error(f"❌ 이미지 표시 중 오류 발생: {str(e)}")
            import traceback
            st.code(traceback.format_exc())