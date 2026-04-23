# 넥스트비전 메타 광고 자동화 SaaS

메타(페이스북/인스타그램) Marketing API 기반 광고 자동화 플랫폼.
내부 운영 + 외부 고객 구독 판매 겸용.

## 현재 단계

- [x] 메타 API 연동 (토큰, 앱, 비즈니스 포트폴리오, 광고 계정, 시스템 사용자, 페이지)
- [x] 캠페인 자동 생성 (`create_campaign.py`)
- [x] 광고세트 자동 생성 (`create_adset.py`)
- [x] 크리에이티브 + 광고 생성 (`create_ad.py`) - 이미지 업로드 지원
- [x] 성과 데이터 수집 (`get_insights.py`)
- [x] 자동 최적화 규칙 (`auto_optimize.py`)
- [x] 페이지 권한 할당 (`assign_page.py`)
- [x] 환경변수 분리 (`.env` + `config.py`)
- [x] **AI 이미지 자동 생성** (`image_generator.py` - OpenAI gpt-image-1)
- [x] **Pillow 텍스트/CTA 오버레이** (`image_composer.py` - Pretendard 폰트)
- [x] **end-to-end 파이프라인** (`ad_image_pipeline.py`)
- [x] **전체 스크립트 `config.py` 기반 리팩토링 완료** (토큰 하드코딩 제거)
- [x] **30분 간격 스케줄러** (`scheduler.py` + `run_scheduler.bat`)
- [ ] 대시보드 UI
- [ ] 멀티테넌시 (고객사별 토큰/광고 계정 관리)
- [ ] 결제/구독 시스템

## 설치

```bash
pip install -r requirements.txt
```

## 초기 설정

