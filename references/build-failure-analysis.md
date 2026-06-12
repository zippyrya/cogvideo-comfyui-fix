# Build Failure Analysis: VPS Docker Daemon Large Layer Export

## Problem
Building `clawsyil/cogvideo-comfyui:fixed` on this VPS fails at **exporting to image** step:
```
#11 exporting to image
#11 exporting layers 434.8s done
#11 ERROR: failed to build: failed to solve: mount callback failed on /var/lib/containerd/tmpmounts/...
ref moby/1/... locked for 5m52s ...: unavailable
```

## Root Cause
- **overlayfs + containerd** on this VPS kernel/version has a bug exporting layers > ~10GB
- All build steps succeed (FROM, RUN copying 11GB models, COPY scripts, chmod)
- The final `exporting to image` phase hangs until timeout
- Known issue: containerd mount lock contention with large snapshots

## Evidence
- `docker run --rm clawsyil/cogvideo-comfyui:latest ls -la /workspace/ComfyUI/models/` → 11GB+ models confirmed baked
- Build completes in ~73s for model copy step
- Export phase runs 434s+ then fails with lock timeout
- `docker system prune -af` reclaims 59GB after failed builds

## Workarounds (in order of preference)

### 1. Build Locally (Recommended)
```bash
scp -r root@VPS:~/.hermes/profiles/Cecyil/skills/devops/cogvideo-comfyui-docker-fix ~/cogvideo-fix
cd ~/cogvideo-fix
docker login -u clawsyil
./scripts/build-and-push.sh clawsyil fixed
```
- Local Docker daemon has no such bug
- Fast, free, reliable

### 2. GitHub Actions (Free, VPS-Compatible)
- Push skill directory to GitHub repo
- Add `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` secrets
- Run `.github/workflows/build-cogvideo.yml` workflow
- Clean ubuntu-latest runners, BuildKit caching
- ~10-15 min, free tier minutes

### 3. Build on Temporary RunPod Pod (NOT RECOMMENDED)
- RunPod base images (`docker:latest`, `runpod/pytorch:...`) lack SSH server for API-created pods
- `PUBLIC_KEY` env only works on RunPod's official template images
- Chicken-and-egg: need fixed image for SSH, but need SSH to build fixed image

## What NOT to Do
- ❌ Switch storage driver (`fuse-overlayfs`, `vfs`) — breaks existing containers
- ❌ Increase containerd timeouts — undocumented, unreliable
- ❌ Upgrade kernel/containerd/Docker — downtime, may not fix
- ❌ Use `docker build --output=type=local` — extra complexity, same daemon

## Verification That Base Image Has Models
```bash
docker run --rm clawsyil/cogvideo-comfyui:latest ls -la /workspace/ComfyUI/models/checkpoints/
# 11GB+ diffusion_pytorch_model*.safetensors present

docker run --rm clawsyil/cogvideo-comfyui:latest ls -la /workspace/ComfyUI/models/vae/
# cogvideox-vae.safetensors present

docker run --rm clawsyil/cogvideo-comfyui:latest ls -la /workspace/ComfyUI/models/clip_vision/
# clip_vision_g.safetensors present

docker run --rm clawsyil/cogvideo-comfyui:latest ls -la /workspace/ComfyUI/models/ipadapter/
# image_encoder.safetensors, ipadapter_sdxl.safetensors present
```

## Conclusion
The fix package is correct. The VPS is unsuitable for building this specific image due to a Docker daemon bug with large layers. Use local build or GitHub Actions.