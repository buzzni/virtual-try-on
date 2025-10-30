import asyncio
from typing import Dict
import streamlit as st
from PIL import Image
import tempfile
import os
from io import BytesIO
from core.vto_service.service import image_inference_with_prompt
from prompts.prod_image_prompts import product_image_prompt


def product_image_sidebar():
    mode_opts = {
        "default": {"name": "기본", "desc": "기본 모드"},
        "mannequin": {"name": "마네킹 제거", "desc": "마네킹 제거 모드"},
        "person": {"name": "사람 제거", "desc": "옷을 입고있는 사람 제거 모드"},
    }
    mode_keys = list(mode_opts.keys())
    mode_names = [mode_opts[key]["name"] for key in mode_keys]

    selected_mode_name = st.selectbox("모드", mode_names, index=0)
    mode = mode_keys[mode_names.index(selected_mode_name)]
    return {"mode": mode}


def product_image_tab(settings: Dict[str, str]):
    # 이미지 업로드 섹션
    st.subheader("📤 이미지 업로드 (최대 2개)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**이미지 1**")
        uploaded_file_1 = st.file_uploader(
            "첫 번째 이미지 선택",
            type=["jpg", "jpeg", "png", "webp"],
            key="product_upload_1",
        )
        if uploaded_file_1:
            image = Image.open(uploaded_file_1)
            st.image(image, caption="이미지 1", use_container_width=True)

    with col2:
        st.markdown("**이미지 2 (선택사항)**")
        uploaded_file_2 = st.file_uploader(
            "두 번째 이미지 선택",
            type=["jpg", "jpeg", "png", "webp"],
            key="product_upload_2",
        )
        if uploaded_file_2:
            image = Image.open(uploaded_file_2)
            st.image(image, caption="이미지 2", use_container_width=True)

    st.divider()

    # 설정 섹션
    col_setting1, col_setting2 = st.columns(2)
    with col_setting1:
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
            help="결과의 다양성을 조절합니다. 높을수록 더 다양하고 창의적인 결과가 나옵니다.",
        )

        image_count = st.slider(
            "이미지당 생성 개수",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            help="각 이미지당 생성할 개수입니다.",
        )

    with col_setting2:
        st.subheader("")  # 높이 맞추기용
        st.write("")

    if st.button("🚀 상품 이미지 생성", use_container_width=True, type="primary"):
        # 업로드된 이미지 수집
        uploaded_images = []
        if uploaded_file_1:
            uploaded_images.append(uploaded_file_1)
        if uploaded_file_2:
            uploaded_images.append(uploaded_file_2)

        if len(uploaded_images) == 0:
            st.error("❌ 최소 1개의 이미지를 업로드해주세요.")
        else:
            with st.spinner(
                f"상품 이미지 생성 중입니다... ({len(uploaded_images)}개 이미지)"
            ):
                all_results = []
                tmp_paths = []

                try:
                    # 각 이미지에 대해 처리하는 비동기 함수
                    async def process_single_image(uploaded_image):
                        # 임시 파일로 저장
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".png"
                        ) as tmp_file:
                            uploaded_image.seek(0)
                            tmp_file.write(uploaded_image.read())
                            tmp_path = tmp_file.name
                            tmp_paths.append(tmp_path)

                        # 상품 이미지 생성 실행
                        result = await image_inference_with_prompt(
                            prompt=product_image_prompt(type=settings["mode"]),
                            image_paths=tmp_paths,
                            temperature=temperature,
                            image_count=image_count,
                        )
                        return result

                    # 모든 이미지를 병렬로 처리하는 비동기 함수
                    async def process_all_images():
                        return await asyncio.gather(
                            *[process_single_image(img) for img in uploaded_images]
                        )

                    # 비동기 함수 실행
                    all_results = asyncio.run(process_all_images())

                    # 모든 결과 합치기
                    combined_result = {
                        "response": [],
                        "usage": all_results[0]["usage"],  # 첫 번째 usage 사용
                        "debug_info": {},
                    }

                    # 모든 이미지 합치기
                    for result in all_results:
                        combined_result["response"].extend(
                            result.get("response", [])
                        )

                    # 사용량 합산
                    if len(all_results) > 1:
                        total_tokens = sum(
                            r["usage"].total_token_count for r in all_results
                        )
                        total_cost_usd = sum(r["usage"].cost_usd for r in all_results)
                        total_cost_krw = sum(r["usage"].cost_krw for r in all_results)

                        # 첫 번째 usage 객체를 복사하고 값 업데이트
                        combined_result["usage"].total_token_count = total_tokens
                        combined_result["usage"].cost_usd = total_cost_usd
                        combined_result["usage"].cost_krw = total_cost_krw

                    st.session_state.product_image_result = combined_result
                    st.success(
                        f"✅ 상품 이미지 생성 완료! ({len(uploaded_images)}개 이미지, 총 {len(combined_result['response'])}개 결과)"
                    )

                except Exception as e:
                    st.error(f"❌ 상품 이미지 생성 중 오류 발생: {str(e)}")
                    import traceback

                    st.code(traceback.format_exc())
                finally:
                    # 임시 파일 삭제
                    for tmp_path in tmp_paths:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

    st.divider()

    # 사용량 정보
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
            product_images = st.session_state.product_image_result.get(
                "response", []
            )
            debug_info = st.session_state.product_image_result.get("debug_info", {})

            if len(product_images) == 0:
                st.error("❌ 생성된 이미지가 없습니다.")
                with st.expander("🔍 디버깅 정보"):
                    st.json(debug_info)
            else:
                st.markdown(
                    f"**총 {len(product_images)}개의 이미지가 생성되었습니다.**"
                )

                # 상품 이미지 표시
                if product_images:
                    st.markdown("### 🔵 상품 이미지")
                    num_cols = image_count
                    cols = st.columns(num_cols)
                    for idx, image_bytes in enumerate(product_images):
                        with cols[idx % num_cols]:
                            if isinstance(image_bytes, bytes):
                                image = Image.open(BytesIO(image_bytes))
                                st.image(
                                    image, caption=f"이미지 #{idx + 1}", width="stretch"
                                )
                            else:
                                st.warning(
                                    f"⚠️ 상품 이미지 #{idx + 1}의 형식이 올바르지 않습니다."
                                )
                # 디버깅 정보 (옵션)
                with st.expander("🔍 생성 상세 정보"):
                    st.json(debug_info)

        except Exception as e:
            st.error(f"❌ 이미지 표시 중 오류 발생: {str(e)}")
            import traceback

            st.code(traceback.format_exc())
