import os
import sys
import json
import base64
import tempfile
import traceback
from pathlib import Path

import runpod
from runpod.serverless.utils import rp_upload, rp_cleanup

# Set environment variables for model paths
os.environ['HF_HOME'] = '/models'
os.environ['TRANSFORMERS_CACHE'] = '/models/transformers'
os.environ['DIFFUSERS_CACHE'] = '/models/diffusers'

# Add model paths to Python path
sys.path.insert(0, '/workspace/ComfyUI')

import torch
from diffusers import CogVideoXPipeline
from diffusers.utils import export_to_video

# Global pipeline cache
_pipeline = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def load_pipeline():
    """Load CogVideoX pipeline with all models from local paths."""
    global _pipeline
    
    if _pipeline is not None:
        return _pipeline
    
    print("Loading CogVideoX-5b pipeline...")
    
    # Load from local model directory
    model_path = "/models/CogVideoX-5b"
    
    _pipeline = CogVideoXPipeline.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        variant="fp16",
        use_safetensors=True,
    ).to(_device)
    
    # Enable memory efficient attention
    _pipeline.enable_model_cpu_offload()
    _pipeline.vae.enable_slicing()
    _pipeline.vae.enable_tiling()
    
    print("Pipeline loaded successfully")
    return _pipeline

def generate_video(prompt, negative_prompt="", width=720, height=480, num_frames=49, 
                   num_inference_steps=50, guidance_scale=6.0, seed=None, fps=8):
    """Generate video using CogVideoX pipeline."""
    
    pipeline = load_pipeline()
    
    # Set seed for reproducibility
    generator = torch.Generator(device=_device)
    if seed is not None:
        generator.manual_seed(seed)
    else:
        generator.seed()
    
    print(f"Generating video: {prompt[:100]}...")
    print(f"Params: {width}x{height}, {num_frames} frames, {num_inference_steps} steps, guidance={guidance_scale}")
    
    # Generate video frames
    video_frames = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        num_frames=num_frames,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        generator=generator,
    ).frames[0]
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        output_path = tmp.name
    
    export_to_video(video_frames, output_path, fps=fps)
    print(f"Video saved to {output_path}")
    
    return output_path

def handler(event):
    """
    RunPod Serverless handler for CogVideoX video generation.
    
    Expected input format:
    {
        "prompt": "A beautiful sunset over mountains",
        "negative_prompt": "blurry, low quality, distorted",
        "width": 720,
        "height": 480,
        "num_frames": 49,
        "num_inference_steps": 50,
        "guidance_scale": 6.0,
        "seed": 12345,
        "fps": 8
    }
    
    Returns:
    {
        "video_url": "https://replicate.delivery/.../output.mp4",
        "seed": 12345,
        "parameters": {...}
    }
    """
    
    try:
        input_data = event.get("input", {})
        
        # Extract parameters with defaults
        prompt = input_data.get("prompt", "")
        if not prompt:
            return {"error": "Missing required parameter: prompt"}
        
        negative_prompt = input_data.get("negative_prompt", "blurry, low quality, distorted, watermark, text, ugly, deformed")
        width = input_data.get("width", 720)
        height = input_data.get("height", 480)
        num_frames = input_data.get("num_frames", 49)
        num_inference_steps = input_data.get("num_inference_steps", 50)
        guidance_scale = input_data.get("guidance_scale", 6.0)
        seed = input_data.get("seed", None)
        fps = input_data.get("fps", 8)
        
        # Validate parameters
        if width > 720 or height > 480:
            return {"error": "Maximum resolution is 720x480 for CogVideoX-5b"}
        if num_frames > 81:
            return {"error": "Maximum frames is 81 for CogVideoX-5b"}
        
        # Generate video
        video_path = generate_video(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed,
            fps=fps
        )
        
        # Upload to RunPod storage
        print("Uploading video to RunPod storage...")
        video_url = rp_upload.upload(video_path)
        
        # Cleanup temp file
        rp_cleanup.clean([video_path])
        
        return {
            "video_url": video_url,
            "seed": seed,
            "parameters": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_frames": num_frames,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "fps": fps
            }
        }
        
    except Exception as e:
        error_msg = f"Generation failed: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return {"error": error_msg}

# RunPod serverless entrypoint
if __name__ == "__main__":
    print("Starting RunPod Serverless handler for CogVideoX...")
    runpod.serverless.start({"handler": handler})
