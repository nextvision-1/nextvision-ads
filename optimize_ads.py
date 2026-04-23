"""
optimize_ads.py - 기존 광고 이미지 3개를 Meta 최적화 기준으로 재가공

사용법:
    1. ad_images/ 폴더에 원본 이미지 3개를 넣으세요:
       - concept1.png (호기심 자극형)
       - concept2.png (혜택 강조형)
       - concept3.png (셀러 관점형)
    2. python optimize_ads.py 실행
    3. ad_images/ 폴더에 _optimized.png 파일이 생성됩니다

최적화 내용:
    - CTA 버튼 제거 (Meta가 자체 제공)
    - 텍스트를 핵심 단어 2~3개로 축소
    - 텍스트 면적 10% 이하 유지
    - 1080x1080 피드 정사각형 규격
"""

from pathlib import Path
from image_composer import (
    compose_ad, resize_to_ad_format, load_bold_font, load_regular_font,
    _wrap_text, _draw_text_multiline, META_OUTPUT_SIZES, AD_IMAGE_DIR
)
from PIL import Image, ImageDraw

# 이미지 경로
IMG_DIR = AD_IMAGE_DIR


def optimize_image(
    input_path: str,
    headline: str,
    subtext: str = None,
    output_name: str = 'optimized.png',
):
    """
    기존 이미지에서 텍스트 오버레이를 최소화하여 재생성.
    CTA 버튼 없음, 텍스트 최소화.
    """
    W, H = 1080, 1080

    # 1. 원본 이미지 로드 + 리사이즈
    bg = Image.open(input_path).convert('RGBA')
    bg = resize_to_ad_format(bg, (W, H))

    # 2. 오버레이 레이어
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 3. 하단 그라데이션 (가볍게 — 텍스트가 적으니까)
    box_h = int(H * 0.35)
    box_top = H - box_h
    for i in range(box_h):
        alpha = int(180 * (i / box_h) ** 1.3)
        draw.rectangle([0, box_top + i, W, box_top + i + 1], fill=(0, 0, 0, alpha))

    # 4. 헤드라인만 (크고 굵게, 핵심 단어만)
    headline_size = int(W * 0.09)
    font_headline = load_bold_font(headline_size)
    pad_x = int(W * 0.06)
    max_text_width = W - pad_x * 2

    headline_lines = _wrap_text(headline, font_headline, max_text_width)

    # 서브텍스트
    subtext_lines = []
    subtext_size = int(W * 0.038)
    font_subtext = load_regular_font(subtext_size)
    if subtext:
        subtext_lines = _wrap_text(subtext, font_subtext, max_text_width)

    # 위치 계산 (하단에서 올림)
    headline_total_h = int(headline_size * 1.25 * len(headline_lines))
    subtext_total_h = int(subtext_size * 1.3 * len(subtext_lines)) if subtext_lines else 0
    subtext_gap = int(subtext_size * 0.6) if subtext_lines else 0

    block_total_h = headline_total_h + subtext_total_h + subtext_gap
    bottom_margin = int(H * 0.08)
    current_y = H - bottom_margin - block_total_h

    # 헤드라인 그리기
    shadow_px = max(3, int(headline_size * 0.04))
    _draw_text_multiline(
        draw, headline_lines, font_headline,
        pad_x, current_y, (255, 255, 255),
        line_spacing=1.25, align='left',
        shadow=True, shadow_offset=shadow_px,
    )
    current_y += headline_total_h

    # 서브텍스트 그리기
    if subtext_lines:
        current_y += subtext_gap
        sub_shadow_px = max(2, int(subtext_size * 0.04))
        _draw_text_multiline(
            draw, subtext_lines, font_subtext,
            pad_x, current_y, (220, 220, 220),
            line_spacing=1.3, align='left',
            shadow=True, shadow_offset=sub_shadow_px,
        )

    # 5. 합성 + 저장
    final = Image.alpha_composite(bg, overlay).convert('RGB')
    output_path = str(IMG_DIR / output_name)
    final.save(output_path, quality=95)
    print(f'[완료] 최적화 이미지 저장: {output_path}')
    return output_path


# ============================================================
# 3개 컨셉 최적화 설정
# ============================================================
CONCEPTS = [
    {
        'input': 'ai_1776761730.png',
        'output': 'concept1_optimized.png',
        'headline': '빈박스 리뷰 끝',
        'subtext': '실배송 구매평 체험단으로 바꾸세요',
    },
    {
        'input': 'ai_1776762832.png',
        'output': 'concept2_optimized.png',
        'headline': '0원 체험',
        'subtext': '빈박스 리뷰 그만 사세요',
    },
    {
        'input': 'ai_1776762975.png',
        'output': 'concept3_optimized.png',
        'headline': '진짜 리뷰',
        'subtext': '어뷰징으로 지워지는 빈박스 리뷰 말고 진짜 리뷰',
    },
]


if __name__ == '__main__':
    print('=== 광고 이미지 최적화 (Meta 기준) ===\n')
    print('CTA 버튼 제거 + 텍스트 최소화\n')

    for c in CONCEPTS:
        input_path = IMG_DIR / c['input']
        if not input_path.exists():
            print(f'[건너뜀] {c["input"]} 파일이 없습니다. ad_images/ 폴더에 넣어주세요.')
            continue
        optimize_image(
            input_path=str(input_path),
            headline=c['headline'],
            subtext=c['subtext'],
            output_name=c['output'],
        )

    print('\n=== 완료 ===')
    print(f'최적화된 이미지는 {IMG_DIR} 폴더에 저장됩니다.')
    print('이 이미지들을 Streamlit 광고 탭에서 업로드하세요.')
