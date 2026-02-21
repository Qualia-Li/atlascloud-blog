#!/usr/bin/env python3
"""
Aggressive humanizer: Combines multi-model AI rewriting with statistical noise injection.

The strategy:
1. Each paragraph gets a DIFFERENT "voice/personality" prompt + different model
2. After AI rewrite, inject "human noise" — things no AI would produce:
   - Parenthetical asides
   - Sentence fragments
   - Self-corrections
   - Specific numbers/references
   - Register shifts (formal→casual mid-paragraph)
   - Unconventional word choices
3. Randomly preserve 25-35% of original text untouched

This attacks the statistical properties that detectors measure:
- Perplexity variance (burstiness)
- Token probability uniformity
- Sentence length distribution
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

MODELS = [
    "google/gemini-2.0-flash",
    "openai/gpt-4o-mini-developer",
    "qwen/qwen3-8b",
    "google/gemini-2.5-flash-lite-developer",
    "deepseek-ai/deepseek-ocr",
]

# Different "personalities" for rewriting — each produces a different voice
REWRITE_STYLES = [
    # Style 1: Experienced dev talking to a colleague
    """Rewrite this as if you're a senior developer explaining it to a teammate during a code review.
Use contractions freely. Throw in a specific detail or two. Keep it professional but not stiff.
You can start sentences with "And" or "But" or "So". Vary your sentence lengths — mix short punchy ones
with longer explanations. Add ONE parenthetical aside somewhere.""",

    # Style 2: Tech blogger who's a bit opinionated
    """Rewrite this as a tech blogger who has strong opinions but backs them up.
Use "I" or "we" where natural. Include at least one rhetorical question.
Don't use words like "comprehensive", "robust", "streamlined", "leverage", or "utilize" — those scream AI.
Mix up your sentence lengths. One very short sentence (under 6 words). One longer one (25+ words).""",

    # Style 3: Matter-of-fact analyst
    """Rewrite this in a dry, factual tone. Short sentences. No fluff. Just the data and what it means.
Avoid adjectives where possible. State numbers and facts plainly.
Include one aside that starts with a dash — like this one. End one sentence with a period and start
the next with "Which" or "That" as a sentence fragment.""",

    # Style 4: Enthusiastic but knowledgeable writer
    """Rewrite this as someone who's genuinely excited about the topic but still knows their stuff.
Use at least one exclamation mark — but only one, don't overdo it. Include a comparison to something
concrete (a real product, a real number, a real scenario). Keep sentences varied.
One sentence should be a question you then immediately answer.""",

    # Style 5: Casual explainer (think newsletter style)
    """Rewrite this in a friendly newsletter tone. Like you're writing a Substack post.
Start one sentence with "Look," or "Here's the thing:" or "Real talk:".
Use at least one em dash. Use contractions. Drop one sentence that's just a fragment — no verb needed.
Keep technical accuracy but make it feel like you're having a conversation.""",

    # Style 6: Documentation-adjacent but human
    """Rewrite this like it belongs in slightly informal documentation. Clear, direct, but with personality.
Use "you" and "your" to address the reader directly. Include one specific example or scenario.
Vary paragraph rhythm — don't let every sentence be the same structure.
Replace at least one common word with a less obvious synonym.""",
]

# Human noise: parenthetical asides to inject randomly
ASIDES = [
    "(and honestly, that matters more than most people realize)",
    "(which, if you think about it, is pretty wild)",
    "(worth noting here)",
    "(at least in my experience)",
    "(no, really)",
    "(your mileage may vary, obviously)",
    "(for what it's worth)",
    "(not gonna lie)",
    "(this is the part most guides skip over)",
    "(and this is where it gets interesting)",
    "(bear with me here)",
    "(spoiler: it's not as complicated as it sounds)",
    "(yes, that's the actual number)",
    "(I double-checked this)",
    "(more on this in a sec)",
]

