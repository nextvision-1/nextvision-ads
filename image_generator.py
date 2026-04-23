"""
image_generator.py - AI 기반 광고 이미지 생성 모듈

현재 지원: OpenAI gpt-image-1 (DALL-E 3 후속)
확장: ImageProvider 추상화로 다른 모델 쉽게 추가 가능

주의:
  - AI는 한글 텍스트를 제대로 못 그립니다. 텍스트 없는 배경 이미지만 생성하고
    image_composer.py 로 한글 텍스트를 별도 오버레이하세요.
  - 프롬프트에 "no text", "텍스트 없음" 을 명시해서 AI가 글자를 넣지 않도록 유도합니다.

사용 예:
    from image_generator import generate_ad_background, build_prompt

    prompt = build_prompt(
        product_name='스마트 체온계',
        industry='건강기능식품',
        style='밝고 깨끗한 미니멀',
        target_audience='30-40대 주부',
    )
    image_path = generate_ad_background(prompt, size='1024x1024', quality='medium')
    print('생성된 이미지:', image_path)
"""

import base64
import time
from pathlib import Path
from typing import Optional

from config import OPENAI_API_KEY, AD_IMAGE_DIR, is_openai_configured


# ============================================================
# 메타 광고 규격별 size 매핑 (gpt-image-1 지원 size 기준)
# ============================================================
META_AD_SIZES = {
    'feed_square':   '1024x1024',   # 1:1 피드 광고 (기본)
    'feed_portrait': '1024x1536',   # 2:3 세로 피드 광고
    'feed_landscape':'1536x1024',   # 3:2 가로 (링크 광고에 근접)
    'story_reel':    '1024x1536',   # 9:16 스토리/릴스 (크롭 필요)
}

QUALITY_COSTS = {
    'low':    0.02,  # 참고용 원가 (USD/이미지)
    'medium': 0.07,
    'high':   0.19,
    'auto':   None,
}


# ============================================================
# Provider 추상화 (나중에 Stability, Imagen 추가 용이)
# ============================================================
class ImageProvider:
    """이미지 생성 provider 추상 베이스 클래스."""
    name: str = 'base'

    def generate(self, prompt: str, size: str, quality: str, output_path: str) -> str:
        raise NotImplementedError


