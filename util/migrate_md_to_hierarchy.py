#!/usr/bin/env python3
"""Migrate old-format course notes into the new notes hierarchy.

Old format (one .md per Coursera course-module):
    # Module N: Title            <- week grouping (no folder level in new schema)
    # Article: Title             <- becomes an article folder
    ## Sub-Article: Title (Video|Reading)
    ### Video Transcript:        <- stripped
    ...content...

New format written to ./output:
    <mirrored input subdirs>/<NN_article>/<NN_sub_article>.md      raw content
    <mirrored input subdirs>/<NN_article>/<NN_sub_article>.ai.md   AI artifact placeholder

Usage:
    python migrate_md_to_hierarchy.py            parse ./input, write ./output (output is wiped first)
    python migrate_md_to_hierarchy.py --install  additionally merge ./output into ../notes

Drop old .md files into ./input. To land content in the right course/module,
mirror the notes layout inside input, e.g.:
    input/aws_cloud_support_professional/01_intro_to_it_and_aws/01_module1.md

Cleanup performed on the way through:
- zero-width characters and "Added to Selection..." copy-paste junk removed
- "### Video Transcript" header lines stripped
- duplicated transcript paragraphs (copy-paste doubles) collapsed
- sub-articles with an identical title AND identical content are skipped;
  same title with different content gets a numeric suffix
"""
import os
import re
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, 'input')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')
NOTES_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'notes'))

AI_PLACEHOLDER = "AI Compiled Reading Artifact will go here.\n"

MODULE_RE = re.compile(r'^#\s*Module\s+(\d+)\s*:?\s*(.*)$', re.I)
ARTICLE_RE = re.compile(r'^#\s*Article\s*:?\s*(.*)$', re.I)
SUB_RE = re.compile(r'^#{0,3}\s*Sub-Article\s*:?\s*(.*)$', re.I)
TRANSCRIPT_RE = re.compile(r'^#{1,4}\s*Video Transcript\s*:?\s*$', re.I)
TYPE_RE = re.compile(r'\(\s*(video|reading)\s*\)\s*$', re.I)
JUNK_RE = re.compile(r':?[ \t]*Added to Selection\. Press \[CTRL \+ S\] to save as a note[ \t]*', re.I)


def slugify(name, max_len=60):
    slug = re.sub(r'[^A-Za-z0-9]+', '_', name.strip()).strip('_').lower()
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip('_')
        if '_' in slug[30:]:
            slug = slug[:slug.rindex('_')]
    return slug or 'untitled'


def clean_paragraphs(lines):
    """Join content lines into paragraphs, collapse whitespace, and drop
    duplicated long chunks (copy-paste doubles inside transcripts)."""
    paras = []
    for line in lines:
        line = re.sub(r'\s+', ' ', line).strip()
        if line:
            paras.append(line)

    seen = []
    out = []
    for p in paras:
        if len(p) > 150:
            # Strip out any earlier long chunk embedded inside this paragraph
            for s in seen:
                if s in p:
                    p = p.replace(s, ' ')
            p = re.sub(r'\s{2,}', ' ', p).strip()
            if not p or p in seen:
                continue
            seen.append(p)
        out.append(p)
    return '\n\n'.join(out).strip()


def parse_file(text, report):
    """Return list of articles: {'title': str, 'subs': [{'title','type','lines'}]}"""
    text = text.replace('​', '').replace('﻿', '')
    text = JUNK_RE.sub(' ', text)

    module_title = None
    articles = []
    current_article = None
    current_sub = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or re.fullmatch(r'=+', stripped):
            continue
        if TRANSCRIPT_RE.match(stripped):
            continue

        m = SUB_RE.match(stripped)
        if m and stripped.lower().lstrip('# ').startswith('sub-article'):
            title = m.group(1).strip()
            sub_type = None
            tm = TYPE_RE.search(title)
            if tm:
                sub_type = tm.group(1).capitalize()
                title = TYPE_RE.sub('', title).strip()
            if current_article is None:
                # No "# Article:" seen yet -- fall back to the module heading
                current_article = {'title': module_title or 'General', 'subs': []}
                articles.append(current_article)
            current_sub = {'title': title, 'type': sub_type, 'lines': []}
            current_article['subs'].append(current_sub)
            continue

        m = ARTICLE_RE.match(stripped)
        if m:
            current_article = {'title': m.group(1).strip(), 'subs': []}
            articles.append(current_article)
            current_sub = None
            continue

        m = MODULE_RE.match(stripped)
        if m:
            module_title = f"Module {m.group(1)} {m.group(2).strip()}".strip()
            report['modules_seen'].append(module_title)
            continue

        if current_sub is not None:
            current_sub['lines'].append(line)
        else:
            report['stray_lines'] += 1

    return [a for a in articles if a['subs']]


