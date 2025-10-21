import streamlit as st

from core.st_pretotype.component import (
    sidebar,
    vto_tab,
    virtual_model_tab,
)
from core.st_pretotype.product_image_component import product_image_sidebar, product_image_tab

# 페이지 설정
st.set_page_config(page_title="Virtual Try-On", layout="wide")

# 세션 상태 초기화
if "log_messages" not in st.session_state:
    st.session_state.log_messages = []

if "analys" not in st.session_state:
    st.session_state.analys = None

# 페이지 정의
def vto_page():
    st.title("🎨 가상 피팅 모드")
    with st.sidebar:
        settings = sidebar()
    vto_tab(settings)

def virtual_model_page():
    st.title("🎨 가상 모델 피팅 모드")
    with st.sidebar:
        settings = sidebar()
    virtual_model_tab(settings)

def product_page():
    st.title("🖼️ 상품 이미지 생성 모드")
    with st.sidebar:
        st.header("⚙️ 상품 이미지 설정")
        settings = product_image_sidebar()
    product_image_tab(settings)

# 네비게이션 설정
page = st.navigation([
    st.Page(vto_page, title="가상 피팅 모드", icon="👔"),
    st.Page(virtual_model_page, title="가상 모델 피팅 모드", icon="👔"),
    st.Page(product_page, title="상품 이미지 생성", icon="📸")
])

page.run()

# PYTHONPATH=. uv run streamlit run scripts/vto_pretotype.py
