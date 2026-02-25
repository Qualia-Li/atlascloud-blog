---
name: verify-articles
description: Verify Atlas Cloud blog articles for completeness, broken URLs, and compliance with article requirements. Checks guidance images, media examples, related article cross-references, em dashes, CJK characters, and more.
---

# Verify Articles Skill

Verify all markdown articles in `articles/*.md` against the Atlas Cloud blog article requirements.

## How to Run

Scan all `.md` files in the `articles/` directory (relative to the repo root at `/Users/quanlaili/proj/atlascloud-blog`).

## Checks to Perform

For each article file, run ALL of the following checks:

### 1. YAML Frontmatter
- Must have `title`, `description`, `keywords`, `slug`, `date`, `author`
- `slug` must match the filename (without `.md`)

### 2. Guidance Images (REQUIRED)
Every article MUST contain both API guidance images:
- `![How to create an API key on Atlas Cloud](https://static.atlascloud.ai/uploads/Guidance1_4b3c2abb20.jpg)`
- `![API key management on Atlas Cloud console](https://static.atlascloud.ai/uploads/Guidance2_1eef025803.jpg)`

### 3. Media Examples (REQUIRED)
Determine article type from content, then verify:

**Video model articles** (content mentions Seedance, Kling, Sora, Veo, or video generation as primary topic):
- MUST have at least one YouTube thumbnail link in format: `[![alt](https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)`
- VIDEO_ID must be from the approved list:
  - Seedance 2.0: 8ik_8AHIiqE, a05ZwmGX1-Q, FfW0F5k9VT0, 5G6yZFvnLNQ, INWDLI63z0s, LtKRTycjVRg, nffvWtsue-I, OP0q7xt8DtY, VC0aLZZ6B-k, XMcvZ9Qru4c
  - Kling 3.0: KNFb9xu566M, PrOoWKFfhsU, Ta2nPFaYLy0
  - General comparison: j-qDCyXubyE

**Image model articles** (content focuses on image generation -- Flux, Imagen, Ideogram, etc.):
- MUST have at least one sample generated image (non-guidance `![...](...jpg|png|webp)`)

### 4. Related Articles Cross-References
- Extract all slugs from `## Related Articles` links (pattern: `/blog/SLUG?utm_...`)
- Each slug MUST have a corresponding `articles/SLUG.md` file
- Flag any slug that has no matching local file

### 5. Content Quality
- **No em dashes** (`---` the character U+2014 `\u2014`): must use `--` instead
- **No CJK characters** in English content (Unicode ranges: \u4e00-\u9fff, \u3000-\u303f, \u3040-\u309f, \u30a0-\u30ff, \uff00-\uffef)
- **No broken external media URLs**: Check any non-YouTube, non-guidance image/video URLs (CDN links like `oss-us-west-1.aliyuncs.com`, `cloudfront.net`, `klingai.com`) -- flag URLs from known-temporary CDNs like `v16-kling-fdl.klingai.com` as likely broken

### 6. Atlas Cloud URLs
- `/playground` paths should be flagged (known 404) -- use `/models` instead
- `docs.atlascloud.ai` should be `www.atlascloud.ai/docs` (avoids redirect)

### 7. No Specific Resolution/Framerate Specs for Model Capabilities
- Flag any specific resolution+framerate claims about model capabilities such as: `4K/60fps`, `2K/24fps`, `1080p/30fps`, `1080p/24fps`
- These are problematic because Atlas Cloud may support the same resolutions, making them misleading as competitor differentiators
- Use descriptive terms instead: "ultra-high-definition", "high-definition", "cinematic quality", etc.
- **Exception**: User-facing SETTINGS recommendations (like "Best settings: 1080p" or `"resolution": "1080p"` in code examples) are OK -- only flag model capability claims

## Output Format

Print a report grouped by file, with a summary at the end:

```
=== articles/example-article.md ===
[PASS] Frontmatter: complete
[PASS] Guidance images: 2/2 found
[PASS] Media examples: 3 YouTube videos found
[FAIL] Related articles: "best-sora-2-api-alternatives-2026" has no matching .md file
[FAIL] Content: Em dash found on line 45
[PASS] Atlas Cloud URLs: OK

=== SUMMARY ===
8 articles checked
6 passed all checks
2 articles have issues (12 total issues)
```

Mark each check as [PASS] or [FAIL] with details. At the end, provide a summary count.
