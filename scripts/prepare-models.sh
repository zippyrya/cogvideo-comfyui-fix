#!/bin/bash
# prepare-models.sh — Download & organize models for CogVideo ComfyUI
# Run ONCE locally or in a build container to prepare /models directory
# Then COPY /models into Docker image at /models/

set -e

MODELS_DIR="/models"
mkdir -p "$MODELS_DIR"/{checkpoints,vae,clip_vision,ipadapter,CogVideo/loras,diffusion_models,text_encoders}

echo "=== Preparing CogVideo models at $MODELS_DIR ==="

# 1. CogVideoX-2B (base text-to-video)
# huggingface-cli download THUDM/CogVideoX-2b --local-dir "$MODELS_DIR/CogVideo/CogVideoX-2b"

# 2. CogVideoX-5B (higher quality)
# huggingface-cli download THUDM/CogVideoX-5b --local-dir "$MODELS_DIR/CogVideo/CogVideoX-5b"

# 3. CogVideoX-Fun (image-to-video, inpainting)
# huggingface-cli download THUDM/CogVideoX-Fun-V1.1-2b-InP --local-dir "$MODELS_DIR/CogVideo/CogVideoX-Fun-2b-InP"
# huggingface-cli download THUDM/CogVideoX-Fun-V1.1-5b-InP --local-dir "$MODELS_DIR/CogVideo/CogVideoX-Fun-5b-InP"

# 4. VAE (required)
# huggingface-cli download THUDM/CogVideoX-2b --include "vae/*" --local-dir "$MODELS_DIR/vae/"

# 5. T5-XXL Text Encoder (required)
# huggingface-cli download google/t5-v1_1-xxl --local-dir "$MODELS_DIR/text_encoders/t5-v1_1-xxl"

# 6. CLIP Vision (for IPAdapter)
# huggingface-cli download openai/clip-vit-large-patch14 --local-dir "$MODELS_DIR/clip_vision/"

# 7. Symlink checkpoints → diffusion_models for CogVideo
ln -sfn "$MODELS_DIR/checkpoints" "$MODELS_DIR/diffusion_models"

echo "=== Model preparation complete ==="
echo "Directory structure:"
find "$MODELS_DIR" -type f -name "*.safetensors" -o -name "*.bin" -o -name "*.json" | head -30

# Verify critical files
echo ""
echo "=== Verification ==="
for f in \
    "$MODELS_DIR/vae/cogvideox-vae.safetensors" \
    "$MODELS_DIR/clip_vision/clip_vision_g.safetensors" \
    "$MODELS_DIR/ipadapter/image_encoder.safetensors" \
    "$MODELS_DIR/ipadapter/ipadapter_sdxl.safetensors"; do
    if [ -f "$f" ]; then
        echo "✅ $f ($(du -h "$f" | cut -f1))"
    else
        echo "❌ MISSING: $f"
    fi
done