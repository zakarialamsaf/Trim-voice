# Trim a Voice — Suppression du silence en fin d'enregistrement

Script Python pour supprimer automatiquement le silence en fin de fichier audio. Utile quand l'orateur a oublié d'arrêter l'enregistrement (ex. : 30 s de parole dans un fichier de 5 min).

**Fonctionne pour :**
- Voix **normale** (parole à volume standard)
- Voix **chuchotée** (whisper)

## Prérequis

- **Python 3.8+**
- **ffmpeg** (requis par pydub pour manipuler les fichiers audio)

## Installation

### Option rapide (Windows)

```bash
setup.bat       # Invite de commandes
# ou
.\setup.ps1     # PowerShell
```

### Installation manuelle

1. **Aller dans le dossier du projet**

   ```bash
   cd 7Sam
   ```

2. **Créer un environnement virtuel (recommandé)**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux / macOS
   ```

3. **Installer les dépendances**

   ```bash
   pip install -r requirements.txt
   ```

4. **Installer ffmpeg**

**Windows :**

- Télécharger : https://ffmpeg.org/download.html (ou via winget : `winget install ffmpeg`)
- Ajouter `ffmpeg` au PATH système

**Linux :**

```bash
sudo apt install ffmpeg   # Debian/Ubuntu
sudo dnf install ffmpeg   # Fedora
```

**macOS :**

```bash
brew install ffmpeg
```

## Utilisation

### Commande de base

```bash
python trim_speech.py <fichier ou dossier> [fichier ou dossier] ...
```

### Exemples

```bash
# Un seul fichier (ex: 25.wav de 8 min → garde la parole, supprime le reste)
python trim_speech.py "NormalSpeech/25.wav"

# Voix NORMALE (seuil par défaut -40 dB)
python trim_speech.py NormalVoice
python trim_speech.py data/training/voix_normale

# Voix CHUCHOTÉE (seuil plus sensible -45 à -50 dB)
python trim_speech.py WhisperSpeech -t -48

# Plusieurs dossiers (mixte normal + whisper — utiliser -48 pour tout garder)
python trim_speech.py NormalVoice WhisperSpeech -t -48

# Si -t ne coupe rien (bruit de fond constant) : utiliser -e (méthode énergie)
python trim_speech.py "./NormalSpeech/25.wav" -e

# Idéal : lancer séparément avec le bon seuil pour chaque type
python trim_speech.py NormalVoice                    # voix normale
python trim_speech.py WhisperSpeech -t -48           # chuchoté

# Sauvegarder dans un nouveau dossier sans modifier les originaux
python trim_speech.py WhisperSpeech --no-in-place -o output_trimmed

# Test sans modification (dry-run)
python trim_speech.py WhisperSpeech --dry-run
```

### Choix du seuil (`-t`)

| Type de voix | Seuil recommandé |
|--------------|-------------------|
| **Normale**  | `-40` (défaut)    |
| **Chuchotée**| `-45` à `-50`     |

## Options

| Option | Description |
|--------|-------------|
| `-t`, `--silence-thresh` | Seuil de silence en dB. Normal : -40 (défaut). Chuchoté : -45 à -50 |
| `--min-silence-len` | Durée minimale de silence pour être considéré (ms, défaut : 500) |
| `--keep-silence` | Silence à garder après la parole (ms, défaut : 300) |
| `-o`, `--output` | Dossier de sortie (avec `--no-in-place`) |
| `--no-in-place` | Sauvegarder dans un dossier de sortie au lieu de modifier les fichiers |
| `--dry-run` | Afficher les fichiers sans les modifier |
| `-e`, `--energy` | Méthode énergie (quand le seuil dB ne suffit pas, ex. bruit constant) |
| `--debug` | Afficher l'analyse (avec `-e`) |

## Format supporté

- `.wav` / `.wave`
- `.mp3`

## Structure du projet

```
trim-a-voice/
├── trim_speech.py      # Script principal
├── requirements.txt   # Dépendances Python
├── setup.bat          # Installation rapide (Windows CMD)
├── setup.ps1          # Installation rapide (PowerShell)
└── README.md          # Ce fichier
```
