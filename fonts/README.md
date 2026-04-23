# fonts/ - 광고 이미지 생성용 폰트

## Pretendard 설치 방법

이 프로젝트는 기본적으로 **Pretendard** 오픈소스 한글 폰트를 사용합니다.
상업 사용 가능 (SIL Open Font License).

### 다운로드

1. https://github.com/orioncactus/pretendard/releases 접속
2. 최신 릴리즈의 `Pretendard-X.X.X.zip` 다운로드
3. 압축 해제 후 `public/static/` 폴더에서 아래 3개 파일을 이 `fonts/` 폴더로 복사:
   - `Pretendard-Regular.otf`
   - `Pretendard-SemiBold.otf`
   - `Pretendard-Bold.otf`

### 설치 확인

```
python image_composer.py
```

실행 시 "폰트 로드 성공: Pretendard" 메시지가 나오면 OK.

## 폴백

Pretendard 파일이 없으면 자동으로 시스템의 **맑은 고딕**(Windows 기본)을 사용합니다.
SaaS로 고객에게 배포할 때는 Pretendard 번들 권장 (라이선스 명시).
