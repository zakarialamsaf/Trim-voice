# Trim a Voice — Remove Trailing Silence from Recordings

A Python script to automatically remove trailing silence from audio files. Useful when the speaker forgot to stop the recording (e.g. 30s of speech in a 5-minute file).

**Works for:**
- **Normal voice** (standard volume speech)
- **Whispered voice** (whisper)

## Requirements

- **Python 3.8+**
- **ffmpeg** (required by pydub to handle audio files)

## Installation

### Quick setup (Windows)

```bash
setup.bat       # Command Prompt
# or
.\setup.ps1     # PowerShell
```

### Manual installation

1. **Go to the project folder**

   ```bash
   cd trim-a-voice
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux / macOS
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install ffmpeg**

**Windows:**

- Download: https://ffmpeg.org/download.html (or via winget: `winget install ffmpeg`)
- Add `ffmpeg` to the system PATH

**Linux:**

```bash
sudo apt install ffmpeg   # Debian/Ubuntu
sudo dnf install ffmpeg   # Fedora
```

**macOS:**

```bash
brew install ffmpeg
```

## Usage

### Basic command

```bash
python trim_speech.py <file or folder> [file or folder] ...
```

### Examples

```bash
# Single file (e.g. 25.wav of 8 min → keeps speech, removes the rest)
python trim_speech.py "NormalSpeech/25.wav"

# Normal voice (default threshold -40 dB)
python trim_speech.py NormalSpeech
python trim_speech.py data/training/normal_voice

# Whispered voice (more sensitive threshold -45 to -50 dB)
python trim_speech.py WhisperSpeech -t -48

# Multiple folders (mixed normal + whisper — use -48 to keep everything)
python trim_speech.py NormalSpeech WhisperSpeech -t -48

# If -t doesn't cut anything (constant background noise): use -e (energy method)
python trim_speech.py "./NormalSpeech/25.wav" -e

# Best practice: run separately with the right threshold for each type
python trim_speech.py NormalSpeech                   # normal voice
python trim_speech.py WhisperSpeech -t -48           # whispered

# Save to a new folder without modifying the originals
python trim_speech.py WhisperSpeech --no-in-place -o output_trimmed

# Test without modifying files (dry-run)
python trim_speech.py WhisperSpeech --dry-run
```

### Threshold guide (`-t`)

| Voice type   | Recommended threshold |
|--------------|-----------------------|
| **Normal**   | `-40` (default)       |
| **Whispered**| `-45` to `-50`        |

## Options

| Option | Description |
|--------|-------------|
| `-t`, `--silence-thresh` | Silence threshold in dB. Normal: -40 (default). Whispered: -45 to -50 |
| `--min-silence-len` | Minimum silence duration to be considered (ms, default: 500) |
| `--keep-silence` | Silence to keep after speech (ms, default: 300) |
| `-o`, `--output` | Output folder (used with `--no-in-place`) |
| `--no-in-place` | Save to output folder instead of modifying files in place |
| `--dry-run` | List files without modifying them |
| `-e`, `--energy` | Energy method (when dB threshold is not enough, e.g. constant background noise) |
| `--debug` | Show energy analysis (with `-e`) |

## Supported formats

- `.wav` / `.wave`
- `.mp3`

## Project structure

```
trim-a-voice/
├── trim_speech.py      # Main script
├── requirements.txt    # Python dependencies
├── setup.bat           # Quick setup (Windows CMD)
├── setup.ps1           # Quick setup (PowerShell)
└── README.md           # This file
```
