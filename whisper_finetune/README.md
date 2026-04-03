# Whisper Fine-Tuning — Two Models Pipeline

Fine-tunes two Whisper models on a whispered speech dataset with stratified train/val/test split, encoder layer freezing, early stopping, and corpus-level WER/CER evaluation.

## Models

| # | Model ID | Description |
|---|----------|-------------|
| 1 | `openai/whisper-small.en` | Standard Whisper small (English) |
| 2 | `distil-whisper/distil-small.en` | Distilled Whisper small (English) |

## Project Structure

```
whisper_finetune/
├── config.yaml      # All paths, hyperparameters, and settings
├── config.py        # Loads YAML config + CLI flags
├── data.py          # Dataset, collator, stratified 3-way split
├── model.py         # Model/processor loading, encoder freezing
├── training.py      # Seq2SeqTrainer loop for one model
├── evaluation.py    # Test-set inference + WER/CER reporting
├── utils.py         # Text normalization
├── __main__.py      # Orchestrates the full pipeline
├── requirements.txt # Python dependencies
└── README.md
train.py             # Entry point
```

## Setup

```bash
pip install -r whisper_finetune/requirements.txt
```

## Configuration

Edit `whisper_finetune/config.yaml`:

```yaml
paths:
  manifest: "./normal2whisper_work/manifest.csv"

models:
  - id: "openai/whisper-small.en"
    output_dir: "./whisper-small-finetuned_v4"
  - id: "distil-whisper/distil-small.en"
    output_dir: "./distil-whisper-finetuned_v4"

data:
  sample_rate: 16000
  val_size: 0.15
  test_size: 0.15
  seed: 42

model:
  freeze_layers: 4

training:
  max_steps: 2000
  learning_rate: 1.0e-5
  warmup_ratio: 0.1
  lr_scheduler: "cosine"
  train_batch_size: 4
  eval_batch_size: 4
  gradient_accumulation_steps: 4
  eval_steps: 200
  save_steps: 200
  logging_steps: 50
  dataloader_num_workers: 2
  early_stopping_patience: 3
```

## Usage

```bash
# Train both models + evaluate on test set
python train.py

# Use a custom config file
python train.py --config /path/to/my_config.yaml

# Skip training, only evaluate existing checkpoints
python train.py --skip-training

# Train only, skip test-set evaluation
python train.py --skip-eval
```

## Pipeline Steps

1. **Load & Split** — Reads the manifest CSV, filters invalid rows, performs a stratified 3-way split (70/15/15) by `source` column
2. **Train Model 1** — Fine-tunes `whisper-small.en` with encoder layers 0-3 frozen, early stopping (patience=3), saves best checkpoint
3. **Train Model 2** — Same process for `distil-small.en`
4. **Evaluate** — Runs both best checkpoints on the held-out test set, reports corpus-level WER and CER, declares a winner

## Manifest Format

The input CSV must have these columns:

| Column | Description |
|--------|-------------|
| `path` | Absolute path to the audio file |
| `transcript` | Ground-truth transcription |
| `source` | Category label (used for stratified splitting) |

## Output

Each model saves to its `output_dir`:

```
whisper-small-finetuned_v4/
├── best_model/          # Best checkpoint (model + processor)
├── checkpoint-200/
├── checkpoint-400/
└── ...
```

## Requirements

- Python 3.9+
- CUDA GPU (bf16 or fp16 auto-detected; falls back to fp32 on CPU)
- ~4 GB VRAM per model with batch_size=4 and gradient checkpointing
