# Atlas Cloud Blog Content

SEO-optimized blog articles and marketing content for [Atlas Cloud](https://www.atlascloud.ai).

## Architecture

Atlas Cloud is a blog/content site. Articles are written as markdown files in this repo and uploaded to **PageGun** (the hosting platform at `~/proj/pagegun`) via the upload script. PageGun stores the articles in Supabase + Cloudflare R2 and serves them at `pagegun.com/p/Yd2m7cXN/articles/{slug}`.

- **Project ID**: `Yd2m7cXN`
- **User ID**: `1fcb7bc9-f747-4b81-b205-c1c970ac10aa`
- **Live URL pattern**: `https://www.pagegun.com/p/Yd2m7cXN/articles/{slug}`
- **Image CDN**: `https://fs.pagegun.com/u/{user_id}/images/{filename}`
- **Static assets**: `https://static.atlascloud.ai/uploads/`

### Workflow

1. Write/edit articles in `articles/*.md` (with YAML frontmatter)
2. Add sample images to `resources/samples/`
3. Run `python3 scripts/upload-to-pagegun.py` to upload everything (images to R2, articles to Supabase, snapshots to R2)
4. Local preview: run PageGun dev server (`cd ~/proj/pagegun && pnpm dev`) then visit `http://localhost:3000/p/Yd2m7cXN/articles/{slug}`

## Articles

### Video Generation API Guides

| File | Description |
|------|-------------|
| `veo-3-1-api-guide.md` | Google Veo 3.1 API guide on Atlas Cloud. Film-grade AI video with native audio at $0.03/sec, Python examples, and comparisons. |
| `sora-2-api-guide.md` | Sora 2 API guide on Atlas Cloud. OpenAI's video generator with pricing, Python code examples, and comparisons to top models. |
| `kling-3-0-review.md` | Complete Kling 3.0 review with features, pricing tiers, API access, free credits, and comparisons to Seedance, Sora, and Veo. |
| `kling-video-o3-api-guide.md` | Kling Video O3 API guide on Atlas Cloud. Omni multimodal video-to-video, reference-to-video, and style transfer capabilities. |
| `wan-2-6-api-guide.md` | Wan 2.6 API guide on Atlas Cloud. Alibaba's budget video generator at $0.07/sec with Python examples and model comparisons. |
| `hailuo-2-3-api-guide.md` | Hailuo 2.3 API guide on Atlas Cloud. MiniMax's anime and illustration video AI at $0.08/sec with Python examples and tips. |
| `luma-ray-3-api-guide.md` | Luma Ray 3 API guide on Atlas Cloud. The first reasoning AI video model at $0.10/sec with Python examples and comparisons. |
| `pixverse-v4-5-api-guide.md` | PixVerse V4.5 API guide on Atlas Cloud. Over 20 cinematic camera controls at $0.09/sec with Python examples and comparisons. |
| `vidu-q3-api-guide.md` | Vidu Q3 API guide on Atlas Cloud. AI video with native audio and Smart Cuts at $0.07/sec, Python examples, and comparisons. |

### Video Generation -- Seedance 2.0

| File | Description |
|------|-------------|
| `how-to-use-seedance-2-0-video-generation.md` | Step-by-step guide to generating AI videos with Seedance 2.0. Includes working prompts, API examples, and optimization tips. |
| `best-seedance-2-0-prompts-guide.md` | 15 proven Seedance 2.0 prompts for viral AI video content. Covers cinematic, product, social media, and creative video styles. |
| `seedance-2-0-pricing-breakdown.md` | Full Seedance 2.0 pricing breakdown for 2026. Compare Jimeng, Dreamina plans, and third-party API costs with free credits. |

### Video Generation Comparisons & Guides

| File | Description |
|------|-------------|
| `best-ai-video-generation-models-2026.md` | Compare the best AI video models of 2026. Seedance 2.0, Kling 3.0, Veo 3.1, Sora 2, Wan 2.6, and Hailuo 2.3 fully ranked. |
| `seedance-vs-kling-vs-sora-vs-veo.md` | Head-to-head comparison of the top 4 AI video models in 2026. Seedance 2.0 vs Kling 3.0 vs Sora 2 vs Veo 3.1 on all metrics. |
| `cheapest-ai-video-generation-api-2026.md` | Compare AI video API pricing for 2026. Per-second and per-video costs for Seedance, Kling, Sora, Veo, Wan, and more models. |
| `ai-image-to-video-models-compared.md` | Compare the best AI image-to-video models in 2026. Seedance, Kling, Wan, Hailuo, Vidu, PixVerse, and Luma with benchmarks. |
| `ai-video-models-native-audio-compared.md` | Compare AI video models with native audio generation. Veo 3.1 vs Kling 3.0 vs Vidu Q3 on audio quality, sync, and pricing. |

### Image Generation API Guides

| File | Description |
|------|-------------|
| `image-generation-api-guide.md` | Complete guide to AI image generation APIs on Atlas Cloud. Compare Flux 2 Pro, Imagen 4, and Ideogram v3 with code examples. |
| `flux-2-pro-deep-dive.md` | Deep dive into Flux 2 Pro by Black Forest Labs. 32B parameters, photorealism, reference images, and text rendering via API. |
| `imagen-4-ultra-api-guide.md` | Google Imagen 4 Ultra API guide on Atlas Cloud. Three quality tiers from $0.04 to $0.08 with best text accuracy available. |
| `nano-banana-2-api-guide.md` | Google Nano Banana 2 API guide on Atlas Cloud. Pricing, Python examples, 3D figurine generation tips, and model comparisons. |
| `seedream-v5-lite-api-guide.md` | ByteDance Seedream v5.0 Lite API guide on Atlas Cloud. Fast image generation at $0.026/pic with Python examples and tips. |
| `z-image-turbo-api-guide.md` | Z-Image Turbo API guide on Atlas Cloud. The cheapest AI image generation at just $0.01 per image, ultra-fast and open source. |

### Image Generation Comparisons & Prompts

| File | Description |
|------|-------------|
| `best-ai-image-generation-models-2026.md` | Compare the best AI image models in 2026. Flux 2 Pro, Imagen 4 Ultra, Nano Banana 2, Seedream, Z-Image Turbo, and Ideogram. |
| `cheapest-ai-image-generation-api-2026.md` | Compare AI image API pricing for 2026. Per-image costs for Z-Image Turbo, Seedream, Flux, Imagen, Nano Banana, and others. |
| `nano-banana-2-prompts-guide.md` | 15+ proven Nano Banana 2 prompts for 3D figurines, character art, and product shots. Includes prompt structure and examples. |

### Tutorials & How-To Guides

| File | Description |
|------|-------------|
| `how-to-build-ai-video-pipeline-python.md` | Build a complete AI video generation pipeline in Python with Atlas Cloud. Covers image gen, video creation, and batch processing. |
| `generate-100-videos-week-atlas-cloud.md` | Generate 100+ AI marketing videos per week for under $50 using Atlas Cloud. Step-by-step with cost breakdowns and automation. |
| `how-to-create-ai-product-videos.md` | Create AI product videos at scale for e-commerce and marketing. Python batch scripts, prompt templates, and cost analysis. |
| `how-to-generate-ai-product-photography.md` | Generate AI product photos with Flux 2 Pro, Imagen 4 Ultra, and Nano Banana 2. Prompt templates, batch scripts, and costs. |

## Repo Structure

```
articles/       -- Blog article markdown (.md) and PDFs (.pdf)
resources/      -- Reference docs, images, videos, YouTube links, Google Docs links
scripts/        -- Utility scripts (SEO checker, etc.)
```

## SEO Checker

```bash
# Check a single article
python3 scripts/seo-checker.py articles/seedance-2-0-pricing-breakdown.md

# Check all articles
python3 scripts/seo-checker.py articles/
```

Checks: H1/H2/H3 structure, links & UTM tracking, content length, keyword density, meta tags, images/alt text, CTAs, FAQ sections, related articles.

## UTM Convention

All Atlas Cloud links use: `utm_medium=article&utm_source=blog&utm_campaign={topic-slug}`

## Resources

- `resources/youtube-videos.md` -- All YouTube videos referenced in articles (from @AtlasCloudAI channel)
- `resources/google-docs-links.md` -- Google Doc links for all articles

Images and videos should be stored in `resources/` (not `articles/`).
