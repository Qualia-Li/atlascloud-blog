#!/usr/bin/env python3
"""Generate sample images for blog articles using Atlas Cloud API."""

import requests
import time
import os
import sys

API_KEY = os.environ.get("ATLAS_CLOUD_API_KEY", "apikey-e4735068ccdd4955b91db68b1e403176")
BASE_URL = "https://api.atlascloud.ai/api/v1"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "samples")

SAMPLES = [
    # Nano Banana 2 samples
    {
        "model": "google/nano-banana-2/text-to-image",
        "prompt": "3D collectible figurine of a cyberpunk cat hacker wearing a tiny hoodie and glowing goggles, sitting on a miniature desk with holographic screens, product photography with studio lighting, sharp detail, sealed in premium collector box with transparent window",
        "filename": "nano-banana-2-figurine.png",
    },
    {
        "model": "google/nano-banana-2/text-to-image",
        "prompt": "A serene Japanese garden at golden hour, cherry blossom trees in full bloom, a stone path leading to a traditional wooden bridge over a koi pond, soft warm light filtering through petals, photorealistic, highly detailed",
        "filename": "nano-banana-2-landscape.png",
    },
    # Seedream v5.0 Lite samples
    {
        "model": "bytedance/seedream-v5.0-lite",
        "prompt": "Professional product photography of a luxury watch on a dark marble surface, dramatic side lighting, reflections, bokeh background with warm amber tones, 8K quality, commercial advertising style",
        "filename": "seedream-product-photo.png",
    },
    {
        "model": "bytedance/seedream-v5.0-lite",
        "prompt": "A cozy coffee shop interior with exposed brick walls, warm Edison bulb lighting, barista pouring latte art, steam rising from cups, morning sunlight through large windows, photorealistic",
        "filename": "seedream-lifestyle.png",
    },
    # Z-Image Turbo samples
    {
        "model": "z-image/turbo",
        "prompt": "A futuristic city skyline at dusk, neon lights reflecting off glass skyscrapers, flying vehicles in the sky, cyberpunk aesthetic, detailed architecture, dramatic clouds with purple and orange sunset",
        "filename": "z-image-turbo-cityscape.png",
    },
    {
        "model": "z-image/turbo",
        "prompt": "Portrait of a young woman with freckles, natural lighting, shallow depth of field, wearing a denim jacket, autumn forest background with golden leaves, photorealistic, 85mm lens look",
        "filename": "z-image-turbo-portrait.png",
    },
    # Imagen 4 Ultra samples
    {
        "model": "google/imagen4-ultra",
        "prompt": "A hand-lettered sign reading 'ATLAS CLOUD AI' made of glowing neon tubes mounted on a weathered brick wall, night scene, rain puddles reflecting the neon light, cinematic photography",
        "filename": "imagen4-ultra-text.png",
    },
    {
        "model": "google/imagen4-ultra",
        "prompt": "Aerial view of a stunning coral reef teeming with tropical fish, crystal clear turquoise water, sunbeams penetrating the surface, underwater photography, National Geographic quality",
        "filename": "imagen4-ultra-nature.png",
    },
]


def generate_image(sample):
    """Submit an image generation request."""
    print(f"  Submitting: {sample['filename']} ({sample['model']})")
    resp = requests.post(
        f"{BASE_URL}/model/generateImage",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": sample["model"],
            "prompt": sample["prompt"],
            "width": 1024,
            "height": 1024,
        },
    )
    data = resp.json()
    if data.get("code") != 200:
        print(f"  ERROR submitting {sample['filename']}: {data}")
        return None
    return data["data"]["id"]


def poll_result(request_id, max_wait=120):
    """Poll for completion."""
    for _ in range(max_wait // 5):
        time.sleep(5)
        resp = requests.get(
            f"{BASE_URL}/model/prediction/{request_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        data = resp.json()["data"]
        if data["status"] == "completed" and data.get("outputs"):
            return data["outputs"][0]
        elif data["status"] == "failed":
            print(f"  FAILED: {data.get('error', 'unknown error')}")
            return None
    print(f"  TIMEOUT after {max_wait}s")
    return None


def download_image(url, filepath):
    """Download image to disk."""
    resp = requests.get(url)
    with open(filepath, "wb") as f:
        f.write(resp.content)
    print(f"  Saved: {filepath} ({len(resp.content)} bytes)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Submit all requests first
    pending = []
    for sample in SAMPLES:
        filepath = os.path.join(OUTPUT_DIR, sample["filename"])
        if os.path.exists(filepath):
            print(f"  Skipping (exists): {sample['filename']}")
            continue
        request_id = generate_image(sample)
        if request_id:
            pending.append((request_id, sample))

    if not pending:
        print("All images already exist. Nothing to do.")
        return

    print(f"\nWaiting for {len(pending)} images to complete...")

    # Poll for results
    for request_id, sample in pending:
        filepath = os.path.join(OUTPUT_DIR, sample["filename"])
        print(f"\n  Polling: {sample['filename']}...")
        url = poll_result(request_id)
        if url:
            download_image(url, filepath)
        else:
            print(f"  Could not retrieve: {sample['filename']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
