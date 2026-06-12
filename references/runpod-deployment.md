# RunPod Deployment Reference for CogVideo ComfyUI

## Pod Creation (Python SDK)

```python
import runpod

runpod.api_key = "YOUR_API_KEY"

pod = runpod.create_pod(
    name="cogvideo-comfyui",
    image_name="yourname/cogvideo-comfyui:fixed",
    gpu_type_id="NVIDIA GeForce RTX 4090",  # or A6000, A5000, 4090
    gpu_count=1,
    network_volume_id="<VOLUME_ID>",        # Your persistent volume
    volume_mount_path="/workspace",         # Mount point
    container_disk_in_gb=20,                # Ephemeral container disk
    ports="8188/http,22/tcp,8888/http",     # ComfyUI, SSH, Jupyter
    env={"PUBLIC_KEY": "ssh-ed25519 AAAA..."},  # Your SSH public key
    docker_args="--shm-size=16g",           # Shared memory for PyTorch
)

print(f"Pod ID: {pod['id']}")
```

## Wait for Pod Ready

```python
import time

pod_id = pod['id']
for _ in range(60):
    pod = runpod.get_pod(pod_id)
    if pod['desiredStatus'] == 'RUNNING' and pod.get('runtime', {}).get('ports'):
        print("Pod ready!")
        print(f"Ports: {pod['runtime']['ports']}")
        break
    time.sleep(5)
```

## Network Volume Setup

```python
# Create once, reuse across pods
volume = runpod.create_network_volume(
    name="comfyui-models",
    size=50,                    # GB (50-100 GB recommended for models + outputs + LoRAs)
    data_center_id="US-EAST-1",   # Match GPU region (pick closest to you/GPU availability)
)
print(f"Volume ID: {volume['id']}")  # Use in pod creation
```

### Via Console (Manual)
1. **Storage → Network Volumes** (NOT S3-Compatible Storage)
2. **New Network Volume**
3. Name: `cogvideo-models`
4. Size: **50-100 GB**
5. Region: **`US-EAST-1`** (or closest with GPU availability)
6. Create → copy **Volume ID** (format: `vol_abc123`)

**Cost**: ~$0.10/GB/month → 50 GB = **$5/month** (resizeable later, increase only)

### Region Selection
| Your Location | Recommended Region |
|---------------|-------------------|
| US East (NY, NJ, FL) | `US-EAST-1` |
| US West (CA, WA) | `US-CA-2` |
| US Central (TX, IL) | `US-KS-1` |
| Europe | `EU-RO-1` or `EU-SE-1` |
| Canada | `CA-MTL-1` |

**Note**: S3-Compatible Storage is NOT needed for ComfyUI — Network Volumes mount as block storage at `/workspace` (ext4/xfs). S3 is only for object storage backups/datasets.

## GPU Type Fallback Order

```python
GPU_FALLBACK = [
    "NVIDIA GeForce RTX 4090",   # 24GB, best price/perf
    "NVIDIA RTX A6000",          # 48GB, enterprise
    "NVIDIA RTX A5000",          # 24GB, enterprise
    "NVIDIA GeForce RTX 3090",   # 24GB, older
]
```

## Cost Estimates (US-CA-2, on-demand)

| GPU | $/hr | 24h | 30d (min_workers=0) |
|-----|------|-----|---------------------|
| RTX 4090 | ~$0.69 | $16.56 | ~$0 (scales to 0) |
| RTX A6000 | ~$1.64 | $39.36 | ~$0 |
| RTX A5000 | ~$1.19 | $28.56 | ~$0 |

**Network Volume**: ~$0.10/GB/month (50GB = $5/mo)

## Pod Lifecycle Commands

```python
# Stop (keeps volume, pauses billing)
runpod.stop_pod(pod_id)

# Resume
runpod.resume_pod(pod_id)

# Terminate (keeps volume, deletes pod)
runpod.terminate_pod(pod_id)

# Get logs
logs = runpod.get_pod_logs(pod_id)
```