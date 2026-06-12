---
name: cogvideo-comfyui-docker-fix
category: devops
description: Fix clawsyil/cogvideo-comfyui:latest for RunPod deployment — volume masking, missing folder_paths, wrong model locations, blocking entrypoint, no auto-download
---

# CogVideo ComfyUI Docker Fix

## Critical Issues in `clawsyil/cogvideo-comfyui:latest`

1. **Volume masks models** — Mounting network volume at `/workspace` hides container's `/workspace/ComfyUI/models/` (11GB+ baked models)
2. **Missing folder_paths** — `CogVideoXWrapper` needs `CogVideo` → `models/CogVideo/` and `cogvideox_loras` → `models/CogVideo/loras/` (not in default `folder_paths.py`)
3. **Models in wrong locations** — Models in `checkpoints/` but CogVideo expects `diffusion_models/` or `CogVideo/` — no `CogVideo` folder exists
4. **Blocking entrypoint** — `post_start.sh` ends with `exec python main.py --listen 0.0.0.0 --port 8188` — blocks, pod dies if ComfyUI crashes
5. **No auto-model download** — Only triggers via UI nodes, not at startup

## Fix Files (in skill directory)

| File | Purpose |
|------|---------|
| `Dockerfile.fixed` | Multi-stage: copies baked models to `/models`, adds fix scripts, new entrypoint |
| `pre_start.sh` | Runs at container start: symlinks `/models` → `/workspace/ComfyUI/models`, creates `CogVideo/` folders, writes `extra_model_paths.yaml`, verifies models |
| `post_start.sh` | Background ComfyUI + SSH + Jupyter, health check on port 8188, wait loop |
| `extra_model_paths.yaml` | Defines `CogVideo: models/CogVideo/` and `cogvideox_loras: models/CogVideo/loras/` |

## Build & Push

**⚠️ CRITICAL: Do NOT build on this VPS.** The Docker daemon hangs exporting the 11GB model layer (overlayfs/containerd bug — `mount callback failed`, `ref locked for 5m+`). All build steps succeed (copying models takes ~73s), but final image export times out. **Build locally or use GitHub Actions.**

### Option A: Build locally (recommended if you have a local machine with Docker)
```bash
# 1. Copy fix files to your machine
scp -r root@your-vps:~/.hermes/profiles/Cecyil/skills/devops/cogvideo-comfyui-docker-fix ~/cogvideo-fix

# 2. Login to Docker Hub
docker login -u clawsyil

# 3. Build & push
cd ~/cogvideo-fix
./scripts/build-and-push.sh clawsyil fixed
```

### Option B: GitHub Actions (free, reliable, works from VPS-only environments) ⭐
**One-time setup:**
1. Push this skill directory to a GitHub repo: `clawsyil/cogvideo-comfyui-fix`
2. Add GitHub Secrets: `DOCKERHUB_USERNAME=clawsyil`, `DOCKERHUB_TOKEN=<your-docker-hub-access-token>`
3. Run workflow: **Actions → Build & Push CogVideo ComfyUI Fixed → Run workflow**

**Workflow file:** `.github/workflows/build-cogvideo.yml` (included in skill)
- Runs on `ubuntu-latest` with BuildKit caching
- Builds `linux/amd64` image
- Pushes `clawsyil/cogvideo-comfyui:fixed` and `:latest`
- Verifies image by pulling and checking `/models/` and `extra_model_paths.yaml`
- Typical runtime: ~10-15 min

### Option C: Build on temporary RunPod pod (~$0.05, 5 min) — **NOT RECOMMENDED**
RunPod base images (`docker:latest`, `runpod/pytorch:...`) do NOT have SSH server configured for API-created pods — the `PUBLIC_KEY` env var only works on RunPod's official template images. Custom images must have SSH pre-configured (the fixed image does). This creates a chicken-and-egg problem.

### What the script does
- Validates all 4 fix files exist
- Verifies base image has models baked in (it does — 11GB in checkpoints/, vae/, clip_vision/, ipadapter/)
- Builds `clawsyil/cogvideo-comfyui:fixed` (and `:latest`)
- Pushes both tags to your Docker Hub

## Deploy on RunPod — Region & Volume Locking

**⚠️ Network volumes are region-locked.** The volume must be in the SAME region as the GPU you want. If a region has no GPU capacity (e.g., US-WA-1 exhausted), you must:
1. Delete the volume in the exhausted region
2. Create a new volume in a region WITH GPU capacity (US-EAST-1, US-KS-1, EU-RO-1)
3. Use the new volume ID

### GPU Capacity Fallback (in create-pod.py)
The script tries GPUs in order and falls back on capacity errors:
```python
GPU_TYPE = "NVIDIA RTX A6000"  # A40 not in RunPod GPU list as primary
FALLBACK_GPUS = ["NVIDIA RTX A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 4090", "NVIDIA GeForce RTX 3090"]
```
Error strings that trigger fallback: "capacity", "unavailable", "no longer any instances", "no instances available", "out of capacity".

**Note:** A40 is in fallback chain. Primary is A6000 since A40 GPU type ID varies by region. Adjust `GPU_TYPE` to "NVIDIA RTX A40" if available in your target region.

### Deploy command
```bash
python scripts/create-pod.py $RUNPOD_API_KEY $VOLUME_ID "ssh-ed25519 AAAA..."
```

## Verification Checklist

- [ ] Pod starts, `runtime.ports` populated
- [ ] SSH connects: `ssh -i key root@ip -p port "nvidia-smi"`
- [ ] ComfyUI loads at `http://ip:port` (no red model errors)
- [ ] CogVideo nodes show models in dropdown
- [ ] Generate test video → output in `/workspace/ComfyUI/output/`

## User Workflow Preference: Step-by-Step Approval

**Always present options and wait for explicit approval before any credit-spending action.**

| Step | What to Show | Wait For |
|------|--------------|----------|
| 1 | Region pricing, GPU availability | "Check [region]" or "Try [region]" |
| 2 | Volume creation instructions | User provides Volume ID |
| 3 | Pod creation attempt | "Go ahead" or "Wait and retry" |
| 4 | Connection info (SSH, ComfyUI URL) | User confirms working |

**Never auto-fallback to expensive GPU without confirmation.**

## References

- `references/runpod-deployment.md` — Pod creation, GPU fallback, volume setup, cost estimates
- `references/troubleshooting.md` — Pod stuck, ComfyUI errors, model errors, zombie pods, OOM
- `references/character-consistency.md` — LoRA training, IPAdapter, ControlNet, prompt engineering
- `references/build-failure-analysis.md` — VPS Docker daemon export failure root cause & workarounds
- `references/github-actions-build.md` — GitHub Actions CI/CD build setup (free, reliable, VPS-compatible)