"""
get_insights.py - 메타 광고 성과 데이터 수집

config.py 의 account 객체를 사용합니다.

사용 예:
    from get_insights import get_campaign_insights, print_insights
    data = get_campaign_insights(date_preset='last_30d')
    print_insights(data)
"""

from typing import Optional

from facebook_business.adobjects.adsinsights import AdsInsights

from config import account


DEFAULT_FIELDS = [
    AdsInsights.Field.campaign_name,
    AdsInsights.Field.adset_name,
    AdsInsights.Field.impressions,
    AdsInsights.Field.clicks,
    AdsInsights.Field.ctr,
    AdsInsights.Field.cpm,
    AdsInsights.Field.cpc,
    AdsInsights.Field.spend,
    AdsInsights.Field.actions,
    AdsInsights.Field.purchase_roas,
]


def get_insights(
    level: str = 'campaign',
    date_preset: str = 'last_30d',
    fields: Optional[list] = None,
    extra_params: Optional[dict] = None,
) -> list:
    """광고 성과 데이터 조회.

    Args:
        level: account / campaign / adset / ad
        date_preset: today / yesterday / last_7d / last_30d / this_month 등
        fields: 조회할 필드 (None 이면 DEFAULT_FIELDS)
        extra_params: API 에 추가로 넘길 파라미터
    """
    if level not in ('account', 'campaign', 'adset', 'ad'):
        raise ValueError('level 은 account/campaign/adset/ad 중 하나: ' + level)

    if fields is None:
        fields = DEFAULT_FIELDS

    params = {'date_preset': date_preset, 'level': level}
    if extra_params:
        params.update(extra_params)

    insights = account.get_insights(fields=fields, params=params)
    return list(insights)


def get_campaign_insights(date_preset: str = 'last_30d') -> list:
    """캠페인 레벨 성과 조회 (편의 함수)."""
    return get_insights(level='campaign', date_preset=date_preset)


def print_insights(insights: list) -> None:
    """조회 결과 보기 좋게 출력."""
    if not insights:
        print('데이터가 없어요 (광고 집행 이력 없음)')
        return

    for insight in insights:
        print('===========================')
        if insight.get('campaign_name'):
            print('캠페인:', insight.get('campaign_name'))
        if insight.get('adset_name'):
            print('광고세트:', insight.get('adset_name'))
        print('노출수:', insight.get('impressions', 0))
        print('클릭수:', insight.get('clicks', 0))
        print('CTR:', insight.get('ctr', 0), '%')
        print('CPM:', insight.get('cpm', 0), '원')
        print('CPC:', insight.get('cpc', 0), '원')
        print('지출:', insight.get('spend', 0), '원')

        roas_list = insight.get('purchase_roas', [])
        if roas_list:
            print('ROAS:', roas_list[0].get('value', 0))


if __name__ == '__main__':
    print('=== get_insights.py - 최근 30일 캠페인 성과 ===\n')
    data = get_campaign_insights(date_preset='last_30d')
    print_insights(data)
