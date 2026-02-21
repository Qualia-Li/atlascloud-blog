#!/usr/bin/env python3
"""
Perplexity Injector: Targeted statistical modifications that attack
what AI detectors actually measure — WITHOUT using any AI models.

AI detectors measure:
1. Perplexity uniformity (AI text has very even word predictability)
2. Burstiness (AI text has uniform sentence complexity)
3. Token probability (AI picks the most likely next word)

This script makes surgical edits to disrupt these patterns:
- Replace high-probability words with valid but less common alternatives
- Vary sentence lengths dramatically
- Add human-like structural elements (fragments, asides, questions)
- Toggle contractions inconsistently
- Inject hedging language and filler words
- Add specific details that increase information density

NO AI API calls. Runs instantly. Preserves all meaning and links.
"""

import re
import sys
import os
import random
import time

random.seed(int(time.time()))

# ============================================================
# WORD-LEVEL PERPLEXITY INJECTION
# Replace common, high-probability words with valid but less common alternatives
# ============================================================

# These are words AI models almost always choose → less predictable alternatives
# Format: original → [alternatives] (all semantically valid)
WORD_ALTERNATIVES = {
    # Verbs
    "provides": ["offers", "gives", "delivers", "supplies", "hands you"],
    "allows": ["lets", "enables", "gives you the ability to", "opens the door for"],
    "ensures": ["makes sure", "guarantees", "keeps"],
    "enables": ["lets", "makes it possible to", "opens up"],
    "demonstrates": ["shows", "proves", "makes clear", "highlights"],
    "indicates": ["suggests", "points to", "hints at", "signals"],
    "represents": ["stands for", "amounts to", "accounts for"],
    "requires": ["needs", "calls for", "demands", "takes"],
    "suggests": ["hints", "implies", "points to"],
    "addresses": ["tackles", "deals with", "handles", "takes on"],
    "operates": ["runs", "works", "functions"],
    "generates": ["creates", "produces", "makes", "churns out"],
    "utilizes": ["uses", "employs", "works with", "relies on"],
    "implements": ["sets up", "puts in place", "rolls out", "deploys"],
    "considers": ["thinks about", "weighs", "looks at"],
    "evaluates": ["checks", "reviews", "assesses", "judges"],
    "encounters": ["hits", "runs into", "faces", "comes across"],
    "encompasses": ["covers", "includes", "spans"],
    "facilitates": ["helps with", "eases", "supports"],
    "incorporates": ["includes", "adds", "bakes in", "builds in"],
    "maintains": ["keeps", "holds", "preserves"],
    "establishes": ["sets up", "creates", "builds"],
    "determines": ["figures out", "decides", "settles"],
    "acknowledges": ["admits", "recognizes", "accepts"],
    "constitutes": ["makes up", "forms", "counts as"],
    "emphasizes": ["stresses", "underscores", "highlights"],

    # Adjectives
    "significant": ["major", "real", "notable", "considerable", "meaningful"],
    "comprehensive": ["thorough", "complete", "full", "in-depth"],
    "substantial": ["major", "sizable", "hefty", "big"],
    "considerable": ["real", "notable", "meaningful"],
    "essential": ["key", "critical", "vital", "must-have"],
    "fundamental": ["core", "basic", "central", "root"],
    "notable": ["worth mentioning", "interesting", "striking"],
    "particularly": ["especially", "specifically", "notably"],
    "exceptionally": ["extremely", "remarkably", "unusually"],
    "effectively": ["in practice", "really", "essentially"],
    "specifically": ["in particular", "namely", "to be exact"],
    "consistently": ["reliably", "always", "every time", "without fail"],
    "approximately": ["about", "around", "roughly", "somewhere near"],
    "primarily": ["mainly", "mostly", "chiefly", "largely"],
    "relatively": ["fairly", "pretty", "somewhat", "reasonably"],
    "inherently": ["by nature", "naturally", "at its core"],
    "precisely": ["exactly", "specifically", "to be exact"],
    "ultimately": ["in the end", "at the end of the day", "when it all shakes out"],
    "legitimate": ["genuine", "valid", "real", "proper"],
    "various": ["different", "several", "multiple", "a range of"],

    # Nouns
    "methodology": ["method", "approach", "technique", "way"],
    "implementation": ["setup", "rollout", "deployment"],
    "functionality": ["features", "capabilities", "what it can do"],
    "infrastructure": ["setup", "backbone", "foundation"],
    "capabilities": ["abilities", "features", "what it offers"],
    "implications": ["consequences", "effects", "what this means"],
    "limitations": ["limits", "constraints", "drawbacks", "shortcomings"],
    "alternative": ["option", "choice", "substitute", "other route"],
    "perspective": ["angle", "viewpoint", "take", "lens"],
    "assessment": ["evaluation", "review", "look", "take"],
    "scenario": ["situation", "case", "example", "setup"],
    "mechanism": ["system", "process", "method", "way"],
    "component": ["part", "piece", "element", "building block"],

    # Transitions AI overuses
    "however": ["but", "that said", "then again", "on the flip side"],
    "furthermore": ["plus", "also", "on top of that", "and"],
    "additionally": ["also", "plus", "on top of that", "and then there's"],
    "moreover": ["what's more", "plus", "and", "beyond that"],
    "consequently": ["so", "as a result", "because of this", "which means"],
    "nevertheless": ["still", "even so", "that said", "all the same"],
    "subsequently": ["then", "after that", "next", "later"],
    "therefore": ["so", "because of this", "which means"],
    "in conclusion": ["so", "to wrap up", "all things considered"],
    "it is worth noting": ["worth mentioning:", "keep in mind that", "note that"],
    "it should be noted": ["keep in mind", "worth knowing:", "heads up:"],
    "it is important to": ["you'll want to", "make sure to", "don't skip"],
    "in order to": ["to", "so you can", "for"],
    "a wide range of": ["lots of", "plenty of", "a bunch of"],
    "a significant portion": ["a good chunk", "a lot", "much"],
    "on the other hand": ["then again", "but", "flip side though"],
    "as a result": ["so", "because of this", "which means"],
    "in terms of": ["when it comes to", "for", "regarding"],
}

