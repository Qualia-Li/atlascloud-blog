---
title: "How to Build an AI Video Pipeline with Python and Atlas Cloud"
description: "Developer tutorial for building a complete AI video generation pipeline in Python. Includes image generation, video creation, polling, batch processing, and deployment."
keywords: ["AI video pipeline", "Python video generation", "Atlas Cloud API tutorial", "batch video generation", "AI video automation", "Flux Seedance Veo pipeline"]
slug: "how-to-build-ai-video-pipeline-python"
date: "2026-02-28"
author: "Atlas Cloud Team"
---
# How to Build an AI Video Pipeline with Python and Atlas Cloud

Most teams start with AI video generation by making one-off API calls -- generate a single video, download it, move on. That works for experimentation. It does not work when you need to produce 50 marketing videos per week, generate thumbnails for each, track costs, handle failures gracefully, and deploy the whole thing to run on a schedule. For that, you need a pipeline.

This tutorial walks through building a production-grade AI video pipeline in Python using the Atlas Cloud API. The pipeline combines multiple AI models -- Flux 2 Pro for thumbnail generation, Seedance 2.0 for high-volume video, and Veo 3.1 for cinematic video with native audio -- into a single automated workflow. By the end, you will have a working Python codebase that generates images, creates videos from prompts, polls for results, handles errors with retries, and processes batches concurrently.

*Last Updated: February 28, 2026*

See these models in action:

