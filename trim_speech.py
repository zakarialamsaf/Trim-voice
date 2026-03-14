#!/usr/bin/env python3
"""
Script pour garder uniquement la parole et supprimer le silence en fin d'enregistrement.
Utile quand l'orateur a oublié d'arrêter l'enregistrement (ex: 30s de parole dans un fichier de 5min).
"""

import argparse
import array
import math
from pathlib import Path
from typing import Optional

try:
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
except ImportError:
    print("Installation requise: pip install pydub")
    print("Sur Windows, ffmpeg doit aussi être installé: https://ffmpeg.org/download.html")
    exit(1)


def _rms(samples: array.array) -> float:
    """RMS (énergie) d'un segment d'échantillons."""
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def _find_speech_end_energy(
    audio: AudioSegment,
    chunk_ms: int = 500,
    speech_ref_sec: float = 60.0,
    ratio_thresh: float = 0.5,
    debug: bool = False,
) -> int:
    """
    Trouve la fin de la parole en comparant l'énergie par chunk.
    Utilise les N premières secondes comme référence "parole", puis cherche
    où l'énergie tombe et reste basse.
    """
    sample_width = audio.sample_width
    array_type = {1: "b", 2: "h", 4: "i"}.get(sample_width, "h")
    samples = array.array(array_type)
    samples.frombytes(audio.raw_data)
    frame_rate = audio.frame_rate
    channels = audio.channels
    frames_per_chunk = int(frame_rate * channels * chunk_ms / 1000)

    speech_ref_chunks = int(speech_ref_sec * 1000 / chunk_ms)
    chunk_energies = []

    for i in range(0, len(samples), frames_per_chunk):
        chunk = samples[i : i + frames_per_chunk]
        if len(chunk) < frames_per_chunk // 2:
            break
        chunk_energies.append(_rms(chunk))

    if not chunk_energies:
        return len(audio)

    # Référence : 90e percentile des premiers chunks (niveau PAROLE, pas bruit)
    ref_chunks = chunk_energies[: min(speech_ref_chunks, len(chunk_energies))]
    ref_chunks_sorted = sorted(ref_chunks)
    idx = int(len(ref_chunks_sorted) * 0.90)
    ref = ref_chunks_sorted[max(0, idx - 1)] if ref_chunks_sorted else 0
    if ref < 1:
        return len(audio)

    if debug:
        tail = chunk_energies[-20:]  # 20 derniers chunks = 10 sec
        print(f"  [DEBUG] ref(90p)={ref:.0f} seuil={ref*ratio_thresh:.0f}")
        print(f"  [DEBUG] Énergie fin (10 dernières sec): {[int(x) for x in tail]}")
        print(f"  [DEBUG] Min/max global: {min(chunk_energies):.0f} / {max(chunk_energies):.0f}")

    # Chercher la DERNIÈRE chunk avec énergie "parole" (en partant de la fin)
    thresh = ref * ratio_thresh
    for i in range(len(chunk_energies) - 1, -1, -1):
        if chunk_energies[i] >= thresh:
            end_ms = min((i + 2) * chunk_ms + 300, len(audio))  # +2 pour inclure le chunk, +300ms marge
            if debug:
                print(f"  [DEBUG] ref={ref:.0f} seuil={thresh:.0f}")
                print(f"  [DEBUG] Dernière parole à chunk {i} -> découpe à {end_ms/1000:.1f}s")
            return end_ms

    if debug:
        print(f"  [DEBUG] ref={ref:.0f} - aucune parole détectée")
    return len(audio)


def _audio_format(path: str) -> str:
    """Retourne le format pydub à partir de l'extension (normalise .wave → wav)."""
    suffix = Path(path).suffix.lower()
    return "wav" if suffix in (".wav", ".wave") else (suffix[1:] or "wav")


def trim_trailing_silence(
    audio_path: str,
    output_path: Optional[str] = None,
    silence_thresh_db: int = -40,
    min_silence_len_ms: int = 500,
    keep_silence_ms: int = 300,
    use_energy: bool = False,
    debug: bool = False,
) -> tuple[float, float]:
    """
    Détecte la parole et supprime le silence en fin de fichier.
    
    Returns:
        (durée_originale, durée_trimée) en secondes
    """
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0

    if use_energy:
        # Méthode énergie : compare l'énergie par chunk (pour bruit de fond constant)
        end_ms = _find_speech_end_energy(audio, debug=debug)
    else:
        # Méthode seuil dB : segments non-silencieux
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len_ms,
            silence_thresh=silence_thresh_db,
            seek_step=10,
        )

        if not nonsilent_ranges:
            if output_path and output_path != audio_path:
                audio.export(output_path, format=_audio_format(audio_path))
            return duration_sec, duration_sec

        end_ms = min(nonsilent_ranges[-1][1] + keep_silence_ms, len(audio))
    trimmed = audio[:end_ms]
    trimmed_duration_sec = len(trimmed) / 1000.0

    out = output_path or audio_path
    trimmed.export(out, format=_audio_format(audio_path))

    return duration_sec, trimmed_duration_sec


