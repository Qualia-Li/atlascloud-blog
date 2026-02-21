#!/usr/bin/env python3
"""
SEO Checker Script for Atlas Cloud Blog Articles
Checks: H1/H2/H3 structure, links, content length, keyword density,
        meta tags, alt text placeholders, title/description length.

Usage:
    python seo-checker.py articles/seedance-2-0-pricing-breakdown.md
    python seo-checker.py articles/  # Check all .md files in directory
"""

import re
import sys
import os
import glob
from collections import Counter
from pathlib import Path


# --- Configuration ---
MIN_WORD_COUNT = 1500
MAX_WORD_COUNT = 5000
IDEAL_KEYWORD_DENSITY_MIN = 0.5   # percent
IDEAL_KEYWORD_DENSITY_MAX = 2.5   # percent
MAX_TITLE_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 160
MIN_INTERNAL_LINKS = 3
MIN_EXTERNAL_LINKS = 1
MIN_H2_COUNT = 3
MIN_H3_COUNT = 2


class SEOChecker:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.raw_content = ""
        self.frontmatter = {}
        self.body = ""
        self.issues = []
        self.warnings = []
        self.passes = []

    def load(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.raw_content = f.read()
        self._parse_frontmatter()

    def _parse_frontmatter(self):
        """Extract YAML frontmatter and body content."""
        if self.raw_content.startswith("---"):
            parts = self.raw_content.split("---", 2)
            if len(parts) >= 3:
                fm_text = parts[1].strip()
                self.body = parts[2].strip()
                for line in fm_text.split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        # Handle arrays
                        if val.startswith("["):
                            val = [
                                v.strip().strip('"').strip("'")
                                for v in val.strip("[]").split(",")
                            ]
                        self.frontmatter[key] = val
            else:
                self.body = self.raw_content
        else:
            self.body = self.raw_content

    def _get_plain_text(self):
        """Strip markdown formatting to get plain text for word count."""
        text = self.body
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Remove inline code
        text = re.sub(r"`[^`]+`", "", text)
        # Remove markdown links but keep text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Remove images
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Remove markdown formatting
        text = re.sub(r"[#*_~>|]", "", text)
        # Remove table separators
        text = re.sub(r"\|?-+\|?", "", text)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def check_title(self):
        """Check title tag length."""
        title = self.frontmatter.get("title", "")
        if not title:
            self.issues.append("MISSING: No title in frontmatter")
            return
        length = len(title)
        if length > MAX_TITLE_LENGTH:
            self.warnings.append(
                f"TITLE LENGTH: {length} chars (max {MAX_TITLE_LENGTH}). "
                f"Will be truncated in Google: \"{title[:MAX_TITLE_LENGTH]}...\""
            )
        else:
            self.passes.append(f"Title length OK: {length}/{MAX_TITLE_LENGTH} chars")

    def check_description(self):
        """Check meta description length."""
        desc = self.frontmatter.get("description", "")
        if not desc:
            self.issues.append("MISSING: No description in frontmatter")
            return
        length = len(desc)
        if length > MAX_DESCRIPTION_LENGTH:
            self.warnings.append(
                f"DESCRIPTION LENGTH: {length} chars (max {MAX_DESCRIPTION_LENGTH}). "
                f"Will be truncated in Google."
            )
        else:
            self.passes.append(f"Description length OK: {length}/{MAX_DESCRIPTION_LENGTH} chars")

    def _strip_code_blocks(self, text):
        """Remove code blocks to avoid false positives in heading/link analysis."""
        return re.sub(r"```[\s\S]*?```", "", text)

    def check_headings(self):
        """Check H1, H2, H3 tag structure."""
        clean_body = self._strip_code_blocks(self.body)
        h1s = re.findall(r"^# (.+)$", clean_body, re.MULTILINE)
        h2s = re.findall(r"^## (.+)$", clean_body, re.MULTILINE)
        h3s = re.findall(r"^### (.+)$", clean_body, re.MULTILINE)

        # H1 checks
        if len(h1s) == 0:
            self.issues.append("MISSING: No H1 tag found")
        elif len(h1s) > 1:
            self.warnings.append(f"MULTIPLE H1: Found {len(h1s)} H1 tags (should be exactly 1)")
        else:
            self.passes.append(f"H1 OK: \"{h1s[0]}\"")

        # H2 checks
        if len(h2s) < MIN_H2_COUNT:
            self.warnings.append(
                f"LOW H2 COUNT: {len(h2s)} H2 tags (recommend {MIN_H2_COUNT}+)"
            )
        else:
            self.passes.append(f"H2 count OK: {len(h2s)} tags")

        # H3 checks
        if len(h3s) < MIN_H3_COUNT:
            self.warnings.append(
                f"LOW H3 COUNT: {len(h3s)} H3 tags (recommend {MIN_H3_COUNT}+)"
            )
        else:
            self.passes.append(f"H3 count OK: {len(h3s)} tags")

        # Report heading structure
        print(f"\n  Heading Structure:")
        for h1 in h1s:
            print(f"    H1: {h1}")
        for h2 in h2s:
            print(f"    H2: {h2}")
        for h3 in h3s:
            print(f"      H3: {h3}")

    def check_links(self):
        """Check internal and external links, UTM parameters."""
        # Find all markdown links
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", self.body)

        internal_links = []
        external_links = []
        atlas_links = []
        links_without_utm = []

        for text, url in links:
            if url.startswith("/") or url.startswith("#"):
                internal_links.append((text, url))
            elif "atlascloud.ai" in url:
                atlas_links.append((text, url))
                if "utm_" not in url:
                    links_without_utm.append((text, url))
            else:
                external_links.append((text, url))

        # Check counts
        total_internal = len(internal_links) + len(atlas_links)
        if total_internal < MIN_INTERNAL_LINKS:
            self.warnings.append(
                f"LOW INTERNAL LINKS: {total_internal} (recommend {MIN_INTERNAL_LINKS}+)"
            )
        else:
            self.passes.append(f"Internal links OK: {total_internal}")

        # Check UTM on Atlas Cloud links
        if links_without_utm:
            self.issues.append(
                f"MISSING UTM: {len(links_without_utm)} Atlas Cloud links without UTM tracking:"
            )
            for text, url in links_without_utm:
                self.issues.append(f"  - [{text}]({url})")
        else:
            if atlas_links:
                self.passes.append(f"UTM tracking OK: All {len(atlas_links)} Atlas Cloud links have UTM params")

        # Check UTM format
        for text, url in atlas_links:
            if "utm_" in url:
                if "utm_medium=article" not in url:
                    self.warnings.append(f"UTM FORMAT: Missing utm_medium=article in: {url[:80]}...")
                if "utm_source=blog" not in url:
                    self.warnings.append(f"UTM FORMAT: Missing utm_source=blog in: {url[:80]}...")
                if "utm_campaign=" not in url:
                    self.warnings.append(f"UTM FORMAT: Missing utm_campaign in: {url[:80]}...")

        # Report link summary
        print(f"\n  Links Summary:")
        print(f"    Internal/blog links: {len(internal_links)}")
        print(f"    Atlas Cloud links: {len(atlas_links)}")
        print(f"    External links: {len(external_links)}")
        print(f"    Total links: {len(links)}")

    def check_content_length(self):
        """Check word count."""
        plain_text = self._get_plain_text()
        word_count = len(plain_text.split())

        if word_count < MIN_WORD_COUNT:
            self.warnings.append(
                f"SHORT CONTENT: {word_count} words (recommend {MIN_WORD_COUNT}+)"
            )
        elif word_count > MAX_WORD_COUNT:
            self.warnings.append(
                f"LONG CONTENT: {word_count} words (recommend under {MAX_WORD_COUNT})"
            )
        else:
            self.passes.append(f"Word count OK: {word_count} words")

        print(f"\n  Content Length: {word_count} words")

    def check_keyword_density(self):
        """Check keyword density for primary keywords."""
        keywords = self.frontmatter.get("keywords", [])
        if not keywords:
            self.warnings.append("MISSING: No keywords defined in frontmatter")
            return

        if isinstance(keywords, str):
            keywords = [keywords]

        plain_text = self._get_plain_text().lower()
        total_words = len(plain_text.split())

        if total_words == 0:
            return

        print(f"\n  Keyword Density:")
        for kw in keywords:
            kw_lower = kw.lower()
            # Count occurrences (case-insensitive, whole phrase)
            count = len(re.findall(re.escape(kw_lower), plain_text))
            density = (count * len(kw_lower.split()) / total_words) * 100

            status = ""
            if density < IDEAL_KEYWORD_DENSITY_MIN:
                status = " [LOW]"
                self.warnings.append(
                    f"LOW KEYWORD DENSITY: \"{kw}\" at {density:.1f}% "
                    f"(found {count}x, recommend {IDEAL_KEYWORD_DENSITY_MIN}–{IDEAL_KEYWORD_DENSITY_MAX}%)"
                )
            elif density > IDEAL_KEYWORD_DENSITY_MAX:
                status = " [HIGH - possible stuffing]"
                self.warnings.append(
                    f"HIGH KEYWORD DENSITY: \"{kw}\" at {density:.1f}% "
                    f"(found {count}x, recommend under {IDEAL_KEYWORD_DENSITY_MAX}%)"
                )
            else:
                status = " [OK]"
                self.passes.append(f"Keyword density OK: \"{kw}\" at {density:.1f}%")

            print(f"    \"{kw}\": {count} occurrences, {density:.1f}%{status}")

    def check_images(self):
        """Check for image placeholders and alt text."""
        images = re.findall(r"!\[([^\]]*)\]\(([^)]*)\)", self.body)
        image_placeholders = re.findall(r"\[IMAGE:([^\]]+)\]", self.body)

        total_images = len(images) + len(image_placeholders)

        if total_images == 0:
            self.warnings.append("NO IMAGES: Article has no images or image placeholders")
        else:
            self.passes.append(f"Images found: {total_images} ({len(images)} embedded, {len(image_placeholders)} placeholders)")

        # Check alt text
        for alt, src in images:
            if not alt.strip():
                self.issues.append(f"MISSING ALT: Image at {src} has no alt text")

        print(f"\n  Images: {len(images)} embedded, {len(image_placeholders)} placeholders")

    def check_cta(self):
        """Check for call-to-action elements."""
        # Look for CTA patterns: blockquotes with links, "Get Started", "Sign Up", etc.
        cta_patterns = [
            r">\s*\[.+\]\(.+\)",  # Blockquote with link
            r"(?i)get started",
            r"(?i)sign up",
            r"(?i)free credit",
            r"(?i)try .+ free",
        ]
        cta_count = 0
        for pattern in cta_patterns:
            matches = re.findall(pattern, self.body)
            cta_count += len(matches)

        if cta_count == 0:
            self.warnings.append("NO CTA: No call-to-action elements found")
        elif cta_count < 2:
            self.warnings.append(f"LOW CTA: Only {cta_count} CTA element(s) (recommend 2+)")
        else:
            self.passes.append(f"CTA elements OK: {cta_count} found")

        print(f"\n  CTA Elements: {cta_count}")

    def check_related_articles(self):
        """Check for related articles section."""
        if "## Related Articles" in self.body or "## Related" in self.body:
            related_links = re.findall(
                r"- \[([^\]]+)\]\(([^)]+)\)",
                self.body.split("## Related")[1] if "## Related" in self.body else ""
            )
            self.passes.append(f"Related articles OK: {len(related_links)} links")
            print(f"\n  Related Articles: {len(related_links)} links")
        else:
            self.warnings.append("MISSING: No 'Related Articles' section found")

    def check_faq(self):
        """Check for FAQ section (good for featured snippets)."""
        if "## Frequently Asked Questions" in self.body or "## FAQ" in self.body:
            self.passes.append("FAQ section present (good for featured snippets)")
        else:
            self.warnings.append("NO FAQ: Consider adding a FAQ section for featured snippets")

    def run_all_checks(self):
        """Run all SEO checks."""
        self.load()
        print(f"\n{'='*70}")
        print(f"  SEO REPORT: {self.filename}")
        print(f"{'='*70}")

        self.check_title()
        self.check_description()
        self.check_headings()
        self.check_content_length()
        self.check_keyword_density()
        self.check_links()
        self.check_images()
        self.check_cta()
        self.check_related_articles()
        self.check_faq()

        # Print summary
        print(f"\n{'─'*70}")
        print(f"  SUMMARY")
        print(f"{'─'*70}")

        if self.issues:
            print(f"\n  ERRORS ({len(self.issues)}):")
            for issue in self.issues:
                print(f"    ❌ {issue}")

        if self.warnings:
            print(f"\n  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"    ⚠️  {warning}")

        if self.passes:
            print(f"\n  PASSED ({len(self.passes)}):")
            for passed in self.passes:
                print(f"    ✅ {passed}")

        # Score
        total_checks = len(self.issues) + len(self.warnings) + len(self.passes)
        score = len(self.passes) / total_checks * 100 if total_checks > 0 else 0
        print(f"\n  SEO SCORE: {score:.0f}/100")
        print(f"  ({len(self.passes)} passed, {len(self.warnings)} warnings, {len(self.issues)} errors)")
        print(f"{'='*70}\n")

        return len(self.issues) == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python seo-checker.py <file.md or directory/>")
        print("  python seo-checker.py articles/seedance-2-0-pricing-breakdown.md")
        print("  python seo-checker.py articles/")
        sys.exit(1)

    target = sys.argv[1]
    files = []

    if os.path.isdir(target):
        files = sorted(glob.glob(os.path.join(target, "*.md")))
        if not files:
            print(f"No .md files found in {target}")
            sys.exit(1)
    elif os.path.isfile(target):
        files = [target]
    else:
        print(f"File or directory not found: {target}")
        sys.exit(1)

    all_passed = True
    total_errors = 0
    total_warnings = 0
    total_passes = 0

    for filepath in files:
        # Skip non-article files
        if os.path.basename(filepath) in ["reddit-comments.md"]:
            continue
        checker = SEOChecker(filepath)
        passed = checker.run_all_checks()
        if not passed:
            all_passed = False
        total_errors += len(checker.issues)
        total_warnings += len(checker.warnings)
        total_passes += len(checker.passes)

    if len(files) > 1:
        print(f"\n{'='*70}")
        print(f"  OVERALL SUMMARY ({len(files)} articles)")
        print(f"{'='*70}")
        print(f"  Total errors:   {total_errors}")
        print(f"  Total warnings: {total_warnings}")
        print(f"  Total passed:   {total_passes}")
        total = total_errors + total_warnings + total_passes
        overall_score = total_passes / total * 100 if total > 0 else 0
        print(f"  Overall score:  {overall_score:.0f}/100")
        print(f"{'='*70}\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
