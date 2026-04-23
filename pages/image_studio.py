"""이미지 스튜디오 페이지 - AI 광고 이미지 생성."""

import streamlit as st
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def render():
    st.title('이미지 스튜디오')
    st.caption('AI로 광고 이미지를 자동 생성하고 텍스트를 오버레이합니다.')

    # OpenAI 키 확인
    from config import is_openai_configured
    if not is_openai_configured():
        st.warning('OpenAI API 키가 설정되지 않았어요. .env 파일에 OPENAI_API_KEY 를 추가해주세요.')

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader('상품 정보')
        product_name = st.text_input('상품명', placeholder='예: 스마트 체온계')
        industry = st.text_input('업종/카테고리', placeholder='예: 건강기능식품')
        target_audience = st.text_input('타겟 고객', placeholder='예: 30-40대 주부')
        style = st.text_input('스타일', value='밝고 깨끗한 모던 스타일')
        mood = st.text_input('분위기', placeholder='예: 신뢰감 있는, 따뜻한')

        st.subheader('텍스트 오버레이')
        headline = st.text_input('헤드라인', placeholder='예: 매일 아침 건강 체크')
        subtext = st.text_input('서브 텍스트', placeholder='예: 정확한 측정, 30초 완료')
        cta_text = st.text_input('CTA 버튼', value='자세히 보기')

        st.subheader('이미지 설정')
        col_q, col_f = st.columns(2)
        with col_q:
            quality = st.selectbox(
                '품질',
                ['low', 'medium', 'high'],
                index=1,
                format_func=lambda x: {
                    'low': '낮음 (~$0.02)',
                    'medium': '보통 (~$0.07)',
                    'high': '높음 (~$0.19)',
                }.get(x, x),
            )
        with col_f:
            ad_format = st.selectbox(
                '규격',
                ['feed_square', 'feed_portrait', 'feed_landscape', 'story_reel'],
                format_func=lambda x: {
                    'feed_square': '피드 정사각 (1080x1080)',
                    'feed_portrait': '피드 세로 (1080x1350)',
                    'feed_landscape': '피드 가로 (1200x628)',
                    'story_reel': '스토리/릴스 (1080x1920)',
                }.get(x, x),
            )

        # 기존 이미지 사용 옵션
        use_existing = st.checkbox('이미 가지고 있는 이미지 사용 (AI 생성 건너뛰기)')
        uploaded_bg = None
        if use_existing:
            uploaded_bg = st.file_uploader('배경 이미지 업로드', type=['jpg', 'jpeg', 'png'])

        generate_btn = st.button('이미지 생성', type='primary', use_container_width=True)

    with col_right:
        st.subheader('미리보기')

        if generate_btn:
            if not product_name or not headline:
                st.warning('상품명과 헤드라인을 입력해주세요.')
                return

            if use_existing and not uploaded_bg:
                st.warning('배경 이미지를 업로드해주세요.')
                return

            try:
                import tempfile
                from image_composer import compose_ad

                if use_existing and uploaded_bg:
                    # 업로드된 이미지 사용
                    suffix = '.' + uploaded_bg.name.split('.')[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_bg.getvalue())
                        bg_path = tmp.name
                    st.info('업로드된 이미지에 텍스트 오버레이 중...')
                else:
                    # AI 이미지 생성
                    if not is_openai_configured():
                        st.error('OpenAI API 키가 필요합니다.')
                        return

                    with st.spinner('AI 이미지 생성 중... (10~30초 소요)'):
                        from image_generator import build_prompt, generate_ad_background, META_AD_SIZES
                        prompt = build_prompt(
                            product_name=product_name,
                            industry=industry,
                            target_audience=target_audience or None,
                            style=style,
                            mood=mood or None,
                        )
                        st.caption('생성 프롬프트: ' + prompt[:100] + '...')

                        size = META_AD_SIZES.get(ad_format, '1024x1024')
                        bg_path = generate_ad_background(
                            prompt=prompt,
                            size=size,
                            quality=quality,
                        )

                # 텍스트 오버레이
                with st.spinner('텍스트 오버레이 적용 중...'):
                    final_path = compose_ad(
                        background_path=bg_path,
                        headline=headline,
                        subtext=subtext or None,
                        cta_text=cta_text or None,
                        ad_format=ad_format,
                    )

                # 결과 표시
                st.image(final_path, caption='생성된 광고 이미지', use_container_width=True)
                st.success('이미지 생성 완료\!')
                st.caption('저장 경로: ' + final_path)

                # 다운로드 버튼
                with open(final_path, 'rb') as f:
                    st.download_button(
                        '이미지 다운로드',
                        data=f.read(),
                        file_name=Path(final_path).name,
                        mime='image/png',
                    )

                # 세션에 저장 (광고 생성 탭에서 사용 가능)
                st.session_state['last_generated_image'] = final_path

            except Exception as e:
                error_msg = str(e)
                if 'API access blocked' in error_msg:
                    st.error('Meta API 접근이 차단되어 있어요. developers.facebook.com 에서 계정 확인을 완료해주세요.')
                elif 'openai' in error_msg.lower() or 'api key' in error_msg.lower():
                    st.error('OpenAI API 오류: ' + error_msg)
                else:
                    st.error('이미지 생성 실패: ' + error_msg)
        else:
            st.info('왼쪽에서 상품 정보와 텍스트를 입력하고 [이미지 생성] 버튼을 눌러주세요.')
