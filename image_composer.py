"""
image_composer.py - Pillow 기반 광고 이미지 후처리/오버레이

AI 가 생성한 배경 이미지 위에 한글 텍스트/CTA/로고를 오버레이합니다.
AI 가 한글 텍스트를 제대로 못 그리는 문제를 해결하기 위한 핵심 모듈.

기능:
  - 헤드라인 + 서브텍스트 + CTA 버튼 오버레이
  - 하단 반투명 박스로 텍스트 가독성 확보
  - 로고 합성 (선택)
  - 메타 광고 규격 리사이즈/크롭 (1080x1080, 1200x628, 1080x1920)

사용 예:
    from image_composer import compose_ad

    result_path = compose_ad(
        background_path='./ad_images/ai_12345.png',
        headline='매일 아침 건강 체크',
        subtext='정확한 측정, 30초 완료',
        cta_text='자세히 보기',
        logo_path='./brand/logo.png',  # 선택
        output_path='./ad_images/final_12345.png',
    )
"""

from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from config import FONTS_DIR, AD_IMAGE_DIR


# ============================================================
# 폰트 경로 (Pretendard 우선, 폴백: 시스템 맑은 고딕)
# ============================================================
PRETENDARD_REGULAR = FONTS_DIR / 'Pretendard-Regular.otf'
PRETENDARD_SEMIBOLD = FONTS_DIR / 'Pretendard-SemiBold.otf'
PRETENDARD_BOLD = FONTS_DIR / 'Pretendard-Bold.otf'

# Windows 시스템 폰트 (폴백)
WINDOWS_MALGUN = Path('C:/Windows/Fonts/malgun.ttf')
WINDOWS_MALGUN_BOLD = Path('C:/Windows/Fonts/malgunbd.ttf')


def _resolve_font(preferred_paths: list, size: int) -> ImageFont.FreeTypeFont:
    """우선순위대로 폰트 파일을 찾아서 로드."""
    for p in preferred_paths:
        if p and Path(p).exists():
            return ImageFont.truetype(str(p), size)
    # 최종 폴백: PIL 기본 폰트 (한글 안 보일 수 있음)
    print('[경고] Pretendard/맑은고딕 폰트를 찾지 못해서 기본 폰트 사용 (한글 깨질 수 있음)')
    return ImageFont.load_default()


def load_bold_font(size: int) -> ImageFont.FreeTypeFont:
    return _resolve_font([PRETENDARD_BOLD, WINDOWS_MALGUN_BOLD, WINDOWS_MALGUN], size)


def load_semibold_font(size: int) -> ImageFont.FreeTypeFont:
    return _resolve_font([PRETENDARD_SEMIBOLD, PRETENDARD_BOLD, WINDOWS_MALGUN_BOLD], size)


def load_regular_font(size: int) -> ImageFont.FreeTypeFont:
    return _resolve_font([PRETENDARD_REGULAR, WINDOWS_MALGUN], size)


# ============================================================
# 메타 광고 규격
# ============================================================
META_OUTPUT_SIZES = {
    'feed_square':   (1080, 1080),
    'feed_portrait': (1080, 1350),
    'feed_landscape':(1200, 628),
    'story_reel':    (1080, 1920),
}


# ============================================================
# 텍스트 래핑 (한글 기준)
# ============================================================
def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """한글 텍스트를 max_width에 맞게 여러 줄로 분할."""
    # 한글은 공백으로 끊기 어려운 경우가 많아 글자 단위 fallback
    words = text.split()
    lines = []

    # 먼저 공백 기준으로 시도
    if words:
        current = []
        for word in words:
            test = ' '.join(current + [word])
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(' '.join(current))
                current = [word]
        if current:
            lines.append(' '.join(current))

    # 여전히 너무 긴 줄이 있으면 글자 단위로 재분할
    final_lines = []
    for line in lines:
        bbox = font.getbbox(line)
        if bbox[2] - bbox[0] <= max_width:
            final_lines.append(line)
        else:
            buf = ''
            for ch in line:
                test = buf + ch
                b = font.getbbox(test)
                if b[2] - b[0] <= max_width:
                    buf = test
                else:
                    if buf:
                        final_lines.append(buf)
                    buf = ch
            if buf:
                final_lines.append(buf)
    return final_lines


