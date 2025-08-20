@echo off
cd /d C:\Users\Home\pycharmProjects\kapi   <-- 본인의 프로젝트 경로로 수정
call .venv\Scripts\activate.bat
python update_symbols.py