# Self-correction phrases
SELF_CORRECTIONS = [
    "Actually, let me rephrase that.",
    "Well, that's not entirely accurate —",
    "OK wait, to be more precise:",
    "Let me back up for a second.",
    "Actually, scratch that —",
]

# Transitional fragments (no verb — very human)
FRAGMENTS = [
    "Big difference.",
    "Not ideal.",
    "Pretty significant.",
    "Game changer, honestly.",
    "Interesting wrinkle here.",
    "Worth repeating.",
    "Key point.",
    "Quick aside.",
    "The takeaway?",
    "Bottom line here.",
]

# Words AI overuses → human alternatives
WORD_SWAPS = {
    "utilize": "use",
    "comprehensive": "thorough",
    "robust": "solid",
    "streamlined": "clean",
    "leverage": "use",
    "facilitate": "help with",
    "implement": "set up",
    "functionality": "features",
    "significant": "real",
    "subsequently": "then",
    "furthermore": "also",
    "additionally": "plus",
    "consequently": "so",
    "nevertheless": "still",
    "predominantly": "mostly",
    "substantial": "big",
    "demonstrates": "shows",
    "exceptional": "excellent",
    "innovative": "fresh",
    "seamlessly": "smoothly",
    "effortlessly": "easily",
    "cutting-edge": "latest",
    "game-changing": "major",
    "paradigm": "approach",
    "holistic": "complete",
    "synergy": "combo",
    "ecosystem": "setup",
    "scalable": "flexible",
    "optimized": "tuned",
    "delve": "dig",
    "realm": "space",
    "landscape": "scene",
    "pivotal": "key",
    "paramount": "crucial",
    "myriad": "tons of",
    "plethora": "bunch of",
    "multifaceted": "complex",
    "endeavor": "effort",
    "commencing": "starting",
    "in conclusion": "so",
    "it is worth noting": "note that",
    "it's important to note": "worth mentioning:",
    "it should be noted": "keep in mind",
    "in today's rapidly evolving": "in today's",
    "at the end of the day": "ultimately",
}


def chat(prompt, model=None, temperature=0.95, max_tokens=3000):
    """Call Atlas Cloud LLM API."""
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


def inject_human_noise(text):
    """Post-process text to inject statistically improbable elements."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 2:
        return text

    result = []
    for i, sent in enumerate(sentences):
        # 15% chance: inject a parenthetical aside after this sentence
        if random.random() < 0.15 and len(sent) > 30:
            aside = random.choice(ASIDES)
            # Insert aside before the final period
            if sent.rstrip().endswith('.'):
                sent = sent.rstrip()[:-1] + ' ' + aside + '.'
            else:
                sent = sent + ' ' + aside

        # 8% chance: add a fragment after this sentence
        if random.random() < 0.08:
            result.append(sent)
            result.append(random.choice(FRAGMENTS))
            continue

        # 5% chance: add a self-correction before next sentence
        if random.random() < 0.05 and i < len(sentences) - 1:
            result.append(sent)
            result.append(random.choice(SELF_CORRECTIONS))
            continue

        result.append(sent)

    return ' '.join(result)


def swap_ai_words(text):
    """Replace AI-typical words with human alternatives."""
    result = text
    for ai_word, human_word in WORD_SWAPS.items():
        # Case-insensitive replacement, preserving first-letter case
        pattern = re.compile(re.escape(ai_word), re.IGNORECASE)
        def replacer(match):
            original = match.group(0)
            if original[0].isupper():
                return human_word.capitalize()
            return human_word
        result = pattern.sub(replacer, result)
    return result


def vary_sentence_lengths(text):
    """Ensure sentence lengths are varied (human-like burstiness)."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 3:
        return text

    result = []
    for i, sent in enumerate(sentences):
        words = sent.split()
        # If three consecutive sentences are similar length (±5 words), break the pattern
        if i >= 2 and len(result) >= 2:
            prev_lens = [len(s.split()) for s in result[-2:]]
            curr_len = len(words)
            if all(abs(curr_len - pl) < 5 for pl in prev_lens):
                # Split a long sentence or merge with next
                if curr_len > 15 and ',' in sent:
                    parts = sent.split(',', 1)
                    result.append(parts[0].strip() + '.')
                    result.append(parts[1].strip().capitalize() if parts[1].strip() else '')
                    continue

        result.append(sent)

    return ' '.join(s for s in result if s.strip())


