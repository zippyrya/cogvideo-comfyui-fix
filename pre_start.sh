#!/bin/bash
set -e

# Ensure symlink exists (in case volume mounted at /workspace)
if [ ! -L /workspace/ComfyUI/models ]; then
    ln -sf /models /workspace/ComfyUI/models
fi

# Create CogVideo folder structure for custom node
mkdir -p /models/CogVideo/loras
mkdir -p /models/diffusion_models

# Symlink checkpoints -> diffusion_models for CogVideo models
if [ ! -L /models/diffusion_models ]; then
    ln -sf /models/checkpoints /models/diffusion_models
fi

# Verify critical models exist
echo "=== Verifying models ==="
ls -la /models/checkpoints/ | head -5
ls -la /models/vae/
ls -la /models/clip_vision/
ls -la /models/ipadapter/

# Write extra_model_paths.yaml (idempotent)
cat > /workspace/ComfyUI/extra_model_paths.yaml << 'EOF'
comfyui:
  base_path: /workspace/ComfyUI/
  CogVideo: models/CogVideo/
  cogvideox_loras: models/CogVideo/loras/
EOF

echo "=== pre_start.sh complete ==="
exec /post_start.sh