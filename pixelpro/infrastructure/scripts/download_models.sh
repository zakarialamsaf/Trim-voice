#!/bin/bash
# Download AI model weights to /app/models
# Run once before starting workers, or bake into Docker image

set -e
MODELS_DIR="${MODELS_DIR:-/app/models}"
mkdir -p "$MODELS_DIR"

echo "Downloading Real-ESRGAN weights..."
wget -q -O "$MODELS_DIR/RealESRGAN_x4plus.pth" \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"

wget -q -O "$MODELS_DIR/RealESRGAN_x2plus.pth" \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"

echo "Downloading GFPGAN weights..."
wget -q -O "$MODELS_DIR/GFPGANv1.4.pth" \
  "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth"

echo "Downloading U2Net (rembg) weights..."
# rembg downloads automatically on first use to ~/.u2net/
# Force download here:
python3 -c "from rembg import new_session; new_session('u2net'); print('U2Net ready')"

echo "All models downloaded successfully."
