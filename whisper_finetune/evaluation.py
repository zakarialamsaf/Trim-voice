"""Test-set evaluation for fine-tuned models."""

import gc
import logging

import librosa
import numpy as np
import torch
from jiwer import cer, wer
from transformers import WhisperForConditionalGeneration, WhisperProcessor

from .utils import normalize_text

logger = logging.getLogger(__name__)


def evaluate_on_test_set(test_records, model_configs, sample_rate, use_bf16, use_fp16):
    """Evaluate fine-tuned models on the held-out test set.

    Args:
        test_records: List of test sample dicts with 'path' and 'transcript' keys.
        model_configs: List of dicts with keys 'name', 'processor_id', 'model_path'.
        sample_rate: Audio sample rate.
        use_bf16: Whether to use bfloat16.
        use_fp16: Whether to use float16.

    Returns:
        Dict mapping model name to {'wer': float, 'cer': float, 'samples': int}.
    """
    logger.info("=" * 65)
    logger.info("EVALUATING ON HELD-OUT TEST SET")
    logger.info("=" * 65)
    logger.info("  Test samples: %d", len(test_records))

    dtype = torch.bfloat16 if use_bf16 else (torch.float16 if use_fp16 else torch.float32)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load all models
    models = []
    for cfg in model_configs:
        processor = WhisperProcessor.from_pretrained(cfg["processor_id"])
        model = WhisperForConditionalGeneration.from_pretrained(
            cfg["model_path"], torch_dtype=dtype
        ).to(device).eval()
        models.append({
            "name": cfg["name"],
            "processor": processor,
            "model": model,
            "refs": [],
            "hyps": [],
        })

    eval_errors = 0
    for i, sample in enumerate(test_records, 1):
        try:
            audio, _ = librosa.load(sample["path"], sr=sample_rate, mono=True)
            audio = np.clip(audio, -1.0, 1.0)
            ref = normalize_text(sample["transcript"])
            if not ref.strip():
                continue

            for m in models:
                inp = m["processor"](
                    audio, sampling_rate=sample_rate, return_tensors="pt"
                ).input_features.to(device, dtype=dtype)
                with torch.no_grad():
                    decoded = m["processor"].batch_decode(
                        m["model"].generate(inp), skip_special_tokens=True
                    )[0]
                m["refs"].append(ref)
                m["hyps"].append(normalize_text(decoded))

            if i % 100 == 0:
                logger.info("  %d/%d evaluated...", i, len(test_records))

        except Exception as e:
            eval_errors += 1
            logger.warning("Eval error on sample %d: %s", i, e)

    # Corpus-level WER/CER
    results = {}
    logger.info("")
    logger.info("=" * 65)
    logger.info("RESULTS (corpus-level, held-out test set)")
    logger.info("=" * 65)

    for m in models:
        w = wer(m["refs"], m["hyps"])
        c = cer(m["refs"], m["hyps"])
        results[m["name"]] = {"wer": w, "cer": c, "samples": len(m["refs"])}
        logger.info("  %-20s WER: %.1f%%  CER: %.1f%%  (%d samples)",
                     m["name"], w * 100, c * 100, len(m["refs"]))

    if eval_errors > 0:
        logger.info("  Skipped %d samples due to errors", eval_errors)

    # Compare if exactly two models
    if len(models) == 2:
        w1 = results[models[0]["name"]]["wer"]
        w2 = results[models[1]["name"]]["wer"]
        diff = w1 - w2
        if abs(diff) < 0.01:
            logger.info("\nBoth models are comparable - prefer distil-whisper for speed.")
        elif diff > 0:
            logger.info("\nWINNER: %s (WER %.1f%% lower)", models[1]["name"], diff * 100)
        else:
            logger.info("\nWINNER: %s (WER %.1f%% lower)", models[0]["name"], -diff * 100)

    logger.info("=" * 65)

    # Cleanup
    for m in models:
        del m["model"]
    torch.cuda.empty_cache()
    gc.collect()

    return results
