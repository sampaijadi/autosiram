@echo off
title Python CMS Editor
echo Starting premium CMS Editor...
echo Your browser will open in 2 seconds.

:: Launch the browser in a new thread
start "" "http://localhost:5000"

:: Start the python server
python editor.py

pause
