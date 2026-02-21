#!/usr/bin/env python3
"""
Rule-based text humanizer to reduce AI detection scores.
No API calls needed — runs instantly.

Targets the key signals AI detectors look for:
1. Low perplexity (predictable word choices) → inject unusual synonyms
2. Uniform burstiness (similar sentence lengths) → vary dramatically
3. AI-typical phrases → replace with human-typical phrases
4. Formal consistency → mix formal/informal
"""

import re
import sys
import os
import random

random.seed(42)  # Reproducible but randomized

# === AI-TYPICAL PHRASES → HUMAN REPLACEMENTS ===
AI_PHRASES = {
    # Formal connectors AI loves
    "Furthermore,": random.choice(["Plus,", "And also —", "On top of that,", "Oh, and"]),
    "Moreover,": random.choice(["And get this —", "Also worth mentioning:", "Here's another thing:"]),
    "Additionally,": random.choice(["Also,", "And", "Plus,"]),
    "In conclusion,": random.choice(["So yeah,", "Bottom line:", "All in all,"]),
    "It's worth noting that": random.choice(["Thing is,", "Here's what people miss:", "Quick note:"]),
    "It is worth noting that": random.choice(["Thing is,", "Real talk:", "What most people miss:"]),
    "In this guide,": "",  # Remove entirely
    "In this article,": "",
    "In this review,": "",
    "In this section,": "",
    "Let's dive in": "Let's get into it",
    "Let's explore": "Let's look at",
    "without further ado": "",
    "Whether you're a": "If you're a",
    "Whether you are a": "If you're a",
    "wide range of": "ton of",
    "a wide variety of": "all kinds of",
    "utilize": "use",
    "utilize": "use",
    "leveraging": "using",
    "leverage": "use",
    "comprehensive": "full",
    "seamless": "smooth",
    "seamlessly": "smoothly",
    "robust": "solid",
    "cutting-edge": "latest",
    "state-of-the-art": "top-tier",
    "groundbreaking": "seriously impressive",
    "game-changing": "huge",
    "landscape": "space",
    "ecosystem": "space",
    "paradigm": "approach",
    "synergy": "combo",
    "holistic": "overall",
    "streamline": "simplify",
    "optimize": "improve",
    "facilitate": "help with",
    "innovative": "clever",
    "revolutionize": "shake up",
    "empower": "let",
    "delve into": "dig into",
    "delve": "dig",
    "plethora": "bunch",
    "myriad": "ton",
    "paramount": "super important",
    "pivotal": "key",
    "crucial": "important",
    "significant": "big",
    "substantial": "solid",
    "encompasses": "covers",
    "aforementioned": "that",
    "subsequently": "then",
    "nevertheless": "still",
    "notwithstanding": "even so",
    "henceforth": "from now on",
    "thereby": "so",
    "wherein": "where",
    "commenced": "started",
    "terminated": "ended",
    "endeavor": "try",
    "ascertain": "figure out",
    "regarding": "about",
    "pertaining to": "about",
    "in regard to": "about",
    "in terms of": "for",
    "with respect to": "about",
    "in order to": "to",
    "for the purpose of": "to",
    "on the other hand,": "But then again,",
    "as a result,": "So",
    "as a consequence,": "Because of that,",
    "it should be noted": "worth mentioning",
    "it is important to note": "heads up —",
    "it is essential to": "you really need to",
    "needless to say,": "obviously,",
    "at the end of the day,": "when it comes down to it,",
    "having said that,": "that said,",
    "it goes without saying": "obviously",
    "in today's world": "these days",
    "in the current landscape": "right now",
    "moving forward": "going forward",
    "as we move forward": "going forward",
    "first and foremost": "first off",
}

# Sentence starters to inject randomly
HUMAN_STARTERS = [
    "Look, ", "So here's the thing — ", "Real talk: ", "Now, ",
    "OK so ", "Honestly, ", "The way I see it, ", "From what I've seen, ",
]

# Interjections to inject randomly between sentences
INTERJECTIONS = [
    " (which surprised me, honestly.)", " — and yeah, that matters.",
    " — not bad at all.", " (wild, right?).", " — I was impressed.",
    " — no joke.", " which is kinda cool.", " — go figure.",
]


def replace_ai_phrases(text):
    """Replace AI-typical phrases with human alternatives."""
    for ai_phrase, human_phrase in AI_PHRASES.items():
        # Case-insensitive replacement but try to preserve some casing
        pattern = re.compile(re.escape(ai_phrase), re.IGNORECASE)
        text = pattern.sub(human_phrase, text)
    return text


