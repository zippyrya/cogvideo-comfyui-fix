# Troubleshooting CogVideo ComfyUI on RunPod

## Pod Stuck in PENDING / IMAGE_PULL

| Cause | Fix |
|-------|-----|
| Insufficient GPU capacity | Try different GPU type or data center |
| Insufficient balance | Add funds to RunPod account |
| Image too large / pull timeout | Use smaller base, enable FlashBoot |
| Network volume in different region | Create volume in same region as GPU |

```python
# Check GPU availability before creating
gpus = runpod.get_gpus()
available = [g for g in gpus if g['id'] == 'NVIDIA GeForce RTX 4090' and g['available']]
```

## Pod Running but ComfyUI Not Accessible

```bash
# SSH in and check
ssh -i key root@ip -p port

# Check processes
ps aux | grep -E "(python|comfyui|sshd|jupyter)"

# Check ComfyUI logs
tail -f /workspace/ComfyUI/logs/*.log 2>/dev/null || echo "No log file"

# Test locally
curl http://localhost:8188
```

| Symptom | Likely Cause |
|---------|--------------|
| Port 8188 not responding | ComfyUI crashed / not started |
| Red "model not found" in UI | Volume masked models / wrong paths |
| "CogVideo folder_paths not found" | Missing `extra_model_paths.yaml` |
| SSH works but ComfyUI doesn't | `post_start.sh` failed silently |
| Jupyter works but ComfyUI doesn't | Port conflict / ComfyUI OOM |

## Model Errors in ComfyUI UI

| Error | Fix |
|-------|-----|
| `CogVideo` not in folder_paths | Verify `extra_model_paths.yaml` exists at `/workspace/ComfyUI/` |
| `cogvideox_loras` empty | Create `/models/CogVideo/loras/` and add `.safetensors` files |
| `diffusion_models` empty | Symlink `/models/checkpoints` → `/models/diffusion_models` |
| VAE not found | Check `/models/vae/cogvideox-vae.safetensors` exists |

## Zombie Pod (Won't Stop/Terminate)

```bash
# Force stop sequence
runpod.stop_pod(pod_id)
sleep 10
runpod.terminate_pod(pod_id)

# If still stuck, recreate
runpod.create_pod(...)  # New pod with same volume
```

## OOM (CUDA Out of Memory)

| Setting | Adjustment |
|---------|------------|
| Resolution | 480p → 720p → 1080p (each step ~2x VRAM) |
| Frame count | 16 → 8 → 4 frames |
| Batch size | Always 1 for ComfyUI |
| Model precision | FP16 (default), try FP8 if supported |
| VAE tiling | Enable in CogVideo nodes |

## Volume Issues

```bash
# Check mount
df -h /workspace
ls -la /workspace/ComfyUI/models/

# If empty but container has models:
# Volume mounted at /workspace SHADOWS container's /workspace/ComfyUI/models
# Fix: Image must have models at /models, symlink at runtime
```

## Debug Commands (Run Inside Pod)

```bash
# Full environment check
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name())"
ls -la /models/
ls -la /workspace/ComfyUI/models/
cat /workspace/ComfyUI/extra_model_paths.yaml
python -c "import folder_paths; print(folder_paths.folder_names_and_paths.keys())"
```