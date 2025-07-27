@echo off
echo Windows環境でのデータベーステストを実行します...
echo.

REM Python仮想環境の確認
python --version
echo.

REM uvが利用可能な場合
if exist "uv.lock" (
    echo uvを使用してテストを実行します...
    uv run python test_windows.py
) else (
    REM 通常のPython環境
    echo 通常のPython環境でテストを実行します...
    python test_windows.py
)

echo.
echo テスト完了！
pause
