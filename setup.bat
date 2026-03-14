@echo off
echo === Trim Speech - Installation ===
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH.
    echo Installez Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Créer et activer l'environnement virtuel
if not exist "venv" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
)
echo Activation de venv...
call venv\Scripts\activate.bat

REM Installer les dépendances
echo Installation des dependances...
pip install -r requirements.txt

echo.
echo === Installation terminee ===
echo.
echo Pour utiliser: venv\Scripts\activate puis python trim_speech.py WhisperSpeech
echo.
pause