class OpenAIProvider(ImageProvider):
    """OpenAI gpt-image-1 (DALL-E 3의 차세대 모델)."""
    name = 'openai-gpt-image-1'

    def __init__(self, api_key: Optional[str] = None):
        if not api_key and not is_openai_configured():
            raise RuntimeError(
                'OpenAI API 키가 설정되지 않았어요.\n'
                '.env 파일에 OPENAI_API_KEY=sk-... 를 추가하세요.\n'
                '키 발급: https://platform.openai.com/api-keys'
            )
        self.api_key = api_key or OPENAI_API_KEY

    def generate(
        self,
        prompt: str,
        size: str = '1024x1024',
        quality: str = 'medium',
        output_path: Optional[str] = None,
    ) -> str:
        """OpenAI gpt-image-1 로 이미지 생성 후 파일 경로 반환."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                'openai 패키지가 설치되지 않았어요.\n'
                '설치: pip install openai'
            )

        client = OpenAI(api_key=self.api_key)

        print(f'[AI] 이미지 생성 중... (size={size}, quality={quality})')
        print(f'[AI] 프롬프트: {prompt[:80]}{"..." if len(prompt) > 80 else ""}')

        response = client.images.generate(
            model='gpt-image-1',
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        image_b64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)

        if output_path is None:
            ts = int(time.time())
            output_path = str(AD_IMAGE_DIR / f'ai_{ts}.png')

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(image_bytes)

        print(f'[완료] 저장: {output_path}')
        return output_path


# ============================================================
# 기본 provider (OpenAI)
# ============================================================
_default_provider: Optional[ImageProvider] = None


def get_default_provider() -> ImageProvider:
    """기본 provider 반환. 캐싱해서 재사용."""
    global _default_provider
    if _default_provider is None:
        _default_provider = OpenAIProvider()
    return _default_provider


def set_default_provider(provider: ImageProvider) -> None:
    """provider 교체 (Stability, Imagen 등으로 변경 시)."""
    global _default_provider
    _default_provider = provider


# ============================================================
# 프롬프트 빌더
# ============================================================
def build_prompt(
    product_name: str,
    industry: str,
    style: str = '밝고 깨끗한 모던 스타일',
    target_audience: Optional[str] = None,
    mood: Optional[str] = None,
    extra_hints: Optional[str] = None,
) -> str:
    """
    상품 정보로부터 AI 이미지 생성용 프롬프트 자동 조립.

    Args:
        product_name: 상품/서비스명 (예: "스마트 체온계")
        industry: 업종 (예: "건강기능식품", "뷰티", "패션", "교육")
        style: 비주얼 스타일 (예: "밝고 깨끗한 모던", "고급스러운 어두운 톤")
        target_audience: 타겟 (예: "30-40대 주부", "20대 직장인 여성")
        mood: 분위기 (예: "활기찬", "차분한", "신뢰감 있는")
        extra_hints: 추가 지시사항 (자유 텍스트)

    Returns:
        조립된 프롬프트 문자열
    """
    parts = [
        f'Ultra high-resolution, premium commercial product photography for "{product_name}" in the {industry} industry.',
        f'Visual style: {style}.',
        'Shot with a professional DSLR camera (Canon EOS R5 or equivalent), 85mm lens, f/2.8 aperture.',
        'Perfect studio lighting setup: key light with softbox, fill light, and rim light for depth.',
        'Extremely sharp focus on the product, beautiful bokeh background.',
        'Color grading: rich, vibrant colors with professional post-processing.',
        'The product is the hero element, composed using the rule of thirds, with premium materials and textures visible.',
    ]
    if target_audience:
        parts.append(f'The image should emotionally resonate with {target_audience} — evoke aspiration and trust.')
    if mood:
        parts.append(f'Overall mood and atmosphere: {mood}. Convey this through lighting and color temperature.')
    if extra_hints:
        parts.append(extra_hints)

    # 텍스트/로고 완전 차단 (영어 프롬프트가 더 잘 먹힘)
    parts.append(
        'EXTREMELY IMPORTANT: This image must be PURELY VISUAL. '
        'Absolutely NO text, NO words, NO letters, NO numbers, NO logos, NO watermarks, '
        'NO labels, NO signs, NO writing, NO typographic elements of ANY kind whatsoever. '
        'Do not render any characters from any alphabet or writing system. '
        'If you feel tempted to add text — DO NOT. The image is text-free.'
    )
    parts.append(
        'Composition requirement: Leave the bottom 30% of the image with a softer, '
        'slightly darker or gradient-friendly area (out-of-focus, smooth surface, or gentle shadow) '
        'to allow text overlay in post-production. '
        'The top 70% should contain the main visual interest and product.'
    )

    return ' '.join(parts)


# ============================================================
# 최상위 헬퍼
# ============================================================
def generate_ad_background(
    prompt: str,
    size: str = '1024x1024',
    quality: str = 'medium',
    output_path: Optional[str] = None,
    provider: Optional[ImageProvider] = None,
) -> str:
    """
    광고용 배경 이미지 생성 (텍스트 없음).

    오버레이는 image_composer.compose_ad() 로 추가.
    """
    if size not in ('1024x1024', '1024x1536', '1536x1024', 'auto'):
        raise ValueError(
            f'지원하지 않는 size: {size}\n'
            '사용 가능: 1024x1024 (1:1), 1024x1536 (2:3 세로), '
            '1536x1024 (3:2 가로), auto'
        )
    if quality not in ('low', 'medium', 'high', 'auto'):
        raise ValueError(f'quality는 low/medium/high/auto 중 하나: {quality}')

    provider = provider or get_default_provider()
    return provider.generate(prompt, size=size, quality=quality, output_path=output_path)


# ============================================================
# CLI 테스트
# ============================================================
if __name__ == '__main__':
    print('=== image_generator.py 테스트 ===\n')

    if not is_openai_configured():
        print('[경고] OpenAI API 키가 설정되지 않았어요.')
        print('       .env 에 OPENAI_API_KEY=sk-... 를 추가하면 실제 이미지 생성 가능합니다.')
        print('       지금은 프롬프트 빌더만 테스트합니다.\n')

    prompt = build_prompt(
        product_name='스마트 체온계',
        industry='건강기능식품',
        style='밝고 깨끗한 미니멀',
        target_audience='30-40대 주부',
        mood='신뢰감 있는',
    )
    print('[프롬프트]')
    print(prompt)
    print()

    if is_openai_configured():
        print('[실행] 실제 이미지 생성 시도 (비용 ~$0.07)...')
        path = generate_ad_background(prompt, size='1024x1024', quality='medium')
        print(f'\n[완료] 생성된 이미지: {path}')
    else:
        print('[스킵] API 키 없어서 실제 생성은 건너뜁니다.')
