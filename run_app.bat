@echo off
SET APP_ROOT = "C:\Users\pycharmProjects\kapi"
call "%APP_ROOT%\.venv\Scripts\activate.bat"
cd "%APP_ROOT%"
python app.py
python reply_bot.py