"""Configuration: loads from config.yaml, with optional CLI overrides."""

import argparse
import logging
from pathlib import Path

import torch
import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"


def _load_yaml(path):
    """Read and parse a YAML config file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args():
    """Parse CLI args. Only --config and workflow flags; everything else lives in YAML."""
    parser = argparse.ArgumentParser(
        description="Fine-tune two Whisper models on a whispered speech dataset.",
    )
    parser.add_argument(
        "--config", type=str, default=str(DEFAULT_CONFIG_PATH),
        help="Path to YAML config file (default: whisper_finetune/config.yaml).",
    )
    parser.add_argument("--skip-training", action="store_true",
                        help="Skip training and only run evaluation.")
    parser.add_argument("--skip-eval", action="store_true",
                        help="Skip test-set evaluation after training.")
    return parser.parse_args()


def load_config(config_path=None):
    """Load the full configuration from YAML.

    Returns:
        dict with keys: paths, models, data, model, training.
    """
    path = config_path or str(DEFAULT_CONFIG_PATH)
    cfg = _load_yaml(path)
    logger.info("Loaded config from %s", path)
    return cfg


def build_training_config(cfg):
    """Build the trainer-level config dict with auto-detected precision.

    Args:
        cfg: The full YAML config dict.

    Returns:
        dict ready to pass into Seq2SeqTrainingArguments.
    """
    use_bf16 = torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False
    use_fp16 = (not use_bf16) and torch.cuda.is_available()

    t = cfg["training"]
    d = cfg["data"]

    config = {
        "max_steps":                   t["max_steps"],
        "learning_rate":               t["learning_rate"],
        "warmup_ratio":                t["warmup_ratio"],
        "lr_scheduler_type":           t["lr_scheduler"],
        "per_device_train_batch_size": t["train_batch_size"],
        "per_device_eval_batch_size":  t["eval_batch_size"],
        "gradient_accumulation_steps": t["gradient_accumulation_steps"],
        "eval_steps":                  t["eval_steps"],
        "save_steps":                  t["save_steps"],
        "logging_steps":               t["logging_steps"],
        "bf16":                        use_bf16,
        "fp16":                        use_fp16,
        "dataloader_num_workers":      t["dataloader_num_workers"],
        "seed":                        d["seed"],
        "early_stopping_patience":     t["early_stopping_patience"],
    }

    logger.info("Config:")
    logger.info("  Manifest    : %s", cfg["paths"]["manifest"])
    logger.info("  Models      : %s", ", ".join(m["id"] for m in cfg["models"]))
    logger.info("  Val size    : %.0f%%", d["val_size"] * 100)
    logger.info("  Test size   : %.0f%%", d["test_size"] * 100)
    logger.info("  BF16        : %s", use_bf16)
    logger.info("  FP16        : %s", use_fp16)
    logger.info("  Max steps   : %d", t["max_steps"])
    logger.info("  Freeze      : encoder layers 0-%d", cfg["model"]["freeze_layers"] - 1)

    return config
