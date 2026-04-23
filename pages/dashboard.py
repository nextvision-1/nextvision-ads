"""성과 대시보드 페이지 — 커스텀 메트릭 + 학습 단계 모니터링."""

import streamlit as st
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def render():
    st.title('성과 대시보드')

    # 기간·레벨 선택
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        date_preset = st.selectbox(
            '기간',
            ['today', 'yesterday', 'last_7d', 'last_30d', 'this_month'],
            index=2,
            format_func=lambda x: {
                'today': '오늘',
                'yesterday': '어제',
                'last_7d': '최근 7일',
                'last_30d': '최근 30일',
                'this_month': '이번 달',
            }.get(x, x),
        )
    with col2:
        level = st.selectbox(
            '레벨',
            ['campaign', 'adset', 'ad'],
            format_func=lambda x: {
                'campaign': '캠페인',
                'adset': '광고세트',
                'ad': '광고',
            }.get(x, x),
        )
    with col3:
        show_advanced = st.checkbox('커스텀 메트릭 표시', value=True, help='Hook Rate, Frequency, CPA 등 전문가 지표를 함께 표시합니다.')

    # 데이터 조회 버튼
    if st.button('조회', type='primary', use_container_width=False):
        with st.spinner('성과 데이터 수집 중...'):
            try:
                from get_insights import get_insights
                from facebook_business.adobjects.adsinsights import AdsInsights

                # 기본 + 커스텀 메트릭 필드
                fields = [
                    AdsInsights.Field.campaign_name,
                    AdsInsights.Field.adset_name,
                    AdsInsights.Field.ad_name,
                    AdsInsights.Field.impressions,
                    AdsInsights.Field.clicks,
                    AdsInsights.Field.ctr,
                    AdsInsights.Field.cpm,
                    AdsInsights.Field.cpc,
                    AdsInsights.Field.spend,
                    AdsInsights.Field.actions,
                    AdsInsights.Field.purchase_roas,
                    AdsInsights.Field.frequency,
                    AdsInsights.Field.reach,
                ]
                # 영상 메트릭 (Hook Rate 계산용)
                if show_advanced:
                    fields.extend([
                        AdsInsights.Field.video_thruplay_watched_actions,
                        AdsInsights.Field.video_p75_watched_actions,
                        AdsInsights.Field.cost_per_action_type,
                    ])

                data = get_insights(level=level, date_preset=date_preset, fields=fields)

                if not data:
                    st.info('해당 기간에 데이터가 없어요. (광고 집행 이력 없음)')
                    return

                # 데이터 파싱
                total_impressions = 0
                total_clicks = 0
                total_spend = 0.0
                total_reach = 0

                rows = []
                learning_warnings = []

                for item in data:
                    impressions = int(item.get('impressions', 0) or 0)
                    clicks = int(item.get('clicks', 0) or 0)
                    spend = float(item.get('spend', 0) or 0)
                    ctr = float(item.get('ctr', 0) or 0)
                    cpm = float(item.get('cpm', 0) or 0)
                    cpc = float(item.get('cpc', 0) or 0)
                    frequency = float(item.get('frequency', 0) or 0)
                    reach = int(item.get('reach', 0) or 0)

                    total_impressions += impressions
                    total_clicks += clicks
                    total_spend += spend
                    total_reach += reach

                    name = (
                        item.get('campaign_name')
                        or item.get('adset_name')
                        or item.get('ad_name', '-')
                    )

                    row = {
                        '이름': name,
                        '노출': f'{impressions:,}',
                        '클릭': f'{clicks:,}',
                        'CTR': f'{ctr:.2f}%',
                        'CPM': f'{cpm:,.0f}원',
                        'CPC': f'{cpc:,.0f}원' if cpc > 0 else '-',
                        '지출': f'{spend:,.0f}원',
                    }

                    # ROAS
                    roas_list = item.get('purchase_roas', []) or []
                    if roas_list:
                        roas_val = float(roas_list[0].get('value', 0))
                        row['ROAS'] = f'{roas_val:.2f}'
                    else:
                        row['ROAS'] = '-'

                    if show_advanced:
                        # Frequency (피로도 지표)
                        freq_str = f'{frequency:.1f}'
                        if frequency > 4.0:
                            freq_str += ' (피로)'
                        row['Frequency'] = freq_str

                        # CPA 계산
                        actions = item.get('actions', []) or []
                        total_actions = sum(
                            int(a.get('value', 0))
                            for a in actions
                            if a.get('action_type') in ('purchase', 'lead', 'complete_registration', 'link_click')
                        )
                        if total_actions > 0 and spend > 0:
                            cpa = spend / total_actions
                            row['CPA'] = f'{cpa:,.0f}원'
                        else:
                            row['CPA'] = '-'

                        # Hook Rate (3초 영상 시청률) — 영상 광고일 때만
                        video_views = item.get('video_thruplay_watched_actions', []) or []
                        if video_views and impressions > 0:
                            views_3s = sum(int(v.get('value', 0)) for v in video_views)
                            hook_rate = (views_3s / impressions) * 100
                            row['Hook Rate'] = f'{hook_rate:.1f}%'
                        else:
                            row['Hook Rate'] = '-'

                        # Hold Rate (75% 영상 시청률)
                        video_p75 = item.get('video_p75_watched_actions', []) or []
                        if video_p75 and impressions > 0:
                            p75_views = sum(int(v.get('value', 0)) for v in video_p75)
                            hold_rate = (p75_views / impressions) * 100
                            row['Hold Rate'] = f'{hold_rate:.1f}%'
                        else:
                            row['Hold Rate'] = '-'

                        # 학습 단계 경고 (광고세트 레벨일 때)
                        if level == 'adset':
                            # 주당 전환 50건 미달 체크 (7일 기준)
                            weekly_conversions = sum(
                                int(a.get('value', 0))
                                for a in actions
                                if a.get('action_type') in ('purchase', 'lead', 'complete_registration')
                            )
                            adset_name = item.get('adset_name', '-')
                            if 0 < weekly_conversions < 50 and date_preset == 'last_7d':
                                learning_warnings.append(
                                    f'**{adset_name}**: 주간 전환 {weekly_conversions}건 (50건 미달 — 학습 미완료 가능성)'
                                )
                            if frequency > 4.0:
                                learning_warnings.append(
                                    f'**{adset_name}**: Frequency {frequency:.1f} (4.0 초과 — 크리에이티브 교체 권장)'
                                )

                    rows.append(row)

                # ---- 상단 요약 카드 ----
                if show_advanced:
                    m1, m2, m3, m4, m5 = st.columns(5)
                else:
                    m1, m2, m3, m4 = st.columns(4)
                    m5 = None

                m1.metric('총 노출', f'{total_impressions:,}')
                m2.metric('총 클릭', f'{total_clicks:,}')
                avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                m3.metric('평균 CTR', f'{avg_ctr:.2f}%')
                m4.metric('총 지출', f'{total_spend:,.0f}원')
                if m5 is not None:
                    avg_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
                    m5.metric('평균 CPM', f'{avg_cpm:,.0f}원')

                # ---- 학습 단계 경고 ----
                if learning_warnings:
                    st.divider()
                    st.subheader('학습 단계 알림')
                    for warn in learning_warnings:
                        st.warning(warn)

                # ---- 테이블 ----
                st.divider()
                st.dataframe(rows, use_container_width=True)

                # ---- 진단 가이드 ----
                if show_advanced:
                    with st.expander('지표 해석 가이드'):
                        st.markdown(
                            '**CTR이 낮다면** → 크리에이티브(이미지/헤드라인)가 관심을 못 끌고 있음\n\n'
                            '**CTR은 높은데 전환이 없다면** → 랜딩페이지 문제 (로딩 속도, 내용 불일치)\n\n'
                            '**CPM이 높다면** → 타겟이 너무 좁거나 경쟁이 심한 오디언스\n\n'
                            '**Frequency > 4.0** → 같은 사람에게 너무 많이 노출, 크리에이티브 교체 필요\n\n'
                            '**Hook Rate** → 영상 광고에서 처음 3초에 관심을 끌었는지 (25% 이상 양호)\n\n'
                            '**Hold Rate** → 영상의 75% 이상을 시청한 비율 (메시지 전달력 지표)'
                        )

            except Exception as e:
                error_msg = str(e)
                if 'API access blocked' in error_msg:
                    st.error('Meta API 접근이 차단되어 있어요. developers.facebook.com 에서 계정 확인을 완료해주세요.')
                else:
                    st.error(f'데이터 조회 실패: {error_msg}')
    else:
        st.info('위에서 기간과 레벨을 선택하고 [조회] 버튼을 눌러주세요.')
