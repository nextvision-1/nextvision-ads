"""자동 최적화 페이지."""

import streamlit as st
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def render():
    st.title('자동 최적화')
    st.caption('CPA/ROAS/Frequency 기반으로 광고세트를 자동 최적화합니다.')

    # 기준값 설정
    st.subheader('최적화 기준값')
    col1, col2, col3 = st.columns(3)
    with col1:
        target_cpa = st.number_input('목표 CPA (원)', min_value=1000, value=10000, step=1000)
        min_spend = st.number_input('최소 지출 기준 (원)', min_value=0, value=5000, step=1000)
    with col2:
        target_roas = st.number_input('목표 ROAS', min_value=0.1, value=3.0, step=0.1)
        budget_increase = st.number_input('예산 증액 비율', min_value=1.0, max_value=2.0, value=1.2, step=0.05)
    with col3:
        max_frequency = st.number_input('최대 Frequency', min_value=1.0, value=4.0, step=0.5)
        date_preset = st.selectbox(
            '평가 기간',
            ['last_3d', 'last_7d', 'last_14d', 'last_30d'],
            index=1,
            format_func=lambda x: {
                'last_3d': '최근 3일',
                'last_7d': '최근 7일',
                'last_14d': '최근 14일',
                'last_30d': '최근 30일',
            }.get(x, x),
        )

    st.divider()

    # 규칙 설명
    with st.expander('최적화 규칙 설명'):
        st.markdown(
            '- **저성과 중지**: CPA가 목표의 150% 초과 시 광고세트 자동 중지\n'
            '- **고성과 증액**: ROAS가 목표 초과 시 예산 자동 증액\n'
            '- **피로도 경고**: Frequency가 기준 초과 시 크리에이티브 교체 권장\n'
            '- **판단 보류**: 지출이 최소 기준 미달 시 데이터 부족으로 보류'
        )

    # 실행 버튼
    col_dry, col_real = st.columns(2)
    with col_dry:
        dry_run = st.button('리포트만 보기 (Dry Run)', use_container_width=True)
    with col_real:
        real_run = st.button('실제 최적화 적용', type='primary', use_container_width=True)

    if dry_run or real_run:
        is_dry = dry_run
        mode_text = '[DRY RUN] 리포트만' if is_dry else '[실제 적용]'

        with st.spinner(f'{mode_text} 최적화 실행 중...'):
            try:
                from auto_optimize import run_optimization
                summary = run_optimization(
                    target_cpa=target_cpa,
                    target_roas=target_roas,
                    max_frequency=max_frequency,
                    min_spend=min_spend,
                    budget_increase=budget_increase,
                    date_preset=date_preset,
                    include_paused=True,
                    dry_run=is_dry,
                )

                # 결과 표시
                st.subheader('최적화 결과')

                r1, r2, r3, r4, r5 = st.columns(5)
                r1.metric('중지', len(summary.get('paused', [])))
                r2.metric('증액', len(summary.get('boosted', [])))
                r3.metric('경고', len(summary.get('warnings', [])))
                r4.metric('보류', len(summary.get('skipped', [])))
                r5.metric('정상', len(summary.get('normal', [])))

                # 중지된 광고세트
                paused = summary.get('paused', [])
                if paused:
                    st.warning('저성과로 중지된 광고세트:')
                    for p in paused:
                        st.write(f"- {p['adset']} (CPA: {p['cpa']:,.0f}원)")

                # 증액된 광고세트
                boosted = summary.get('boosted', [])
                if boosted:
                    st.success('고성과로 예산 증액된 광고세트:')
                    for b in boosted:
                        st.write(f"- {b['adset']} (ROAS: {b['roas']:.2f}, {b['old_budget']:,}원 -> {b['new_budget']:,}원)")

                # 경고
                warnings = summary.get('warnings', [])
                if warnings:
                    st.info('피로도 경고:')
                    for w in warnings:
                        st.write(f"- {w['adset']}: {w['reason']}")

                if not paused and not boosted and not warnings and not summary.get('normal', []):
                    st.info('점검할 광고세트가 없어요.')

                if is_dry:
                    st.caption('Dry Run 모드: 실제 광고세트에는 변경이 적용되지 않았습니다.')

            except Exception as e:
                error_msg = str(e)
                if 'API access blocked' in error_msg:
                    st.error('Meta API 접근이 차단되어 있어요. developers.facebook.com 에서 계정 확인을 완료해주세요.')
                else:
                    st.error(f'최적화 실행 실패: {error_msg}')
