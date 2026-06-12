#!/usr/bin/env python3
# create-pod.py — One-command pod creation for CogVideo ComfyUI
# Usage: python create-pod.py <API_KEY> <VOLUME_ID> <SSH_PUBLIC_KEY>

import sys
import os
import time
import runpod

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <API_KEY> <VOLUME_ID> <SSH_PUBLIC_KEY>")
        print("Example: python create-pod.py \$RUNPOD_API_KEY vol_abc123 \"ssh-ed25519 AAAA...\"")
        sys.exit(1)

    api_key = sys.argv[1]
    volume_id = sys.argv[2]
    ssh_key = sys.argv[3]

    runpod.api_key = api_key

    # Config
    IMAGE = "clawsyil/cogvideo-comfyui:fixed"
    GPU_TYPE = "NVIDIA RTX A6000"  # A40 not in RunPod GPU list, use A6000 as primary, A40 as fallback
    FALLBACK_GPUS = ["NVIDIA RTX A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 4090", "NVIDIA GeForce RTX 3090"]
    POD_NAME = "cogvideo-comfyui"

    print(f"Creating pod with image: {IMAGE}")
    print(f"Volume: {volume_id}")
    print(f"GPU: {GPU_TYPE} (fallback: {', '.join(FALLBACK_GPUS)})")

    # Try primary GPU, fallback on capacity error
    pod = None
    gpu_types = [GPU_TYPE] + FALLBACK_GPUS

    for gpu in gpu_types:
        try:
            print(f"\nTrying GPU: {gpu}...")
            pod = runpod.create_pod(
                name=POD_NAME,
                image_name=IMAGE,
                gpu_type_id=gpu,
                gpu_count=1,
                network_volume_id=volume_id,
                volume_mount_path="/workspace",
                container_disk_in_gb=20,
                ports="8188/http,22/tcp,8888/http",
                env={"PUBLIC_KEY": ssh_key},
                docker_args="--shm-size=16g",
            )
            print(f"✅ Pod created: {pod['id']}")
            break
        except Exception as e:
            err = str(e).lower()
            if any(kw in err for kw in ["capacity", "unavailable", "no longer any instances", "no instances available", "out of capacity"]):
                print(f"⚠️  No capacity for {gpu}, trying next...")
                continue
            else:
                raise

    if not pod:
        print("❌ All GPU types exhausted")
        sys.exit(1)

    pod_id = pod['id']

    # Wait for RUNNING + ports
    print("\nWaiting for pod to be ready...")
    for i in range(60):
        pod = runpod.get_pod(pod_id)
        status = pod.get('desiredStatus')
        runtime = pod.get('runtime', {})
        ports = runtime.get('ports', [])

        if status == 'RUNNING' and ports:
            print(f"\n✅ Pod READY after {i*5}s")
            print(f"Status: {status}")
            print(f"Ports:")
            for p in ports:
                proto = p['type'].upper()
                print(f"  {proto}: {p['ip']}:{p['publicPort']} -> {p['privatePort']}")

            # Extract connection info
            comfyui = next((p for p in ports if p['privatePort'] == 8188), None)
            ssh = next((p for p in ports if p['privatePort'] == 22), None)
            jupyter = next((p for p in ports if p['privatePort'] == 8888), None)

            print(f"\n=== CONNECTION INFO ===")
            if comfyui:
                print(f"ComfyUI:  http://{comfyui['ip']}:{comfyui['publicPort']}")
            if ssh:
                print(f"SSH:      ssh -i ~/.ssh/your_key root@{ssh['ip']} -p {ssh['publicPort']}")
            if jupyter:
                print(f"Jupyter:  http://{jupyter['ip']}:{jupyter['publicPort']}?token=")

            # Save connection info
            with open(f"pod-{pod_id}-connection.txt", "w") as f:
                f.write(f"POD_ID={pod_id}\n")
                if comfyui:
                    f.write(f"COMFYUI_URL=http://{comfyui['ip']}:{comfyui['publicPort']}\n")
                if ssh:
                    f.write(f"SSH_HOST={ssh['ip']}\n")
                    f.write(f"SSH_PORT={ssh['publicPort']}\n")
                if jupyter:
                    f.write(f"JUPYTER_URL=http://{jupyter['ip']}:{jupyter['publicPort']}\n")

            print(f"\nSaved to pod-{pod_id}-connection.txt")
            return

        elif status in ['FAILED', 'TERMINATED']:
            print(f"\n❌ Pod failed: {status}")
            print(f"Error: {pod.get('lastError', 'Unknown')}")
            sys.exit(1)

        print(f"  [{i*5}s] Status: {status}, Ports: {len(ports)}")
        time.sleep(5)

    print("\n❌ Timeout waiting for pod")
    sys.exit(1)

if __name__ == "__main__":
    main()