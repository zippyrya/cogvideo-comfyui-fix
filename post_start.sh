#!/bin/bash
set -e

cd /workspace/ComfyUI

# Start SSH
/usr/sbin/sshd -D &

# Start JupyterLab
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
    --ServerApp.token='' --ServerApp.password='' &

# Start ComfyUI in BACKGROUND with health check
python main.py --listen 0.0.0.0 --port 8188 &
COMFYUI_PID=$!

# Health check: wait for port 8188
echo "Waiting for ComfyUI on port 8188..."
for i in {1..60}; do
    if curl -sf http://localhost:8188 >/dev/null 2>&1; then
        echo "ComfyUI ready"
        break
    fi
    sleep 1
done

# Keep container alive: wait on background processes
wait $COMFYUI_PID