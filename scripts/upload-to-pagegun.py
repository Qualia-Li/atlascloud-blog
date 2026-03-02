#!/usr/bin/env python3
"""Upload all blog articles and images to PageGun (Supabase + R2)."""

import boto3
import yaml
import json
import os
import re
import sys
import requests
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

# --- Config ---
PROJECT_ID = "Yd2m7cXN"
USER_ID = "1fcb7bc9-f747-4b81-b205-c1c970ac10aa"

SUPABASE_URL = "https://nbsxsmrdqvrsqpspmlfk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ic3hzbXJkcXZyc3Fwc3BtbGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjEyNTI2OSwiZXhwIjoyMDY3NzAxMjY5fQ.K2BNcWF8v3Qau1gNXlvoTlSiB_opzeocbLkgi8abof0"

R2_ENDPOINT = "https://a4fb9d6ecf7e7aae6ae32628de7b2c0e.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "55e9330349b413b9052d8d05ec81c17b"
R2_SECRET_KEY = "825567c9735b09b99d4786d336541fe0d5390255188abd4edd53fd375116e79f"
R2_BUCKET = "pagegun"
R2_PUBLIC_URL = "https://fs.pagegun.com"

ARTICLES_DIR = Path(__file__).parent.parent / "articles"
SAMPLES_DIR = Path(__file__).parent.parent / "resources" / "samples"


def nanoid(size=8):
    """Generate a nanoid-like ID."""
    import string, random
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=size))


def get_s3_client():
    """Create R2 (S3-compatible) client."""
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name="auto",
    )


def upload_image_to_r2(s3, filepath):
    """Upload an image to R2 and return the public URL."""
    filename = os.path.basename(filepath)
    key = f"u/{USER_ID}/images/{filename}"

    with open(filepath, "rb") as f:
        content = f.read()

    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=content,
        ContentType="image/png",
    )
    url = f"{R2_PUBLIC_URL}/{key}"
    print(f"  Uploaded image: {filename} -> {url}")
    return filename, url