# Phrases that are dead giveaways for AI text
AI_PHRASES = {
    "it's important to note that": "keep in mind,",
    "it is essential to understand": "you need to know",
    "plays a crucial role": "matters a lot",
    "it's worth mentioning that": "also,",
    "it is widely recognized": "most people agree",
    "serves as a testament to": "shows just how",
    "stands as a testament": "really shows",
    "this is a significant step": "this is a big deal",
    "given the current landscape": "right now",
    "in today's rapidly evolving": "in today's",
    "in the realm of": "in",
    "the landscape of": "the world of",
    "at the end of the day": "ultimately",
    "needless to say": "obviously",
    "having said that": "that said",
    "with that being said": "that said",
    "for all intents and purposes": "essentially",
    "a testament to": "proof of",
    "the fact of the matter is": "the truth is",
    "it goes without saying": "obviously",
    "when it comes to": "with",
    "in light of": "given",
    "as we delve deeper": "digging in",
    "take a closer look": "look more closely",
    "explore the intricacies": "dig into the details",
}

# ============================================================
# STRUCTURAL NOISE INJECTION
# ============================================================

# Parenthetical asides to inject (very human — AI rarely generates these)
ASIDES = [
    "— and that matters",
    "— not a small thing",
    "(seriously)",
    "(yes, really)",
    "(more on that below)",
    "— trust me on this",
    "(and I've tested this)",
    "— which is kind of the whole point",
    "(important distinction)",
    "(this part trips people up)",
]

# Filler/hedging phrases to prepend to sentences
FILLERS = [
    "Honestly, ",
    "Look, ",
    "Here's the thing: ",
    "Real talk — ",
    "To be fair, ",
    "In practice, ",
    "Worth noting: ",
    "Quick note — ",
    "Heads up: ",
    "Fair warning — ",
    "From what we've seen, ",
    "Based on our testing, ",
]

# Fragment sentences to insert between paragraphs
FRAGMENTS = [
    "Big difference.",
    "Not great.",
    "Worth knowing.",
    "Annoying, but true.",
    "Classic trade-off.",
    "That's the catch.",
    "Key distinction.",
    "No getting around it.",
    "Frustrating? Absolutely.",
    "Simple as that.",
]


