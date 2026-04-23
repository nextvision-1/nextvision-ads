"""
app.py - 넥스트비전 메타 광고 자동화 대시보드

실행:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title='넥스트비전 광고 자동화',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

# --- 사이드바 네비게이션 ---
st.sidebar.title('넥스트비전')
st.sidebar.caption('메타 광고 자동화 플랫폼')
st.sidebar.divider()

page = st.sidebar.radio(
    '메뉴',
    ['성과 대시보드', '광고 생성', '이미지 스튜디오', '자동 최적화', '설정'],
    index=0,
)

st.sidebar.divider()
st.sidebar.caption('v0.1.0 | NextVision')

# --- 페이지 라우팅 ---
if page == '성과 대시보드':
    from pages import dashboard
    dashboard.render()

elif page == '광고 생성':
    from pages import create_ads
    create_ads.render()

elif page == '이미지 스튜디오':
    from pages import image_studio
    image_studio.render()

elif page == '자동 최적화':
    from pages import optimizer
    optimizer.render()

elif page == '설정':
    from pages import settings
    settings.render()
