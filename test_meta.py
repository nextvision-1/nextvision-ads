"""
test_meta.py - 메타 API 연결 테스트

config.py 에서 토큰/계정ID 를 자동으로 불러와 연결을 확인합니다.

실행:
    python test_meta.py
"""

from config import account


def main():
    print('=== 메타 API 연결 테스트 ===')
    try:
        account_info = account.api_get(fields=['name', 'account_status', 'currency', 'timezone_name'])
        print('[성공] 연결 완료')
        print('광고 계정 이름:', account_info.get('name'))
        print('계정 상태:', account_info.get('account_status'))
        print('통화:', account_info.get('currency'))
        print('시간대:', account_info.get('timezone_name'))
    except Exception as e:
        print('[실패]', e)


if __name__ == '__main__':
    main()
