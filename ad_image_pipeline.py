"""
ad_image_pipeline.py - end-to-end 광고 이미지 자동화 파이프라인

상품 정보 하나만 넣으면:
  상품 정보 → AI 이미지 생성 → 텍스트 오버레이 → 메타 광고 업로드

SaaS 핵심 엔드포인트. 스케줄러/대시보드에서 이 함수를 호출합니다.

사용 예:
    from ad_image_pipeline import create_full_ad

    ad = create_full_ad(
        product_name='스마트 체온계',
        industry='건강기능식품',
        target_audience='30-40대 주부',
        headline='매일 아침 건강 체크',
        subtext='정확한 측정, 30초 완료',
        cta_text='자세히 보기',
        link_url='https://nextvision.io.kr/thermo',
        adset_id='120245636876020166',
        ad_name='봄프로모션_체온계_01',
        cta_type='LEARN_MORE',
        ad_format='feed_square',
        logo_path='./brand/logo.png',   # 선택
        quality='medium',
    )
    print('광고 ID:', ad.get_id())

파이프라인이 만들어내는 결과물:
  1) ad_images/ai_<ts>.png          - AI 원본 배경
  2) ad_images/ai_<ts>_final.png    - 텍스트 오버레이 된 최종 이미지
  3) 메타 광고 계정에 업로드된 크리에이티브 + 광고 (PAUSED 상태)
"""

from pathlib import Path
from typing import Optional

from config import DEFAULT_LANDING_URL, is_openai_configured
from image_generator import build_prompt, generate_ad_background
from image_composer import compose_ad
from create_ad import create_image_ad


def create_full_ad(
    # --- 상품 정보 (프롬프트용) ---
    product_name: str,
    industry: str,
    # --- 광고 카피 ---
    headline: str,
    ad_name: str,
    subtext: Optional[str] = None,
    cta_text: str = '자세히 보기',
    # --- 메타 광고 설정 ---
    adset_id: str = None,
    link_url: Optional[str] = None,
    cta_type: str = 'LEARN_MORE',
    status: str = 'PAUSED',
    # --- AI 이미지 옵션 ---
    target_audience: Optional[str] = None,
    style: str = '밝고 깨끗한 모던 스타일',
    mood: Optional[str] = None,
    extra_hints: Optional[str] = None,
    quality: str = 'medium',
    # --- 이미지 규격 ---
    ad_format: str = 'feed_square',
    # --- 브랜딩 ---
    logo_path: Optional[str] = None,
    # --- 제공된 이미지로 스킵 (AI 건너뛰기) ---
    skip_ai_use_image: Optional[str] = None,
):
    """
    상품 정보부터 메타 광고 등록까지 한 번에 처리.

    Args:
        product_name: 상품/서비스명
        industry: 업종
        headline: 광고 메인 카피
        ad_name: 광고 관리 이름 (메타에 저장)
        subtext: 서브 카피 (선택)
        cta_text: CTA 버튼 텍스트 (기본 '자세히 보기')
        adset_id: 기존 광고세트 ID (필수)
        link_url: 랜딩 URL (기본: DEFAULT_LANDING_URL)
        cta_type: 메타 CTA 타입 (LEARN_MORE, SHOP_NOW, SIGN_UP 등)
        status: 'PAUSED' | 'ACTIVE' (기본 PAUSED - 안전)
        target_audience: 타겟 (프롬프트용)
        style: 비주얼 스타일 (프롬프트용)
        mood: 분위기 (프롬프트용)
        extra_hints: 추가 지시 (프롬프트용)
        quality: AI 이미지 품질 ('low' | 'medium' | 'high' | 'auto')
        ad_format: 'feed_square' | 'feed_portrait' | 'feed_landscape' | 'story_reel'
        logo_path: 로고 파일 경로 (선택)
        skip_ai_use_image: AI 건너뛰고 이 이미지 파일을 배경으로 사용

    Returns:
        facebook_business.adobjects.ad.Ad 객체
    """
    if adset_id is None:
        raise ValueError('adset_id 는 필수입니다. 먼저 create_adset.py 로 광고세트를 만드세요.')

    link_url = link_url or DEFAULT_LANDING_URL

    # ========================================================
    # STEP 1: 배경 이미지 확보
    # ========================================================
    if skip_ai_use_image:
        print('\n[STEP 1] 제공된 이미지 사용 (AI 건너뛰기)')
        if not Path(skip_ai_use_image).exists():
            raise FileNotFoundError(f'이미지 파일을 찾을 수 없어요: {skip_ai_use_image}')
        bg_path = skip_ai_use_image
    else:
        print('\n[STEP 1] AI 배경 이미지 생성')
        if not is_openai_configured():
            raise RuntimeError(
                'OpenAI API 키가 .env 에 설정되지 않았어요.\n'
                '키가 없다면 skip_ai_use_image 로 이미지 파일 경로를 직접 제공할 수 있습니다.'
            )

        # AI 프롬프트 조립
        prompt = build_prompt(
            product_name=product_name,
            industry=industry,
            style=style,
            target_audience=target_audience,
            mood=mood,
            extra_hints=extra_hints,
        )

        # ad_format에 맞는 AI 생성 size 결정
        ai_size_map = {
            'feed_square':    '1024x1024',
            'feed_portrait':  '1024x1536',
            'feed_landscape': '1536x1024',
            'story_reel':     '1024x1536',
        }
        ai_size = ai_size_map.get(ad_format, '1024x1024')

        bg_path = generate_ad_background(prompt, size=ai_size, quality=quality)

    # ========================================================
    # STEP 2: 텍스트/CTA/로고 오버레이
    # ========================================================
    print('\n[STEP 2] 텍스트 오버레이')
    final_image_path = compose_ad(
        background_path=bg_path,
        headline=headline,
        subtext=subtext,
        cta_text=cta_text,
        logo_path=logo_path,
        ad_format=ad_format,
    )

    # ========================================================
    # STEP 3: 메타에 광고 업로드
    # ========================================================
    print('\n[STEP 3] 메타 광고 업로드')
    ad = create_image_ad(
        adset_id=adset_id,
        image_path=final_image_path,
        headline=headline,
        message=subtext or headline,  # 메타 광고 본문 (이미지 위 텍스트)
        ad_name=ad_name,
        link_url=link_url,
        cta_type=cta_type,
        status=status,
    )

    print(f'\n[완료] 전체 파이프라인 종료 - 광고 ID: {ad.get_id()}')
    return ad


# ============================================================
# CLI 실행 예시
# ============================================================
if __name__ == '__main__':
    print('=== ad_image_pipeline.py 데모 ===\n')

    # 데모 실행 전 확인
    print('이 데모는 실제로 메타 광고를 생성합니다 (PAUSED 상태).')
    print('광고세트 ID 를 아래 DEMO_ADSET_ID 에 설정한 뒤 실행하세요.\n')

    DEMO_ADSET_ID = '120245636876020166'  # 실제 광고세트 ID로 변경

    try:
        ad = create_full_ad(
            product_name='스마트 체온계',
            industry='건강기능식품',
            headline='매일 아침 건강 체크',
            subtext='정확한 측정, 30초 완료',
            cta_text='자세히 보기',
            ad_name='데모_체온계_01',
            adset_id=DEMO_ADSET_ID,
            target_audience='30-40대 주부',
            style='밝고 깨끗한 미니멀',
            mood='신뢰감 있는',
            quality='medium',
            ad_format='feed_square',
            cta_type='LEARN_MORE',
        )
        print(f'\n광고 생성 완료: {ad.get_id()}')
    except Exception as e:
        print(f'\n[실패] {type(e).__name__}: {e}')
