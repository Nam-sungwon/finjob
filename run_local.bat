@echo off
py -m pip install -r requirements.txt
py collector\collector.py
py -m http.server 8000
