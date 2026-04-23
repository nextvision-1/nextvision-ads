"""
create_adset.py - 메타 광고세트 자동 생성

config.py 의 account 객체를 사용합니다.

사용 예:
    from create_adset import create_adset
    adset = create_adset(
        campaign_id='120245636461170166',
        name='20-45세 전국 타겟',
        daily_budget=10000,
        targeting_mode='advantage_plus',  # 권장: Advantage+ AI 타겟팅
    )
"""

from typing import Optional

from facebook_business.adobjects.adset import AdSet

from config import account


# 타겟팅 모드 설명 (전자책 기반)
TARGETING_MODES = {
    'advantage_plus': {
        'label': 'Advantage+ (권장)',
        'description': 'Meta AI가 최적 타겟을 자동 탐색. 2024년 이후 대부분의 경우 가장 좋은 성과.',
        'advantage_audience': 1,
    },
    'manual': {
        'label': '수동 타겟팅',
        'description': '직접 관심사/연령/성별 등을 설정. 예산이 작거나 매우 특수한 타겟에 적합.',
        'advantage_audience': 0,
    },
    'suggestion': {
        'label': 'Advantage+ 제안형',
        'description': '수동 타겟을 "제안"으로 넣고, AI가 추가 확장. 커스텀/유사 오디언스와 함께 사용 권장.',
        'advantage_audience': 1,
    },
}

# 학습 단계 관련 상수
LEARNING_PHASE_INFO = {
    'min_conversions_per_week': 50,
    'min_days_no_edit': 3,
    'max_budget_change_pct': 20,
    'warning': (
        '학습 단계 주의사항:\n'
        '- 광고세트 생성 후 최소 3~5일은 수정하지 마세요\n'
        '- 주당 50건 이상의 전환이 필요합니다\n'
        '- 예산 변경은 20% 이내로 하세요 (초과 시 학습 리셋)\n'
        '- 타겟, 크리에이티브 추가/삭제도 학습을 리셋시킵니다'
    ),
}


def create_adset(
    campaign_id: str,
    name: str,
    daily_budget: int = 10000,
    billing_event: str = 'IMPRESSIONS',
    optimization_goal: str = 'LINK_CLICKS',
    bid_strategy: str = 'LOWEST_COST_WITHOUT_CAP',
    targeting_mode: str = 'advantage_plus',
    countries: Optional[list] = None,
    age_min: int = 18,
    age_max: int = 65,
    genders: Optional[list] = None,
    interests: Optional[list] = None,
    custom_audiences: Optional[list] = None,
    lookalike_audiences: Optional[list] = None,
    custom_targeting: Optional[dict] = None,
    status: str = 'PAUSED',
) -> AdSet:
    """광고세트 생성.

    Args:
        campaign_id: 상위 캠페인 ID
        name: 광고세트 이름
        daily_budget: 일일 예산 (원, 최소 1000). CBO 캠페인이면 무시될 수 있음.
        billing_event: IMPRESSIONS / LINK_CLICKS 등
        optimization_goal: LINK_CLICKS / REACH / OFFSITE_CONVERSIONS 등
        bid_strategy: LOWEST_COST_WITHOUT_CAP 등
        targeting_mode: 'advantage_plus' (권장) / 'manual' / 'suggestion'
        countries: 국가 리스트 (기본 ['KR'])
        age_min/age_max: 연령대 (advantage_plus 모드에서는 넓게 설정됨)
        genders: 성별 [1]=남성, [2]=여성, None=전체
        interests: 관심사 타겟팅 리스트 (예: [{'id': 6003139266461, 'name': '건강'}])
        custom_audiences: 커스텀 오디언스 ID 리스트
        lookalike_audiences: 유사 타겟 오디언스 ID 리스트
        custom_targeting: 추가 targeting 딕셔너리 (기본값 덮어쓰기)
        status: PAUSED 또는 ACTIVE
    """
    if status not in ('PAUSED', 'ACTIVE'):
        raise ValueError('status 는 PAUSED 또는 ACTIVE 만 가능: ' + status)
    if targeting_mode not in TARGETING_MODES:
        raise ValueError('targeting_mode 는 ' + '/'.join(TARGETING_MODES.keys()) + ' 중 하나: ' + targeting_mode)

    if countries is None:
        countries = ['KR']

    mode_info = TARGETING_MODES[targeting_mode]

    # 타겟팅 구성
    targeting = {
        'geo_locations': {'countries': countries},
        'targeting_automation': {'advantage_audience': mode_info['advantage_audience']},
    }

    # Advantage+ 모드에서는 연령/성별을 넓게 설정 (AI가 최적화)
    if targeting_mode == 'advantage_plus':
        targeting['age_min'] = 18
        targeting['age_max'] = 65
        print('[광고세트] Advantage+ 타겟팅: Meta AI가 최적 오디언스를 탐색합니다.')
    else:
        targeting['age_min'] = age_min
        targeting['age_max'] = age_max
        if genders:
            targeting['genders'] = genders
        if interests:
            targeting['interests'] = interests
        print('[광고세트] 수동 타겟팅: 연령 ' + str(age_min) + '-' + str(age_max) + '세')

    # 커스텀/유사 오디언스 (suggestion 모드에서 특히 효과적)
    if custom_audiences or lookalike_audiences:
        audiences = []
        if custom_audiences:
            audiences.extend([{'id': aid} for aid in custom_audiences])
        if lookalike_audiences:
            audiences.extend([{'id': aid} for aid in lookalike_audiences])
        targeting['custom_audiences'] = audiences
        print('[광고세트] 커스텀/유사 오디언스 ' + str(len(audiences)) + '개 설정')

    if custom_targeting:
        targeting.update(custom_targeting)

    print('[광고세트] 생성 중: ' + name + ' (' + mode_info['label'] + ')')
    adset = account.create_ad_set(
        fields=[AdSet.Field.name],
        params={
            'name': name,
            'campaign_id': campaign_id,
            'daily_budget': daily_budget,
            'billing_event': billing_event,
            'optimization_goal': optimization_goal,
            'bid_strategy': bid_strategy,
            'targeting': targeting,
            'status': status,
        }
    )
    print('[완료] 광고세트 생성 - ID: ' + str(adset.get_id()) + ' (status: ' + status + ')')
    print('[학습] ' + LEARNING_PHASE_INFO['warning'].split('\n')[1])
    return adset


if __name__ == '__main__':
    DEMO_CAMPAIGN_ID = '120245636461170166'

    print('=== create_adset.py 데모 실행 ===\n')
    adset = create_adset(
        campaign_id=DEMO_CAMPAIGN_ID,
        name='테스트 광고세트 - Advantage+ 타겟팅',
        daily_budget=10000,
        targeting_mode='advantage_plus',
        status='PAUSED',
    )
    print('\n[성공] 광고세트 ID:', adset.get_id())
