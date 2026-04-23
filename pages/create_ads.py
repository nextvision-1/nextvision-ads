"""광고 생성 페이지 — CBO/ASC, Advantage+ 타겟팅, 페르소나 가이드 포함."""

import streamlit as st
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


# --- 페르소나 프리셋 (전자책 기반: 동일 제품도 타겟별 완전히 다른 컨셉) ---
PERSONA_PRESETS = {
    '직접 입력': {
        'headline': '',
        'message': '',
        'description': '직접 헤드라인과 광고 문구를 작성합니다.',
    },
    '건강 관심 부모': {
        'headline': '우리 아이 건강, 매일 간편하게 체크하세요',
        'message': '아이가 아플 때 빠른 대처가 중요합니다. 정확한 체온 측정으로 우리 가족 건강을 지켜보세요.',
        'description': '자녀 건강 관리에 관심 있는 30~45세 부모 타겟. 아이 건강·육아 관점에서 접근.',
    },
    '자기관리 직장인': {
        'headline': '바쁜 아침, 30초로 건강 상태 확인',
        'message': '출근 전 체온 한 번이면 컨디션 파악 끝. 스마트한 건강 관리의 시작.',
        'description': '건강 자기관리에 관심 있는 25~40세 직장인 타겟. 효율·시간 절약 관점.',
    },
    '부모님 선물': {
        'headline': '부모님께 드리는 건강한 안심',
        'message': '멀리 계신 부모님 건강이 걱정되시나요? 매일 쉽게 체크할 수 있는 선물을 보내드리세요.',
        'description': '부모님 건강 걱정하는 30~50세 자녀 타겟. 효도·선물·안심 관점.',
    },
    '헬스 & 피트니스': {
        'headline': '운동 전후 컨디션 체크, 프로처럼',
        'message': '오버트레이닝 방지의 첫 걸음. 체온 변화로 몸 상태를 정확히 파악하세요.',
        'description': '운동/헬스에 적극적인 20~35세 타겟. 퍼포먼스·데이터 관점.',
    },
}


