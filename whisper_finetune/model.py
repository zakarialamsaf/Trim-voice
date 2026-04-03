"""Model loading and encoder layer freezing."""

import logging
import re

from transformers import WhisperForConditionalGeneration, WhisperProcessor

logger = logging.getLogger(__name__)


def load_model_and_processor(model_id):
    """Load a Whisper model and its processor from HuggingFace.

    Returns:
        Tuple of (model, processor).
    """
    processor = WhisperProcessor.from_pretrained(model_id)
    model = WhisperForConditionalGeneration.from_pretrained(model_id)

    model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(
        language="en", task="transcribe"
    )
    model.config.suppress_tokens = []

    return model, processor


def freeze_encoder_layers(model, num_layers_to_freeze):
    """Freeze the first N encoder layers using explicit layer index matching.

    Returns:
        Number of frozen parameters.
    """
    frozen_count = 0
    for name, param in model.model.encoder.named_parameters():
        match = re.search(r'layers\.(\d+)', name)
        if match and int(match.group(1)) < num_layers_to_freeze:
            param.requires_grad = False
            frozen_count += 1
    return frozen_count


def log_model_info(model, freeze_layers, frozen_count):
    """Log trainable vs total parameter counts."""
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    logger.info(
        "  Encoder 0-%d frozen (%d params) | Trainable: %.1fM / %.1fM",
        freeze_layers - 1, frozen_count, trainable / 1e6, total / 1e6,
    )
