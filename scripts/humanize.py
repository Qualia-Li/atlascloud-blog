#!/usr/bin/env python3
"""
Humanize articles using backtranslation + LLM rewriting via Atlas Cloud API.
Strategy: translate to Chinese → back to English → polish. This breaks AI patterns.
"""

import requests
import json
import re
import sys
import os
import time

API_KEY = "apikey-e4735068ccdd4955b91db68b1e403176"
BASE_URL = "https://api.atlascloud.ai/v1"

def chat(prompt, system="You are a helpful translator and editor.", temperature=0.9, max_tokens=4000):
    """Call Atlas Cloud LLM API."""
    for attempt in range(3):
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.0-flash",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=120
            )
            data = resp.json()
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                # Strip thinking tags if present
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                return content
            else:
                print(f"  Unexpected response: {json.dumps(data)[:200]}", flush=True)
        except Exception as e:
            print(f"  API error (attempt {attempt+1}): {e}", flush=True)
            time.sleep(5)
    return None


def split_into_sections(body):
    """Split markdown body into logical sections based on ## headings."""
    sections = []
    current = []

    for line in body.split("\n"):
        if line.startswith("## ") and current:
            sections.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current))

    return sections


def is_preserved_section(section):
    """Check if a section should be preserved as-is."""
    stripped = section.strip()
    # Related articles sections
    if stripped.startswith("## Related Articles"):
        return True
    # Very short sections
    if len(stripped) < 50:
        return True
    return False


def extract_protected_blocks(text):
    """Extract code blocks, tables, image placeholders, and URLs for protection."""
    protected = {}
    counter = [0]

    def protect(match):
        key = f"__PROTECTED_{counter[0]}__"
        protected[key] = match.group(0)
        counter[0] += 1
        return key

    # Protect code blocks
    text = re.sub(r'```[\s\S]*?```', protect, text)
    # Protect tables (lines starting with |)
    text = re.sub(r'(?m)^\|.+\|$', protect, text)
    # Protect image placeholders
    text = re.sub(r'\[IMAGE:[^\]]+\]', protect, text)
    # Protect blockquote CTAs
    text = re.sub(r'(?m)^> \[.+\].*$', protect, text)
    # Protect markdown links (but keep the text)
    # Actually, let's protect the entire link syntax
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', protect, text)
    # Protect horizontal rules
    text = re.sub(r'(?m)^---$', protect, text)

    return text, protected


def restore_protected_blocks(text, protected):
    """Restore protected blocks."""
    for key, value in protected.items():
        text = text.replace(key, value)
    return text


def backtranslate_section(section, topic):
    """
    Backtranslation: English → Chinese → English.
    This naturally introduces variation that breaks AI detection patterns.
    """
    # Extract and protect special blocks
    text, protected = extract_protected_blocks(section)

    # Skip if mostly protected content
    plain_text = text
    for key in protected:
        plain_text = plain_text.replace(key, "")
    if len(plain_text.strip()) < 100:
        return section

    # Step 1: Translate to Chinese
    print("    Step 1: Translating to Chinese...", flush=True)
    chinese = chat(
        f"""Translate the following English text to Chinese (Simplified).
Keep all tokens that look like __PROTECTED_X__ exactly as they are - do not translate them.
Keep all markdown headings (lines starting with #, ##, ###) in English but translate the rest.
Keep all **bold** and *italic* formatting markers.

Text:
{text}""",
        system="You are a professional English-to-Chinese translator. Translate naturally and idiomatically.",
        temperature=0.7
    )

    if not chinese:
        print("    Failed to translate to Chinese, skipping section", flush=True)
        return section

    # Step 2: Translate back to English with a human blogger voice
    print("    Step 2: Translating back to English with human voice...", flush=True)
    english = chat(
        f"""Translate the following Chinese text back to English. Write it as if you're a casual tech blogger who has personally tested the product.

IMPORTANT RULES:
- Keep all __PROTECTED_X__ tokens exactly as they are
- Keep markdown heading levels (##, ###) exactly as they are
- Keep **bold** and *italic* formatting
- Write in FIRST PERSON (I, we, my)
- Use contractions (don't, won't, it's, that's)
- Be opinionated and casual - use phrases like "honestly", "look", "the thing is"
- Vary sentence length A LOT - some very short (3-5 words), some long
- Start some sentences with And, But, So, Now
- Add personal touches like "in my testing", "from what I've seen"
- Sound like a real person, NOT like AI

Chinese text:
{chinese}""",
        system="You are a casual American tech blogger translating Chinese back to English. Write naturally and personally, like you're talking to a friend about tech.",
        temperature=1.0
    )

    if not english:
        print("    Failed to translate back, skipping section", flush=True)
        return section

    # Restore protected blocks
    result = restore_protected_blocks(english, protected)

    return result


def process_article(filepath):
    """Process a single article file."""
    print(f"\n{'='*60}", flush=True)
    print(f"Processing: {filepath}", flush=True)
    print(f"{'='*60}", flush=True)

    with open(filepath, 'r') as f:
        content = f.read()

    # Extract frontmatter
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter = f"---{parts[1]}---"
        body = parts[2]
    else:
        frontmatter = ""
        body = content

    # Get topic
    title_match = re.search(r'title:\s*"([^"]+)"', content)
    topic = title_match.group(1) if title_match else "AI video generation"

    # Split into sections
    sections = split_into_sections(body)
    print(f"  Found {len(sections)} sections", flush=True)

    # Process each section
    result_sections = []
    for i, section in enumerate(sections):
        if is_preserved_section(section):
            print(f"  Section {i+1}/{len(sections)}: preserved (special)", flush=True)
            result_sections.append(section)
        elif len(section.strip()) < 100:
            print(f"  Section {i+1}/{len(sections)}: preserved (too short)", flush=True)
            result_sections.append(section)
        else:
            print(f"  Section {i+1}/{len(sections)}: backtranslating ({len(section)} chars)...", flush=True)
            result = backtranslate_section(section, topic)
            result_sections.append(result)
            print(f"    Done.", flush=True)
            time.sleep(3)  # Rate limiting

    # Reconstruct
    final = frontmatter + "\n".join(result_sections)

    # Verify URLs preserved
    original_urls = set(re.findall(r'https?://[^\s\)\"\']+', content))
    final_urls = set(re.findall(r'https?://[^\s\)\"\']+', final))
    missing = original_urls - final_urls
    if missing:
        print(f"\n  ⚠️  WARNING: {len(missing)} URLs lost! Falling back to original for safety.", flush=True)
        for url in missing:
            print(f"    Missing: {url}", flush=True)
        # Don't save if URLs are lost
        return False

    with open(filepath, 'w') as f:
        f.write(final)

    print(f"  ✅ Saved: {filepath}", flush=True)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 humanize.py <article.md or directory/>")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isdir(path):
        files = sorted([
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.endswith('.md') and f != 'reddit-comments.md'
        ])
        for filepath in files:
            process_article(filepath)
    else:
        process_article(path)

    print(f"\n{'='*60}", flush=True)
    print("All done! Run the SEO checker to verify.", flush=True)
    print(f"{'='*60}", flush=True)