def _draw_text_multiline(
    draw: ImageDraw.ImageDraw,
    lines: list,
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    color: Tuple[int, int, int],
    line_spacing: float = 1.25,
    align: str = 'left',
    max_width: Optional[int] = None,
    shadow: bool = True,
    shadow_offset: int = 3,
    shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
) -> int:
    """여러 줄 텍스트 그리기 (그림자 포함). 마지막 y 좌표 반환."""
    for line in lines:
        if align == 'center' and max_width:
            bbox = font.getbbox(line)
            lw = bbox[2] - bbox[0]
            lx = x + (max_width - lw) // 2
        else:
            lx = x
        # 텍스트 그림자 (가독성 극대화)
        if shadow:
            for dx, dy in [(shadow_offset, shadow_offset), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                draw.text((lx + dx, y + dy), line, font=font, fill=shadow_color)
        draw.text((lx, y), line, font=font, fill=color)
        y += int(font.size * line_spacing)
    return y


# ============================================================
# 광고 규격 리사이즈/크롭
# ============================================================
def resize_to_ad_format(
    img: Image.Image,
    target: Tuple[int, int],
) -> Image.Image:
    """이미지를 광고 규격에 맞게 center-crop 후 리사이즈."""
    target_w, target_h = target
    src_w, src_h = img.size

    # 비율 맞춰 center crop
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # 원본이 더 넓음 → 좌우 크롭
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        cropped = img.crop((left, 0, left + new_w, src_h))
    else:
        # 원본이 더 좁음 → 상하 크롭
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        cropped = img.crop((0, top, src_w, top + new_h))

    return cropped.resize(target, Image.LANCZOS)


# ============================================================
# 메인 오버레이 함수
# ============================================================
def compose_ad(
    background_path: str,
    headline: str,
    subtext: Optional[str] = None,
    cta_text: Optional[str] = None,
    logo_path: Optional[str] = None,
    output_path: Optional[str] = None,
    ad_format: str = 'feed_square',
    text_color: Tuple[int, int, int] = (255, 255, 255),
    cta_bg_color: Tuple[int, int, int] = (24, 119, 242),   # 메타 브랜드 블루
    cta_text_color: Tuple[int, int, int] = (255, 255, 255),
    overlay_opacity: int = 200,  # 0~255, 하단 반투명 박스 (강화)
) -> str:
    """
    AI 배경 이미지에 헤드라인/서브텍스트/CTA 오버레이해서 최종 광고 이미지 생성.

    Args:
        background_path: AI로 생성한 배경 이미지 경로
        headline: 주요 카피 (예: '매일 아침 건강 체크')
        subtext: 보조 카피 (예: '정확한 측정, 30초 완료')
        cta_text: CTA 버튼 텍스트 (예: '자세히 보기')
        logo_path: 로고 파일 경로 (PNG 권장, 투명 배경)
        output_path: 저장 경로 (미지정 시 자동 생성)
        ad_format: 'feed_square' | 'feed_portrait' | 'feed_landscape' | 'story_reel'
        text_color: 텍스트 RGB
        cta_bg_color: CTA 버튼 배경 RGB
        cta_text_color: CTA 버튼 텍스트 RGB
        overlay_opacity: 텍스트 박스 투명도 (0=투명, 255=불투명)

    Returns:
        저장된 최종 이미지 경로
    """
    if ad_format not in META_OUTPUT_SIZES:
        raise ValueError(
            f'지원하지 않는 ad_format: {ad_format}\n'
            f'사용 가능: {list(META_OUTPUT_SIZES.keys())}'
        )

    target_size = META_OUTPUT_SIZES[ad_format]
    W, H = target_size

    # 1. 배경 로드 + 광고 규격 맞추기
    bg = Image.open(background_path).convert('RGBA')
    bg = resize_to_ad_format(bg, target_size)

    # 2. 오버레이 레이어
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 3. 하단 그라데이션(반투명 검정 박스)으로 텍스트 영역 확보 (강화)
    box_h = int(H * 0.45)
    box_top = H - box_h
    for i in range(box_h):
        # 위쪽으로 갈수록 투명해지는 그라데이션 (1.2 = 더 빠르게 불투명)
        alpha = int(overlay_opacity * (i / box_h) ** 1.2)
        draw.rectangle([0, box_top + i, W, box_top + i + 1], fill=(0, 0, 0, alpha))

    # 4. 폰트 크기 계산 (이미지 너비 비율) — 크게 키움
    headline_size = int(W * 0.085)
    subtext_size = int(W * 0.042)
    cta_size = int(W * 0.045)

    font_headline = load_bold_font(headline_size)
    font_subtext = load_regular_font(subtext_size)
    font_cta = load_semibold_font(cta_size)

    # 5. 헤드라인 그리기
    pad_x = int(W * 0.06)
    max_text_width = W - pad_x * 2

    headline_lines = _wrap_text(headline, font_headline, max_text_width)

    # 하단 여백 기준으로 아래에서부터 쌓아올림
    cta_height = int(cta_size * 2.5) if cta_text else 0
    cta_gap = int(H * 0.03) if cta_text else 0
    subtext_gap = int(subtext_size * 0.6) if subtext else 0

    # 전체 텍스트 블록 예상 높이
    headline_total_h = int(headline_size * 1.25 * len(headline_lines))
    subtext_lines = []
    subtext_total_h = 0
    if subtext:
        subtext_lines = _wrap_text(subtext, font_subtext, max_text_width)
        subtext_total_h = int(subtext_size * 1.3 * len(subtext_lines))

    block_total_h = headline_total_h + subtext_total_h + subtext_gap + cta_height + cta_gap
    bottom_margin = int(H * 0.06)
    current_y = H - bottom_margin - block_total_h

    headline_y = current_y
    shadow_px = max(3, int(headline_size * 0.04))
    _draw_text_multiline(
        draw, headline_lines, font_headline,
        pad_x, headline_y, text_color,
        line_spacing=1.25, align='left',
        shadow=True, shadow_offset=shadow_px,
    )
    current_y = headline_y + headline_total_h

    # 6. 서브텍스트
    if subtext_lines:
        current_y += subtext_gap
        sub_shadow_px = max(2, int(subtext_size * 0.04))
        _draw_text_multiline(
            draw, subtext_lines, font_subtext,
            pad_x, current_y, (255, 255, 255),
            line_spacing=1.3, align='left',
            shadow=True, shadow_offset=sub_shadow_px,
        )
        current_y += subtext_total_h

    # 7. CTA 버튼
    if cta_text:
        current_y += cta_gap
        cta_padding_x = int(cta_size * 1.2)
        cta_padding_y = int(cta_size * 0.5)
        cta_bbox = font_cta.getbbox(cta_text)
        cta_w = (cta_bbox[2] - cta_bbox[0]) + cta_padding_x * 2
        cta_h = (cta_bbox[3] - cta_bbox[1]) + cta_padding_y * 2

        cta_x = pad_x
        cta_y = current_y

        draw.rounded_rectangle(
            [cta_x, cta_y, cta_x + cta_w, cta_y + cta_h],
            radius=int(cta_h * 0.25),
            fill=(*cta_bg_color, 255),
        )
        # CTA 버튼 그림자 효과
        draw.text(
            (cta_x + cta_padding_x + 1, cta_y + cta_padding_y - cta_bbox[1] + 1),
            cta_text,
            font=font_cta,
            fill=(0, 0, 0, 100),
        )
        draw.text(
            (cta_x + cta_padding_x, cta_y + cta_padding_y - cta_bbox[1]),
            cta_text,
            font=font_cta,
            fill=cta_text_color,
        )

    # 8. 로고 (우상단)
    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path).convert('RGBA')
        logo_max_w = int(W * 0.15)
        ratio = logo_max_w / logo.width
        logo = logo.resize((logo_max_w, int(logo.height * ratio)), Image.LANCZOS)
        logo_margin = int(W * 0.04)
        overlay.paste(
            logo,
            (W - logo.width - logo_margin, logo_margin),
            logo,
        )

    # 9. 합성 + 저장
    final = Image.alpha_composite(bg, overlay).convert('RGB')

    if output_path is None:
        stem = Path(background_path).stem
        output_path = str(AD_IMAGE_DIR / f'{stem}_final.png')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, quality=92)
    print(f'[완료] 최종 광고 이미지 저장: {output_path}')
    return output_path


# ============================================================
# CLI 테스트 (AI 없이도 동작)
# ============================================================
if __name__ == '__main__':
    print('=== image_composer.py 테스트 ===\n')

    # 테스트용 플레인 배경 만들기
    test_bg = Image.new('RGB', (1024, 1024), (40, 80, 130))
    # 간단한 그라데이션
    for y in range(1024):
        r = int(40 + (180 - 40) * (y / 1024))
        g = int(80 + (120 - 80) * (y / 1024))
        b = int(130 + (200 - 130) * (y / 1024))
        for x in range(1024):
            test_bg.putpixel((x, y), (r, g, b))

    test_bg_path = str(AD_IMAGE_DIR / 'test_background.png')
    test_bg.save(test_bg_path)
    print(f'[테스트] 더미 배경 생성: {test_bg_path}')

    result = compose_ad(
        background_path=test_bg_path,
        headline='매일 아침 건강 체크',
        subtext='정확한 측정, 30초 완료. 스마트한 가족 건강 관리.',
        cta_text='자세히 보기',
        ad_format='feed_square',
    )
    print(f'\n[완료] 테스트 결과: {result}')
