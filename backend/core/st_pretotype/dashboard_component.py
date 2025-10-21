import streamlit as st
from PIL import Image
from io import BytesIO
import zipfile
import tempfile
import os
from datetime import datetime


def dashboard_page():
    """결과 대시보드 페이지"""
    st.markdown("## 📊 작업 결과 대시보드")
    st.markdown("완료된 작업들의 결과를 확인하고 선택하여 다운로드할 수 있습니다.")
    
    st.divider()
    
    # 디버깅: 세션 상태 확인
    with st.expander("🔍 디버깅: 세션 상태 확인", expanded=False):
        st.write("**현재 세션 상태 키:**")
        session_keys = list(st.session_state.keys())
        st.write(session_keys)
        
        relevant_keys = ["vto_result", "vto_side_result", "vm_result", "vm_side_result", 
                        "product_image_result", "vto_analys", "analyze_result"]
        st.write("\n**관련 키 존재 여부:**")
        for key in relevant_keys:
            exists = key in st.session_state
            value = st.session_state.get(key)
            has_data = value is not None
            st.write(f"- {key}: 존재={exists}, 데이터={has_data}")
    
    # 세션 상태 확인
    vto_result = st.session_state.get("vto_result")
    vto_side_result = st.session_state.get("vto_side_result")
    vm_result = st.session_state.get("vm_result")
    vm_side_result = st.session_state.get("vm_side_result")
    product_result = st.session_state.get("product_image_result")
    vto_analys = st.session_state.get("vto_analys")
    analyze_result = st.session_state.get("analyze_result")
    
    # 완료 상태 확인
    vto_complete = vto_result is not None and vto_side_result is not None
    vm_complete = vm_result is not None and vm_side_result is not None
    product_complete = product_result is not None
    analyze_complete = analyze_result is not None or vto_analys is not None
    
    # 선택 상태 초기화
    if "dashboard_selections" not in st.session_state:
        st.session_state.dashboard_selections = {
            "fitting": None,  # "vto" or "vm"
            "product": False,
            "analyze": False,
            "selected_images": {
                "front": [],
                "back": [],
                "side_left": [],
                "side_right": [],
                "product": []
            }
        }
    
    # 작업 상태 카드
    st.markdown("### 📋 작업 완료 상태")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 가상 피팅 관련
        st.markdown("#### 👔 가상 피팅")
        
        vto_status = "✅ 완료" if vto_complete else "❌ 미완료" if vto_result else "⚠️ 측면 이미지 필요"
        st.info(f"**가상 피팅 모드:** {vto_status}")
        if vto_complete:
            vto_count = len(vto_result.get("front_images", [])) + len(vto_result.get("back_images", []))
            vto_side_count = len(vto_side_result.get("left_images", [])) + len(vto_side_result.get("right_images", []))
            st.caption(f"정면/후면: {vto_count}개, 측면: {vto_side_count}개")
        
        vm_status = "✅ 완료" if vm_complete else "❌ 미완료" if vm_result else "⚠️ 측면 이미지 필요"
        st.info(f"**가상 모델 피팅 모드:** {vm_status}")
        if vm_complete:
            vm_count = len(vm_result.get("front_images", [])) + len(vm_result.get("back_images", []))
            vm_side_count = len(vm_side_result.get("left_images", [])) + len(vm_side_result.get("right_images", []))
            st.caption(f"정면/후면: {vm_count}개, 측면: {vm_side_count}개")
    
    with col2:
        # 기타 작업
        st.markdown("#### 📸 기타 작업")
        
        product_status = "✅ 완료" if product_complete else "❌ 미완료"
        st.info(f"**상품 이미지 생성:** {product_status}")
        if product_complete:
            product_count = len(product_result.get("front_images", []))
            st.caption(f"생성 이미지: {product_count}개")
        
        analyze_status = "✅ 완료" if analyze_complete else "❌ 미완료"
        st.info(f"**의류 이미지 분석:** {analyze_status}")
        if analyze_complete:
            st.caption("분석 데이터 사용 가능")
    
    st.divider()
    
    # 다운로드 선택 섹션
    st.markdown("### 📦 다운로드 선택")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 👔 가상 피팅 선택")
        
        # 라디오 버튼으로 둘 중 하나만 선택
        fitting_options = ["선택 안 함"]
        if vto_complete:
            fitting_options.append("가상 피팅 모드")
        if vm_complete:
            fitting_options.append("가상 모델 피팅 모드")
        
        selected_fitting = st.radio(
            "피팅 결과 선택 (둘 중 하나)",
            fitting_options,
            index=0,
            key="fitting_selection"
        )
        
        # 선택 상태 업데이트
        if selected_fitting == "가상 피팅 모드":
            st.session_state.dashboard_selections["fitting"] = "vto"
        elif selected_fitting == "가상 모델 피팅 모드":
            st.session_state.dashboard_selections["fitting"] = "vm"
        else:
            st.session_state.dashboard_selections["fitting"] = None
    
    with col2:
        st.markdown("#### 📸 상품 이미지")
        
        product_disabled = not product_complete
        product_selected = st.checkbox(
            "상품 이미지 생성 결과",
            disabled=product_disabled,
            key="product_selection"
        )
        st.session_state.dashboard_selections["product"] = product_selected
        
        if product_disabled:
            st.caption("⚠️ 먼저 상품 이미지를 생성해주세요.")
    
    with col3:
        st.markdown("#### 🔍 의류 분석")
        
        analyze_disabled = not analyze_complete
        analyze_selected = st.checkbox(
            "의류 이미지 분석 결과",
            disabled=analyze_disabled,
            key="analyze_selection"
        )
        st.session_state.dashboard_selections["analyze"] = analyze_selected
        
        if analyze_disabled:
            st.caption("⚠️ 의류 이미지 분석을 실행해주세요.")
        elif vto_analys and not analyze_result:
            st.caption("ℹ️ 가상피팅 분석 결과 사용")
    
    st.divider()
    
    # 선택 요약
    st.markdown("### 📋 선택 요약")
    
    selected_items = []
    if st.session_state.dashboard_selections["fitting"] == "vto":
        selected_items.append("✅ 가상 피팅 모드 결과")
    elif st.session_state.dashboard_selections["fitting"] == "vm":
        selected_items.append("✅ 가상 모델 피팅 모드 결과")
    
    if st.session_state.dashboard_selections["product"]:
        selected_items.append("✅ 상품 이미지 생성 결과")
    
    if st.session_state.dashboard_selections["analyze"]:
        selected_items.append("✅ 의류 이미지 분석 결과")
    
    if selected_items:
        for item in selected_items:
            st.markdown(item)
    else:
        st.warning("⚠️ 다운로드할 항목을 선택해주세요.")
    
    st.divider()
    
    # 다운로드 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        download_disabled = len(selected_items) == 0
        
        if st.button(
            "📥 선택한 항목 ZIP 다운로드",
            use_container_width=True,
            type="primary",
            disabled=download_disabled
        ):
            with st.spinner("ZIP 파일을 생성 중입니다..."):
                try:
                    # 선택된 이미지 인덱스 가져오기
                    vto_selected_idx = st.session_state.get("vto_selected_image_idx", 0)
                    vm_selected_idx = st.session_state.get("vm_selected_image_idx", 0)
                    
                    zip_bytes = create_download_zip(
                        st.session_state.dashboard_selections,
                        vto_result,
                        vto_side_result,
                        vm_result,
                        vm_side_result,
                        product_result,
                        vto_analys,
                        analyze_result,
                        vto_selected_idx,
                        vm_selected_idx
                    )
                    
                    # 다운로드 버튼 생성
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"vto_results_{timestamp}.zip"
                    
                    st.download_button(
                        label="⬇️ ZIP 파일 다운로드",
                        data=zip_bytes,
                        file_name=filename,
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    st.success("✅ ZIP 파일이 생성되었습니다!")
                    
                except Exception as e:
                    st.error(f"❌ ZIP 파일 생성 중 오류 발생: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())


def create_download_zip(selections, vto_result, vto_side_result, vm_result, vm_side_result, 
                        product_result, vto_analys, analyze_result, vto_selected_idx, vm_selected_idx):
    """선택된 항목들로 ZIP 파일 생성 (선택된 이미지만 포함)"""
    
    # 메모리에 ZIP 파일 생성
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # 가상 피팅 결과 - 선택된 이미지만
        if selections["fitting"] == "vto" and vto_result and vto_side_result:
            front_images = vto_result.get("front_images", [])
            back_images = vto_result.get("back_images", [])
            
            # 선택된 이미지가 정면인지 후면인지 판단
            if vto_selected_idx < len(front_images):
                # 정면 이미지 선택됨
                selected_img = front_images[vto_selected_idx]
                zip_file.writestr("front_001.png", selected_img)
            else:
                # 후면 이미지 선택됨
                back_idx = vto_selected_idx - len(front_images)
                if back_idx < len(back_images):
                    selected_img = back_images[back_idx]
                    zip_file.writestr("back_001.png", selected_img)
            
            # 측면 이미지는 모두 포함
            for idx, img_bytes in enumerate(vto_side_result.get("left_images", [])):
                zip_file.writestr(f"left_side_{idx+1:03d}.png", img_bytes)
            
            for idx, img_bytes in enumerate(vto_side_result.get("right_images", [])):
                zip_file.writestr(f"right_side_{idx+1:03d}.png", img_bytes)
        
        # 가상 모델 피팅 결과 - 선택된 이미지만
        elif selections["fitting"] == "vm" and vm_result and vm_side_result:
            front_images = vm_result.get("front_images", [])
            back_images = vm_result.get("back_images", [])
            
            # 선택된 이미지가 정면인지 후면인지 판단
            if vm_selected_idx < len(front_images):
                # 정면 이미지 선택됨
                selected_img = front_images[vm_selected_idx]
                zip_file.writestr("front_001.png", selected_img)
            else:
                # 후면 이미지 선택됨
                back_idx = vm_selected_idx - len(front_images)
                if back_idx < len(back_images):
                    selected_img = back_images[back_idx]
                    zip_file.writestr("back_001.png", selected_img)
            
            # 측면 이미지는 모두 포함
            for idx, img_bytes in enumerate(vm_side_result.get("left_images", [])):
                zip_file.writestr(f"left_side_{idx+1:03d}.png", img_bytes)
            
            for idx, img_bytes in enumerate(vm_side_result.get("right_images", [])):
                zip_file.writestr(f"right_side_{idx+1:03d}.png", img_bytes)
        
        # 상품 이미지 결과
        if selections["product"] and product_result:
            for idx, img_bytes in enumerate(product_result.get("front_images", [])):
                zip_file.writestr(f"product_{idx+1:03d}.png", img_bytes)
        
        # 의류 분석 결과
        if selections["analyze"]:
            # 분석 결과 JSON 저장
            if analyze_result:
                result_dict = analyze_result.model_dump()
            elif vto_analys:
                result_dict = vto_analys.model_dump()
            else:
                result_dict = {}
            
            import json
            json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
            zip_file.writestr("analyze_result.json", json_str)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()
