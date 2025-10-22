import streamlit as st

from core.st_pretotype.component import (
    sidebar,
    vto_tab,
    virtual_model_tab,
)
from core.st_pretotype.product_image_component import product_image_sidebar, product_image_tab
from core.st_pretotype.side_view_component import side_view_tab
from core.st_pretotype.analyze_component import analyze_page
from core.st_pretotype.dashboard_component import dashboard_page

# 페이지 설정
st.set_page_config(page_title="Virtual Try-On", layout="wide")

# 세션 상태 초기화
if "log_messages" not in st.session_state:
    st.session_state.log_messages = []

if "analys" not in st.session_state:
    st.session_state.analys = None


name_dict = {
    "vto_base" : { "name": "base 모델 모드", "icon": "👔" },
    "vto_model" : { "name": "생성형 모델 모드", "icon": "👔" },
    "product" : { "name": "상품 누끼 따기", "icon": "📸" },
    "analyze" : { "name": "상품 상세페이지 문구 생성", "icon": "🔍" },
    "dashboard" : { "name": "결과 대시보드", "icon": "📊" },
    "side_view" : { "name": "측면 이미지 생성 모드", "icon": "🧍‍♀️" },
}


# 페이지 정의
def vto_page():
    st.title(name_dict["vto_base"]["name"])
    with st.sidebar:
        settings = sidebar()
    vto_tab(settings)

def virtual_model_page():
    st.title(name_dict["vto_model"]["name"])
    with st.sidebar:
        settings = sidebar()
    virtual_model_tab(settings)

def product_page():
    st.title(name_dict["product"]["name"])
    with st.sidebar:
        st.header(f"⚙️ {name_dict['product']['name']} 설정")
        settings = product_image_sidebar()
    product_image_tab(settings)

def side_view_page():
    st.title(name_dict["side_view"]["name"])
    with st.sidebar:
        st.header(f"⚙️ {name_dict['side_view']['name']} 설정")
    side_view_tab()

def analyze_image_page():
    st.title(name_dict["analyze"]["name"])
    analyze_page()

def result_dashboard_page():
    st.title(name_dict["dashboard"]["name"])
    dashboard_page()

# 네비게이션 설정
page = st.navigation([
    st.Page(vto_page, title=name_dict["vto_base"]["name"], icon=name_dict["vto_base"]["icon"]),
    st.Page(virtual_model_page, title=name_dict["vto_model"]["name"], icon=name_dict["vto_model"]["icon"]),
    st.Page(product_page, title=name_dict["product"]["name"], icon=name_dict["product"]["icon"]),
    st.Page(analyze_image_page, title=name_dict["analyze"]["name"], icon=name_dict["analyze"]["icon"]),
    st.Page(result_dashboard_page, title=name_dict["dashboard"]["name"], icon=name_dict["dashboard"]["icon"]),
    #st.Page(side_view_page, title=name_dict["side_view"]["name"], icon=name_dict["side_view"]["icon"]),
])

page.run()

# PYTHONPATH=. uv run streamlit run scripts/vto_pretotype.py