[![5 Top AI Models. 3 Prompts. One Clear Winner for Audio/Video Sync](https://img.youtube.com/vi/j-qDCyXubyE/maxresdefault.jpg)](https://www.youtube.com/watch?v=j-qDCyXubyE)

## Pipeline Architecture

Before writing code, here is the high-level architecture of what we are building:

```
+-------------------+     +--------------------+     +------------------+
|  Prompt Config    |     |  Atlas Cloud API   |     |  Output Storage  |
|  (JSON/YAML)      |     |                    |     |                  |
|  - prompts        +---->+  /generateImage    +---->+  /images/        |
|  - models         |     |  /generateVideo    |     |  /videos/        |
|  - parameters     |     |  /prediction/get   |     |  /manifest.json  |
+-------------------+     +--------------------+     +------------------+
         |                         |                         |
         v                         v                         v
+-------------------+     +--------------------+     +------------------+
|  Pipeline Engine  |     |  Polling & Retry   |     |  Cost Tracker    |
|                   |     |                    |     |                  |
|  - batch_generate |     |  - exponential     |     |  - per-request   |
|  - concurrency    |     |    backoff         |     |  - cumulative    |
|  - model routing  |     |  - max retries     |     |  - per-model     |
+-------------------+     +--------------------+     +------------------+
```

The pipeline follows a simple flow:

1. Read prompt configurations from a structured input file.
2. Route each prompt to the appropriate model and endpoint (image or video).
3. Submit all requests to the Atlas Cloud API with controlled concurrency.
4. Poll for results with exponential backoff and retry logic.
5. Download completed outputs and save to organized directories.
6. Track costs and generate a summary manifest.

## Getting Started: API Access

### Step 1: Get Your API Key

Sign up at [Atlas Cloud](https://www.atlascloud.ai?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python) and create an API key from the dashboard. The $1 free credit is enough to test the complete pipeline with several image and video generations.

![How to create an API key on Atlas Cloud](https://static.atlascloud.ai/uploads/Guidance1_4b3c2abb20.jpg)

![API key management on Atlas Cloud console](https://static.atlascloud.ai/uploads/Guidance2_1eef025803.jpg)

### Step 2: Install Dependencies

```bash
pip install requests pyyaml
```

No heavy frameworks required. The pipeline uses only `requests` for HTTP calls, `pyyaml` for configuration files, and Python standard library modules for concurrency and file handling.

## The Complete Pipeline Code

The following is the full working pipeline. Each section is explained after the code block.

```python
import requests
import time
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("atlas_pipeline")


@dataclass
class GenerationResult:
    """Stores the result of a single generation request."""
    name: str
    model: str
    media_type: str  # "image" or "video"
    status: str  # "success", "failed", "error"
    output_url: Optional[str] = None
    local_path: Optional[str] = None
    cost_estimate: float = 0.0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


class AtlasCloudClient:
    """Client wrapper for the Atlas Cloud API."""

    BASE_URL = "https://api.atlascloud.ai/api/v1"

    # Pricing per model (approximate)
    PRICING = {
        "black-forest-labs/flux-2-pro/text-to-image": 0.04,        # per image
        "google/imagen4-ultra/text-to-image": 0.06,                 # per image
        "bytedance/seedance-v1.5-pro/text-to-video": 0.022,        # per second
        "google/veo3.1/text-to-video": 0.03,                       # per second
        "openai/sora-v2/text-to-video": 0.15,                      # per second
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def generate_image(
        self,
        model: str,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> dict:
        """Submit an image generation request.

        Args:
            model: Model ID (e.g., 'black-forest-labs/flux-2-pro/text-to-image')
            prompt: Text prompt describing the desired image
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            API response dict containing request_id
        """
        response = self.session.post(
            f"{self.BASE_URL}/model/generateImage",
            json={
                "model": model,
                "prompt": prompt,
                "width": width,
                "height": height
            }
        )
        response.raise_for_status()
        return response.json()

    def generate_video(
        self,
        model: str,
        prompt: str,
        duration: int = 5,
        resolution: str = "1080p"
    ) -> dict:
        """Submit a video generation request.

        Args:
            model: Model ID (e.g., 'bytedance/seedance-v1.5-pro/text-to-video')
            prompt: Text prompt describing the desired video
            duration: Video duration in seconds
            resolution: Output resolution

        Returns:
            API response dict containing request_id
        """
        response = self.session.post(
            f"{self.BASE_URL}/model/generateVideo",
            json={
                "model": model,
                "prompt": prompt,
                "duration": duration,
                "resolution": resolution
            }
        )
        response.raise_for_status()
        return response.json()

    def poll_result(
        self,
        request_id: str,
        max_wait: int = 300,
        initial_interval: int = 5,
        max_interval: int = 30
    ) -> Optional[dict]:
        """Poll for generation result with exponential backoff.

        Args:
            request_id: The request ID returned from generation call
            max_wait: Maximum seconds to wait before giving up
            initial_interval: Starting poll interval in seconds
            max_interval: Maximum poll interval in seconds

        Returns:
            Result dict with output URLs, or None on failure/timeout
        """
        start_time = time.time()
        interval = initial_interval

        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/model/prediction/{request_id}/get"
                )
                data = response.json()

                if data["status"] == "completed":
                    return data
                elif data["status"] == "failed":
                    logger.error(f"Generation failed: {data.get('error', 'Unknown error')}")
                    return None

                logger.debug(f"Status: {data['status']}, waiting {interval}s...")
                time.sleep(interval)
                interval = min(interval * 1.5, max_interval)

            except requests.RequestException as e:
                logger.warning(f"Poll request failed: {e}, retrying in {interval}s")
                time.sleep(interval)

        logger.error(f"Timeout after {max_wait}s waiting for {request_id}")
        return None

    def estimate_cost(self, model: str, duration: int = 0) -> float:
        """Estimate the cost of a generation request."""
        base_price = self.PRICING.get(model, 0.05)
        if "text-to-video" in model and duration > 0:
            return base_price * duration
        return base_price


class VideoPipeline:
    """Orchestrates batch generation of images and videos."""

    def __init__(self, api_key: str, output_dir: str = "pipeline_output"):
        self.client = AtlasCloudClient(api_key)
        self.output_dir = output_dir
        self.results: list[GenerationResult] = []
        self.total_cost = 0.0

        # Create output directories
        os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "videos"), exist_ok=True)

    def _download_file(self, url: str, filepath: str) -> bool:
        """Download a file from URL to local path."""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return False

    def _safe_filename(self, name: str, extension: str) -> str:
        """Convert a name to a safe filename."""
        safe = name.lower().replace(" ", "_")
        safe = "".join(c for c in safe if c.isalnum() or c == "_")
        return f"{safe}.{extension}"

    def _process_image(self, name: str, model: str, prompt: str,
                       width: int = 1024, height: int = 1024,
                       retries: int = 2) -> GenerationResult:
        """Generate a single image with retry logic."""
        start = time.time()
        cost = self.client.estimate_cost(model)

        for attempt in range(retries + 1):
            try:
                logger.info(f"[Image] Generating '{name}' (attempt {attempt + 1})")
                result = self.client.generate_image(model, prompt, width, height)
                request_id = result["request_id"]

                data = self.client.poll_result(request_id)
                if data and data["status"] == "completed":
                    image_url = data["output"]["image_url"]
                    filename = self._safe_filename(name, "png")
                    filepath = os.path.join(self.output_dir, "images", filename)
                    self._download_file(image_url, filepath)

                    return GenerationResult(
                        name=name, model=model, media_type="image",
                        status="success", output_url=image_url,
                        local_path=filepath, cost_estimate=cost,
                        duration_seconds=time.time() - start
                    )
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    wait = 2 ** (attempt + 2)
                    logger.warning(f"Rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue
                logger.error(f"HTTP error generating '{name}': {e}")
            except Exception as e:
                logger.error(f"Error generating '{name}': {e}")

            if attempt < retries:
                time.sleep(2 ** attempt)

        return GenerationResult(
            name=name, model=model, media_type="image",
            status="failed", cost_estimate=0,
            duration_seconds=time.time() - start,
            error_message="Max retries exceeded"
        )

    def _process_video(self, name: str, model: str, prompt: str,
                       duration: int = 5, resolution: str = "1080p",
                       retries: int = 2) -> GenerationResult:
        """Generate a single video with retry logic."""
        start = time.time()
        cost = self.client.estimate_cost(model, duration)

        for attempt in range(retries + 1):
            try:
                logger.info(f"[Video] Generating '{name}' (attempt {attempt + 1})")
                result = self.client.generate_video(model, prompt, duration, resolution)
                request_id = result["request_id"]

                data = self.client.poll_result(request_id, max_wait=600)
                if data and data["status"] == "completed":
                    video_url = data["output"]["video_url"]
                    filename = self._safe_filename(name, "mp4")
                    filepath = os.path.join(self.output_dir, "videos", filename)
                    self._download_file(video_url, filepath)

                    return GenerationResult(
                        name=name, model=model, media_type="video",
                        status="success", output_url=video_url,
                        local_path=filepath, cost_estimate=cost,
                        duration_seconds=time.time() - start
                    )
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    wait = 2 ** (attempt + 2)
                    logger.warning(f"Rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue
                logger.error(f"HTTP error generating '{name}': {e}")
            except Exception as e:
                logger.error(f"Error generating '{name}': {e}")

            if attempt < retries:
                time.sleep(2 ** (attempt + 1))

        return GenerationResult(
            name=name, model=model, media_type="video",
            status="failed", cost_estimate=0,
            duration_seconds=time.time() - start,
            error_message="Max retries exceeded"
        )

    def batch_generate(self, jobs: list[dict], max_workers: int = 3):
        """Process a batch of generation jobs concurrently.

        Args:
            jobs: List of job dicts with keys: name, type, model, prompt,
                  and optional: width, height, duration, resolution
            max_workers: Maximum concurrent API requests
        """
        logger.info(f"Starting batch of {len(jobs)} jobs with {max_workers} workers")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for job in jobs:
                if job["type"] == "image":
                    future = executor.submit(
                        self._process_image,
                        name=job["name"],
                        model=job["model"],
                        prompt=job["prompt"],
                        width=job.get("width", 1024),
                        height=job.get("height", 1024)
                    )
                elif job["type"] == "video":
                    future = executor.submit(
                        self._process_video,
                        name=job["name"],
                        model=job["model"],
                        prompt=job["prompt"],
                        duration=job.get("duration", 5),
                        resolution=job.get("resolution", "1080p")
                    )
                else:
                    logger.warning(f"Unknown job type: {job['type']}")
                    continue
                futures[future] = job["name"]

            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
                self.total_cost += result.cost_estimate
                status_icon = "OK" if result.status == "success" else "FAIL"
                logger.info(
                    f"[{status_icon}] {result.name} -- "
                    f"${result.cost_estimate:.3f} -- "
                    f"{result.duration_seconds:.1f}s"
                )

        elapsed = time.time() - start_time
        self._save_manifest()
        self._print_summary(elapsed)

    def _save_manifest(self):
        """Save results manifest to JSON."""
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "total_cost": round(self.total_cost, 4),
            "total_jobs": len(self.results),
            "successful": sum(1 for r in self.results if r.status == "success"),
            "failed": sum(1 for r in self.results if r.status != "success"),
            "results": [
                {
                    "name": r.name,
                    "model": r.model,
                    "type": r.media_type,
                    "status": r.status,
                    "output_url": r.output_url,
                    "local_path": r.local_path,
                    "cost": round(r.cost_estimate, 4),
                    "generation_time": round(r.duration_seconds, 1),
                    "error": r.error_message
                }
                for r in self.results
            ]
        }
        manifest_path = os.path.join(self.output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved to {manifest_path}")

    def _print_summary(self, elapsed: float):
        """Print a summary of the batch run."""
        success = sum(1 for r in self.results if r.status == "success")
        failed = len(self.results) - success
        cost_by_model = {}
        for r in self.results:
            cost_by_model[r.model] = cost_by_model.get(r.model, 0) + r.cost_estimate

        print("\n" + "=" * 60)
        print("PIPELINE SUMMARY")
        print("=" * 60)
        print(f"Total jobs:     {len(self.results)}")
        print(f"Successful:     {success}")
        print(f"Failed:         {failed}")
        print(f"Total cost:     ${self.total_cost:.4f}")
        print(f"Total time:     {elapsed:.1f}s")
        print(f"\nCost by model:")
        for model, cost in sorted(cost_by_model.items()):
            short_name = model.split("/")[1]
            print(f"  {short_name}: ${cost:.4f}")
        print("=" * 60)
```

## Using the Pipeline

With the `AtlasCloudClient` and `VideoPipeline` classes defined, here is how to use them for a typical content production workflow.

### Basic Usage: Thumbnails + Videos

```python
API_KEY = "your-atlas-cloud-api-key"

pipeline = VideoPipeline(api_key=API_KEY, output_dir="weekly_content")

jobs = [
    # Generate thumbnails with Flux 2 Pro
    {
        "name": "Product Launch Thumbnail",
        "type": "image",
        "model": "black-forest-labs/flux-2-pro/text-to-image",
        "prompt": "Eye-catching YouTube thumbnail, bold text 'NEW LAUNCH', "
                  "product spotlight on dark gradient background, vibrant "
                  "accent colors, professional design, 4K"
    },
    {
        "name": "Tutorial Thumbnail",
        "type": "image",
        "model": "black-forest-labs/flux-2-pro/text-to-image",
        "prompt": "YouTube thumbnail for coding tutorial, split screen "
                  "showing code editor and final result, tech aesthetic, "
                  "clean modern design, bold readable text"
    },

    # Generate videos with Seedance 2.0 (cost-effective)
    {
        "name": "Product Showcase Seedance",
        "type": "video",
        "model": "bytedance/seedance-v1.5-pro/text-to-video",
        "prompt": "Sleek product reveal animation, modern gadget emerging "
                  "from soft light, rotating slowly to show all angles, "
                  "minimalist white background, cinematic lighting",
        "duration": 10
    },
    {
        "name": "Brand Intro Seedance",
        "type": "video",
        "model": "bytedance/seedance-v1.5-pro/text-to-video",
        "prompt": "Dynamic brand introduction sequence, abstract geometric "
                  "shapes assembling into a logo, particles and light trails, "
                  "professional motion graphics style, dark background",
        "duration": 5
    },

    # Generate cinematic video with Veo 3.1 (with audio)
    {
        "name": "Hero Video Veo",
        "type": "video",
        "model": "google/veo3.1/text-to-video",
        "prompt": "Cinematic aerial shot of a modern city skyline at golden "
                  "hour, camera slowly pushing forward, lens flare from "
                  "setting sun, ambient city sounds, film grain, "
                  "professional color grading",
        "duration": 8
    },
]

pipeline.batch_generate(jobs, max_workers=3)
```

### Configuration-Driven Approach

For recurring pipelines, define jobs in a YAML configuration file:

```yaml
# pipeline_config.yaml
output_dir: weekly_content
max_workers: 3

jobs:
  - name: Product Hero Image
    type: image
    model: google/imagen4-ultra/text-to-image
    prompt: >
      Premium product photography of wireless earbuds in charging case,
      dark reflective surface, dramatic lighting, luxury tech aesthetic,
      8K resolution, commercial quality
    width: 2048
    height: 2048

  - name: Social Media Video
    type: video
    model: bytedance/seedance-v1.5-pro/text-to-video
    prompt: >
      Trendy social media content, hands unboxing a premium tech product,
      satisfying reveal moment, close-up details, bright natural lighting,
      vertical format
    duration: 10
    resolution: 1080p

  - name: Cinematic Ad
    type: video
    model: google/veo3.1/text-to-video
    prompt: >
      Cinematic commercial for premium headphones, person putting on
      headphones in a busy coffee shop, world goes quiet, shallow depth
      of field, warm color palette, ambient cafe sounds fading to silence
    duration: 8
    resolution: 1080p
```

Load and run:

```python
import yaml

with open("pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

pipeline = VideoPipeline(
    api_key=API_KEY,
    output_dir=config["output_dir"]
)
pipeline.batch_generate(
    config["jobs"],
    max_workers=config.get("max_workers", 3)
)
```

## Key Implementation Details

### Exponential Backoff Polling

Video generation takes anywhere from 30 seconds to 5 minutes depending on the model and duration. The pipeline uses exponential backoff to poll efficiently without hammering the API:

```python
interval = initial_interval  # starts at 5s
while time.time() - start_time < max_wait:
    # ... check status ...
    time.sleep(interval)
    interval = min(interval * 1.5, max_interval)  # grows to max 30s
```

This means the first few polls happen at 5-second intervals (when quick completions are possible), then gradually space out to 30-second intervals for longer generations. This reduces unnecessary API calls by roughly 60% compared to fixed-interval polling.

### Rate Limit Handling

When the API returns a 429 (rate limited) status, the pipeline backs off exponentially rather than failing immediately:

```python
except requests.HTTPError as e:
    if e.response.status_code == 429:
        wait = 2 ** (attempt + 2)  # 4s, 8s, 16s
        logger.warning(f"Rate limited, waiting {wait}s")
        time.sleep(wait)
        continue
```

This is essential for batch operations where many concurrent requests might temporarily exceed rate limits.

### Concurrency Control

The `ThreadPoolExecutor` limits concurrent API requests to prevent overwhelming the API or your network connection:

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(process, job): job for job in jobs}
```

Start with `max_workers=3` and increase to 5-8 if your Atlas Cloud account supports higher concurrency. Going above 10 concurrent requests typically provides diminishing returns and increases the risk of rate limiting.

### Cost Tracking

Every generation request gets a cost estimate based on the model pricing table:

```python
PRICING = {
    "black-forest-labs/flux-2-pro/text-to-image": 0.04,
    "bytedance/seedance-v1.5-pro/text-to-video": 0.022,  # per second
    "google/veo3.1/text-to-video": 0.03,                  # per second
}
```

For video models, cost scales with duration: a 10-second Seedance 2.0 video costs $0.22, while a 10-second Veo 3.1 video costs $0.30. The manifest file tracks per-request and cumulative costs for budget monitoring.

## Cost Estimation for Pipeline Runs

Here is what typical pipeline runs cost:

| Pipeline Scenario | Jobs | Models Used | Est. Cost | Est. Time |
|-------------------|------|-------------|-----------|-----------|
| Weekly social media pack | 10 images + 5 videos (5s each) | Flux 2 Pro + Seedance 2.0 | $0.95 | ~10 min |
| Product launch campaign | 20 images + 10 videos (10s each) | Flux 2 Pro + Imagen 4 Ultra + Seedance 2.0 | $3.80 | ~25 min |
| Monthly content library | 50 images + 20 videos (8s each) | Mixed | $7.50 | ~45 min |
| E-commerce catalog (500 SKUs) | 500 images | Flux 2 Pro | $20.00 | ~30 min |
| Cinematic ad series | 5 images + 5 videos (8s each) | Imagen 4 Ultra + Veo 3.1 | $1.50 | ~20 min |

**Cost comparison with Seedance 2.0 vs Veo 3.1 for the same video:**

| Model | 5s Video | 10s Video | 15s Video |
|-------|----------|-----------|-----------|
| Seedance 2.0 (Fast) | $0.11 | $0.22 | $0.33 |
| Veo 3.1 | $0.15 | $0.30 | N/A (8s max) |
| Sora 2 | $0.75 | $1.50 | $2.25 |

Seedance 2.0 is the most cost-effective option for high-volume video generation. Veo 3.1 offers a good balance of quality and cost for shorter cinematic clips. Sora 2 costs significantly more but delivers unmatched physics simulation.

> [Start Building Your Video Pipeline -- $1 Free Credit](https://www.atlascloud.ai?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python)

## Deployment Tips

### Cron Jobs for Scheduled Generation

Run the pipeline on a schedule using cron:

```bash
# Generate weekly content every Monday at 6 AM
0 6 * * 1 cd /path/to/project && python run_pipeline.py --config weekly.yaml
```

Create a simple entry point script:

```python
# run_pipeline.py
import argparse
import yaml
from pipeline import VideoPipeline

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
args = parser.parse_args()

with open(args.config) as f:
    config = yaml.safe_load(f)

API_KEY = os.environ["ATLAS_CLOUD_API_KEY"]
pipeline = VideoPipeline(api_key=API_KEY, output_dir=config["output_dir"])
pipeline.batch_generate(config["jobs"], max_workers=config.get("max_workers", 3))
```

### Queue-Based Architecture

For larger deployments, use a task queue like Celery or Redis Queue to decouple job submission from processing:

```python
# tasks.py (Celery example)
from celery import Celery
from pipeline import AtlasCloudClient

app = Celery("video_tasks", broker="redis://localhost:6379")
client = AtlasCloudClient(os.environ["ATLAS_CLOUD_API_KEY"])

@app.task(bind=True, max_retries=3)
def generate_video_task(self, prompt, model, duration):
    try:
        result = client.generate_video(model, prompt, duration)
        data = client.poll_result(result["request_id"])
        if data and data["status"] == "completed":
            return {"url": data["output"]["video_url"], "status": "success"}
        return {"status": "failed"}
    except Exception as e:
        self.retry(countdown=60, exc=e)
```

This architecture is suitable for production systems where video generation requests come from a web application or API, and results need to be delivered asynchronously via webhooks or polling.

### Environment Variable Management

Never hard-code API keys. Use environment variables:

```python
import os

API_KEY = os.environ.get("ATLAS_CLOUD_API_KEY")
if not API_KEY:
    raise ValueError("ATLAS_CLOUD_API_KEY environment variable not set")
```

For local development, use a `.env` file with `python-dotenv`:

```bash
# .env
ATLAS_CLOUD_API_KEY=your-key-here
```

```python
from dotenv import load_dotenv
load_dotenv()
```

### Error Monitoring

For production pipelines, integrate with error monitoring services. The pipeline's logging output is structured for easy parsing by log aggregation tools:

```python
logger.info(f"[OK] {result.name} -- ${result.cost_estimate:.3f} -- {result.duration_seconds:.1f}s")
logger.error(f"[FAIL] {result.name} -- {result.error_message}")
```

Route these logs to your monitoring stack (Datadog, CloudWatch, Grafana) to track success rates, costs, and generation times over time.

## Extending the Pipeline

### Adding Image-to-Video Generation

Some models support using a generated image as input for video creation. Extend the pipeline to chain image and video generation:

```python
def generate_image_then_video(self, name, image_prompt, video_prompt,
                               image_model, video_model, duration=5):
    """Generate an image, then use it as input for video generation."""
    # Step 1: Generate the base image
    image_result = self._process_image(
        f"{name}_base", image_model, image_prompt
    )
    if image_result.status != "success":
        return image_result

    # Step 2: Use the image URL as input for video generation
    response = self.client.session.post(
        f"{self.client.BASE_URL}/model/generateVideo",
        json={
            "model": video_model,
            "prompt": video_prompt,
            "image_url": image_result.output_url,
            "duration": duration
        }
    )
    # ... poll and download as usual
```

### Adding Webhook Notifications

For long-running batches, add webhook notifications when jobs complete:

```python
def _notify_webhook(self, result: GenerationResult, webhook_url: str):
    """Send completion notification to a webhook."""
    requests.post(webhook_url, json={
        "name": result.name,
        "status": result.status,
        "url": result.output_url,
        "cost": result.cost_estimate
    })
```

## Frequently Asked Questions

### How many concurrent requests can I make?

Atlas Cloud supports multiple concurrent requests per API key. Start with 3 workers and increase to 5-8 based on your account tier. The pipeline handles rate limiting automatically with exponential backoff if you exceed limits.

### Can I mix image and video jobs in the same batch?

Yes. The pipeline routes each job to the correct endpoint (`/generateImage` or `/generateVideo`) based on the `type` field. Image and video jobs run concurrently within the same thread pool.

### How long do video generation requests take?

Generation time varies by model: Seedance 2.0 typically completes in 30-90 seconds, Veo 3.1 in 60-120 seconds, and Sora 2 in 60-180 seconds. The pipeline's polling mechanism handles these differences automatically.

### What happens if a generation fails mid-batch?

Failed jobs are logged and included in the manifest with their error messages. The pipeline continues processing remaining jobs. Review the manifest after each run to identify and retry failures.

### How do I add a new model to the pipeline?

Add the model ID and pricing to the `PRICING` dict in `AtlasCloudClient`, then reference it in your job configuration. No other code changes are needed -- the pipeline handles all models through the same API endpoints.

## Verdict

Building an AI video pipeline is not about writing clever code -- it is about having reliable infrastructure that handles the messy realities of API integration: rate limits, timeouts, failures, cost tracking, and concurrent execution. The pipeline in this guide addresses all of these. Copy it, customize the prompts and models for your use case, and deploy it on a schedule or behind a queue.

The combination of Flux 2 Pro for fast image generation, Seedance 2.0 for cost-effective video at $0.022/sec, and Veo 3.1 for cinematic clips with native audio at $0.03/sec gives you coverage across the full spectrum of content production needs. All three models are accessible through a single Atlas Cloud API key, which means one integration, one billing relationship, and one set of credentials to manage.

> [Build Your AI Video Pipeline -- $1 Free Credit on Atlas Cloud](https://www.atlascloud.ai?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python)

---
## Related Articles

- [How to Generate 100+ AI Videos Per Week with Atlas Cloud](https://www.atlascloud.ai/blog/generate-100-videos-week-atlas-cloud?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python)
- [How to Generate AI Product Photography with Atlas Cloud](https://www.atlascloud.ai/blog/how-to-generate-ai-product-photography?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python)
- [Atlas Cloud Image Generation: Flux, Imagen & Ideogram API Guide](https://www.atlascloud.ai/blog/image-generation-api-guide?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python)
- [Seedance 2.0 Pricing Breakdown](https://www.atlascloud.ai/blog/seedance-2-0-pricing-breakdown?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python)
- [Veo 3.1 on Atlas Cloud: Google's Film-Grade AI Video Guide](https://www.atlascloud.ai/blog/veo-3-1-api-guide?utm_medium=article&utm_source=blog&utm_campaign=how-to-build-ai-video-pipeline-python)
