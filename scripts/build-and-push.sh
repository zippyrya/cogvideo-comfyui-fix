#!/usr/bin/env bash
# build-and-push.sh — Build fixed CogVideo ComfyUI image and push to Docker Hub
# Usage: ./build-and-push.sh [DOCKERHUB_USERNAME] [TAG]

set -euo pipefail

# Config
DOCKERHUB_USER="${1:-}"
TAG="${2:-fixed}"
IMAGE_NAME="cogvideo-comfyui"
FULL_IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}"
BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[BUILD]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check args
if [[ -z "$DOCKERHUB_USER" ]]; then
    error "Usage: $0 <dockerhub-username> [tag]"
    error "Example: $0 myuser fixed"
    exit 1
fi

# Check Docker login
if ! docker info >/dev/null 2>&1; then
    error "Docker daemon not running"
    exit 1
fi

if ! docker pull "$DOCKERHUB_USER"/doesnotexist 2>&1 | grep -q "pull access denied"; then
    warn "Not logged into Docker Hub. Run 'docker login' first."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 1
fi

# Check required files exist
REQUIRED_FILES=(
    "Dockerfile.fixed"
    "pre_start.sh"
    "post_start.sh"
    "extra_model_paths.yaml"
)

log "Checking build files in $BUILD_DIR..."
for f in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$BUILD_DIR/$f" ]]; then
        error "Missing required file: $f"
        exit 1
    fi
done

# Check models directory exists (for COPY in Dockerfile)
if [[ ! -d "$BUILD_DIR/models" ]]; then
    warn "No ./models/ directory found. Models will NOT be baked into image."
    warn "Run scripts/prepare-models.sh first, or ensure models exist at /models in base image."
    read -p "Continue without baked models? (y/N) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 1
fi

# Build
log "Building $FULL_IMAGE..."
cd "$BUILD_DIR"

docker build \
    --file Dockerfile.fixed \
    --tag "$FULL_IMAGE" \
    --tag "${DOCKERHUB_USER}/${IMAGE_NAME}:latest" \
    --progress=plain \
    .

# Verify image
log "Verifying image..."
docker run --rm "$FULL_IMAGE" ls -la /models/ 2>/dev/null | head -20 || true
docker run --rm "$FULL_IMAGE" cat /workspace/ComfyUI/extra_model_paths.yaml 2>/dev/null || true

# Push
log "Pushing $FULL_IMAGE..."
docker push "$FULL_IMAGE"
docker push "${DOCKERHUB_USER}/${IMAGE_NAME}:latest"

log "✅ Done! Image pushed:"
echo "  $FULL_IMAGE"
echo "  ${DOCKERHUB_USER}/${IMAGE_NAME}:latest"
echo ""
echo "Deploy with:"
echo "  python scripts/create-pod.py \$RUNPOD_API_KEY \$VOLUME_ID \"\$SSH_PUBLIC_KEY\""
echo ""
echo "Or in RunPod Console:"
echo "  Image: ${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}"
echo "  GPU: RTX 4090 (or A6000/A5000 fallback)"
echo "  Volume: your-network-volume at /workspace"
echo "  Ports: 8188/http, 22/tcp, 8888/http"
echo "  Env: PUBLIC_KEY=your-ssh-public-key"