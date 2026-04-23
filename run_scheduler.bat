@echo off
chcp 65001 >nul
title 메타 광고 자동화 스케줄러

echo ==========================================
echo   메타 광고 자동화 스케줄러
echo   30분 간격으로 자동 실행됩니다
echo   종료하려면 Ctrl+C 를 누르세요
echo ==========================================
echo.

cd /d "%~dp0"
python scheduler.py --interval 30

pause
