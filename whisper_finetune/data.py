"""Dataset loading, splitting, and collation."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Union

import librosa
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset as TorchDataset

logger = logging.getLogger(__name__)


class WhisperedDataset(TorchDataset):
    """PyTorch dataset that loads audio on-the-fly and tokenizes transcripts."""

    def __init__(self, records, processor, sample_rate):
        self.records = records
        self.processor = processor
        self.sample_rate = sample_rate
        self.load_errors = 0

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        s = self.records[idx]
        try:
            audio, _ = librosa.load(s["path"], sr=self.sample_rate, mono=True)
            audio = np.clip(audio, -1.0, 1.0)
        except Exception as e:
            self.load_errors += 1
            logger.warning(
                "Failed to load %s: %s (total errors: %d)",
                s["path"], e, self.load_errors,
            )
            audio = np.zeros(self.sample_rate, dtype=np.float32)

        feats = self.processor.feature_extractor(
            audio, sampling_rate=self.sample_rate, return_tensors="pt"
        )
        labels = self.processor.tokenizer(
            str(s["transcript"]), return_tensors="pt",
            truncation=True, max_length=225,
        ).input_ids

        return {
            "input_features": feats.input_features.squeeze(0),
            "labels": labels.squeeze(0),
        }


@dataclass
class DataCollator:
    """Pads input features and labels for Seq2Seq training."""

    processor: Any

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]):
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(
            input_features, return_tensors="pt"
        )
        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(
            label_features, return_tensors="pt"
        )
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all():
            labels = labels[:, 1:]
        batch["labels"] = labels
        return batch


def load_and_split(manifest_path, val_size, test_size, random_seed):
    """Load the manifest CSV and perform a stratified 3-way split.

    Returns:
        Tuple of (train_records, val_records, test_records) as lists of dicts.
    """
    df = pd.read_csv(manifest_path)
    df = df.dropna(subset=["transcript", "path"])
    df = df[df["transcript"].str.strip() != ""]
    df = df[df["path"].apply(os.path.exists)].reset_index(drop=True)

    # 3-way stratified split: train / val / test
    train_df, temp_df = train_test_split(
        df, test_size=(val_size + test_size),
        random_state=random_seed, stratify=df["source"],
    )
    relative_test_size = test_size / (val_size + test_size)
    val_df, test_df = train_test_split(
        temp_df, test_size=relative_test_size,
        random_state=random_seed, stratify=temp_df["source"],
    )

    train_records = train_df.to_dict("records")
    val_records = val_df.to_dict("records")
    test_records = test_df.to_dict("records")

    logger.info("=" * 60)
    logger.info("Total   : %d", len(df))
    logger.info("Train   : %d (%.0f%%)", len(train_records), len(train_records) / len(df) * 100)
    logger.info("Val     : %d (%.0f%%)", len(val_records), len(val_records) / len(df) * 100)
    logger.info("Test    : %d (%.0f%%)", len(test_records), len(test_records) / len(df) * 100)
    logger.info("\n%s", df["source"].value_counts().to_string())
    logger.info("=" * 60)

    return train_records, val_records, test_records
