@echo off
echo Installation des dépendances...
cd %~dp0
pip install -r requirements.txt
echo Exécution du script Python...
python main.py