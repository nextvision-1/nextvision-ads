"""설정 페이지."""

import streamlit as st
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def render():
    st.title('설정')

    # API 상태 확인
    st.subheader('API 연결 상태')

    if st.button('연결 테스트', type='primary'):
        with st.spinner('Meta API 테스트 중...'):
            try:
                from config import account, AD_ACCOUNT_ID, PAGE_ID, SYSTEM_USER_ID, APP_ID, is_openai_configured
                info = account.api_get(fields=['name', 'account_status', 'currency', 'timezone_name'])

                st.success('Meta API 연결 성공\!')
                col1, col2 = st.columns(2)
                with col1:
                    st.write('광고 계정:', info.get('name'))
                    st.write('계정 상태:', info.get('account_status'))
                    st.write('통화:', info.get('currency'))
                with col2:
                    st.write('시간대:', info.get('timezone_name'))
                    st.write('광고 계정 ID:', AD_ACCOUNT_ID)
                    st.write('페이지 ID:', PAGE_ID)

            except Exception as e:
                error_msg = str(e)
                if 'API access blocked' in error_msg:
                    st.error('Meta API 접근이 차단되어 있어요.')
                    st.markdown(
                        '**해결 방법**: [developers.facebook.com](https://developers.facebook.com) 에서 '
                        '계정 확인을 완료해주세요.'
                    )
                else:
                    st.error(f'Meta API 연결 실패: {error_msg}')

        # OpenAI 상태
        try:
            from config import is_openai_configured
            if is_openai_configured():
                st.success('OpenAI API 키 설정됨')
            else:
                st.warning('OpenAI API 키가 설정되지 않았어요. .env 파일에 OPENAI_API_KEY 를 추가해주세요.')
        except Exception:
            pass

    # 현재 설정 표시
    st.divider()
    st.subheader('현재 설정 (.env)')

    try:
        from config import AD_ACCOUNT_ID, PAGE_ID, SYSTEM_USER_ID, APP_ID, ACCESS_TOKEN, DEFAULT_LANDING_URL, AD_IMAGE_DIR, FONTS_DIR, is_openai_configured

        settings = {
            'META_AD_ACCOUNT_ID': AD_ACCOUNT_ID,
            'META_PAGE_ID': PAGE_ID,
            'META_SYSTEM_USER_ID': SYSTEM_USER_ID or '(미설정)',
            'META_APP_ID': APP_ID or '(미설정)',
            'META_ACCESS_TOKEN': ACCESS_TOKEN[:20] + '...' + ACCESS_TOKEN[-6:] if ACCESS_TOKEN else '(미설정)',
            'DEFAULT_LANDING_URL': DEFAULT_LANDING_URL,
            'AD_IMAGE_DIR': str(AD_IMAGE_DIR),
            'FONTS_DIR': str(FONTS_DIR),
            'OpenAI 설정 여부': 'O' if is_openai_configured() else 'X',
        }

        for key, value in settings.items():
            st.text(f'{key}: {value}')

    except Exception as e:
        st.error(f'설정 로딩 실패: {e}')

    # 폰트 상태
    st.divider()
    st.subheader('폰트 상태')
    try:
        from config import FONTS_DIR
        font_files = list(FONTS_DIR.glob('*.otf')) + list(FONTS_DIR.glob('*.ttf'))
        if font_files:
            for f in font_files:
                st.text(f'  {f.name} ({f.stat().st_size / 1024:.0f} KB)')
        else:
            st.warning('fonts/ 폴더에 폰트 파일이 없어요. Pretendard 폰트를 설치해주세요.')
    except Exception:
        st.warning('폰트 폴더를 확인할 수 없어요.')
