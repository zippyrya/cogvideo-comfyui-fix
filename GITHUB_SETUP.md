# CogVideo ComfyUI Docker Fix — GitHub Actions Setup

## One-Time Setup

### 1. Create GitHub Repository
```bash
# On your VPS (or any machine with git)
cd ~/.hermes/profiles/Cecyil/skills/devops/cogvideo-comfyui-docker-fix
git init
git add .
git commit -m "CogVideo ComfyUI fix for RunPod"
gh repo create clawsyil/cogvideo-comfyui-fix --public --push
```
Or create manually at github.com/new → `clawsyil/cogvideo-comfyui-fix`

### 2. Add GitHub Secrets
Go to **Repository → Settings → Secrets and variables → Actions → New repository secret**:

| Secret Name | Value |
|-------------|-------|
| `DOCKERHUB_USERNAME` | `clawsyil` |
| `DOCKERHUB_TOKEN` | Your Docker Hub **Access Token** (not password) |

**Create Docker Hub token**: Docker Hub → Account Settings → Security → New Access Token → "GitHub Actions" → Copy token

### 3. Run Workflow
- Go to **Actions → Build & Push CogVideo ComfyUI Fixed → Run workflow**
- Or push to main branch (workflow triggers on `cogvideo-fix/**` changes)

### 4. Monitor Build
- Actions tab shows live logs
- Build takes ~10-15 min on GitHub runners
- Caches layers for faster rebuilds

### 5. After Success
Image available at:
- `clawsyil/cogvideo-comfyui:fixed`
- `clawsyil/cogvideo-comfyui:latest`

Then deploy pod:
```bash
python scripts/create-pod.py $RUNPOD_API_KEY $VOLUME_ID "ssh-ed25519 AAAA..."
```

---

## Files in This Repo

```
cogvideo-fix/
├── Dockerfile.fixed
├── pre_start.sh
├── post_start.sh
├── extra_model_paths.yaml
├── scripts/
│   ├── build-and-push.sh
│   ├── create-pod.py
│   ├── prepare-models.sh
│   └── verify-models.py
└── references/
    ├── runpod-deployment.md
    ├── troubleshooting.md
    └── character-consistency.md
.github/
└── workflows/
    └── build-cogvideo.yml
```

---

## Rebuild Trigger
Push changes to any file in `cogvideo-fix/` → workflow auto-runs.
Or manually: Actions → Run workflow.