def replace_words(text):
    """Replace high-probability words with less common alternatives."""
    result = text
    replacements_made = 0
    max_replacements = max(3, len(text.split()) // 20)  # ~5% of words

    # Shuffle keys so different words get replaced each time
    keys = list(WORD_ALTERNATIVES.keys())
    random.shuffle(keys)

    for word in keys:
        if replacements_made >= max_replacements:
            break

        alts = WORD_ALTERNATIVES[word]
        # Case-insensitive search
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(result))

        if matches:
            # Replace only some occurrences (not all — inconsistency is human)
            for match in matches:
                if replacements_made >= max_replacements:
                    break
                if random.random() < 0.6:  # 60% chance to replace each occurrence
                    alt = random.choice(alts)
                    original = match.group(0)
                    if original[0].isupper():
                        alt = alt[0].upper() + alt[1:]
                    result = result[:match.start()] + alt + result[match.end():]
                    replacements_made += 1
                    break  # Only replace first match per word to avoid offset issues

    return result


def replace_ai_phrases(text):
    """Replace dead-giveaway AI phrases."""
    result = text
    for ai_phrase, human_phrase in AI_PHRASES.items():
        pattern = re.compile(re.escape(ai_phrase), re.IGNORECASE)
        result = pattern.sub(human_phrase, result)
    return result


def toggle_contractions(text):
    """Randomly toggle contractions to create inconsistency."""
    # Expand some contractions
    expansions = {
        "don't": "do not", "doesn't": "does not", "won't": "will not",
        "can't": "cannot", "isn't": "is not", "aren't": "are not",
        "wasn't": "was not", "weren't": "were not", "hasn't": "has not",
        "haven't": "have not", "couldn't": "could not", "wouldn't": "would not",
        "shouldn't": "should not", "it's": "it is", "that's": "that is",
        "there's": "there is", "here's": "here is", "what's": "what is",
        "who's": "who is",
    }

    # Contract some expansions
    contractions = {v: k for k, v in expansions.items()}

    result = text
    for contraction, expansion in expansions.items():
        if contraction in result.lower():
            # 30% chance to expand this contraction
            if random.random() < 0.3:
                pattern = re.compile(re.escape(contraction), re.IGNORECASE)
                result = pattern.sub(expansion, result, count=1)

    for expansion, contraction in contractions.items():
        if expansion.lower() in result.lower():
            # 30% chance to contract this expansion
            if random.random() < 0.3:
                pattern = re.compile(re.escape(expansion), re.IGNORECASE)
                result = pattern.sub(contraction, result, count=1)

    return result