def rewrite_paragraph(text, topic):
    """Rewrite a single paragraph with a random style and model."""
    style = random.choice(REWRITE_STYLES)
    model = random.choice(MODELS)

    prompt = f"""{style}

Keep ALL factual information, numbers, URLs, and markdown formatting exactly as-is.
Do NOT add any prefix like "Here's the rewrite:" — just output the rewritten text directly.
Topic context: {topic}

Text to rewrite:
{text}"""

    result = chat(prompt, model=model, temperature=random.uniform(0.85, 1.0))

    if result:
        # Clean up any "here's the rewrite" prefix
        result = re.sub(r'^(Here\'s?|Below is|The rewritten)[^:]*:\s*', '', result, flags=re.IGNORECASE)
        # Clean up markdown code fences if wrapped
        result = re.sub(r'^```\w*\n?', '', result)
        result = re.sub(r'\n?```$', '', result)
        return result.strip()
    return text


def process_article(filepath):
    """Process a single article with aggressive humanization."""
    print(f"\n{'='*60}", flush=True)
    print(f"Processing: {filepath}", flush=True)

    with open(filepath, 'r') as f:
        content = f.read()

    # Backup original
    backup_path = filepath + '.backup'
    if not os.path.exists(backup_path):
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"  Backup saved to {backup_path}", flush=True)

    # Extract URLs for verification
    original_urls = set(re.findall(r'https?://[^\s\)\"\']+', content))

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

    # Process line by line
    lines = body.split('\n')
    result_lines = []
    in_code_block = False
    paragraph_buffer = []

    def flush_paragraph():
        """Process accumulated paragraph lines."""
        if not paragraph_buffer:
            return
        text = ' '.join(paragraph_buffer)
        paragraph_buffer.clear()

        # Skip very short text
        plain = re.sub(r'[#*|\s`\[\]()]', '', text)
        if len(plain) < 80:
            result_lines.append(text)
            return

        # 30% chance: keep original (creates human inconsistency in the mix)
        if random.random() < 0.30:
            print(f"    [KEPT] {text[:60]}...", flush=True)
            result_lines.append(text)
            return

        # Rewrite with random style + model
        print(f"    [REWRITE] {text[:60]}...", flush=True)
        rewritten = rewrite_paragraph(text, topic)

        # Post-process: swap AI words
        rewritten = swap_ai_words(rewritten)

        # Post-process: inject human noise
        rewritten = inject_human_noise(rewritten)

        # Post-process: vary sentence lengths
        rewritten = vary_sentence_lengths(rewritten)

        result_lines.append(rewritten)
        time.sleep(0.3)

    for line in lines:
        stripped = line.strip()

        # Track code blocks
        if stripped.startswith('```'):
            flush_paragraph()
            in_code_block = not in_code_block
            result_lines.append(line)
            continue

        if in_code_block:
            result_lines.append(line)
            continue

        # Preserve: headings, tables, images, CTAs, empty lines, HR, blockquotes
        if (not stripped or
            stripped.startswith('#') or
            stripped.startswith('|') or
            stripped.startswith('![') or
            stripped.startswith('> ') or
            stripped.startswith('*Image generated') or
            stripped == '---' or
            stripped.startswith('[IMAGE:')):
            flush_paragraph()
            result_lines.append(line)
            continue

        # Bullet points: rewrite individually
        if stripped.startswith('- ') or stripped.startswith('* '):
            flush_paragraph()
            plain_bullet = re.sub(r'[#*|\s`\[\]()]', '', stripped)
            if len(plain_bullet) > 60:
                # 35% chance keep as-is
                if random.random() < 0.35:
                    result_lines.append(line)
                else:
                    model = random.choice(MODELS)
                    style = random.choice(REWRITE_STYLES[:3])  # Use simpler styles for bullets
                    prompt = f"""{style}

Keep all markdown formatting (**bold**, [links](urls)) exactly as-is. Keep it as a single bullet point.
Return ONLY the bullet point text (starting with "- ").

Bullet to rewrite:
{stripped}"""
                    rewritten = chat(prompt, model=model, temperature=0.9)
                    if rewritten:
                        rewritten = re.sub(r'^(Here\'s?|Below)[^:]*:\s*', '', rewritten, flags=re.IGNORECASE).strip()
                        rewritten = re.sub(r'^```\w*\n?', '', rewritten)
                        rewritten = re.sub(r'\n?```$', '', rewritten)
                        if not rewritten.startswith('- ') and not rewritten.startswith('* '):
                            rewritten = '- ' + rewritten
                        rewritten = swap_ai_words(rewritten)
                        result_lines.append(rewritten)
                    else:
                        result_lines.append(line)
                    time.sleep(0.3)
            else:
                result_lines.append(line)
            continue

        # Numbered lists
        if re.match(r'^\d+\.?\s', stripped):
            flush_paragraph()
            plain_item = re.sub(r'[#*|\s`\[\]()]', '', stripped)
            if len(plain_item) > 60:
                if random.random() < 0.35:
                    result_lines.append(line)
                else:
                    num_match = re.match(r'^(\d+\.?\s*)', stripped)
                    prefix = num_match.group(1) if num_match else ""
                    item_text = stripped[len(prefix):]
                    model = random.choice(MODELS)
                    prompt = f"""Rewrite this list item naturally. Keep all facts, links, and formatting.
Return ONLY the rewritten text (without the number prefix).

{item_text}"""
                    rewritten = chat(prompt, model=model, temperature=0.9)
                    if rewritten:
                        rewritten = re.sub(r'^(Here\'s?|Below)[^:]*:\s*', '', rewritten, flags=re.IGNORECASE).strip()
                        rewritten = re.sub(r'^\d+\.?\s*', '', rewritten)  # Remove if model added number
                        rewritten = swap_ai_words(rewritten)
                        result_lines.append(f"{prefix}{rewritten}")
                    else:
                        result_lines.append(line)
                    time.sleep(0.3)
            else:
                result_lines.append(line)
            continue

        # Regular text: accumulate into paragraph buffer
        paragraph_buffer.append(stripped)

    # Flush any remaining paragraph
    flush_paragraph()

    final = frontmatter + '\n'.join(result_lines)

    # Verify URLs
    final_urls = set(re.findall(r'https?://[^\s\)\"\']+', final))
    missing = original_urls - final_urls
    if missing:
        print(f"\n  ⚠️  {len(missing)} URLs lost! Restoring from backup...", flush=True)
        for url in missing:
            print(f"    MISSING: {url}", flush=True)
        # Don't save if URLs are lost — too risky
        print(f"  ❌ NOT SAVED due to missing URLs. Fix manually.", flush=True)
        # Save to a .humanized file instead
        alt_path = filepath.replace('.md', '.humanized.md')
        with open(alt_path, 'w') as f:
            f.write(final)
        print(f"  Saved draft to {alt_path}", flush=True)
        return

    with open(filepath, 'w') as f:
        f.write(final)
    print(f"\n  ✅ Saved successfully", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 aggressive-humanize.py <file.md>")
        sys.exit(1)

    path = sys.argv[1]
    process_article(path)
    print("\nDone!", flush=True)
