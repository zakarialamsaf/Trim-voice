"""Allow running as: python -m whisper_finetune"""

import logging
import os

from .config import build_training_config, load_config, parse_args
from .data import load_and_split
from .evaluation import evaluate_on_test_set
from .training import train_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Entry point: load data, train both models, evaluate on test set."""
    args = parse_args()
    cfg = load_config(args.config)
    training_config = build_training_config(cfg)

    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    models = cfg["models"]

    # Load & split data
    train_records, val_records, test_records = load_and_split(
        cfg["paths"]["manifest"],
        data_cfg["val_size"],
        data_cfg["test_size"],
        data_cfg["seed"],
    )

    # Train each model
    best_paths = {}
    for m in models:
        best_paths[m["id"]] = os.path.join(m["output_dir"], "best_model")

    if not args.skip_training:
        for m in models:
            best_wer, best_path = train_model(
                model_id=m["id"],
                output_dir=m["output_dir"],
                train_records=train_records,
                val_records=val_records,
                test_records=test_records,
                training_config=training_config,
                sample_rate=data_cfg["sample_rate"],
                freeze_layers=model_cfg["freeze_layers"],
            )
            best_paths[m["id"]] = best_path
            logger.info("%s done | Best WER: %.4f", m["id"], best_wer)

    # Evaluate on held-out test set
    if not args.skip_eval:
        # Use first model's processor_id for all (matches original notebook behavior)
        processor_id = models[0]["id"]
        evaluate_on_test_set(
            test_records=test_records,
            model_configs=[
                {
                    "name": m["id"].split("/")[-1],
                    "processor_id": processor_id,
                    "model_path": best_paths[m["id"]],
                }
                for m in models
            ],
            sample_rate=data_cfg["sample_rate"],
            use_bf16=training_config["bf16"],
            use_fp16=training_config["fp16"],
        )


if __name__ == "__main__":
    main()
