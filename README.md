# Atlas Cloud Blog Content

SEO-optimized blog articles and marketing content for [Atlas Cloud](https://www.atlascloud.ai).

## Articles

| File | Topic | Target Keywords |
|------|-------|----------------|
| `seedance-2-0-pricing-breakdown.md` | Seedance 2.0 pricing guide | Seedance 2.0 pricing, cost, plans |
| `how-to-use-seedance-2-0-video-generation.md` | Seedance 2.0 tutorial | How to use Seedance 2.0, tutorial, guide |
| `best-seedance-2-0-prompts-guide.md` | 15 best prompts | Seedance 2.0 prompts, prompt guide |
| `kling-3-0-review.md` | Kling 3.0 review | Kling 3.0 review, pricing, API |
| `sora-2-api-guide.md` | Sora 2 API guide | Sora 2 API, pricing, tutorial |
| `veo-3-1-api-guide.md` | Veo 3.1 API guide | Veo 3.1 API, Google Veo 3 pricing |
| `generate-100-videos-week-atlas-cloud.md` | Bulk video generation guide | AI video at scale, bulk video API |
| `image-generation-api-guide.md` | Image generation guide | AI image API, Flux, Imagen 4, Ideogram |

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

## Image & Video Placeholders

- `[IMAGE: description]` placeholders indicate where generated images should be inserted.
- `[VIDEO: description]` placeholders indicate where generated videos should be embedded.

Generate media via Atlas Cloud API and upload to CDN before publishing.
