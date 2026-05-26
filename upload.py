#!/usr/bin/env python3
"""
Blog upload service for liuwwei3.github.io.

Usage:
    python3 upload.py <source-file.md> [--title "custom"] [--dry-run]

Output: single-line JSON on stdout. Exit code 0 = success.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── constants ──
REPO_ROOT = Path(__file__).resolve().parent
BLOGS_DIR = REPO_ROOT / "blogs"
FIGURES_DIR = BLOGS_DIR / "figures"
INDEX_PATH = REPO_ROOT / "index.md"
README_PATH = REPO_ROOT / "README.md"
NAV_LINK = "[← 回到首页](..)"

# patterns
IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
MD_REF_RE = re.compile(r'\[([^\]]*)\]\(([^)]*\.md[^)]*)\)')
IMG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}


# ── helpers ──

def chinese_count(text: str) -> int:
    """Count CJK Unified Ideographs (U+4E00-U+9FFF) + Ext-A (U+3400-U+4DBF)."""
    total = 0
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            total += 1
    return total


def format_wc(count: int) -> str:
    return f"约 {count / 10000:.1f} 万字"


def strip_fences(text: str) -> str:
    """Remove fenced code blocks and math blocks for accurate counting."""
    # ``` ... ```
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # $$ ... $$
    text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)
    return text


def find_h1(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.startswith('# '):
            return line[2:].strip()
    return None


def slugify(title: str, source_path: str) -> str:
    """Derive a safe filename slug. Use the source filename by default."""
    base = os.path.splitext(os.path.basename(source_path))[0]
    return re.sub(r'[^a-zA-Z0-9_-]', '-', base) + '.md'


def extract_refs(text: str) -> list[tuple[str, str]]:
    """
    Extract local file references.
    Returns list of (raw_path, 'image'|'md').
    """
    refs = []
    for match in IMAGE_RE.finditer(text):
        path = match.group(2)
        if not path.startswith(('http://', 'https://', '#')):
            ext = os.path.splitext(path)[1].lower()
            if ext in IMG_EXTENSIONS:
                refs.append((path, 'image'))
    for match in MD_REF_RE.finditer(text):
        path = match.group(2).split('#')[0]  # strip anchor
        if not path.startswith(('http://', 'https://')):
            refs.append((path, 'md'))
    return refs


def refs_in_dir(refs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Deduplicate refs by basename, keeping first occurrence."""
    seen = set()
    result = []
    for path, typ in refs:
        key = (os.path.basename(path), typ)
        if key not in seen:
            seen.add(key)
            result.append((path, typ))
    return result


# ── core operations ──

def check_git_clean(repo: Path) -> tuple[bool, str]:
    """Return (is_clean, description)."""
    r = subprocess.run(
        ['git', 'status', '--porcelain'], cwd=repo,
        capture_output=True, text=True
    )
    dirty = [l for l in r.stdout.strip().split('\n') if l and not l.startswith('??')]
    if dirty:
        return False, f"Working tree dirty ({len(dirty)} modified files)"
    return True, "clean"


