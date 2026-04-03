"""Training loop for a single Whisper model."""

import gc
import logging
import os
import time

import numpy as np
import torch
from jiwer import cer, wer
from transformers import (
    EarlyStoppingCallback,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from .data import DataCollator, WhisperedDataset
from .model import freeze_encoder_layers, load_model_and_processor, log_model_info
from .utils import normalize_text

logger = logging.getLogger(__name__)


def train_model(model_id, output_dir, train_records, val_records, test_records,
                training_config, sample_rate, freeze_layers):
    """Fine-tune a single Whisper model.

    Returns:
        Tuple of (best_wer, best_model_path).
    """
    logger.info("")
    logger.info("=" * 65)
    logger.info("  MODEL  : %s", model_id)
    logger.info("  Train  : %d  Val: %d  Test: %d",
                len(train_records), len(val_records), len(test_records))
    logger.info("=" * 65)

    os.makedirs(output_dir, exist_ok=True)

    model, processor = load_model_and_processor(model_id)
    frozen_count = freeze_encoder_layers(model, freeze_layers)
    log_model_info(model, freeze_layers, frozen_count)

    train_ds = WhisperedDataset(train_records, processor, sample_rate)
    val_ds = WhisperedDataset(val_records, processor, sample_rate)
    collator = DataCollator(processor=processor)

    def compute_metrics(pred):
        """Compute corpus-level WER and CER."""
        pred_ids = pred.predictions
        if isinstance(pred_ids, tuple):
            pred_ids = pred_ids[0]
        pred_ids = np.array(pred_ids)
        if len(pred_ids.shape) == 3:
            pred_ids = np.argmax(pred_ids, axis=-1)

        label_ids = pred.label_ids
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id

        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        pred_norm = [normalize_text(p) for p in pred_str]
        label_norm = [normalize_text(l) for l in label_str]

        pairs = [(r, h) for r, h in zip(label_norm, pred_norm) if r.strip()]
        if not pairs:
            return {"wer": 1.0, "cer": 1.0}
        refs, hyps = zip(*pairs)
        return {
            "wer": wer(list(refs), list(hyps)),
            "cer": cer(list(refs), list(hyps)),
        }

    args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        max_steps=training_config["max_steps"],
        learning_rate=training_config["learning_rate"],
        warmup_ratio=training_config["warmup_ratio"],
        lr_scheduler_type=training_config["lr_scheduler_type"],
        per_device_train_batch_size=training_config["per_device_train_batch_size"],
        per_device_eval_batch_size=training_config["per_device_eval_batch_size"],
        gradient_accumulation_steps=training_config["gradient_accumulation_steps"],
        gradient_checkpointing=True,
        bf16=training_config["bf16"],
        fp16=training_config["fp16"],
        eval_strategy="steps",
        eval_steps=training_config["eval_steps"],
        save_strategy="steps",
        save_steps=training_config["save_steps"],
        logging_steps=training_config["logging_steps"],
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        predict_with_generate=True,
        generation_max_length=225,
        push_to_hub=False,
        remove_unused_columns=False,
        report_to="none",
        dataloader_num_workers=training_config["dataloader_num_workers"],
        seed=training_config["seed"],
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        compute_metrics=compute_metrics,
        tokenizer=processor.feature_extractor,
        callbacks=[EarlyStoppingCallback(
            early_stopping_patience=training_config["early_stopping_patience"],
        )],
    )

    start = time.time()
    trainer.train()
    elapsed = time.time() - start

    best_wer = trainer.state.best_metric
    logger.info("Training done!")
    logger.info("   Best WER : %.4f", best_wer)
    logger.info("   Time     : %.1f min", elapsed / 60)

    if train_ds.load_errors > 0:
        logger.warning("   %d audio load errors during training", train_ds.load_errors)
    if val_ds.load_errors > 0:
        logger.warning("   %d audio load errors during validation", val_ds.load_errors)

    best_path = os.path.join(output_dir, "best_model")
    trainer.save_model(best_path)
    processor.save_pretrained(best_path)
    logger.info("   Saved    : %s", best_path)

    del model, trainer, train_ds, val_ds
    torch.cuda.empty_cache()
    gc.collect()

    return best_wer, best_path
