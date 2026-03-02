#!/usr/bin/env python3
"""
Fix all PageGun data to exactly match the format produced by PageGun's own publish flow.

Fixes:
1. DB: type='article', config={} (PageGun stores metadata in top-level columns, not config)
2. R2 snapshots: exact format from publish-to-r2.ts
3. R2 index: exact format from r2-snapshot.ts updatePageIndex
"""

import boto3
import json
import requests
from datetime import datetime, timezone

# --- Config ---
PROJECT_ID = "Yd2m7cXN"

SUPABASE_URL = "https://nbsxsmrdqvrsqpspmlfk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ic3hzbXJkcXZyc3Fwc3BtbGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjEyNTI2OSwiZXhwIjoyMDY3NzAxMjY5fQ.K2BNcWF8v3Qau1gNXlvoTlSiB_opzeocbLkgi8abof0"

R2_ENDPOINT = "https://a4fb9d6ecf7e7aae6ae32628de7b2c0e.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "55e9330349b413b9052d8d05ec81c17b"
R2_SECRET_KEY = "825567c9735b09b99d4786d336541fe0d5390255188abd4edd53fd375116e79f"
R2_BUCKET = "pagegun"


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name="auto",
    )


def main():
    s3 = get_s3_client()
    now = datetime.now(timezone.utc).isoformat()

    # Step 1: Fix DB records - set config={} like PageGun's createArticle does
    print("=== Step 1: Fixing DB records ===")
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/pages?project_id=eq.{PROJECT_ID}",
        headers=supabase_headers(),
        json={
            "type": "article",
            "config": {},  # PageGun stores {} for articles - metadata is in top-level columns
        },
    )
    resp.raise_for_status()
    print(f"  Fixed {len(resp.json())} pages in DB")

    # Step 2: Fetch all pages from Supabase (same query as publish-to-r2.ts)
    print("\n=== Step 2: Fetching pages from Supabase ===")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/pages?project_id=eq.{PROJECT_ID}&status=eq.published&select=*",
        headers=supabase_headers(),
    )
    resp.raise_for_status()
    pages = resp.json()
    print(f"  Found {len(pages)} published pages")

    # Step 3: Rebuild R2 snapshots - exact format from publish-to-r2.ts
    print("\n=== Step 3: Rebuilding R2 snapshots ===")
    for page in pages:
        # Exact snapshot format from publish-to-r2.ts lines 42-62
        snapshot = {
            "version": 1,
            "pageId": page["id"],
            "projectId": PROJECT_ID,
            "publishedAt": now,
            "content": {
                "title": page["title"],
                "slug": page["slug"],
                "subroute": page["subroute"],
                "locale": page.get("locale") or "en",
                "type": page["type"],
                "config": page.get("config"),
                "markdown_content": page.get("markdown_content"),
                "meta_title": page.get("meta_title"),
                "meta_description": page.get("meta_description"),
                "description": page.get("description"),
                "og_image_url": page.get("og_image_url"),
                "author": None,  # No ai_authors join needed
                "author_id": page.get("author_id"),
            },
        }

        key = f"pages/{PROJECT_ID}/{page['id']}.json"
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=json.dumps(snapshot),
            ContentType="application/json",
            CacheControl="public, max-age=60, stale-while-revalidate=300",
        )

        # Update r2 fields in DB
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/pages?id=eq.{page['id']}",
            headers=supabase_headers(),
            json={"r2_snapshot_key": key, "r2_published_at": now},
        )
        print(f"  Snapshot: {page['slug']}")

    # Step 4: Rebuild R2 index - exact format from r2-snapshot.ts updatePageIndex
    print("\n=== Step 4: Rebuilding R2 index ===")
    index = {
        "version": 1,
        "projectId": PROJECT_ID,
        "updatedAt": now,
        "pages": [
            {
                "pageId": p["id"],
                "slug": p["slug"],
                "subroute": p["subroute"],
                "locale": p.get("locale") or "en",
                "title": p["title"],
            }
            for p in pages
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
    print(f"  Index: {len(pages)} entries")

    print(f"\n=== Done! All {len(pages)} pages fixed ===")


if __name__ == "__main__":
    main()