def write_sub(article_dir, seq, sub, report):
    slug = slugify(sub['title'])
    content = clean_paragraphs(sub['lines'])

    # Duplicate handling: same title + same content -> skip entirely
    key = (slug, content)
    if key in report['written_keys']:
        report['dupes_skipped'].append(sub['title'])
        return seq
    # Same title, different content -> numeric suffix keeps both
    if slug in report['slugs_in_dir'].setdefault(article_dir, set()):
        bump = 2
        while f"{slug}_{bump}" in report['slugs_in_dir'][article_dir]:
            bump += 1
        slug = f"{slug}_{bump}"
    report['slugs_in_dir'][article_dir].add(slug)
    report['written_keys'].add(key)

    stem = f"{seq:02d}_{slug}"
    header = f"# {sub['title']}" + (f" ({sub['type']})" if sub['type'] else "")
    raw = header + "\n\n" + (content + "\n" if content else "")

    os.makedirs(article_dir, exist_ok=True)
    with open(os.path.join(article_dir, stem + '.md'), 'w', encoding='utf-8') as f:
        f.write(raw)
    with open(os.path.join(article_dir, stem + '.ai.md'), 'w', encoding='utf-8') as f:
        f.write(AI_PLACEHOLDER)
    report['subs_written'] += 1
    return seq + 1


def migrate():
    os.makedirs(INPUT_DIR, exist_ok=True)
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    report = {
        'files': 0, 'articles_written': 0, 'subs_written': 0,
        'modules_seen': [], 'dupes_skipped': [], 'stray_lines': 0,
        'written_keys': set(), 'slugs_in_dir': {},
    }
    # Article numbering continues across files that share the same output dir,
    # so 01_module1.md .. 01_module3.md produce one continuous article sequence.
    article_counters = {}

    md_files = []
    for root, _dirs, files in os.walk(INPUT_DIR):
        for name in sorted(files):
            if name.lower().endswith('.md'):
                md_files.append(os.path.join(root, name))
    md_files.sort()

    if not md_files:
        print(f"No .md files found in {INPUT_DIR}")
        print("Drop old-format notes there (mirror course/module subfolders) and re-run.")
        return report

    for path in md_files:
        rel_dir = os.path.relpath(os.path.dirname(path), INPUT_DIR)
        out_parent = OUTPUT_DIR if rel_dir == '.' else os.path.join(OUTPUT_DIR, rel_dir)

        with open(path, encoding='utf-8-sig') as f:
            articles = parse_file(f.read(), report)
        report['files'] += 1
        print(f"\n{os.path.relpath(path, INPUT_DIR)}")

        for article in articles:
            counter_key = out_parent
            article_counters[counter_key] = article_counters.get(counter_key, 0) + 1
            art_dir = os.path.join(out_parent, f"{article_counters[counter_key]:02d}_{slugify(article['title'])}")

            sub_seq = 1
            for sub in article['subs']:
                sub_seq = write_sub(art_dir, sub_seq, sub, report)
            if os.path.isdir(art_dir):
                report['articles_written'] += 1
                print(f"  -> {os.path.relpath(art_dir, OUTPUT_DIR)}  ({sub_seq - 1} sub-articles)")

    print("\n--- Summary ---")
    print(f"Files parsed:        {report['files']}")
    print(f"Articles created:    {report['articles_written']}")
    print(f"Sub-articles saved:  {report['subs_written']} (plus one .ai.md placeholder each)")
    if report['modules_seen']:
        print(f"Module headings folded into report (no folder level in new schema):")
        for mt in report['modules_seen']:
            print(f"  - {mt}")
    if report['dupes_skipped']:
        print(f"Exact duplicates skipped: {len(report['dupes_skipped'])}")
        for t in report['dupes_skipped']:
            print(f"  - {t}")
    if report['stray_lines']:
        print(f"Stray lines outside any sub-article ignored: {report['stray_lines']}")
    return report


def install():
    if not os.path.isdir(OUTPUT_DIR) or not os.listdir(OUTPUT_DIR):
        print("Nothing to install -- output/ is empty.")
        return
    shutil.copytree(OUTPUT_DIR, NOTES_DIR, dirs_exist_ok=True)
    print(f"\nInstalled output into {NOTES_DIR}")


if __name__ == '__main__':
    report = migrate()
    if '--install' in sys.argv and report['subs_written']:
        install()
