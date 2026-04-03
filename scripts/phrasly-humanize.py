#!/usr/bin/env python3
"""Humanize paragraph text in markdown articles using the Phrasly API.

Only humanizes prose paragraphs. Preserves:
- Frontmatter, headings, tables, bullet/numbered lists
- Code blocks, images, links, short lines
"""

import json
import os
import re
import sys
import time
import requests

API_URL = "https://api.phrasly.ai/v1/humanize/"
API_KEY = os.environ.get(
    "PHRASLY_API_KEY",
    "a0c6eeb2cd2aa959865e99bbc5f20bea4ffb47a1f2d6687f622316e65d074cb6",
)
ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "..", "articles")


def humanize_text(text):
    """Send text to Phrasly API and return humanized version."""
    resp = requests.post(
        API_URL,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": API_KEY,
        },
        json={"text": text, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["text"]


def process_article(filepath):
    """Process a single markdown article, humanizing only paragraphs."""
    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"Processing: {filename}")
    print(f"{'='*60}")

    with open(filepath, "r") as f:
        content = f.read()

    lines = content.split("\n")

    in_code_block = False
    in_frontmatter = False
    frontmatter_count = 0

    # Identify paragraph blocks: groups of consecutive paragraph lines
    paragraphs = []  # list of (start_idx, end_idx, combined_text)
    current_start = None
    current_lines = []

    def flush():
        nonlocal current_start, current_lines
        if current_lines:
            text = " ".join(l.strip() for l in current_lines)
            paragraphs.append((current_start, current_start + len(current_lines) - 1, text))
        current_start = None
        current_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Frontmatter tracking
        if stripped == "---":
            frontmatter_count += 1
            if frontmatter_count == 1:
                in_frontmatter = True
            elif frontmatter_count == 2:
                in_frontmatter = False
            flush()
            continue

        if in_frontmatter:
            continue

        # Code block tracking
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            flush()
            continue

        if in_code_block:
            continue

        # Determine if this line is a paragraph line
        is_para = True
        if not stripped:
            is_para = False
        elif stripped.startswith("#"):
            is_para = False
        elif stripped.startswith("|"):
            is_para = False
        elif re.match(r"^[-*+]\s", stripped) or re.match(r"^\d+\.\s", stripped):
            is_para = False
        elif stripped.startswith("[![") or stripped.startswith("!["):
            is_para = False
        elif stripped.startswith(">"):
            is_para = False
        elif re.match(r"^\[.*\]\(.*\)$", stripped):
            is_para = False
        elif len(stripped.split()) < 10:
            is_para = False

        if is_para:
            if current_start is None:
                current_start = i
            current_lines.append(line)
        else:
            flush()

    flush()

    print(f"Found {len(paragraphs)} paragraphs to humanize")
    total_words = sum(len(p[2].split()) for p in paragraphs)
    print(f"Total words to humanize: {total_words}")

    # Humanize each paragraph
    for idx, (start, end, text) in enumerate(paragraphs):
        word_count = len(text.split())
        print(
            f"  [{idx+1}/{len(paragraphs)}] Lines {start+1}-{end+1} ({word_count} words)...",
            end=" ",
            flush=True,
        )
        try:
            humanized = humanize_text(text)
            # Replace the original lines with the humanized text
            lines[start] = humanized
            for j in range(start + 1, end + 1):
                lines[j] = "__REMOVE__"
            print("OK", flush=True)
            time.sleep(1)
        except Exception as e:
            print(f"FAILED: {e}", flush=True)

    # Remove placeholder lines and reconstruct
    result_lines = [l for l in lines if l != "__REMOVE__"]
    result = "\n".join(result_lines)

    # Clean up triple+ blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)

    with open(filepath, "w") as f:
        f.write(result)

    print(f"Saved: {filename}")


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            articles = sorted(
                os.path.join(path, f)
                for f in os.listdir(path)
                if f.endswith(".md")
            )
        else:
            articles = [path]
    else:
        articles = sorted(
            os.path.join(ARTICLES_DIR, f)
            for f in os.listdir(ARTICLES_DIR)
            if f.endswith(".md")
        )

    print(f"Found {len(articles)} articles to process")

    for article in articles:
        process_article(article)

    print(f"\nDone! All articles humanized.")


if __name__ == "__main__":
    main()
