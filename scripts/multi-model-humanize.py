#!/usr/bin/env python3
"""
Multi-model humanizer: uses DIFFERENT AI models for different paragraphs
to create inconsistent AI fingerprints that confuse AI detectors.

Also applies aggressive perturbation techniques:
1. Random model selection per paragraph (Gemini, Qwen, GPT, DeepSeek)
2. Sentence-level independent rewriting (breaks contextual patterns)
3. Random preservation of some original sentences (human-AI mix)
4. Word-level synonym injection with unusual choices
5. Deliberate imperfections: fragments, run-ons, colloquialisms
"""

import requests
import json
import re
import sys
import os
import time
import random

random.seed(int(time.time()))

API_KEY = "apikey-e4735068ccdd4955b91db68b1e403176"
BASE_URL = "https://api.atlascloud.ai/v1"

# Different models with different writing fingerprints
MODELS = [
    "google/gemini-2.0-flash",
    "openai/gpt-4o-mini-developer",
    "qwen/qwen3-8b",
    "google/gemini-2.5-flash-lite-developer",
    "deepseek-ai/deepseek-ocr",
]

def chat(prompt, model=None, temperature=0.95, max_tokens=3000):
    """Call Atlas Cloud LLM API with a specific model."""
    if model is None:
        model = random.choice(MODELS)

    for attempt in range(3):
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=120
            )
            data = resp.json()
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                return content
            else:
                print(f"    Unexpected: {str(data)[:100]}", flush=True)
        except Exception as e:
            print(f"    Error (attempt {attempt+1}): {e}", flush=True)
            time.sleep(2)
    return None


def split_sentences(text):
    """Split text into sentences, keeping markdown intact."""
    # Don't split headings, list items, or very short lines
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s for s in sentences if s.strip()]


def rewrite_sentence_batch(sentences, model, context_topic):
    """Rewrite a batch of sentences using a specific model."""
    text = ' '.join(sentences)

    prompt = f"""Rewrite this text. Keep the exact same meaning and all facts/numbers.
Keep any markdown formatting (**bold**, [links](urls), etc.) exactly as-is.
Make it sound natural and human-written. Use contractions. Vary sentence length.
Add slight personality — not robotic, not overly casual. Professional tech blog tone.
Topic context: {context_topic}

Text to rewrite:
{text}

Rewritten text (return ONLY the rewritten text):"""

    result = chat(prompt, model=model, temperature=0.95)
    return result if result else text


def process_section(section, topic):
    """Process a section with multi-model paragraph mixing."""
    lines = section.split('\n')
    result_lines = []

    for line in lines:
        stripped = line.strip()

        # Preserve: headings, tables, code blocks, images, CTAs, empty lines, list formatting
        if (not stripped or
            stripped.startswith('#') or
            stripped.startswith('|') or
            stripped.startswith('```') or
            stripped.startswith('![') or
            stripped.startswith('> [') or
            stripped.startswith('*Image generated') or
            stripped == '---' or
            stripped.startswith('[IMAGE:')):
            result_lines.append(line)
            continue

        # For bullet points, rewrite just the content
        if stripped.startswith('- **') or stripped.startswith('- '):
            # Pick a random model for this bullet
            model = random.choice(MODELS)
            rewritten = rewrite_sentence_batch([stripped], model, topic)
            if rewritten and not rewritten.startswith('```'):
                # Ensure it still starts with -
                if not rewritten.strip().startswith('-'):
                    rewritten = '- ' + rewritten.strip()
                result_lines.append(rewritten)
            else:
                result_lines.append(line)
            time.sleep(0.5)
            continue

        # For regular paragraphs: split into sentences, rewrite in small batches
        # with DIFFERENT models for different sentence groups
        sentences = split_sentences(stripped)

        if len(sentences) <= 1:
            # Short paragraph - 30% chance keep as-is (adds human inconsistency)
            if random.random() < 0.3:
                result_lines.append(line)
            else:
                model = random.choice(MODELS)
                rewritten = rewrite_sentence_batch(sentences, model, topic)
                result_lines.append(rewritten if rewritten else line)
                time.sleep(0.5)
        else:
            # Multi-sentence paragraph: split into groups, each gets a different model
            rewritten_parts = []
            group_size = max(1, len(sentences) // 3)

            for i in range(0, len(sentences), group_size):
                group = sentences[i:i+group_size]

                # 20% chance to keep this group as-is
                if random.random() < 0.2:
                    rewritten_parts.extend(group)
                else:
                    model = random.choice(MODELS)
                    rewritten = rewrite_sentence_batch(group, model, topic)
                    if rewritten:
                        rewritten_parts.append(rewritten)
                    else:
                        rewritten_parts.extend(group)
                    time.sleep(0.5)

            result_lines.append(' '.join(rewritten_parts))

    return '\n'.join(result_lines)


def process_article(filepath):
    """Process a single article."""
    print(f"\n{'='*60}", flush=True)
    print(f"Processing: {filepath}", flush=True)

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

    title_match = re.search(r'title:\s*"([^"]+)"', content)
    topic = title_match.group(1) if title_match else "AI video generation"

    # Split into sections by ## headings
    sections = re.split(r'(^## .+$)', body, flags=re.MULTILINE)

    result_parts = [frontmatter]
    in_code_block = False

    for i, section in enumerate(sections):
        # Check if we're in a code block
        code_count = section.count('```')

        # Skip Related Articles section
        if section.strip().startswith('## Related'):
            result_parts.append(section)
            continue

        # Skip section headings (just add them)
        if section.strip().startswith('## '):
            result_parts.append(section)
            continue

        # Skip very short sections
        plain = re.sub(r'[#*|\s`\[\]]', '', section)
        if len(plain) < 100:
            result_parts.append(section)
            continue

        # Process this section
        print(f"  Section {i+1}/{len(sections)}: processing ({len(section)} chars)...", flush=True)

        # Protect code blocks
        code_blocks = {}
        counter = [0]
        def save_code(match):
            key = f"__CODE_{counter[0]}__"
            code_blocks[key] = match.group(0)
            counter[0] += 1
            return key
        protected = re.sub(r'```[\s\S]*?```', save_code, section)

        # Process
        rewritten = process_section(protected, topic)

        # Restore code blocks
        for key, value in code_blocks.items():
            rewritten = rewritten.replace(key, value)

        result_parts.append(rewritten)

    final = '\n'.join(result_parts)

    # Verify URLs
    original_urls = set(re.findall(r'https?://[^\s\)\"\']+', content))
    final_urls = set(re.findall(r'https?://[^\s\)\"\']+', final))
    missing = original_urls - final_urls
    if missing:
        print(f"  ⚠️  {len(missing)} URLs lost!", flush=True)
        for url in list(missing)[:5]:
            print(f"    {url}", flush=True)

    with open(filepath, 'w') as f:
        f.write(final)

    print(f"  ✅ Saved", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 multi-model-humanize.py <file.md or dir/>")
        sys.exit(1)

    path = sys.argv[1]
    if os.path.isdir(path):
        files = sorted([
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.endswith('.md') and f != 'reddit-comments.md'
        ])
        for f in files:
            process_article(f)
    else:
        process_article(path)

    print("\nDone!", flush=True)
