# GitHub Actions Build Setup for CogVideo ComfyUI Fix

## Overview
Free, reliable CI/CD build for the fixed CogVideo ComfyUI image. Works from VPS-only environments since GitHub runners have clean Docker daemons without the large-layer export bug.

## Workflow File
`.github/workflows/build-cogvideo.yml`

```yaml
name: Build & Push CogVideo ComfyUI Fixed

on:
  workflow_dispatch:
  push:
    paths:
      - 'cogvideo-fix/**'

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push fixed image
        uses: docker/build-push-action@v5
        with:
          context: ./cogvideo-fix
          file: ./cogvideo-fix/Dockerfile.fixed
          push: true
          tags: |
            clawsyil/cogvideo-comfyui:fixed
            clawsyil/cogvideo-comfyui:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

      - name: Verify image
        run: |
          docker pull clawsyil/cogvideo-comfyui:fixed
          docker run --rm clawsyil/cogvideo-comfyui:fixed ls -la /models/
          docker run --rm clawsyil/cogvideo-comfyui:fixed cat /workspace/ComfyUI/extra_model_paths.yaml
```

## One-Time Setup

### 1. Create GitHub Repository
```bash
cd ~/.hermes/profiles/Cecyil/skills/devops/cogvideo-comfyui-docker-fix
git init
git add .
git commit -m "CogVideo ComfyUI fix for RunPod"
gh repo create clawsyil/cogvideo-comfyui-fix --public --push
```

### 2. Add GitHub Secrets
Repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret Name | Value |
|-------------|-------|
| `DOCKERHUB_USERNAME` | `clawsyil` |
| `DOCKERHUB_TOKEN` | Docker Hub **Access Token** (not password) |

**Create Docker Hub token:**
1. https://hub.docker.com/settings/security
2. New Access Token → Name: "GitHub Actions"
3. Copy token (shown once)

### 3. Trigger Build
- **Manual**: Actions → Build & Push CogVideo ComfyUI Fixed → Run workflow
- **Auto**: Push changes to any file under `cogvideo-fix/`

## Build Details

| Aspect | Value |
|--------|-------|
| Runner | `ubuntu-latest` (clean, no daemon bugs) |
| Architecture | `linux/amd64` |
| Cache | GitHub Actions cache (GHA backend) |
| Timeout | 60 min |
| Output tags | `clawsyil/cogvideo-comfyui:fixed`, `:latest` |
| Verification | Pulls image, checks `/models/`, `extra_model_paths.yaml` |

## Expected Runtime
- First run: ~15 min (no cache)
- Subsequent runs: ~5-8 min (BuildKit + GHA cache)
- Free tier: 2000 min/month (plenty)

## Troubleshooting

### "Docker Hub authentication failed"
- Verify `DOCKERHUB_TOKEN` is an **Access Token**, not password
- Check token has "Read, Write, Delete" permissions

### "Build timeout"
- Increase `timeout-minutes` to 90
- Check if base image pull is slow

### "Cache not working"
- Ensure `docker/setup-buildx-action@v3` runs before build
- Cache key includes branch + file hash

## After Build Success
Image available at:
- `clawsyil/cogvideo-comfyui:fixed`
- `clawsyil/cogvideo-comfyui:latest`

Deploy pod:
```bash
python scripts/create-pod.py $RUNPOD_API_KEY $VOLUME_ID "ssh-ed25519 AAAA..."
```