"""
assign_page.py - 시스템 사용자에게 페이지 권한 할당 + 진단

config.py 의 PAGE_ID, SYSTEM_USER_ID 를 사용합니다.
config.py 가 이미 FacebookAdsApi 를 초기화 해 두기 때문에 별도 init 이 필요 없어요.

사용 예:
    from assign_page import assign_system_user_to_page, diagnose_page
    assign_system_user_to_page()
    diagnose_page()  # 페이지-광고계정 연결 상태 진단
"""

from typing import Optional

import requests
from facebook_business.adobjects.page import Page

from config import PAGE_ID, SYSTEM_USER_ID, AD_ACCOUNT_ID, ACCESS_TOKEN


DEFAULT_TASKS = ['MANAGE', 'ADVERTISE', 'ANALYZE', 'CREATE_CONTENT']


def assign_system_user_to_page(
    page_id: Optional[str] = None,
    system_user_id: Optional[str] = None,
    tasks: Optional[list] = None,
) -> dict:
    """시스템 사용자에게 페이지 권한 부여.

    Args:
        page_id: 페이지 ID (None 이면 config 값)
        system_user_id: 시스템 사용자 ID (None 이면 config 값)
        tasks: 부여할 태스크 권한 (기본 ['MANAGE', 'ADVERTISE', 'ANALYZE', 'CREATE_CONTENT'])
    """
    page_id = page_id or PAGE_ID
    system_user_id = system_user_id or SYSTEM_USER_ID
    tasks = tasks or DEFAULT_TASKS

    if not page_id:
        raise ValueError('PAGE_ID 가 설정되어 있지 않아요 (.env 확인)')
    if not system_user_id:
        raise ValueError('SYSTEM_USER_ID 가 설정되어 있지 않아요 (.env 확인)')

    print('[페이지 권한] Page ' + str(page_id) + ' -> User ' + str(system_user_id))
    print('[페이지 권한] tasks: ' + ', '.join(tasks))

    page = Page(page_id)
    result = page.create_assigned_user(
        params={
            'user': system_user_id,
            'tasks': tasks,
        }
    )
    print('[완료] 페이지 권한 할당 완료')
    return result


def diagnose_page(
    page_id: Optional[str] = None,
    ad_account_id: Optional[str] = None,
) -> None:
    """페이지-광고계정 연결 상태 진단."""
    page_id = page_id or PAGE_ID
    ad_account_id = ad_account_id or AD_ACCOUNT_ID

    print('=== 페이지-광고계정 진단 ===\n')

    # 1) 페이지 기본 정보
    print('[1] 페이지 정보 조회...')
    try:
        r = requests.get(
            f'https://graph.facebook.com/v25.0/{page_id}',
            params={'access_token': ACCESS_TOKEN, 'fields': 'name,is_published,verification_status'}
        )
        data = r.json()
        if 'error' in data:
            print(f'  [실패] {data["error"]["message"]}')
        else:
            print(f'  이름: {data.get("name", "?")}')
            print(f'  게시됨: {data.get("is_published", "?")}')
    except Exception as e:
        print(f'  [에러] {e}')

    # 2) 광고 계정이 사용할 수 있는 페이지 목록
    print('\n[2] 광고 계정에서 사용 가능한 페이지 목록...')
    try:
        r = requests.get(
            f'https://graph.facebook.com/v25.0/{ad_account_id}/promote_pages',
            params={'access_token': ACCESS_TOKEN, 'fields': 'id,name'}
        )
        data = r.json()
        if 'error' in data:
            print(f'  [실패] {data["error"]["message"]}')
        else:
            pages = data.get('data', [])
            if not pages:
                print('  [경고] 광고 계정에 연결된 페이지가 없습니다!')
                print('  -> 비즈니스 설정에서 페이지를 광고 계정에 할당해야 합니다.')
            else:
                found = False
                for p in pages:
                    marker = ' <-- 현재 페이지' if p['id'] == page_id else ''
                    print(f'  - {p["name"]} (ID: {p["id"]}){marker}')
                    if p['id'] == page_id:
                        found = True
                if not found:
                    print(f'\n  [경고] PAGE_ID={page_id} 가 이 광고 계정의 사용 가능 페이지에 없습니다!')
                    print('  -> 이것이 광고 크리에이티브 생성 실패 원인입니다.')
                else:
                    print(f'\n  [OK] PAGE_ID={page_id} 가 광고 계정에서 사용 가능합니다.')

    except Exception as e:
        print(f'  [에러] {e}')

    # 3) 시스템 사용자 권한 확인
    print('\n[3] 시스템 사용자 페이지 권한...')
    try:
        r = requests.get(
            f'https://graph.facebook.com/v25.0/{page_id}/assigned_users',
            params={'access_token': ACCESS_TOKEN, 'fields': 'id,name,tasks'}
        )
        data = r.json()
        if 'error' in data:
            print(f'  [실패] {data["error"]["message"]}')
        else:
            users = data.get('data', [])
            if not users:
                print('  페이지에 할당된 사용자가 없습니다.')
            for u in users:
                print(f'  - {u.get("name", "?")} (ID: {u["id"]})')
                print(f'    tasks: {u.get("tasks", [])}')
    except Exception as e:
        print(f'  [에러] {e}')

    print('\n=== 진단 완료 ===')


if __name__ == '__main__':
    import sys
    if '--diagnose' in sys.argv:
        diagnose_page()
    else:
        try:
            assign_system_user_to_page()
        except Exception as e:
            print(f'[경고] 페이지 권한 할당 실패: {e}')
            print('       비즈니스 설정에서 수동으로 할당해야 할 수 있습니다.')
        print()
        diagnose_page()
