@echo off
echo Installation des dépendances...
taskkill /IM chrome.exe /F
cd %~dp0
echo Installation des dépendances...
pip install -r requirements.txt
echo Exécution du script Python...
python main.py
taskkill /IM chrome.exe /F