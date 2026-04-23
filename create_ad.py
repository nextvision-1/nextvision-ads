"""
create_ad.py - 메타 광고 크리에이티브 + 광고(Ad) 자동 생성

기능:
  1) 로컬 이미지를 광고 계정에 업로드하고 image_hash 반환
  2) 이미지 광고 크리에이티브 생성
  3) 링크 전용(이미지 없음) 크리에이티브 생성
  4) 크리에이티브를 기반으로 광고 생성
  5) 원스텝 헬퍼: 이미지 업로드 + 크리에이티브 + 광고 한 번에
"""

from pathlib import Path
from typing import Optional

from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adimage import AdImage

from config import account, PAGE_ID, DEFAULT_LANDING_URL


VALID_CTA_TYPES = {
    'LEARN_MORE', 'SHOP_NOW', 'SIGN_UP', 'SUBSCRIBE', 'CONTACT_US',
    'DOWNLOAD', 'GET_OFFER', 'GET_QUOTE', 'APPLY_NOW', 'BOOK_TRAVEL',
    'INSTALL_APP', 'PLAY_GAME', 'WATCH_MORE', 'MESSAGE_PAGE', 'CALL_NOW',
}


def upload_image(image_path: str) -> str:
    """로컬 이미지를 광고 계정에 업로드하고 image_hash 반환."""
    path = Path(image_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError('이미지 파일을 찾을 수 없어요: ' + str(path))

    print('[업로드] 이미지 업로드 중: ' + path.name)
    image = AdImage(parent_id=account.get_id_assured())
    image[AdImage.Field.filename] = str(path)
    image.remote_create()

    image_hash = image[AdImage.Field.hash]
    print('[완료] 업로드 완료 - hash: ' + image_hash)
    return image_hash


def create_image_creative(
    image_hash: str,
    headline: str,
    message: str,
    link_url: str = None,
    cta_type: str = 'LEARN_MORE',
    name: Optional[str] = None,
    page_id: Optional[str] = None,
) -> AdCreative:
    """이미지 기반 링크 광고 크리에이티브 생성."""
    _validate_cta(cta_type)

    link_url = link_url or DEFAULT_LANDING_URL
    page_id = page_id or PAGE_ID
    creative_name = name or ('크리에이티브 - ' + headline[:20])

    print('[크리에이티브] 생성 중: ' + creative_name)
    creative = account.create_ad_creative(
        fields=[AdCreative.Field.name],
        params={
            'name': creative_name,
            'object_story_spec': {
                'page_id': page_id,
                'link_data': {
                    'image_hash': image_hash,
                    'link': link_url,
                    'message': message,
                    'name': headline,
                    'call_to_action': {
                        'type': cta_type,
                    },
                },
            },
        }
    )
    print('[완료] 크리에이티브 생성 - ID: ' + str(creative.get_id()))
    return creative


def create_link_creative(
    headline: str,
    message: str,
    link_url: str = None,
    cta_type: str = 'LEARN_MORE',
    name: Optional[str] = None,
    page_id: Optional[str] = None,
) -> AdCreative:
    """이미지 없이 링크만 있는 광고 크리에이티브 생성."""
    _validate_cta(cta_type)

    link_url = link_url or DEFAULT_LANDING_URL
    page_id = page_id or PAGE_ID
    creative_name = name or ('링크크리에이티브 - ' + headline[:20])

    print('[크리에이티브] 링크 생성 중: ' + creative_name)
    creative = account.create_ad_creative(
        fields=[AdCreative.Field.name],
        params={
            'name': creative_name,
            'object_story_spec': {
                'page_id': page_id,
                'link_data': {
                    'link': link_url,
                    'message': message,
                    'name': headline,
                    'call_to_action': {
                        'type': cta_type,
                    },
                },
            },
        }
    )
    print('[완료] 크리에이티브 생성 - ID: ' + str(creative.get_id()))
    return creative


def create_ad(
    adset_id: str,
    creative_id: str,
    ad_name: str,
    status: str = 'PAUSED',
) -> Ad:
    """기존 광고세트 + 크리에이티브로 광고(Ad) 생성."""
    if status not in ('PAUSED', 'ACTIVE'):
        raise ValueError('status 는 PAUSED 또는 ACTIVE 만 가능: ' + status)

    print('[광고] 생성 중: ' + ad_name)
    ad = account.create_ad(
        fields=[Ad.Field.name],
        params={
            'name': ad_name,
            'adset_id': adset_id,
            'creative': {'creative_id': creative_id},
            'status': status,
        }
    )
    print('[완료] 광고 생성 - ID: ' + str(ad.get_id()) + ' (status: ' + status + ')')
    return ad


def create_image_ad(
    adset_id: str,
    image_path: str,
    headline: str,
    message: str,
    ad_name: str,
    link_url: str = None,
    cta_type: str = 'LEARN_MORE',
    status: str = 'PAUSED',
    page_id: Optional[str] = None,
) -> Ad:
    """이미지 업로드부터 광고 생성까지 한 번에."""
    image_hash = upload_image(image_path)
    creative = create_image_creative(
        image_hash=image_hash,
        headline=headline,
        message=message,
        link_url=link_url,
        cta_type=cta_type,
        name='크리에이티브 - ' + ad_name,
        page_id=page_id,
    )
    ad = create_ad(
        adset_id=adset_id,
        creative_id=creative.get_id(),
        ad_name=ad_name,
        status=status,
    )
    return ad


def _validate_cta(cta_type: str) -> None:
    if cta_type not in VALID_CTA_TYPES:
        valid = ', '.join(sorted(VALID_CTA_TYPES))
        raise ValueError(
            '지원하지 않는 CTA 타입: ' + cta_type + '\n사용 가능한 값: ' + valid
        )


if __name__ == '__main__':
    DEMO_ADSET_ID = '120245636876020166'
    DEMO_IMAGE_PATH = './ad_images/sample.jpg'

    print('=== create_ad.py 데모 실행 ===\n')

    if Path(DEMO_IMAGE_PATH).exists():
        print('이미지 파일 발견 -> 이미지 광고 생성\n')
        ad = create_image_ad(
            adset_id=DEMO_ADSET_ID,
            image_path=DEMO_IMAGE_PATH,
            headline='지금 바로 시작하세요!',
            message='넥스트비전 마케팅 자동화 솔루션',
            link_url=DEFAULT_LANDING_URL,
            ad_name='테스트 이미지 광고 - 자동생성',
            cta_type='LEARN_MORE',
        )
    else:
        print('[경고] 이미지 파일 없음 (' + DEMO_IMAGE_PATH + ') -> 링크 광고로 폴백\n')
        creative = create_link_creative(
            headline='지금 바로 시작하세요!',
            message='넥스트비전 마케팅 자동화 솔루션',
            link_url=DEFAULT_LANDING_URL,
            cta_type='LEARN_MORE',
        )
        ad = create_ad(
            adset_id=DEMO_ADSET_ID,
            creative_id=creative.get_id(),
            ad_name='테스트 링크 광고 - 자동생성',
        )

    print('\n[성공] 모든 작업 완료 - 최종 광고 ID: ' + str(ad.get_id()))