def inject_sentence_variety(text):
    """Add variety to sentence length and structure."""
    lines = text.split('\n')
    result = []

    for line in lines:
        # Skip non-paragraph lines
        if (line.strip().startswith('#') or line.strip().startswith('|') or
            line.strip().startswith('>') or line.strip().startswith('```') or
            line.strip().startswith('[IMAGE:') or line.strip().startswith('- ') or
            line.strip().startswith('**Step') or len(line.strip()) < 10):
            result.append(line)
            continue

        # Process paragraph text
        sentences = re.split(r'(?<=[.!?])\s+', line)
        new_sentences = []

        for i, sent in enumerate(sentences):
            if not sent.strip():
                continue

            # Randomly add a human starter to some sentences (10% chance)
            if random.random() < 0.08 and i > 0 and not sent.startswith(('And', 'But', 'So', 'Or', 'Now', 'Look', 'OK')):
                starter = random.choice(HUMAN_STARTERS)
                # Lowercase the first letter of original
                if sent[0].isupper() and not sent.startswith(('I ', 'I\'', 'Atlas', 'Seedance', 'Kling', 'Sora', 'Veo', 'ByteDance')):
                    sent = starter + sent[0].lower() + sent[1:]
                else:
                    sent = starter + sent

            # Randomly add interjection after some sentences (5% chance)
            if random.random() < 0.05 and sent.endswith('.'):
                interjection = random.choice(INTERJECTIONS)
                sent = sent[:-1] + interjection

            new_sentences.append(sent)

        result.append(' '.join(new_sentences))

    return '\n'.join(result)


def add_contractions(text):
    """Convert formal language to contractions where natural."""
    contractions = {
        "do not": "don't",
        "does not": "doesn't",
        "did not": "didn't",
        "will not": "won't",
        "would not": "wouldn't",
        "could not": "couldn't",
        "should not": "shouldn't",
        "cannot": "can't",
        "is not": "isn't",
        "are not": "aren't",
        "was not": "wasn't",
        "were not": "weren't",
        "have not": "haven't",
        "has not": "hasn't",
        "had not": "hadn't",
        "it is": "it's",
        "that is": "that's",
        "there is": "there's",
        "what is": "what's",
        "who is": "who's",
        "here is": "here's",
        "I am": "I'm",
        "you are": "you're",
        "we are": "we're",
        "they are": "they're",
        "I have": "I've",
        "you have": "you've",
        "we have": "we've",
        "they have": "they've",
        "I will": "I'll",
        "you will": "you'll",
        "we will": "we'll",
        "they will": "they'll",
        "I would": "I'd",
        "you would": "you'd",
        "we would": "we'd",
    }

    for formal, contracted in contractions.items():
        # Only replace in running text, not in headings or code
        text = re.sub(
            r'(?<![#`|])' + re.escape(formal) + r'(?![`|])',
            contracted,
            text,
            flags=re.IGNORECASE
        )

    return text


def protect_and_process(content):
    """Protect code blocks, tables, and links, then process text."""
    # Split frontmatter
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter = f"---{parts[1]}---"
        body = parts[2]
    else:
        frontmatter = ""
        body = content

    # Protect code blocks
    code_blocks = {}
    counter = [0]
    def save_code(match):
        key = f"__CODE_BLOCK_{counter[0]}__"
        code_blocks[key] = match.group(0)
        counter[0] += 1
        return key
    body = re.sub(r'```[\s\S]*?```', save_code, body)

    # Apply humanization
    body = replace_ai_phrases(body)
    body = add_contractions(body)
    body = inject_sentence_variety(body)

    # Restore code blocks
    for key, value in code_blocks.items():
        body = body.replace(key, value)

    return frontmatter + body


def process_file(filepath):
    """Process a single markdown file."""
    print(f"Processing: {filepath}")

    with open(filepath, 'r') as f:
        content = f.read()

    # Count original URLs
    original_urls = set(re.findall(r'https?://[^\s\)\"\']+', content))

    # Process
    result = protect_and_process(content)

    # Verify URLs preserved
    final_urls = set(re.findall(r'https?://[^\s\)\"\']+', result))
    missing = original_urls - final_urls
    if missing:
        print(f"  ⚠️  {len(missing)} URLs lost! NOT saving.")
        for url in missing:
            print(f"    Missing: {url}")
        return False

    with open(filepath, 'w') as f:
        f.write(result)

    # Stats
    orig_words = len(content.split())
    new_words = len(result.split())
    print(f"  ✅ Done: {orig_words} → {new_words} words")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 rule-humanize.py <file.md or directory/>")
        sys.exit(1)

    path = sys.argv[1]
    if os.path.isdir(path):
        files = sorted([
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.endswith('.md') and f != 'reddit-comments.md'
        ])
        for f in files:
            process_file(f)
    else:
        process_file(path)
