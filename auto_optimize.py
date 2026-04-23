"""
auto_optimize.py - 자동 최적화 규칙 엔진

config.py 의 account 객체를 사용합니다.

규칙 (기본값):
  - Frequency > 4.0      : 피로도 경고 (크리에이티브 교체 권장)
  - CPA > 목표 * 1.5     : 저성과 -> 광고세트 자동 중지
  - ROAS > 목표          : 고성과 -> 예산 20% 증액
  - 지출 < 최소 기준      : 판단 보류

사용 예:
    from auto_optimize import run_optimization
    run_optimization(dry_run=True)   # 실제 적용 없이 리포트만
    run_optimization()               # 실제 광고세트 업데이트
"""

from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adsinsights import AdsInsights

from config import account


# --- 기본 목표 기준값 ---
TARGET_CPA = 10000       # 목표 CPA (원) - 이 이상이면 중지
TARGET_ROAS = 3.0        # 목표 ROAS - 이 이상이면 예산 증액
MAX_FREQUENCY = 4.0      # 최대 노출 빈도 - 이 이상이면 경고
MIN_SPEND = 5000         # 최소 지출 기준 (원) - 이 미만은 판단 안 함
BUDGET_INCREASE = 1.2    # 예산 증액 비율 (20%)


def run_optimization(
    target_cpa: float = TARGET_CPA,
    target_roas: float = TARGET_ROAS,
    max_frequency: float = MAX_FREQUENCY,
    min_spend: float = MIN_SPEND,
    budget_increase: float = BUDGET_INCREASE,
    date_preset: str = 'last_7d',
    include_paused: bool = False,
    dry_run: bool = False,
) -> dict:
    """자동 최적화 실행.

    Args:
        target_cpa/target_roas/max_frequency/min_spend/budget_increase: 기준값
        date_preset: 성과 평가 기간
        include_paused: 활성 광고세트가 없을 때 PAUSED 도 점검 대상에 포함
        dry_run: True 면 실제로는 업데이트 하지 않음 (리포트만)

    Returns:
        요약 딕셔너리 (paused, boosted, warnings, skipped, normal)
    """
    summary = {
        'paused': [],
        'boosted': [],
        'warnings': [],
        'skipped': [],
        'normal': [],
    }

    print('=== 자동 최적화 시작 ===')
    if dry_run:
        print('[DRY RUN] 실제 업데이트는 하지 않습니다\n')
    else:
        print()

    # 활성 광고세트 목록 가져오기
    adsets = account.get_ad_sets(
        fields=[
            AdSet.Field.id,
            AdSet.Field.name,
            AdSet.Field.status,
            AdSet.Field.daily_budget,
        ],
        params={'effective_status': ['ACTIVE']}
    )

    if not adsets and include_paused:
        print('현재 활성화된 광고세트가 없어요. PAUSED 도 확인해볼게요.\n')
        adsets = account.get_ad_sets(
            fields=[
                AdSet.Field.id,
                AdSet.Field.name,
                AdSet.Field.status,
                AdSet.Field.daily_budget,
            ],
            params={'effective_status': ['PAUSED']}
        )

    if not adsets:
        print('점검할 광고세트가 없어요.')
        return summary

    for adset in adsets:
        adset_id = adset['id']
        adset_name = adset['name']
        daily_budget = int(adset.get('daily_budget', 0))

        print('광고세트: ' + adset_name)
        print('현재 예산: ' + format(daily_budget, ',') + '원')

        insights = adset.get_insights(
            fields=[
                AdsInsights.Field.spend,
                AdsInsights.Field.actions,
                AdsInsights.Field.purchase_roas,
                AdsInsights.Field.frequency,
                AdsInsights.Field.cpm,
                AdsInsights.Field.ctr,
            ],
            params={'date_preset': date_preset}
        )

        if not insights:
            print('-> 데이터 없음 (집행 이력 없음)')
            print()
            summary['skipped'].append(adset_name)
            continue

        insight = insights[0]
        spend = float(insight.get('spend', 0) or 0)
        frequency = float(insight.get('frequency', 0) or 0)
        ctr = float(insight.get('ctr', 0) or 0)
        cpm = float(insight.get('cpm', 0) or 0)

        # ROAS 계산
        roas = 0.0
        purchase_roas = insight.get('purchase_roas', []) or []
        if purchase_roas:
            roas = float(purchase_roas[0].get('value', 0) or 0)

        # CPA 계산
        cpa = 0.0
        actions = insight.get('actions', []) or []
        purchases = [a for a in actions if a.get('action_type') == 'purchase']
        if purchases and spend > 0:
            try:
                cpa = spend / float(purchases[0]['value'])
            except (ValueError, ZeroDivisionError):
                cpa = 0.0

        print(
            '지출: ' + format(spend, ',.0f') + '원 | CTR: ' + format(ctr, '.2f')
            + '% | CPM: ' + format(cpm, ',.0f') + '원'
        )
        print(
            'ROAS: ' + format(roas, '.2f') + ' | CPA: ' + format(cpa, ',.0f')
            + '원 | Frequency: ' + format(frequency, '.2f')
        )

        # 규칙 적용
        if spend < min_spend:
            print('-> 데이터 부족 (최소 지출 미달) - 판단 보류')
            summary['skipped'].append(adset_name)

        elif frequency > max_frequency:
            msg = '피로도 경고 (Frequency ' + format(frequency, '.1f') + ') - 크리에이티브 교체 권장'
            print('-> ' + msg)
            summary['warnings'].append({'adset': adset_name, 'reason': msg})

        elif cpa > 0 and cpa > target_cpa * 1.5:
            print('-> 저성과 감지! CPA ' + format(cpa, ',.0f') + '원 (목표의 150% 초과) - 중지')
            if not dry_run:
                adset.api_update(params={'status': 'PAUSED'})
                print('-> 광고세트 중지 완료')
            summary['paused'].append({'adset': adset_name, 'cpa': cpa})

        elif roas > target_roas:
            new_budget = int(daily_budget * budget_increase)
            print('-> 고성과 감지! ROAS ' + format(roas, '.2f') + ' - 예산 증액')
            if not dry_run:
                adset.api_update(params={'daily_budget': new_budget})
                print('-> 예산 ' + format(daily_budget, ',') + '원 -> '
                      + format(new_budget, ',') + '원 증액 완료')
            summary['boosted'].append({
                'adset': adset_name, 'roas': roas,
                'old_budget': daily_budget, 'new_budget': new_budget,
            })

        else:
            print('-> 정상 범위 - 유지')
            summary['normal'].append(adset_name)

        print()

    print('=== 최적화 완료 ===')
    print('중지: ' + str(len(summary['paused']))
          + ' | 증액: ' + str(len(summary['boosted']))
          + ' | 경고: ' + str(len(summary['warnings']))
          + ' | 보류: ' + str(len(summary['skipped']))
          + ' | 정상: ' + str(len(summary['normal'])))
    return summary


if __name__ == '__main__':
    run_optimization(include_paused=True, dry_run=True)
