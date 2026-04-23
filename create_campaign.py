"""
create_campaign.py - 메타 광고 캠페인 자동 생성

config.py 의 account 객체를 사용합니다.

사용 예:
    from create_campaign import create_campaign
    campaign = create_campaign(
        name='봄 프로모션 캠페인',
        objective='OUTCOME_TRAFFIC',
        budget_optimization='CBO',  # 기본값: CBO (권장)
    )
    print(campaign.get_id())

    # 판매 목적이면 ASC 캠페인 추천
    campaign = create_campaign(
        name='판매 캠페인',
        objective='OUTCOME_SALES',
        use_asc=True,  # Advantage+ Shopping Campaign
    )
"""

from typing import Optional

from facebook_business.adobjects.campaign import Campaign

from config import account


VALID_OBJECTIVES = {
    'OUTCOME_AWARENESS',
    'OUTCOME_TRAFFIC',
    'OUTCOME_ENGAGEMENT',
    'OUTCOME_LEADS',
    'OUTCOME_APP_PROMOTION',
    'OUTCOME_SALES',
}

# 목표별 권장 설정 (전자책 기반)
OBJECTIVE_RECOMMENDATIONS = {
    'OUTCOME_SALES': {
        'recommended_budget': 'CBO',
        'recommended_asc': True,
        'tip': 'ASC(Advantage+ Shopping Campaign)가 판매 목적에 가장 효과적입니다.',
    },
    'OUTCOME_TRAFFIC': {
        'recommended_budget': 'CBO',
        'recommended_asc': False,
        'tip': 'CBO + 광고세트 4개 + 크리에이티브 3~4개/세트 구조를 권장합니다.',
    },
    'OUTCOME_AWARENESS': {
        'recommended_budget': 'CBO',
        'recommended_asc': False,
        'tip': '넓은 타겟 + Advantage+ 타겟팅으로 도달을 극대화하세요.',
    },
    'OUTCOME_ENGAGEMENT': {
        'recommended_budget': 'CBO',
        'recommended_asc': False,
        'tip': '참여 목적: 다양한 크리에이티브 컨셉으로 A/B 테스트하세요.',
    },
    'OUTCOME_LEADS': {
        'recommended_budget': 'CBO',
        'recommended_asc': False,
        'tip': '리드 수집: 간결한 폼 + 명확한 CTA가 전환율을 높입니다.',
    },
    'OUTCOME_APP_PROMOTION': {
        'recommended_budget': 'CBO',
        'recommended_asc': False,
        'tip': '앱 설치: Advantage+ 앱 캠페인 활용을 고려하세요.',
    },
}


def create_campaign(
    name: str,
    objective: str = 'OUTCOME_TRAFFIC',
    status: str = 'PAUSED',
    special_ad_categories: Optional[list] = None,
    budget_optimization: str = 'CBO',
    use_asc: bool = False,
    daily_budget: Optional[int] = None,
) -> Campaign:
    """캠페인 생성.

    Args:
        name: 캠페인 이름
        objective: 목표. VALID_OBJECTIVES 중 하나
        status: 'PAUSED' 또는 'ACTIVE'
        special_ad_categories: 특수 광고 카테고리, 해당 없으면 []
        budget_optimization: 'CBO' (캠페인 예산 최적화, 권장) 또는 'ABO' (광고세트별 예산)
        use_asc: True면 Advantage+ Shopping Campaign 으로 생성 (OUTCOME_SALES 전용)
        daily_budget: CBO 사용 시 캠페인 일일 예산 (원). None이면 광고세트에서 설정.
    """
    if objective not in VALID_OBJECTIVES:
        valid = ', '.join(sorted(VALID_OBJECTIVES))
        raise ValueError(
            '지원하지 않는 objective: ' + objective + '\n사용 가능: ' + valid
        )
    if status not in ('PAUSED', 'ACTIVE'):
        raise ValueError('status 는 PAUSED 또는 ACTIVE 만 가능: ' + status)
    if budget_optimization not in ('CBO', 'ABO'):
        raise ValueError('budget_optimization 은 CBO 또는 ABO 만 가능: ' + budget_optimization)
    if use_asc and objective != 'OUTCOME_SALES':
        raise ValueError('ASC(Advantage+ Shopping Campaign)는 OUTCOME_SALES 목표에서만 사용 가능합니다.')

    if special_ad_categories is None:
        special_ad_categories = []

    # CBO 여부 결정
    is_cbo = (budget_optimization == 'CBO')

    params = {
        'name': name,
        'objective': objective,
        'status': status,
        'special_ad_categories': special_ad_categories,
    }

    # ASC (Advantage+ Shopping Campaign) 설정
    if use_asc:
        params['smart_promotion_type'] = 'AUTOMATED_SHOPPING_ADS'
        # ASC는 자체적으로 예산을 관리하므로 is_adset_budget_sharing_enabled 사용 불가
        if daily_budget:
            params['daily_budget'] = daily_budget
        print('[캠페인] ASC (Advantage+ Shopping) 캠페인으로 생성 중: ' + name)
    elif is_cbo and daily_budget:
        # CBO: 캠페인 레벨 예산이 있을 때만 CBO 활성화
        params['is_adset_budget_sharing_enabled'] = True
        params['daily_budget'] = daily_budget
        print('[캠페인] CBO 모드로 생성 중: ' + name + ' (일일예산: ' + str(daily_budget) + '원)')
    else:
        # ABO: 광고세트별 예산 사용
        params['is_adset_budget_sharing_enabled'] = False
        print('[캠페인] 광고세트별 예산 모드로 생성 중: ' + name)

    campaign = account.create_campaign(
        fields=[Campaign.Field.name],
        params=params,
    )
    print('[완료] 캠페인 생성 - ID: ' + str(campaign.get_id())
          + ' (status: ' + status + ', budget: ' + budget_optimization + ')')
    return campaign


def get_recommendation(objective: str) -> dict:
    """목표에 따른 권장 설정 반환."""
    return OBJECTIVE_RECOMMENDATIONS.get(objective, {
        'recommended_budget': 'CBO',
        'recommended_asc': False,
        'tip': 'CBO를 기본으로 사용하고, 광고세트 4개에 크리에이티브 3~4개씩 구성하세요.',
    })


if __name__ == '__main__':
    print('=== create_campaign.py 데모 실행 ===\n')
    campaign = create_campaign(
        name='테스트 캠페인 - 자동생성',
        objective='OUTCOME_TRAFFIC',
        status='PAUSED',
    )
    print('\n[성공] 캠페인 ID:', campaign.get_id())
