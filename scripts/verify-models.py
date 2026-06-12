#!/usr/bin/env python3
# verify-models.py — Verify CogVideo models are correctly placed
# Run inside container after pre_start.sh

import os
import sys

MODELS_DIR = "/models"
COMFYUI_MODELS = "/workspace/ComfyUI/models"

REQUIRED = {
    "checkpoints": [
        "diffusion_pytorch_model-00001-of-00002.safetensors",
        "diffusion_pytorch_model-00002-of-00002.safetensors",
    ],
    "vae": ["cogvideox-vae.safetensors"],
    "clip_vision": ["clip_vision_g.safetensors"],
    "ipadapter": ["image_encoder.safetensors", "ipadapter_sdxl.safetensors"],
    "CogVideo": [],  # Directory must exist
    "CogVideo/loras": [],  # Directory must exist
    "diffusion_models": [],  # Symlink to checkpoints
}

OPTIONAL = {
    "text_encoders": ["t5-v1_1-xxl"],
}

def check_path(path, required=True):
    exists = os.path.exists(path)
    status = "✅" if exists else ("❌" if required else "⚠️")
    size = ""
    if exists and os.path.isfile(path):
        size = f" ({os.path.getsize(path) / 1e9:.2f} GB)"
    elif exists and os.path.isdir(path):
        files = len([f for f in os.listdir(path) if not f.startswith('.')])
        size = f" ({files} files)"
    print(f"  {status} {path}{size}")
    return exists

def main():
    print("=== CogVideo Model Verification ===\n")

    all_ok = True

    # Check /models exists
    print("Base directory:")
    if not check_path(MODELS_DIR):
        print(f"\n❌ CRITICAL: {MODELS_DIR} not found")
        sys.exit(1)

    # Check required
    print("\nRequired models:")
    for category, files in REQUIRED.items():
        cat_path = os.path.join(MODELS_DIR, category)
        if not os.path.exists(cat_path):
            print(f"  ❌ {cat_path} (MISSING DIRECTORY)")
            all_ok = False
            continue

        if not files:
            # Just check directory exists
            check_path(cat_path)
        else:
            for f in files:
                fpath = os.path.join(cat_path, f)
                if not check_path(fpath):
                    all_ok = False

    # Check optional
    print("\nOptional models:")
    for category, files in OPTIONAL.items():
        cat_path = os.path.join(MODELS_DIR, category)
        if os.path.exists(cat_path):
            for f in files:
                fpath = os.path.join(cat_path, f)
                check_path(fpath, required=False)
        else:
            print(f"  ⚠️ {cat_path} (not found)")

    # Check symlinks
    print("\nSymlinks:")
    check_path(os.path.join(MODELS_DIR, "diffusion_models"))
    check_path(COMFYUI_MODELS)

    # Check extra_model_paths.yaml
    print("\nConfig:")
    check_path("/workspace/ComfyUI/extra_model_paths.yaml")

    # Verify folder_paths can be imported
    print("\nComfyUI folder_paths:")
    try:
        sys.path.insert(0, "/workspace/ComfyUI")
        import folder_paths
        keys = list(folder_paths.folder_names_and_paths.keys())
        print(f"  ✅ Loaded ({len(keys)} folder types)")
        for k in ["CogVideo", "cogvideox_loras", "diffusion_models", "vae", "checkpoints"]:
            if k in keys:
                paths = folder_paths.folder_names_and_paths[k][0]
                print(f"    {k}: {paths}")
            else:
                print(f"    {k}: ❌ NOT DEFINED")
    except Exception as e:
        print(f"  ❌ Failed to load folder_paths: {e}")
        all_ok = False

    print(f"\n{'='*40}")
    if all_ok:
        print("✅ ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME CHECKS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()