def resolve_and_copy(
    source_file: str, blogs: Path, figures: Path, dry_run: bool
) -> dict:
    """
    BFS recursive reference resolution. Copy files to blogs/ or blogs/figures/.
    Returns {'copied': [...], 'skipped': [...], 'missing': [...]}.
    """
    copied, skipped, missing = [], [], []
    visited: set[str] = set()  # set of destination basenames already present
    queue: list[tuple[str, str]] = [(source_file, os.path.basename(source_file))]  # (src_abs, dest_basename)

    while queue:
        current_src, _ = queue.pop(0)

        # read current file
        try:
            with open(current_src, encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            missing.append(current_src)
            continue

        refs = extract_refs(content)
        current_dir = os.path.dirname(os.path.abspath(current_src))

        for raw_path, typ in refs:
            basename = os.path.basename(raw_path)
            key = f"{basename}:{typ}"

            if key in visited:
                if key not in [f"{s}:{t}" for s, t, _ in [(c, 'image', '') for c in copied] + [(c, 'md', '') for c in copied]]:
                    skipped.append(basename)
                continue

            # resolve absolute path
            abs_ref = os.path.normpath(os.path.join(current_dir, raw_path))

            if not os.path.exists(abs_ref):
                missing.append(raw_path)
                continue

            # determine destination
            if typ == 'image':
                dest = figures / basename
            else:
                dest = blogs / basename

            dest_rel = f"figures/{basename}" if typ == 'image' else basename

            if dest.exists():
                skipped.append(dest_rel)
                visited.add(key)
                # still recurse into md files even if skipped
                if typ == 'md':
                    queue.append((abs_ref, basename))
                continue

            if not dry_run:
                shutil.copy2(abs_ref, dest)
            copied.append(dest_rel)
            visited.add(key)

            # recurse into newly found markdown files
            if typ == 'md':
                queue.append((os.path.abspath(abs_ref), basename))

    return {'copied': copied, 'skipped': skipped, 'missing': missing}


def rewrite_paths(content: str, source_dir: str) -> str:
    """Rewrite local reference paths for blog directory structure."""
    def replace_image(match):
        alt, path = match.group(1), match.group(2)
        if path.startswith(('http://', 'https://', '#')):
            return match.group(0)
        basename = os.path.basename(path)
        return f'![{alt}](figures/{basename})'

    def replace_md(match):
        text, path = match.group(1), match.group(2)
        if path.startswith(('http://', 'https://')):
            return match.group(0)
        anchor = ''
        if '#' in path:
            path, anchor = path.split('#', 1)
            anchor = '#' + anchor
        basename = os.path.basename(path)
        return f'[{text}]({basename}{anchor})'

    content = IMAGE_RE.sub(replace_image, content)
    content = MD_REF_RE.sub(replace_md, content)
    return content


def insert_nav_links(content: str) -> str:
    """Insert [← 回到首页](..) after H1 and at end. Skip if already present."""
    lines = content.splitlines()
    result = []

    h1_idx = None
    for i, line in enumerate(lines):
        if line.startswith('# '):
            h1_idx = i
            break

    # Check if nav link already near top (within 3 lines after H1)
    has_top_link = False
    if h1_idx is not None:
        nearby = lines[h1_idx + 1:h1_idx + 4]
        has_top_link = any(NAV_LINK in ln for ln in nearby)

    # Check if already at bottom
    has_bottom = False
    for ln in reversed(lines[-3:]):
        if NAV_LINK in ln:
            has_bottom = True
            break

    for i, line in enumerate(lines):
        result.append(line)
        if i == h1_idx and not has_top_link:
            result.append(NAV_LINK)
            result.append('')

    content = '\n'.join(result)

    if not has_bottom:
        content = content.rstrip('\n') + f'\n\n{NAV_LINK}\n'

    return content


def build_article(source_content: str, title: str) -> str:
    """Assemble full blog article with frontmatter and nav links."""
    fm = f'---\nlayout: default\ntitle: {title}\n---\n'
    body = insert_nav_links(source_content)
    # Remove the original H1 heading from body (frontmatter title serves that role)
    # Actually keep H1 for visual consistency in the rendered page
    return fm + body


def update_index(path: Path, entry: str, dry_run: bool) -> bool:
    """Insert entry into index file under ## 博客 heading. Returns True if updated."""
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(json.dumps({"status": "error", "message": f"Index file not found: {path}"}), file=sys.stderr)
        return False

    lines = content.splitlines()
    blog_idx = None
    for i, line in enumerate(lines):
        if line.strip() == '## 博客':
            blog_idx = i
            break

    if blog_idx is None:
        print(json.dumps({"status": "error", "message": "## 博客 section not found in index"}), file=sys.stderr)
        return False

    # Find the first list item after ## 博客
    insert_at = blog_idx + 1
    while insert_at < len(lines) and lines[insert_at].strip() == '':
        insert_at += 1

    # Insert new entry at the front of the list
    lines.insert(insert_at, entry)

    if not dry_run:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    return True


def git_push(repo: Path, files: list, title: str, dry_run: bool) -> Optional[str]:
    """Stage, commit, and push. Returns short commit hash or None on failure."""
    if dry_run:
        return "dry-run"

    # Stage
    subprocess.run(['git', 'add', '--', str(INDEX_PATH), str(README_PATH)] + files,
                   cwd=repo, check=True, capture_output=True)

    # Commit
    msg = f"Publish: {title}"
    r = subprocess.run(['git', 'commit', '-m', msg], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        # Check if nothing to commit
        if 'nothing to commit' in r.stdout or 'nothing to commit' in r.stderr:
            return None
        raise RuntimeError(f"Git commit failed: {r.stderr.strip()}")

    # Get hash
    r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=repo,
                       capture_output=True, text=True, check=True)
    commit_hash = r.stdout.strip()

    # Push
    r = subprocess.run(['git', 'push', 'origin', 'master'], cwd=repo,
                       capture_output=True, text=True)
    push_ok = r.returncode == 0

    return commit_hash if push_ok else f"{commit_hash} (push failed)"


# ── main ──

def main():
    parser = argparse.ArgumentParser(description='Upload a markdown article to the blog.')
    parser.add_argument('source', help='Path to source .md file')
    parser.add_argument('--title', help='Override auto-detected title', default=None)
    parser.add_argument('--dry-run', action='store_true', help='Simulate without writing/git')
    args = parser.parse_args()

    # Resolve source path
    source = os.path.abspath(args.source)
    if not os.path.isfile(source):
        print(json.dumps({"status": "error", "message": f"Source not found: {source}"}))
        sys.exit(1)

    source_dir = os.path.dirname(source)

    # Read source
    with open(source, encoding='utf-8') as f:
        raw = f.read()

    # Title
    title = args.title or find_h1(raw)
    if not title:
        title = os.path.splitext(os.path.basename(source))[0]

    # Git check
    clean, desc = check_git_clean(REPO_ROOT)
    if not clean:
        print(json.dumps({"status": "error", "message": desc}))
        sys.exit(1)

    # Determine output filename
    filename = slugify(title, source)
    dest_path = BLOGS_DIR / filename

    if dest_path.exists() and not args.dry_run:
        print(json.dumps({
            "status": "error",
            "message": f"'{filename}' already exists in blogs/. Remove it first or use a different source."
        }))
        sys.exit(1)

    # Resolve and copy references
    ref_result = resolve_and_copy(source, BLOGS_DIR, FIGURES_DIR, args.dry_run)

    # Rewrite paths in article content
    article_body = rewrite_paths(raw, source_dir)

    # Build final article
    article = build_article(article_body, title)

    # Count Chinese chars (on body only, excluding frontmatter)
    body_only = article.split('---\n', 2)[-1] if article.startswith('---\n') else article
    body_only = strip_fences(body_only)
    cc = chinese_count(body_only)
    wc_display = format_wc(cc)

    # Entry line for README
    slug = os.path.splitext(filename)[0]
    entry = f"- [{title}](blogs/{slug})（{wc_display}）"

    # Execute
    if not args.dry_run:
        # Write article
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(article)

        # Update indexes
        update_index(INDEX_PATH, entry, False)
        update_index(README_PATH, entry, False)

    # Git
    files_to_stage = [str(dest_path)]
    for cp in ref_result['copied']:
        files_to_stage.append(str(BLOGS_DIR / cp))

    commit_hash = git_push(REPO_ROOT, files_to_stage, title, args.dry_run)

    result = {
        "status": "success" if not args.dry_run else "dry_run",
        "title": title,
        "filename": filename,
        "chinese_chars": cc,
        "word_count_display": wc_display,
        "entry_line": entry,
        "commit_hash": commit_hash,
        "copied": ref_result['copied'],
        "skipped": ref_result['skipped'],
        "missing": ref_result['missing'],
    }
    if args.dry_run:
        result["dry_run"] = True

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
