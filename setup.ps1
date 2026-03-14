# Trim Speech - Installation (PowerShell)
Write-Host "=== Trim Speech - Installation ===" -ForegroundColor Cyan
Write-Host ""

# Vérifier Python
try {
    $null = python --version 2>&1
} catch {
    Write-Host "ERREUR: Python n'est pas installe ou pas dans le PATH." -ForegroundColor Red
    Write-Host "Installez Python depuis https://www.python.org/downloads/"
    exit 1
}

# Créer l'environnement virtuel
if (-not (Test-Path "venv")) {
    Write-Host "Creation de l'environnement virtuel..."
    python -m venv venv
}

# Activer et installer
Write-Host "Installation des dependances..."
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

Write-Host ""
Write-Host "=== Installation terminee ===" -ForegroundColor Green
Write-Host ""
Write-Host "Pour utiliser: .\venv\Scripts\Activate.ps1 ; python trim_speech.py WhisperSpeech"