def process_path(
    path: str,
    output_folder: Optional[str] = None,
    in_place: bool = True,
    silence_thresh_db: int = -40,
    min_silence_len_ms: int = 500,
    keep_silence_ms: int = 300,
    dry_run: bool = False,
    use_energy: bool = False,
    debug: bool = False,
) -> None:
    """Traite un fichier ou tous les fichiers WAV/MP3 d'un dossier."""
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"Erreur: n'existe pas: {path}")
        return

    # Fichier unique
    if path_obj.is_file():
        if path_obj.suffix.lower() not in (".wav", ".wave", ".mp3"):
            print(f"Erreur: format non supporté: {path}")
            return
        audio_files = [path_obj]
        folder_path = path_obj.parent
    else:
        folder_path = path_obj
        audio_files = (
            list(folder_path.rglob("*.wav"))
            + list(folder_path.rglob("*.wave"))
            + list(folder_path.rglob("*.mp3"))
        )

    out_path = Path(output_folder) if output_folder else folder_path
    if not in_place and output_folder:
        out_path.mkdir(parents=True, exist_ok=True)
    total_saved = 0.0

    for i, audio_file in enumerate(audio_files, 1):
        rel = audio_file.relative_to(folder_path)
        if in_place:
            dest = str(audio_file)
        else:
            dest = str(out_path / rel)
            Path(dest).parent.mkdir(parents=True, exist_ok=True)

        if dry_run:
            print(f"[DRY-RUN] {rel}")
            continue

        try:
            orig, trimmed = trim_trailing_silence(
                str(audio_file),
                dest if not in_place else None,
                silence_thresh_db=silence_thresh_db,
                min_silence_len_ms=min_silence_len_ms,
                keep_silence_ms=keep_silence_ms,
                use_energy=use_energy,
                debug=debug,
            )
            saved = orig - trimmed
            total_saved += saved
            status = f"  {orig:.1f}s -> {trimmed:.1f}s (-{saved:.1f}s)"
            print(f"[{i}/{len(audio_files)}] {rel} {status}")
        except Exception as e:
            print(f"[ERREUR] {rel}: {e}")

    if not dry_run and total_saved > 0:
        print(f"\nTemps total supprimé: {total_saved:.1f} secondes")


def main():
    parser = argparse.ArgumentParser(
        description="Garde la parole et supprime le silence en fin d'enregistrement."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Fichier(s) ou dossier(s) audio (WAV/MP3)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Dossier de sortie (sinon modification in-place)",
    )
    parser.add_argument(
        "--no-in-place",
        action="store_true",
        help="Sauvegarder dans un dossier de sortie (utiliser -o)",
    )
    parser.add_argument(
        "-t", "--silence-thresh",
        type=int,
        default=-40,
        help="Seuil de silence en dB (défaut: -40). Plus bas = plus sensible (pour whisper: -45 à -50)",
    )
    parser.add_argument(
        "--min-silence-len",
        type=int,
        default=500,
        help="Durée minimale de silence pour être considéré (ms, défaut: 500)",
    )
    parser.add_argument(
        "--keep-silence",
        type=int,
        default=300,
        help="Silence à garder après la parole (ms, défaut: 300)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher les fichiers sans les modifier",
    )
    parser.add_argument(
        "-e", "--energy",
        action="store_true",
        help="Méthode énergie (pour bruit de fond constant, quand -t ne suffit pas)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Afficher l'analyse énergie (premier fichier seulement)",
    )

    args = parser.parse_args()
    in_place = not args.no_in_place and not args.output

    for path in args.paths:
        print(f"\n=== {path} ===")
        process_path(
            path,
            output_folder=args.output,
            in_place=in_place,
            silence_thresh_db=args.silence_thresh,
            min_silence_len_ms=args.min_silence_len,
            keep_silence_ms=args.keep_silence,
            dry_run=args.dry_run,
            use_energy=args.energy,
            debug=args.debug,
        )


if __name__ == "__main__":
    main()
