"""
config.py - 메타 광고 자동화 공통 설정 모듈

모든 스크립트에서 이 파일을 임포트해서 사용하세요.
.env 파일에서 민감정보를 읽어오고 FacebookAdsApi를 한 번만 초기화합니다.

사용 예:
    from config import account, PAGE_ID
    campaigns = account.get_campaigns()

필수 패키지:
    pip install -r requirements.txt
"""

import os
import sys
from pathlib import Path

# --- .env 또는 Streamlit Cloud Secrets 로드 ---
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'

# Streamlit Cloud 환경 감지
_is_streamlit_cloud = False
try:
    import streamlit as st
    if hasattr(st, 'secrets') and len(st.secrets) > 0:
        _is_streamlit_cloud = True
except Exception:
    pass

if not _is_streamlit_cloud:
    # 로컬 환경: .env 파일에서 읽기
    try:
        from dotenv import load_dotenv
    except ImportError:
        print('[오류] python-dotenv 가 설치되어 있지 않아요.')
        print('       설치: pip install python-dotenv')
        sys.exit(1)

    if not ENV_PATH.exists():
        print(f'[오류] .env 파일을 찾을 수 없어요: {ENV_PATH}')
        print('       .env.example 을 복사해서 .env 로 만들고 실제 값을 채워주세요.')
        sys.exit(1)

    load_dotenv(dotenv_path=ENV_PATH)


def _get_config(key: str, default: str = '') -> str:
    """Streamlit Cloud secrets 또는 환경변수에서 값을 읽어옵니다."""
    if _is_streamlit_cloud:
        return st.secrets.get(key, default)
    return os.getenv(key, default)


# --- 메타 설정 ---
ACCESS_TOKEN = _get_config('META_ACCESS_TOKEN')
AD_ACCOUNT_ID = _get_config('META_AD_ACCOUNT_ID')
PAGE_ID = _get_config('META_PAGE_ID')
SYSTEM_USER_ID = _get_config('META_SYSTEM_USER_ID')
APP_ID = _get_config('META_APP_ID')
DEFAULT_LANDING_URL = _get_config('DEFAULT_LANDING_URL', 'https://nextvision.io.kr')

# --- OpenAI 설정 (이미지 생성용) ---
OPENAI_API_KEY = _get_config('OPENAI_API_KEY').strip()

# --- 파일 경로 설정 ---
AD_IMAGE_DIR = Path(os.getenv('AD_IMAGE_DIR', './ad_images'))
if not AD_IMAGE_DIR.is_absolute():
    AD_IMAGE_DIR = BASE_DIR / AD_IMAGE_DIR
AD_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

FONTS_DIR = BASE_DIR / 'fonts'

# --- 필수값 검증 (메타 API는 필수) ---
_REQUIRED = {
    'META_ACCESS_TOKEN': ACCESS_TOKEN,
    'META_AD_ACCOUNT_ID': AD_ACCOUNT_ID,
    'META_PAGE_ID': PAGE_ID,
}
_missing = [k for k, v in _REQUIRED.items() if not v]
if _missing:
    print(f'[오류] .env 에 다음 값이 비어있어요: {", ".join(_missing)}')
    sys.exit(1)

# --- Meta API 초기화 ---
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

_initialized = False


def init_api():
    """FacebookAdsApi 를 초기화. 여러 번 호출해도 한 번만 실제 초기화됩니다."""
    global _initialized
    if not _initialized:
        FacebookAdsApi.init(access_token=ACCESS_TOKEN)
        _initialized = True
    return True


init_api()
account = AdAccount(AD_ACCOUNT_ID)


def is_openai_configured() -> bool:
    """OpenAI API 키가 설정되어 있는지 확인."""
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'))


# --- 디버그용 ---
if __name__ == '__main__':
    print('=== config.py 설정 확인 ===')
    print(f'AD_ACCOUNT_ID: {AD_ACCOUNT_ID}')
    print(f'PAGE_ID: {PAGE_ID}')
    print(f'SYSTEM_USER_ID: {SYSTEM_USER_ID}')
    print(f'APP_ID: {APP_ID}')
    print(f'META TOKEN: {ACCESS_TOKEN[:20]}...{ACCESS_TOKEN[-6:]}')
    print(f'DEFAULT_LANDING_URL: {DEFAULT_LANDING_URL}')
    print(f'AD_IMAGE_DIR: {AD_IMAGE_DIR}')
    print(f'FONTS_DIR: {FONTS_DIR}')
    print(f'OpenAI 설정됨: {is_openai_configured()}')
    print()
    print('Meta API 연결 테스트 중...')
    try:
        info = account.api_get(fields=['name', 'account_status'])
        print(f'[성공] 광고 계정 이름: {info["name"]}')
    except Exception as e:
        print(f'[실패] {e}')