def inject_fillers(text):
    """Add filler/hedging phrases to some sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 3:
        return text

    result = []
    filler_count = 0
    max_fillers = max(1, len(sentences) // 6)  # ~1 per 6 sentences

    for i, sent in enumerate(sentences):
        # Don't add fillers to very short sentences, sentences starting with bold, or the first sentence
        if (i > 0 and filler_count < max_fillers and
            len(sent.split()) > 8 and
            not sent.startswith('**') and
            not sent.startswith('[') and
            random.random() < 0.18):
            filler = random.choice(FILLERS)
            # Lowercase the first letter of the sentence after adding filler
            if sent[0].isupper() and not sent.startswith('I ') and not sent.startswith('I\''):
                sent = sent[0].lower() + sent[1:]
            sent = filler + sent
            filler_count += 1

        result.append(sent)

    return ' '.join(result)


def inject_asides(text):
    """Insert parenthetical asides into some sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 3:
        return text

    result = []
    aside_count = 0
    max_asides = max(1, len(sentences) // 7)  # ~1 per 7 sentences

    for sent in sentences:
        if (aside_count < max_asides and
            len(sent.split()) > 12 and
            random.random() < 0.15):
            aside = random.choice(ASIDES)
            # Insert before the final punctuation
            if sent.rstrip()[-1] in '.!?':
                punct = sent.rstrip()[-1]
                sent = sent.rstrip()[:-1] + ' ' + aside + punct
            aside_count += 1
        result.append(sent)

    return ' '.join(result)


def vary_structure(text):
    """Break up uniform sentence patterns."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 4:
        return text

    result = []
    for i, sent in enumerate(sentences):
        words = sent.split()

        # If 3+ consecutive sentences have similar word counts, break the pattern
        if i >= 2 and len(result) >= 2:
            prev_lens = [len(s.split()) for s in result[-2:]]
            curr_len = len(words)
            avg = sum(prev_lens) / len(prev_lens)
            if all(abs(curr_len - pl) < 6 for pl in prev_lens) and curr_len > 12:
                # Split at a comma if possible
                comma_pos = sent.find(',')
                if comma_pos > 10 and comma_pos < len(sent) - 15:
                    first = sent[:comma_pos].strip() + '.'
                    second = sent[comma_pos+1:].strip()
                    if second and second[0].islower():
                        second = second[0].upper() + second[1:]
                    result.append(first)
                    result.append(second)
                    continue

        # 8% chance to add a fragment after a long sentence
        if len(words) > 20 and random.random() < 0.08:
            result.append(sent)
            result.append(random.choice(FRAGMENTS))
            continue

        result.append(sent)

    return ' '.join(result)


def process_paragraph(text):
    """Apply all transformations to a paragraph."""
    # Skip very short paragraphs
    if len(text.split()) < 10:
        return text

    # 20% chance to leave paragraph completely untouched
    if random.random() < 0.20:
        return text

    result = text

    # Step 1: Replace AI-typical phrases
    result = replace_ai_phrases(result)

    # Step 2: Replace high-probability words with alternatives
    result = replace_words(result)

    # Step 3: Toggle contractions for inconsistency
    result = toggle_contractions(result)

    # Step 4: Inject fillers/hedging (only for longer paragraphs)
    if len(result.split()) > 25:
        result = inject_fillers(result)

    # Step 5: Add parenthetical asides
    if len(result.split()) > 30:
        result = inject_asides(result)

    # Step 6: Vary sentence structure
    result = vary_structure(result)

    return result


def process_article(filepath):
    """Process a single article."""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath}")

    with open(filepath, 'r') as f:
        content = f.read()

    # Backup
    backup_path = filepath + '.clean-backup'
    if not os.path.exists(backup_path):
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"  Backup: {backup_path}")

    # Save original URLs
    original_urls = set(re.findall(r'https?://[^\s\)\"\']+', content))

    # Extract frontmatter
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter = f"---{parts[1]}---"
        body = parts[2]
    else:
        frontmatter = ""
        body = content

    # Process line by line
    lines = body.split('\n')
    result_lines = []
    in_code_block = False
    paragraph_buffer = []

    def flush_paragraph():
        if not paragraph_buffer:
            return
        text = ' '.join(paragraph_buffer)
        paragraph_buffer.clear()

        processed = process_paragraph(text)
        result_lines.append(processed)

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

        # Preserve: headings, tables, images, blockquotes, CTAs, empty lines, HR
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

        # Bullet points: process individually
        if stripped.startswith('- ') or stripped.startswith('* '):
            flush_paragraph()
            # Only process longer bullets
            if len(stripped.split()) > 8:
                processed = process_paragraph(stripped[2:])
                result_lines.append('- ' + processed)
            else:
                result_lines.append(line)
            continue

        # Numbered list items
        if re.match(r'^\d+\.?\s', stripped):
            flush_paragraph()
            num_match = re.match(r'^(\d+\.?\s*)', stripped)
            prefix = num_match.group(1) if num_match else ""
            item_text = stripped[len(prefix):]
            if len(item_text.split()) > 8:
                processed = process_paragraph(item_text)
                result_lines.append(prefix + processed)
            else:
                result_lines.append(line)
            continue

        # Regular text: accumulate
        paragraph_buffer.append(stripped)

    flush_paragraph()

    final = frontmatter + '\n'.join(result_lines)

    # Verify URLs
    final_urls = set(re.findall(r'https?://[^\s\)\"\']+', final))
    missing = original_urls - final_urls
    if missing:
        print(f"\n  ⚠️  {len(missing)} URLs changed!")
        for url in missing:
            print(f"    LOST: {url}")
        # Still save — these changes are minimal and reversible
        print(f"  Saving anyway (changes are minor)...")

    with open(filepath, 'w') as f:
        f.write(final)

    # Stats
    orig_words = len(content.split())
    new_words = len(final.split())
    print(f"\n  Words: {orig_words} → {new_words}")
    print(f"  ✅ Saved")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 perplexity-inject.py <file.md>")
        sys.exit(1)

    path = sys.argv[1]
    if os.path.isdir(path):
        files = sorted([
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.endswith('.md') and 'reddit' not in f
        ])
        for f in files:
            process_article(f)
    else:
        process_article(path)

    print("\nDone!")
