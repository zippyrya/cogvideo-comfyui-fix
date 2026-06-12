# Character Consistency Guide for CogVideo

## Methods (Ranked by Consistency vs Effort)

| Method | Consistency | Effort | VRAM | Best For |
|--------|-------------|--------|------|----------|
| **LoRA Training** | ★★★★★ | High (hours + GPU) | 24GB+ | Same character across many videos |
| **IPAdapter + Ref Images** | ★★★★☆ | Low (minutes) | 16GB+ | Few reference shots, quick iteration |
| **ControlNet (Pose/Depth)** | ★★★☆☆ | Medium | 16GB+ | Specific poses, camera moves |
| **Consistent Prompt + Seed** | ★★☆☆☆ | None | 12GB+ | Quick tests, background chars |

---

## 1. LoRA Training (Best Consistency)

### Requirements
- 20-50 images of character (consistent lighting, angles)
- Caption file per image (`image.txt` with description)
- ~2-4 hours on RTX 4090 / A6000
- Output: `character_lora.safetensors` (~100-500MB)

### Training Command (kohya-ss)
```bash
# Prepare dataset
mkdir -p dataset/character
# Put images + captions in dataset/character/

# Train (SDXL/CogVideo compatible)
accelerate launch train_network.py \
  --pretrained_model_name_or_path="THUDM/CogVideoX-5b" \
  --train_data_dir="dataset" \
  --output_dir="output/lora" \
  --output_name="character_lora" \
  --network_module="networks.lora" \
  --network_dim=32 \
  --network_alpha=16 \
  --learning_rate=1e-4 \
  --lr_scheduler="cosine_with_restarts" \
  --train_batch_size=1 \
  --max_train_epochs=10 \
  --mixed_precision="fp16" \
  --save_every_n_epochs=1
```

### Use in ComfyUI
1. Copy `character_lora.safetensors` → `/models/CogVideo/loras/`
2. Add **CogVideo LoRA Select** node
3. Select `character_lora`, set strength 0.8-1.0

---

## 2. IPAdapter + Reference Images (Fastest Good Consistency)

### Requirements
- 1-4 reference images of character
- IPAdapter models (already in image: `image_encoder.safetensors`, `ipadapter_sdxl.safetensors`)
- CLIP Vision (`clip_vision_g.safetensors`)

### ComfyUI Workflow
```
Load Image (ref) → CLIP Vision Encode → IPAdapter Apply → CogVideo Sampler
```

### Nodes Needed
- **Load Image** (reference)
- **CLIP Vision Loader** (`clip_vision_g.safetensors`)
- **IPAdapter Loader** (`ipadapter_sdxl.safetensors`, `image_encoder.safetensors`)
- **IPAdapter Apply** (connect to CogVideo sampler)
- **CogVideo Sampler** (with IPAdapter conditioning)

### Tips
- Use multiple reference images (different angles) → average embeddings
- Weight: 0.5-0.8 for subtle, 0.8-1.2 for strong likeness
- Combine with ControlNet for pose control

---

## 3. ControlNet (Pose/Structure Control)

### Models (Download to `/models/controlnet/`)
| Model | Use Case |
|-------|----------|
| `cogvideox-controlnet-pose.safetensors` | Human pose |
| `cogvideox-controlnet-depth.safetensors` | Depth/structure |
| `cogvideox-controlnet-canny.safetensors` | Edge guidance |

### Workflow
```
ControlNet Video (pose/depth) → CogVideo Sampler (with ControlNet conditioning)
```

### Tips
- Extract pose from reference video → `dwpose` or `openpose`
- Depth from reference frames → `MiDaS` or `DepthAnything`
- Weight: 0.5-1.0 (higher = more faithful to control)

---

## 4. Prompt Engineering for Consistency

### Character Prompt Template
```
{character_name}, {detailed_appearance}, {clothing}, {style}, {lighting}, {camera}
```

### Example
```
A young woman named "Elena", long auburn hair in loose waves, green eyes, light freckles across nose,
wearing cream linen blouse, soft natural lighting, medium shot, shallow depth of field,
cinematic 4k, highly detailed, photorealistic
```

### Consistency Boosters
- **Fixed seed** per character
- **Same negative prompt** always
- **Character name** in every prompt (trains association)
- **Embeddings** (textual inversion) for recurring traits

---

## Recommended Setup for Your Use Case

### If: "Content videos with specific realistic characters, multiple videos per character"

| Priority | Setup |
|----------|-------|
| **1** | Train LoRA for each main character (one-time cost) |
| **2** | Use IPAdapter for secondary/one-off characters |
| **3** | ControlNet for specific shots (walking, sitting, action) |
| **4** | Bake LoRAs into Docker image for instant access |

### Docker Image Additions
```dockerfile
# In Dockerfile.fixed, after COPY pre_start.sh:
COPY models/CogVideo/loras/ /models/CogVideo/loras/
# Or download at build time:
# RUN huggingface-cli download your-org/character-loras --local-dir /models/CogVideo/loras/
```

### Workflow Template (Save as JSON)
```json
{
  "nodes": [
    "CogVideo Sampler (base)",
    "CogVideo LoRA Select (character_lora, strength=1.0)",
    "IPAdapter Apply (reference_image, weight=0.7)",
    "ControlNet Apply (pose_video, weight=0.8)",
    "Video Encode (H.264, 8fps, 720p)"
  ]
}
```

---

## Quick Test Checklist

- [ ] LoRA loads in **CogVideo LoRA Select** dropdown
- [ ] IPAdapter applies without error
- [ ] ControlNet video input works
- [ ] Output video shows character consistency across:
  - [ ] Different prompts (same character, different scenes)
  - [ ] Different seeds (same prompt)
  - [ ] Different durations (2s vs 6s)