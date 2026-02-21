#!/usr/bin/env python3
"""Generate model-specific images for blog articles via Atlas Cloud API."""

import requests
import time
import os
import sys

API_KEY = "apikey-e4735068ccdd4955b91db68b1e403176"
BASE_URL = "https://api.atlascloud.ai/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "generated")

# All images to generate: (filename, model, prompt, width, height)
IMAGES = [
    # --- image-generation-api-guide.md ---
    # --- image-generation-api-guide.md ---
    ("flux2pro-product-headphones.jpg",
     "black-forest-labs/flux-2-pro/text-to-image",
     "Professional product photo of wireless headphones on marble surface, studio lighting, clean white background, commercial photography",
     1024, 1024),

    ("imagen4-ultra-landscape-sunset.png",
     "google/imagen4-ultra",
     "Photorealistic landscape of a serene mountain lake at golden hour, crystal clear water reflecting snow-capped peaks, warm sunset lighting, atmospheric haze, professional nature photography",
     1536, 864),

    ("ideogram-v3-typography-poster.jpg",
     "ideogram-ai/ideogram-v3-quality",
     'Modern minimalist poster design with bold typography reading "ATLAS CLOUD" in clean sans-serif font, gradient background from deep purple to electric blue, professional graphic design',
     1024, 1024),

    # --- best-seedance-2-0-prompts-guide.md ---
    ("imagen4-ultra-space-reveal.png",
     "google/imagen4-ultra",
     "Epic cinematic scene of a rocket launching into a star-filled night sky, dramatic clouds parting to reveal the cosmos, volumetric lighting, golden hour atmosphere, professional sci-fi cinematography",
     1536, 864),

    ("imagen4-ultra-luxury-product.png",
     "google/imagen4-ultra",
     "Luxury watch floating above a reflective surface, dramatic studio lighting, golden accents, bokeh background, premium product photography, hyper-detailed",
     1536, 864),

    ("imagen4-ultra-mercury-morph.png",
     "google/imagen4-ultra",
     "Liquid mercury morphing into a geometric sphere, chrome reflections, abstract satisfying loop aesthetic, studio lighting on dark background, 3D render, ultra-detailed",
     1536, 864),

    ("imagen4-ultra-concert-volumetric.png",
     "google/imagen4-ultra",
     "Dramatic concert stage with volumetric laser beams cutting through smoke, silhouette of performer, neon purple and blue lighting, music video aesthetic, cinematic wide shot",
     1536, 864),

    # --- kling-3-0-review.md ---
    ("imagen4-ultra-kling-samurai-scene.png",
     "google/imagen4-ultra",
     "Cinematic samurai standing in a field of red spider lilies at sunset, traditional armor, wind-blown petals, dramatic orange sky, Japanese landscape, movie poster quality",
     1536, 864),

    # --- sora-2-api-guide.md ---
    ("imagen4-ultra-glass-sphere-physics.png",
     "google/imagen4-ultra",
     "Photorealistic glass sphere rolling down a white marble staircase, realistic physics, light refracting through glass, caustics, clean architectural interior, studio lighting",
     1536, 864),

    # --- veo-3-1-api-guide.md ---
    ("imagen4-ultra-aerial-fjord.png",
     "google/imagen4-ultra",
     "Aerial drone shot over a misty Norwegian fjord at sunrise, dramatic cliffs, turquoise water, low hanging clouds, golden morning light, professional landscape photography, 4K quality",
     1536, 864),

    # --- generate-100-videos-week.md ---
    ("ideogram-v3-batch-workflow.jpg",
     "ideogram-ai/ideogram-v3-quality",
     'Clean infographic diagram showing "Batch Video Generation Workflow" with three steps: "Upload Assets" > "Select Models" > "Generate at Scale", modern flat design, Atlas Cloud branding colors purple and blue',
     1536, 864),
]


def submit_generation(name, model, prompt, width, height):
    """Submit an image generation request, return prediction ID."""
    resp = requests.post(
        f"{BASE_URL}/model/generateImage",
        headers=HEADERS,
        json={"model": model, "prompt": prompt, "width": width, "height": height}
    )
    data = resp.json()
    if data.get("code") != 200:
        print(f"  ERROR submitting {name}: {data}", file=sys.stderr)
        return None
    pred_id = data["data"]["id"]
    print(f"  Submitted {name} -> {pred_id} (model: {model.split('/')[0]})")
    return pred_id


def poll_result(pred_id, timeout=120):
    """Poll for completion, return output URL."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{BASE_URL}/model/prediction/{pred_id}",
            headers=HEADERS
        )
        data = resp.json()["data"]
        status = data["status"]
        if status == "completed" and data.get("outputs"):
            return data["outputs"][0]
        if status == "failed":
            print(f"  FAILED {pred_id}: {data.get('error')}", file=sys.stderr)
            return None
        time.sleep(3)
    print(f"  TIMEOUT {pred_id}", file=sys.stderr)
    return None


def download_image(url, filepath):
    """Download image to local file."""
    resp = requests.get(url, stream=True)
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    size_kb = os.path.getsize(filepath) / 1024
    print(f"  Downloaded {os.path.basename(filepath)} ({size_kb:.0f} KB)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Submit all generations in parallel
    print(f"\n=== Submitting {len(IMAGES)} image generations ===\n")
    jobs = []
    for name, model, prompt, w, h in IMAGES:
        filepath = os.path.join(OUTPUT_DIR, name)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
            print(f"  SKIP {name} (already exists)")
            continue
        pred_id = submit_generation(name, model, prompt, w, h)
        if pred_id:
            jobs.append((name, pred_id, filepath))
        time.sleep(0.5)  # small delay to avoid rate limiting

    if not jobs:
        print("\nAll images already generated!")
        return

    # Poll for results and download
    print(f"\n=== Waiting for {len(jobs)} results ===\n")
    time.sleep(5)  # initial wait

    for name, pred_id, filepath in jobs:
        url = poll_result(pred_id)
        if url:
            download_image(url, filepath)
        else:
            print(f"  FAILED to get {name}")

    # Also download the test image we already generated
    test_path = os.path.join(OUTPUT_DIR, "flux2pro-product-headphones.jpg")
    if not os.path.exists(test_path) or os.path.getsize(test_path) < 10000:
        print("\n  Downloading earlier test image...")
        download_image(
            "https://d1q70pf5vjeyhc.cloudfront.net/predictions/4e2b0c10acc04a78bbcb534faf27a772/1.jpg",
            test_path
        )

    print(f"\n=== Done! Images saved to {OUTPUT_DIR} ===")
    print(f"Total files: {len(os.listdir(OUTPUT_DIR))}")


if __name__ == "__main__":
    main()