def render():
    st.title('광고 생성')

    # 세션 상태 초기화
    for key in ('last_campaign_id', 'last_adset_id', '_create_msg'):
        if key not in st.session_state:
            st.session_state[key] = ''

    # 이전 생성 결과 메시지 표시 (rerun 후에도 유지)
    if st.session_state._create_msg:
        msg = st.session_state._create_msg
        st.session_state._create_msg = ''
        if msg.startswith('OK_CAMP:'):
            cid = msg[8:]
            st.success(f'캠페인 생성 완료! ID: {cid}')
            st.info('광고세트 탭으로 이동하면 캠페인 ID가 자동 입력되어 있어요.')
        elif msg.startswith('OK_ADSET:'):
            asid = msg[9:]
            st.success(f'광고세트 생성 완료! ID: {asid}')
            st.info('광고 탭으로 이동하면 광고세트 ID가 자동 입력되어 있어요.')
        elif msg.startswith('ERR:'):
            st.error(msg[4:])

    tab1, tab2, tab3 = st.tabs(['캠페인', '광고세트', '광고'])

    # ================================================================
    # 캠페인 탭 — CBO 기본 + ASC 추천
    # ================================================================
    with tab1:
        st.subheader('새 캠페인 만들기')
        if st.session_state.last_campaign_id:
            st.caption(f'최근 생성된 캠페인 ID: `{st.session_state.last_campaign_id}`')

        with st.form('campaign_form'):
            camp_name = st.text_input('캠페인 이름', placeholder='예: 봄 프로모션 캠페인')
            camp_objective = st.selectbox(
                '캠페인 목표',
                ['OUTCOME_TRAFFIC', 'OUTCOME_AWARENESS', 'OUTCOME_ENGAGEMENT',
                 'OUTCOME_LEADS', 'OUTCOME_APP_PROMOTION', 'OUTCOME_SALES'],
                format_func=lambda x: {
                    'OUTCOME_TRAFFIC': '트래픽',
                    'OUTCOME_AWARENESS': '인지도',
                    'OUTCOME_ENGAGEMENT': '참여',
                    'OUTCOME_LEADS': '리드',
                    'OUTCOME_APP_PROMOTION': '앱 프로모션',
                    'OUTCOME_SALES': '판매 (ASC 권장)',
                }.get(x, x),
            )

            col1, col2 = st.columns(2)
            with col1:
                budget_mode = st.selectbox(
                    '예산 최적화',
                    ['CBO', 'ABO'],
                    format_func=lambda x: {
                        'CBO': 'CBO - 캠페인 예산 최적화 (권장)',
                        'ABO': 'ABO - 광고세트별 예산',
                    }.get(x, x),
                    help='CBO: Meta AI가 성과 좋은 광고세트에 예산을 자동 분배합니다. 대부분의 경우 CBO가 더 효율적입니다.',
                )
            with col2:
                camp_status = st.selectbox(
                    '상태',
                    ['PAUSED', 'ACTIVE'],
                    format_func=lambda x: '일시중지' if x == 'PAUSED' else '활성',
                )

            # ASC 옵션 (판매 목적일 때만 의미 있지만, 폼 안에서 조건부 표시 불가하므로 항상 표시)
            use_asc = st.checkbox(
                'Advantage+ Shopping Campaign (ASC) 사용',
                value=False,
                help='판매(OUTCOME_SALES) 목적일 때 가장 효과적. Meta AI가 타겟팅부터 크리에이티브 배치까지 자동 최적화합니다.',
            )

            # CBO일 때 캠페인 예산 설정 옵션
            camp_daily_budget = st.number_input(
                'CBO 캠페인 일일 예산 (원, 0이면 광고세트에서 설정)',
                min_value=0, value=0, step=5000,
                help='CBO 모드에서 캠페인 전체 일일 예산. 0이면 각 광고세트에서 설정합니다.',
            )

            camp_submit = st.form_submit_button('캠페인 생성', type='primary')

        # 목표별 권장사항 표시 (폼 바깥)
        from create_campaign import get_recommendation
        rec = get_recommendation(camp_objective)
        st.info(f'**권장사항:** {rec["tip"]}')

        if camp_objective == 'OUTCOME_SALES' and not use_asc:
            st.warning('판매 목적이라면 ASC(Advantage+ Shopping Campaign)를 켜는 것을 강력히 권장합니다.')

        # 구조 가이드
        with st.expander('권장 캠페인 구조 (전문가 가이드)'):
            st.markdown(
                '**CBO 1개 캠페인 안에 최적 구조:**\n\n'
                '- 광고세트 4개 (각각 다른 크리에이티브 컨셉)\n'
                '- 각 광고세트에 크리에이티브 3~4개\n'
                '- 광고세트별 타겟이 겹쳐도 OK (Meta AI가 최적 분배)\n'
                '- 크리에이티브 컨셉은 반드시 달라야 함 (단순 색상/문구 변경 X)\n\n'
                '**판매 목적이라면:**\n'
                '- ASC(Advantage+ Shopping Campaign)를 기본으로 사용\n'
                '- ASC는 타겟팅~크리에이티브 배치까지 Meta AI가 전체 최적화\n'
                '- 기존 고객 데이터(커스텀 오디언스)가 있으면 성과 극대화'
            )

        if camp_submit:
            if not camp_name:
                st.warning('캠페인 이름을 입력해주세요.')
            elif use_asc and camp_objective != 'OUTCOME_SALES':
                st.warning('ASC는 판매(OUTCOME_SALES) 목적에서만 사용 가능합니다.')
            else:
                with st.spinner('캠페인 생성 중...'):
                    try:
                        from create_campaign import create_campaign
                        campaign = create_campaign(
                            name=camp_name,
                            objective=camp_objective,
                            status=camp_status,
                            budget_optimization=budget_mode,
                            use_asc=use_asc,
                            daily_budget=camp_daily_budget if camp_daily_budget > 0 else None,
                        )
                        cid = campaign.get_id()
                        st.session_state.last_campaign_id = cid
                        st.session_state._create_msg = f'OK_CAMP:{cid}'
                        st.rerun()
                    except Exception as e:
                        st.error(f'캠페인 생성 실패: {e}')

    # ================================================================
    # 광고세트 탭 — Advantage+ 타겟팅 + 학습 단계 안내
    # ================================================================
    with tab2:
        st.subheader('새 광고세트 만들기')
        if st.session_state.last_campaign_id:
            st.caption(f'최근 캠페인 ID: `{st.session_state.last_campaign_id}` (아래에 자동 입력됨)')

        # 학습 단계 안내 (항상 표시)
        with st.expander('머신러닝 학습 단계 안내 (중요)', expanded=False):
            st.markdown(
                '**광고세트 생성 후 반드시 지켜야 할 규칙:**\n\n'
                '1. **최소 3~5일은 수정하지 마세요** — 학습 단계에서 수정하면 처음부터 다시 학습\n'
                '2. **주당 전환 50건** 이상이어야 학습 완료 — 예산이 너무 적으면 학습 불가\n'
                '3. **예산 변경은 20% 이내** — 20% 초과 변경 시 학습 리셋\n'
                '4. **타겟/크리에이티브 추가·삭제 금지** — 학습 중에는 건드리지 마세요\n\n'
                '학습이 완료되면 Meta AI가 최적의 타겟에게 최적의 시간에 광고를 노출합니다.'
            )

        with st.form('adset_form'):
            adset_campaign_id = st.text_input(
                '캠페인 ID',
                value=st.session_state.last_campaign_id,
                placeholder='캠페인 탭에서 생성한 ID 입력',
            )
            adset_name = st.text_input('광고세트 이름', placeholder='예: Advantage+_전국타겟_컨셉A')

            # 타겟팅 모드 선택
            targeting_mode = st.selectbox(
                '타겟팅 모드',
                ['advantage_plus', 'suggestion', 'manual'],
                format_func=lambda x: {
                    'advantage_plus': 'Advantage+ (권장) — Meta AI 자동 타겟팅',
                    'suggestion': 'Advantage+ 제안형 — 수동 타겟 + AI 확장',
                    'manual': '수동 타겟팅 — 직접 연령/관심사 설정',
                }.get(x, x),
                help='Advantage+: Meta AI가 최적 타겟을 자동 탐색. 2024년 이후 대부분의 경우 가장 좋은 성과를 냅니다.',
            )

            col1, col2 = st.columns(2)
            with col1:
                daily_budget = st.number_input('일일 예산 (원)', min_value=1000, value=10000, step=1000)
                age_min = st.number_input(
                    '최소 연령',
                    min_value=13, max_value=65,
                    value=18,
                    help='Advantage+ 모드에서는 18-65세로 자동 설정됩니다.',
                )
            with col2:
                optimization = st.selectbox(
                    '최적화 목표',
                    ['LINK_CLICKS', 'REACH', 'OFFSITE_CONVERSIONS', 'IMPRESSIONS'],
                    format_func=lambda x: {
                        'LINK_CLICKS': '링크 클릭',
                        'REACH': '도달',
                        'OFFSITE_CONVERSIONS': '전환 (픽셀 필요)',
                        'IMPRESSIONS': '노출',
                    }.get(x, x),
                )
                age_max = st.number_input(
                    '최대 연령',
                    min_value=13, max_value=65,
                    value=65,
                    help='Advantage+ 모드에서는 18-65세로 자동 설정됩니다.',
                )

            adset_status = st.selectbox(
                '상태', ['PAUSED', 'ACTIVE'],
                format_func=lambda x: '일시중지' if x == 'PAUSED' else '활성',
                key='adset_status',
            )
            adset_submit = st.form_submit_button('광고세트 생성', type='primary')

        if adset_submit:
            adset_campaign_id = adset_campaign_id.strip()
            if not adset_campaign_id or not adset_name:
                st.warning('캠페인 ID와 광고세트 이름을 입력해주세요.')
            elif not adset_campaign_id.isdigit():
                st.warning(f'캠페인 ID는 숫자만 가능합니다. 현재 입력: "{adset_campaign_id}"')
            else:
                with st.spinner('광고세트 생성 중...'):
                    try:
                        from create_adset import create_adset
                        adset = create_adset(
                            campaign_id=adset_campaign_id,
                            name=adset_name,
                            daily_budget=daily_budget,
                            optimization_goal=optimization,
                            targeting_mode=targeting_mode,
                            age_min=age_min,
                            age_max=age_max,
                            status=adset_status,
                        )
                        asid = adset.get_id()
                        st.session_state.last_adset_id = asid
                        st.session_state._create_msg = f'OK_ADSET:{asid}'
                        st.rerun()
                    except Exception as e:
                        st.error(f'광고세트 생성 실패: {e}')

    # ================================================================
    # 광고 탭 — 페르소나 기반 크리에이티브 가이드
    # ================================================================
    with tab3:
        st.subheader('새 광고 만들기')
        if st.session_state.last_adset_id:
            st.caption(f'최근 광고세트 ID: `{st.session_state.last_adset_id}` (아래에 자동 입력됨)')

        # 크리에이티브 다양화 가이드
        with st.expander('크리에이티브 다양화 가이드 (핵심 전략)', expanded=False):
            st.markdown(
                '**동일 제품이라도 타겟별 완전히 다른 컨셉을 만드세요:**\n\n'
                '- 같은 제품 사진에 문구만 바꾸는 것은 Meta가 "같은 광고"로 인식\n'
                '- 페르소나(타겟 유형)별로 다른 관점·감정·상황으로 접근\n'
                '- 아래 페르소나 프리셋을 활용하거나, 직접 컨셉을 작성하세요\n\n'
                '**광고세트 1개당 3~4개의 서로 다른 크리에이티브**를 넣는 것이 이상적입니다.'
            )

        # 페르소나 선택
        persona = st.selectbox(
            '타겟 페르소나 프리셋',
            list(PERSONA_PRESETS.keys()),
            help='페르소나를 선택하면 해당 타겟에 맞는 헤드라인과 문구가 자동 입력됩니다. 자유롭게 수정 가능.',
        )
        selected_persona = PERSONA_PRESETS[persona]
        if persona != '직접 입력':
            st.caption(f'**{persona}**: {selected_persona["description"]}')

        st.info('이미지가 필요한 광고는 [이미지 스튜디오] 탭에서 AI로 생성할 수 있어요.')

        with st.form('ad_form'):
            ad_adset_id = st.text_input(
                '광고세트 ID',
                value=st.session_state.last_adset_id,
                placeholder='광고세트 탭에서 생성한 ID 입력',
            )
            ad_name = st.text_input('광고 이름', placeholder='예: 봄프로모션_건강부모_01')

            col1, col2 = st.columns(2)
            with col1:
                headline = st.text_input(
                    '헤드라인',
                    value=selected_persona['headline'],
                    placeholder='예: 매일 아침 건강 체크',
                )
                message = st.text_area(
                    '광고 문구',
                    value=selected_persona['message'],
                    placeholder='광고 본문 내용',
                    height=100,
                )
            with col2:
                link_url = st.text_input('랜딩 URL', value='https://nextvision.io.kr')
                cta_type = st.selectbox(
                    'CTA 버튼',
                    ['LEARN_MORE', 'SHOP_NOW', 'SIGN_UP', 'CONTACT_US', 'GET_OFFER'],
                    format_func=lambda x: {
                        'LEARN_MORE': '자세히 알아보기',
                        'SHOP_NOW': '지금 구매하기',
                        'SIGN_UP': '가입하기',
                        'CONTACT_US': '문의하기',
                        'GET_OFFER': '할인 받기',
                    }.get(x, x),
                )

            image_file = st.file_uploader('광고 이미지 업로드', type=['jpg', 'jpeg', 'png'])
            ad_status = st.selectbox(
                '상태', ['PAUSED', 'ACTIVE'],
                format_func=lambda x: '일시중지' if x == 'PAUSED' else '활성',
                key='ad_status',
            )
            ad_submit = st.form_submit_button('광고 생성', type='primary')

        if ad_submit:
            if not ad_adset_id or not ad_name or not headline:
                st.warning('광고세트 ID, 광고 이름, 헤드라인을 입력해주세요.')
            elif not image_file:
                st.warning('광고 이미지를 업로드해주세요.')
            else:
                with st.spinner('광고 생성 중...'):
                    try:
                        import tempfile
                        from create_ad import create_image_ad

                        suffix = '.' + image_file.name.split('.')[-1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(image_file.getvalue())
                            tmp_path = tmp.name

                        ad = create_image_ad(
                            adset_id=ad_adset_id,
                            image_path=tmp_path,
                            headline=headline,
                            message=message or headline,
                            ad_name=ad_name,
                            link_url=link_url,
                            cta_type=cta_type,
                            status=ad_status,
                        )
                        st.success(f'광고 생성 완료! ID: {ad.get_id()}')
                        st.info('같은 광고세트에 다른 페르소나의 크리에이티브도 추가해보세요 (3~4개 권장).')
                    except Exception as e:
                        st.error(f'광고 생성 실패: {e}')