def parse_frontmatter(md_text):
    """Parse YAML frontmatter from markdown."""
    if not md_text.startswith("---"):
        return {}, md_text

    parts = md_text.split("---", 2)
    if len(parts) < 3:
        return {}, md_text

    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return frontmatter or {}, body


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_existing_pages():
    """Get existing pages for this project."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/pages",
        headers=supabase_headers(),
        params={"project_id": f"eq.{PROJECT_ID}", "select": "id,slug,title"},
    )
    resp.raise_for_status()
    return {p["slug"]: p for p in resp.json()}


def upsert_page(page_data, existing_pages):
    """Insert or update a page in Supabase."""
    slug = page_data["slug"]

    if slug in existing_pages:
        # Update existing
        page_id = existing_pages[slug]["id"]
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/pages?id=eq.{page_id}",
            headers=supabase_headers(),
            json=page_data,
        )
    else:
        # Insert new
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/pages",
            headers=supabase_headers(),
            json=page_data,
        )

    resp.raise_for_status()
    result = resp.json()
    action = "Updated" if slug in existing_pages else "Created"
    page_id = result[0]["id"] if result else page_data["id"]
    print(f"  {action}: {slug} (id={page_id})")
    return result[0] if result else page_data


def publish_to_r2(s3, page_data):
    """Publish page snapshot to R2 for static serving."""
    page_id = page_data["id"]
    snapshot = {
        "version": 1,
        "pageId": page_id,
        "projectId": PROJECT_ID,
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "content": {
            "title": page_data["title"],
            "slug": page_data.get("slug"),
            "subroute": page_data.get("subroute"),
            "locale": page_data.get("locale", "en"),
            "type": page_data.get("type", "articles"),
            "markdown_content": page_data.get("markdown_content"),
            "meta_title": page_data.get("title"),
            "meta_description": page_data.get("description"),
            "description": page_data.get("description"),
            "og_image_url": page_data.get("og_image_url"),
            "author_id": page_data.get("author_id"),
        },
    }
    if page_data.get("config"):
        snapshot["content"]["config"] = page_data["config"]

    snapshot_key = f"pages/{PROJECT_ID}/{page_id}.json"
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=snapshot_key,
        Body=json.dumps(snapshot),
        ContentType="application/json",
        CacheControl="public, max-age=60, stale-while-revalidate=300",
    )

    # Update page with snapshot key
    now = datetime.now(timezone.utc).isoformat()
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/pages?id=eq.{page_id}",
        headers=supabase_headers(),
        json={"r2_snapshot_key": snapshot_key, "r2_published_at": now},
    )
    return snapshot_key


def update_page_index(s3, all_pages):
    """Update the project page index in R2."""
    index = {
        "version": 1,
        "projectId": PROJECT_ID,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "pages": [
            {
                "pageId": p["id"],
                "slug": p.get("slug"),
                "subroute": p.get("subroute", "articles"),
                "locale": p.get("locale", "en"),
                "title": p["title"],
            }
            for p in all_pages
        ],
    }
    index_key = f"pages/{PROJECT_ID}/index.json"
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=index_key,
        Body=json.dumps(index),
        ContentType="application/json",
        CacheControl="public, max-age=60, stale-while-revalidate=300",
    )
    print(f"\n  Updated page index: {index_key} ({len(all_pages)} pages)")


def main():
    s3 = get_s3_client()

    # 1. Upload images to R2
    print("=== Uploading images to R2 ===")
    image_urls = {}
    for img_path in sorted(SAMPLES_DIR.glob("*.png")):
        filename, url = upload_image_to_r2(s3, img_path)
        image_urls[filename] = url

    # 2. Get existing pages
    print("\n=== Checking existing pages ===")
    existing_pages = get_existing_pages()
    print(f"  Found {len(existing_pages)} existing pages")

    # 3. Process and upload articles
    print("\n=== Uploading articles ===")
    all_pages = []
    md_files = sorted(ARTICLES_DIR.glob("*.md"))
    print(f"  Found {len(md_files)} articles")

    for md_path in md_files:
        md_text = md_path.read_text()
        frontmatter, body = parse_frontmatter(md_text)

        if not frontmatter.get("title"):
            print(f"  SKIP (no title): {md_path.name}")
            continue

        slug = frontmatter.get("slug", md_path.stem)

        # Rewrite local image paths to R2 URLs
        for filename, url in image_urls.items():
            body = body.replace(f"../resources/samples/{filename}", url)

        # Build config
        categories = frontmatter.get("keywords", [])[:5]
        config = {
            "title": frontmatter["title"],
            "meta_title": frontmatter["title"],
            "description": frontmatter.get("description", ""),
            "meta_description": frontmatter.get("description", ""),
            "categories": categories,
        }

        # Use first image as featured image / og_image
        og_image = None
        # Check for first image in markdown body
        img_match = re.search(r'!\[.*?\]\((https://[^\)]+)\)', body)
        if img_match:
            og_image = img_match.group(1)

        page_id = nanoid(8)
        page_data = {
            "id": page_id,
            "user_id": USER_ID,
            "title": frontmatter["title"],
            "slug": slug,
            "subroute": "articles",
            "locale": "en",
            "type": "article",
            "status": "published",
            "description": frontmatter.get("description", ""),
            "markdown_content": body,
            "config": config,
            "categories": categories,
            "project_id": PROJECT_ID,
            "og_image_url": og_image,
        }

        result = upsert_page(page_data, existing_pages)
        # Use the actual id from DB for snapshots
        page_data["id"] = result["id"]
        all_pages.append(page_data)

    # 4. Publish all pages to R2 snapshots
    print("\n=== Publishing snapshots to R2 ===")
    for page_data in all_pages:
        key = publish_to_r2(s3, page_data)
        print(f"  Published: {page_data['slug']} -> {key}")

    # 5. Update page index
    print("\n=== Updating page index ===")
    update_page_index(s3, all_pages)

    print(f"\n=== Done! {len(all_pages)} articles uploaded ===")


if __name__ == "__main__":
    main()