1. `.env.example` 을 `.env` 로 복사 후 실제 값 입력:

   ```bash
   cp .env.example .env
   ```

   필수 항목:
   - `META_ACCESS_TOKEN` - 메타 Marketing API 토큰
   - `META_AD_ACCOUNT_ID` - `act_` 접두어 포함
   - `META_PAGE_ID` - 페이스북 페이지 ID
   - `OPENAI_API_KEY` - AI 이미지 생성용 (https://platform.openai.com/api-keys)

2. **Pretendard 폰트 설치** (광고 이미지 텍스트용):
   - https://github.com/orioncactus/pretendard/releases 에서 최신 버전 다운로드
   - `Pretendard-Regular.otf`, `Pretendard-SemiBold.otf`, `Pretendard-Bold.otf` 를 `fonts/` 폴더로 복사
   - 없으면 시스템 맑은 고딕으로 자동 폴백 (Windows)

3. 연결 테스트:

   ```bash
   python config.py          # 메타 API + OpenAI 설정 확인
   python image_composer.py  # 이미지 오버레이 테스트 (AI 없이)
   ```

## 파일 구조

```
.
├── .env                     # 실제 토큰/ID (Git 제외)
├── .env.example             # 템플릿
├── .gitignore
├── config.py                # 공통 설정 + API 초기화
├── requirements.txt
├── fonts/                   # Pretendard 폰트 (직접 설치)
│   └── README.md
├── ad_images/               # 생성된 이미지 저장 (자동 생성)
│
├── test_meta.py             # API 연결 테스트
├── assign_page.py           # 시스템 사용자에게 페이지 권한 할당
├── create_campaign.py       # 캠페인 생성
├── create_adset.py          # 광고세트 생성
├── create_ad.py             # 크리에이티브 + 광고 생성 (이미지 지원)
├── get_insights.py          # 성과 데이터 조회
├── auto_optimize.py         # 자동 최적화 규칙
│
├── image_generator.py       # AI 이미지 생성 (OpenAI gpt-image-1)
├── image_composer.py        # Pillow 텍스트/CTA 오버레이
├── ad_image_pipeline.py     # end-to-end (상품정보 → 광고 등록)
│
├── scheduler.py             # 30분 간격 자동 실행 (APScheduler)
├── run_scheduler.bat        # Windows 더블클릭 실행용
├── logs/                    # 스케줄러 실행 로그 (자동 생성)
└── reports/                 # 수집된 성과/최적화 리포트 JSON (자동 생성)
```

## 전체 자동화 파이프라인 사용법

### 단 한 번 호출로 광고 이미지 생성 + 업로드

```python
from ad_image_pipeline import create_full_ad

ad = create_full_ad(
    # 상품 정보 (AI 프롬프트용)
    product_name='스마트 체온계',
    industry='건강기능식품',
    target_audience='30-40대 주부',
    style='밝고 깨끗한 미니멀',
    mood='신뢰감 있는',

    # 광고 카피 (텍스트 오버레이)
    headline='매일 아침 건강 체크',
    subtext='정확한 측정, 30초 완료',
    cta_text='자세히 보기',

    # 메타 광고 설정
    ad_name='봄프로모션_체온계_01',
    adset_id='120245636876020166',
    link_url='https://nextvision.io.kr/thermo',
    cta_type='LEARN_MORE',
    status='PAUSED',          # 안전을 위해 기본 PAUSED

    # 이미지 품질/규격
    quality='medium',          # low/medium/high/auto
    ad_format='feed_square',   # feed_square/feed_portrait/feed_landscape/story_reel
)
print('광고 ID:', ad.get_id())
```

파이프라인이 자동으로:
1. AI로 배경 이미지 생성 (gpt-image-1)
2. Pretendard 폰트로 헤드라인/서브텍스트/CTA 오버레이
3. 메타 광고 계정에 크리에이티브 + 광고 업로드 (PAUSED)

### 이미 만든 이미지 사용 (AI 건너뛰기)

```python
ad = create_full_ad(
    product_name='...',
    industry='...',
    headline='...',
    ad_name='...',
    adset_id='...',
    skip_ai_use_image='./my_images/banner.jpg',  # 여기만 추가
)
```

### 이미지 생성만 (광고 업로드 없이)

```python
from image_generator import build_prompt, generate_ad_background
from image_composer import compose_ad

prompt = build_prompt(
    product_name='스마트 체온계',
    industry='건강기능식품',
    target_audience='30-40대 주부',
)
bg = generate_ad_background(prompt, size='1024x1024', quality='medium')
final = compose_ad(bg, headline='매일 아침 건강 체크', subtext='30초 측정', cta_text='자세히 보기')
```

## 비용 참고 (OpenAI gpt-image-1)

| quality | 1장 비용 (USD) | 월 100장 기준 |
|---------|---------------|--------------|
| low     | ~$0.02        | ~$2          |
| medium  | ~$0.07        | ~$7          |
| high    | ~$0.19        | ~$19         |

SaaS 가격 정책 참고용. A/B 테스트는 low 로 많이 뽑고, 성과 좋은 것만 high로 재생성하는 전략 추천.

## 개별 스크립트 사용법 (리팩토링 후)

모든 스크립트가 `config.py` 를 임포트하므로 `.env` 만 세팅하면 바로 실행돼요.

```python
# 연결 테스트
python test_meta.py

# 캠페인 생성 (함수로도, 직접 실행으로도 가능)
from create_campaign import create_campaign
c = create_campaign(name='봄 프로모션', objective='OUTCOME_TRAFFIC')

# 광고세트 생성
from create_adset import create_adset
s = create_adset(campaign_id=c.get_id(), name='20-45세', daily_budget=10000)

# 성과 조회
from get_insights import get_campaign_insights, print_insights
print_insights(get_campaign_insights('last_7d'))

# 자동 최적화 (dry_run 먼저 돌려보고 실제 적용)
from auto_optimize import run_optimization
run_optimization(dry_run=True)

# 시스템 사용자에 페이지 권한 부여
from assign_page import assign_system_user_to_page
assign_system_user_to_page()
```

## 스케줄러 사용법

```bash
# APScheduler 설치 (처음 한 번)
pip install apscheduler

# 방법 1: bat 파일 더블클릭
run_scheduler.bat

# 방법 2: 직접 실행
python scheduler.py                  # 기본 30분 간격
python scheduler.py --interval 60    # 60분 간격
python scheduler.py --once           # 1회만 실행 (테스트용)
```

30분마다 자동으로 성과 데이터를 수집하고 최적화 규칙을 적용합니다. 실행 로그는 `logs/scheduler.log`, 리포트는 `reports/` 폴더에 JSON으로 저장됩니다. 종료하려면 `Ctrl+C`.

## 남은 TODO

- Streamlit 기반 대시보드 UI

## 보안 주의사항

- `.env` 는 절대 Git에 커밋하지 마세요 (`.gitignore` 에 포함됨)
- Access Token 을 코드에 직접 입력하지 마세요
- SaaS 로 판매할 때는 고객사별 토큰을 DB 에 암호화 저장하는 구조가 필요합니다
- OpenAI API Key 는 사용량 알림 설정해두세요 (악용 방지)
