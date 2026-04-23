"""
scheduler.py - 30분 간격 자동 실행 스케줄러

APScheduler 를 사용해서 아래 작업을 주기적으로 실행합니다:
  1) auto_optimize.run_optimization() - 광고세트 자동 최적화
  2) get_insights.get_campaign_insights() - 성과 데이터 수집 + 로그 저장

실행:
    python scheduler.py                  # 기본 30분 간격
    python scheduler.py --interval 60    # 60분 간격
    python scheduler.py --once           # 1회만 실행 (스케줄러 없이)

요구 패키지:
    pip install apscheduler
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path 에 추가 (어디서 실행하든 import 가능)
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# --- 로깅 설정 ---
LOG_DIR = PROJECT_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            LOG_DIR / 'scheduler.log',
            encoding='utf-8',
            mode='a',
        ),
    ],
)
logger = logging.getLogger('scheduler')


def save_report(data: dict, report_type: str) -> Path:
    """리포트를 JSON 파일로 저장."""
    reports_dir = PROJECT_DIR / 'reports'
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{report_type}_{timestamp}.json'
    filepath = reports_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    logger.info('리포트 저장: %s', filepath)
    return filepath


def job_optimize():
    """자동 최적화 작업."""
    logger.info('=== 자동 최적화 시작 ===')
    try:
        from auto_optimize import run_optimization
        summary = run_optimization(
            include_paused=False,
            dry_run=False,
        )
        save_report(summary, 'optimize')
        total_actions = (
            len(summary.get('paused', []))
            + len(summary.get('boosted', []))
            + len(summary.get('warnings', []))
        )
        logger.info(
            '최적화 완료 - 중지: %d, 증액: %d, 경고: %d, 정상: %d',
            len(summary.get('paused', [])),
            len(summary.get('boosted', [])),
            len(summary.get('warnings', [])),
            len(summary.get('normal', [])),
        )
    except Exception as e:
        logger.error('최적화 실패: %s', e, exc_info=True)


def job_collect_insights():
    """성과 데이터 수집 작업."""
    logger.info('=== 성과 데이터 수집 시작 ===')
    try:
        from get_insights import get_insights

        # 캠페인 레벨 최근 7일
        campaign_data = get_insights(level='campaign', date_preset='last_7d')

        report = {
            'collected_at': datetime.now().isoformat(),
            'date_preset': 'last_7d',
            'campaigns': [],
        }
        for item in campaign_data:
            report['campaigns'].append(dict(item))

        save_report(report, 'insights')
        logger.info('성과 수집 완료 - 캠페인 %d개', len(campaign_data))
    except Exception as e:
        logger.error('성과 수집 실패: %s', e, exc_info=True)


def run_all_jobs():
    """모든 작업을 순차 실행."""
    logger.info('=' * 50)
    logger.info('스케줄 작업 실행: %s', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info('=' * 50)
    job_collect_insights()
    job_optimize()
    logger.info('전체 작업 완료\n')


def start_scheduler(interval_minutes: int = 30):
    """APScheduler 로 반복 실행 시작."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        logger.error('APScheduler 가 설치되어 있지 않아요.')
        logger.error('설치: pip install apscheduler')
        sys.exit(1)

    scheduler = BlockingScheduler()

    # 시작 즉시 1회 실행
    logger.info('스케줄러 시작 - %d분 간격 실행', interval_minutes)
    logger.info('종료하려면 Ctrl+C 를 누르세요.\n')
    run_all_jobs()

    # 이후 interval 간격으로 반복
    scheduler.add_job(
        run_all_jobs,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='main_job',
        name=f'{interval_minutes}분 간격 자동 실행',
        max_instances=1,
        coalesce=True,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info('스케줄러 종료')
        scheduler.shutdown(wait=False)


def main():
    parser = argparse.ArgumentParser(
        description='메타 광고 자동화 스케줄러',
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='실행 간격 (분, 기본: 30)',
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='스케줄러 없이 1회만 실행',
    )
    args = parser.parse_args()

    if args.once:
        logger.info('[1회 실행 모드]')
        run_all_jobs()
    else:
        start_scheduler(interval_minutes=args.interval)


if __name__ == '__main__':
    main()
