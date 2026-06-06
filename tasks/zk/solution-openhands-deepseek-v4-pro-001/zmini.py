#!/usr/bin/env python3
"""zmini.py - Compact Zettelkasten note-taking assistant for Markdown notebooks.

Usage: py -3.11 zmini.py [--notebook-dir DIR] <command> [options]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Notebook discovery
# ---------------------------------------------------------------------------


def find_notebook(start_dir: Path | None = None) -> Path | None:
    """Walk upward from *start_dir* (defaults to cwd) until a `.zk` subdirectory is found."""
    if start_dir is None:
        start_dir = Path.cwd()
    start_dir = start_dir.resolve()
    for parent in [start_dir, *start_dir.parents]:
        if (parent / ".zk").is_dir():
            return parent
    return None


def resolve_notebook(args_nb: str | None, env_nb: str | None) -> Path:
    """Determine notebook root with the documented precedence: CLI flag > env var > auto-detect."""
    if args_nb:
        nb = Path(args_nb).resolve()
        if not (nb / ".zk").is_dir():
            print(f"zmini: error: '{nb}' is not a notebook (no .zk directory)", file=sys.stderr)
            sys.exit(1)
        return nb
    if env_nb:
        nb = Path(env_nb).resolve()
        if not (nb / ".zk").is_dir():
            print(f"zmini: error: ZK_NOTEBOOK_DIR '{nb}' is not a notebook", file=sys.stderr)
            sys.exit(1)
        return nb
    nb = find_notebook()
    if nb is None:
        print("zmini: error: no notebook found; run 'zmini init' first", file=sys.stderr)
        sys.exit(1)
    return nb


# ---------------------------------------------------------------------------
# Minimal TOML reader for the config subset we need
# ---------------------------------------------------------------------------

def _toml_strip_comment(line: str) -> str:
    """Strip inline comment from a TOML value line (handles quoted strings)."""
    in_string = False
    quote_char = ""
    for i, ch in enumerate(line):
        if ch in ('"', "'") and (i == 0 or line[i - 1] != "\\"):
            if not in_string:
                in_string = True
                quote_char = ch
            elif ch == quote_char:
                in_string = False
        elif ch == "#" and not in_string:
            return line[:i].rstrip()
    return line


def read_config_toml(path: Path) -> dict:
    """Parse a minimal TOML file for the supported config subset. Returns a nested dict."""
    if not path.is_file():
        return {}
    result: dict = {}
    current_section: dict | None = None
    current_path: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Section header
        m = re.match(r"^\[([^\]]+)\]$", line)
        if m:
            parts = [p.strip() for p in m.group(1).split(".")]
            current_path = parts
            d = result
            for p in parts:
                if p not in d:
                    d[p] = {}
                d = d[p]
            current_section = d
            continue

        # Key = value
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$', line)
        if m and current_section is not None:
            key = m.group(1)
            raw_val = _toml_strip_comment(m.group(2)).strip()
            # Try to parse as boolean
            if raw_val.lower() == "true":
                current_section[key] = True
            elif raw_val.lower() == "false":
                current_section[key] = False
            else:
                # Strip surrounding quotes
                val = raw_val
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                current_section[key] = val
    return result


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content: str) -> dict:
    """Extract a simple dict from YAML frontmatter. Handles scalars and bare lists."""
    m = _FRONTMATTER_RE.match(content)
    if not m:
        return {}
    fm_text = m.group(1)
    result: dict = {}
    current_key: str | None = None

    for line in fm_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item
        list_match = re.match(r"^\s*-\s+(.+)$", line)
        if list_match and current_key:
            val = list_match.group(1).strip().strip("'").strip('"')
            if current_key not in result:
                result[current_key] = []
            result[current_key].append(val)
            continue

        # Inline list: key: [a, b, c]
        inline_list = re.match(r"^(\w[\w_-]*)\s*:\s*\[(.+)\]$", stripped)
        if inline_list:
            k = inline_list.group(1)
            items = [item.strip().strip("'").strip('"') for item in inline_list.group(2).split(",")]
            result[k] = items
            current_key = k
            continue

        # Scalar: key: value
        scalar = re.match(r"^(\w[\w_-]*)\s*:\s*(.*)$", stripped)
        if scalar:
            k = scalar.group(1)
            v = scalar.group(2).strip().strip("'").strip('"')
            result[k] = v
            current_key = k

    return result


# ---------------------------------------------------------------------------
# Note model & extraction
# ---------------------------------------------------------------------------

_HASHTAG_RE = re.compile(r"(?<!\w)#([\w_/-]+)")
_COLONTAG_RE = re.compile(r":([\w_/-]+):")
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
_WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def slugify(text: str) -> str:
    """Convert *text* to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_title(content: str, filepath: Path, default_title: str = "Untitled") -> str:
    """Title precedence: frontmatter ``title`` → first ``# Heading`` → filename stem."""
    fm = parse_frontmatter(content)
    if fm.get("title"):
        return str(fm["title"])

    for line in content.splitlines():
        h1 = re.match(r"^#\s+(.+)$", line)
        if h1:
            return h1.group(1).strip()

    return filepath.stem


def extract_tags(content: str, config: dict | None = None) -> list[str]:
    """Extract tags from frontmatter ``tags``/``keywords`` and inline patterns.

    Reads config ``format.markdown.hashtags`` / ``colon_tags`` to toggle behaviour
    (both default to ``True``).
    """
    fm = parse_frontmatter(content)
    tags: list[str] = []

    # Frontmatter tags and keywords
    for key in ("tags", "keywords"):
        val = fm.get(key)
        if isinstance(val, list):
            tags.extend(val)
        elif isinstance(val, str):
            tags.append(val)

    fmt = (config or {}).get("format", {}).get("markdown", {})
    use_hashtags = fmt.get("hashtags", True) if isinstance(fmt, dict) else True
    use_colons = fmt.get("colon_tags", True) if isinstance(fmt, dict) else True

    # Inline #hashtags (exclude those inside fenced code blocks)
    body = _strip_code_blocks(content)
    if use_hashtags:
        for m in _HASHTAG_RE.finditer(body):
            tags.append(m.group(1))

    # Colon tags
    if use_colons:
        for m in _COLONTAG_RE.finditer(body):
            tags.append(m.group(1))

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append(t)
    return unique


def _strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks so inline patterns aren't matched inside them."""
    return re.sub(r"```.*?```", "", content, flags=re.DOTALL)


def extract_links(content: str, notebook_root: Path, note_path: Path) -> list[str]:
    """Return a list of relative target paths for links from *note_path*."""
    body = _strip_code_blocks(content)
    links: list[str] = []

    # Markdown links [text](path)
    for m in _MD_LINK_RE.finditer(body):
        target = m.group(2)
        # Ignore external URLs
        if re.match(r"^https?://", target):
            continue
        links.append(_resolve_link_target(target, notebook_root, note_path))

    # Wiki links [[target]]
    for m in _WIKI_LINK_RE.finditer(body):
        target = m.group(1)
        # Strip anchor / alias
        target = target.split("#")[0].split("|")[0].strip()
        if target:
            links.append(_find_note_by_ref(target, notebook_root))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for lnk in links:
        if lnk not in seen:
            seen.add(lnk)
            unique.append(lnk)
    return unique


def _resolve_link_target(target: str, notebook_root: Path, note_path: Path) -> str:
    """Resolve a markdown link target to a relative path within the notebook."""
    # Resolve relative to the note's directory
    note_dir = note_path.parent
    resolved = (note_dir / target).resolve()
    try:
        return str(resolved.relative_to(notebook_root)).replace("\\", "/")
    except ValueError:
        return target


def _find_note_by_ref(ref: str, notebook_root: Path) -> str:
    """Try to find a note matching a wiki-link reference by path or title stem."""
    # Direct path match
    candidate = (notebook_root / ref).resolve()
    try:
        rel = candidate.relative_to(notebook_root)
        if candidate.is_file():
            return str(rel).replace("\\", "/")
    except ValueError:
        pass

    # Try adding .md extension
    candidate_md = (notebook_root / (ref + ".md")).resolve()
    try:
        rel = candidate_md.relative_to(notebook_root)
        if candidate_md.is_file():
            return str(rel).replace("\\", "/")
    except ValueError:
        pass

    # Search for note whose filename stem matches
    ref_slug = slugify(ref)
    for md_file in notebook_root.rglob("*.md"):
        if md_file.parent.name == ".zk":
            continue
        if md_file.stem.lower() == ref.lower():
            try:
                return str(md_file.relative_to(notebook_root)).replace("\\", "/")
            except ValueError:
                pass
        if slugify(md_file.stem) == ref_slug:
            try:
                return str(md_file.relative_to(notebook_root)).replace("\\", "/")
            except ValueError:
                pass

    return ref


def word_count(content: str) -> int:
    """Count words in note body (excluding frontmatter)."""
    body = _FRONTMATTER_RE.sub("", content)
    return len(body.split())


class Note:
    __slots__ = ("path", "title", "tags", "links", "word_count", "created", "modified")

    def __init__(self, path: str, title: str, tags: list[str], links: list[str],
                 word_count: int, created: float, modified: float):
        self.path = path
        self.title = title
        self.tags = tags
        self.links = links
        self.word_count = word_count
        self.created = created
        self.modified = modified

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "title": self.title,
            "tags": self.tags,
            "links": self.links,
            "word_count": self.word_count,
        }


def load_notes(notebook_root: Path, config: dict | None = None) -> list[Note]:
    """Discover and parse all Markdown notes under *notebook_root* (excluding ``.zk``)."""
    notes: list[Note] = []
    for md_file in sorted(notebook_root.rglob("*.md")):
        # Skip files inside .zk
        try:
            md_file.relative_to(notebook_root / ".zk")
            continue
        except ValueError:
            pass

        try:
            rel = str(md_file.relative_to(notebook_root)).replace("\\", "/")
        except ValueError:
            rel = md_file.name

        content = md_file.read_text(encoding="utf-8", errors="replace")
        title = extract_title(content, md_file)
        tags = extract_tags(content, config)
        links = extract_links(content, notebook_root, md_file)
        wc = word_count(content)
        stat = md_file.stat()
        notes.append(Note(
            path=rel,
            title=title,
            tags=tags,
            links=links,
            word_count=wc,
            created=stat.st_ctime,
            modified=stat.st_mtime,
        ))
    return notes


# ---------------------------------------------------------------------------
# Tag filter expression engine
# ---------------------------------------------------------------------------

def _split_tag_expr(expr: str) -> list[str]:
    """Split a tag expression into tokens: ``tag``, ``,``, ``|``, ``-tag``."""
    tokens = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch in (",", "|"):
            tokens.append(ch)
            i += 1
        elif ch == "-":
            # Negative tag token
            j = i + 1
            while j < len(expr) and expr[j] not in (",", "|"):
                j += 1
            tokens.append("-" + expr[i + 1:j].strip().lower())
            i = j
        else:
            j = i
            while j < len(expr) and expr[j] not in (",", "|"):
                j += 1
            tag = expr[i:j].strip().lower()
            if tag.startswith("not "):
                tokens.append("-" + tag[4:])
            else:
                tokens.append(tag)
            i = j
    return [t for t in tokens if t]


def evaluate_tag_filter(note_tags: list[str], expr: str) -> bool:
    """Evaluate a tag filter expression against a note's tags.

    Grammar (lowest to highest precedence):
      expr   := or_term ('|' or_term)*
      or_term := and_term (',' and_term)*
      and_term := 'NOT'? tag  |  '-' tag  |  tag

    Tags are matched case-insensitively.
    """
    if not expr.strip():
        return True
    note_lower = {t.lower() for t in note_tags}
    tokens = _split_tag_expr(expr)
    return _eval_or(tokens, 0, note_lower)[0]


def _eval_or(tokens: list[str], pos: int, note_tags: set[str]) -> tuple[bool, int]:
    result, pos = _eval_and(tokens, pos, note_tags)
    while pos < len(tokens) and tokens[pos] == "|":
        pos += 1
        right, pos = _eval_and(tokens, pos, note_tags)
        result = result or right
    return result, pos


def _eval_and(tokens: list[str], pos: int, note_tags: set[str]) -> tuple[bool, int]:
    result, pos = _eval_term(tokens, pos, note_tags)
    while pos < len(tokens) and tokens[pos] == ",":
        pos += 1
        right, pos = _eval_term(tokens, pos, note_tags)
        result = result and right
    return result, pos


def _eval_term(tokens: list[str], pos: int, note_tags: set[str]) -> tuple[bool, int]:
    if pos >= len(tokens):
        return True, pos
    token = tokens[pos]
    pos += 1
    if token.startswith("-"):
        return token[1:] not in note_tags, pos
    return token in note_tags, pos


# ---------------------------------------------------------------------------
# Link graph helpers
# ---------------------------------------------------------------------------

def _link_targets_match(note: Note, target_ref: str, all_notes: list[Note]) -> bool:
    """Check if *note* links to *target_ref* (path or id)."""
    target_lower = target_ref.lower()
    for lnk in note.links:
        if lnk.lower() == target_lower:
            return True
        if lnk.lower().rstrip(".md") == target_lower.rstrip(".md"):
            return True
    return False


def _find_note_by_ref_internal(ref: str, all_notes: list[Note]) -> Note | None:
    """Find a note matching *ref* (path, path without .md, or title)."""
    ref_lower = ref.lower()
    for n in all_notes:
        if n.path.lower() == ref_lower:
            return n
        if n.path.lower().rstrip(".md") == ref_lower.rstrip(".md"):
            return n
    return None


def _incoming_links(note: Note, all_notes: list[Note]) -> list[Note]:
    """Return notes that link to *note*."""
    result = []
    for other in all_notes:
        if other.path == note.path:
            continue
        if _link_targets_match(other, note.path, all_notes):
            result.append(other)
    return result


def _traverse_links(seed_notes: list[Note], all_notes: list[Note],
                    direction: str, max_distance: int | None) -> set[str]:
    """BFS outward from *seed_notes* following links.

    *direction*: ``'forward'`` (follow outgoing links) or ``'backward'`` (follow incoming links).
    """
    all_by_path = {n.path: n for n in all_notes}
    visited: set[str] = set()
    frontier = [n.path for n in seed_notes]
    distance = 0

    while frontier:
        next_frontier = []
        for path in frontier:
            if path in visited:
                continue
            visited.add(path)
            note = all_by_path.get(path)
            if note is None:
                continue
            if max_distance is not None and distance >= max_distance:
                continue
            if direction == "forward":
                for lnk in note.links:
                    target = _normalize_link_target(lnk)
                    if target in all_by_path and target not in visited:
                        next_frontier.append(target)
            else:
                for incoming in _incoming_links(note, all_notes):
                    if incoming.path not in visited:
                        next_frontier.append(incoming.path)
        frontier = next_frontier
        distance += 1
    return visited


def _normalize_link_target(lnk: str) -> str:
    """Normalize a link target that might lack a ``.md`` extension."""
    return lnk if lnk.endswith(".md") else lnk + ".md"


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def _parse_sort(sort_spec: str) -> tuple[str, bool]:
    """Parse a sort spec like ``title``, ``+title``, or ``-title``.

    Returns ``(key, ascending)``.
    """
    spec = sort_spec.strip()
    if spec.startswith("-"):
        return spec[1:], False
    if spec.startswith("+"):
        return spec[1:], True
    return spec, True


# ---------------------------------------------------------------------------
# Filters from list/graph args
# ---------------------------------------------------------------------------

def _match_text(note: Note, content_cache: dict, notebook_root: Path,
                queries: list[str], strategy: str) -> bool:
    """Check if *note* matches all *queries*."""
    if not queries:
        return True
    if strategy == "re":
        for q in queries:
            try:
                pat = re.compile(q, re.IGNORECASE)
            except re.error as e:
                print(f"zmini: error: invalid regex '{q}': {e}", file=sys.stderr)
                sys.exit(1)
            text = content_cache.get(note.path, "")
            if not pat.search(note.title) and not pat.search(text):
                return False
    else:
        for q in queries:
            ql = q.lower()
            text = content_cache.get(note.path, "").lower()
            if ql not in note.title.lower() and ql not in text:
                return False
    return True


def _read_note_body(notebook_root: Path, note_path: str) -> str:
    """Read a note's full body text (for text matching)."""
    try:
        return (notebook_root / note_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    target = Path(args.DIR) if args.DIR else Path.cwd()
    target = target.resolve()
    zk_dir = target / ".zk"
    templates_dir = zk_dir / "templates"
    config_file = zk_dir / "config.toml"

    zk_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        config_file.write_text(textwrap.dedent("""\
            [note]
            default_title = "Untitled"
            filename = "{{id}}-{{slug title}}"

            [format.markdown]
            hashtags = true
            colon_tags = true
            """), encoding="utf-8")


def cmd_new(args: argparse.Namespace) -> None:
    notebook_root = resolve_notebook(args.notebook_dir, os.environ.get("ZK_NOTEBOOK_DIR"))
    config = read_config_toml(notebook_root / ".zk" / "config.toml")

    note_cfg = config.get("note", {})
    default_title = note_cfg.get("default_title", "Untitled")
    filename_tpl = note_cfg.get("filename", "{{id}}-{{slug title}}")

    title = args.title if args.title else default_title

    # Generate ID
    if args.id:
        note_id = args.id
    else:
        note_id = datetime.now().strftime("%Y%m%d%H%M%S")

    # Build filename: explicit flag overrides template
    if args.filename:
        filename = args.filename
    else:
        slug = slugify(title) if title != default_title else ""
        filename = filename_tpl.replace("{{id}}", note_id).replace("{{slug title}}", slug)
        # Clean up: remove trailing/leading hyphens and double hyphens
        filename = re.sub(r"-+", "-", filename).strip("-")
        if not filename:
            filename = note_id
    if not filename.endswith(".md"):
        filename += ".md"

    # Determine target directory
    if args.dir:
        note_dir = notebook_root / args.dir
    else:
        note_dir = notebook_root
    note_dir.mkdir(parents=True, exist_ok=True)

    filepath = note_dir / filename

    # Check for duplicate
    if filepath.exists():
        print(f"zmini: error: '{filepath.relative_to(notebook_root)}' already exists", file=sys.stderr)
        sys.exit(1)

    # Build content
    frontmatter = f"---\ntitle: {title}\n---\n\n"
    if args.interactive:
        body = sys.stdin.read()
    else:
        body = ""
    content = frontmatter + body

    filepath.write_text(content, encoding="utf-8")

    if args.print_path:
        try:
            print(str(filepath.relative_to(notebook_root)).replace("\\", "/"))
        except ValueError:
            print(str(filepath).replace("\\", "/"))


def cmd_list(args: argparse.Namespace) -> None:
    notebook_root = resolve_notebook(args.notebook_dir, os.environ.get("ZK_NOTEBOOK_DIR"))
    config = read_config_toml(notebook_root / ".zk" / "config.toml")

    notes = load_notes(notebook_root, config)
    all_by_path = {n.path: n for n in notes}

    # Apply named filter
    if args.filter:
        filter_cfg = config.get("filter", {}).get(args.filter)
        if filter_cfg is None:
            print(f"zmini: error: unknown filter '{args.filter}'", file=sys.stderr)
            sys.exit(1)
        if "tag" in filter_cfg and not args.tag:
            args.tag = [str(filter_cfg["tag"])]
        if "exclude" in filter_cfg and not args.exclude:
            args.exclude = [str(filter_cfg["exclude"])]

    # Build content cache for text matching
    content_cache: dict[str, str] = {}
    if args.match:
        for n in notes:
            content_cache[n.path] = _read_note_body(notebook_root, n.path)

    # Filtering
    filtered = []
    for note in notes:
        if not _match_text(note, content_cache, notebook_root,
                           args.match or [], args.match_strategy):
            continue

        if args.tag:
            combined = "|".join(args.tag) if len(args.tag) > 1 else args.tag[0]
            if not evaluate_tag_filter(note.tags, combined):
                continue

        # Link filters
        if args.link_to:
            # Resolve targets; error on missing
            link_targets = []
            for lt in args.link_to:
                ref = _find_note_by_ref_internal(lt, notes)
                if ref is None:
                    print(f"zmini: error: link target not found: '{lt}'", file=sys.stderr)
                    sys.exit(1)
                link_targets.append(ref)

            if args.recursive:
                # Notes linking *to* the target(s) — traverse backwards (incoming links)
                reachable = _traverse_links(link_targets, notes, "backward", args.max_distance)
                seed_paths = {t.path for t in link_targets}
                if note.path in seed_paths or note.path not in reachable:
                    continue
            else:
                ok = False
                for tgt in link_targets:
                    if _link_targets_match(note, tgt.path, notes):
                        ok = True
                        break
                if not ok:
                    continue

        if args.linked_by:
            # Resolve sources; error on missing
            link_sources = []
            for lb in args.linked_by:
                ref = _find_note_by_ref_internal(lb, notes)
                if ref is None:
                    print(f"zmini: error: link source not found: '{lb}'", file=sys.stderr)
                    sys.exit(1)
                link_sources.append(ref)

            if args.recursive:
                # Notes linked *by* the source(s) — traverse forwards (outgoing links)
                reachable = _traverse_links(link_sources, notes, "forward", args.max_distance)
                seed_paths = {s.path for s in link_sources}
                if note.path in seed_paths or note.path not in reachable:
                    continue
            else:
                ok = False
                for src in link_sources:
                    if _link_targets_match(src, note.path, notes):
                        ok = True
                        break
                if not ok:
                    continue

        # Orphan filter
        if args.orphan:
            incoming = _incoming_links(note, notes)
            if incoming:
                continue

        # Missing backlink filter
        if args.missing_backlink:
            incoming = _incoming_links(note, notes)
            has_missing = False
            for inc in incoming:
                if not _link_targets_match(inc, note.path, notes):
                    continue
                # Check if note links back to inc
                if not _link_targets_match(note, inc.path, notes):
                    has_missing = True
                    break
            if not has_missing:
                continue

        # Exclude paths
        if args.exclude:
            excluded = False
            for ex in args.exclude:
                ex_clean = ex.replace("\\", "/").rstrip("/")
                if note.path == ex_clean or note.path.startswith(ex_clean + "/"):
                    excluded = True
                    break
            if excluded:
                continue

        filtered.append(note)

    # Sort
    sort_key, ascending = _parse_sort(args.sort)
    if sort_key == "title":
        filtered.sort(key=lambda n: n.title.lower(), reverse=not ascending)
    elif sort_key == "path":
        filtered.sort(key=lambda n: n.path.lower(), reverse=not ascending)
    elif sort_key == "created":
        filtered.sort(key=lambda n: n.created, reverse=not ascending)
    elif sort_key == "modified":
        filtered.sort(key=lambda n: n.modified, reverse=not ascending)
    elif sort_key == "word-count":
        filtered.sort(key=lambda n: n.word_count, reverse=not ascending)
    else:
        filtered.sort(key=lambda n: n.path.lower())

    # Limit
    if args.limit and args.limit > 0:
        filtered = filtered[:args.limit]

    # Output
    fmt = args.format or "short"
    if fmt == "json":
        print(json.dumps([n.to_dict() for n in filtered], indent=2))
    elif fmt == "jsonl":
        for n in filtered:
            print(json.dumps(n.to_dict()))
    elif fmt == "path":
        for n in filtered:
            print(n.path)
    elif fmt == "title":
        for n in filtered:
            print(n.title)
    else:  # short
        for n in filtered:
            print(n.path)


def cmd_tag_list(args: argparse.Namespace) -> None:
    notebook_root = resolve_notebook(args.notebook_dir, os.environ.get("ZK_NOTEBOOK_DIR"))
    config = read_config_toml(notebook_root / ".zk" / "config.toml")
    notes = load_notes(notebook_root, config)

    # Aggregate tag → note count
    tag_counts: dict[str, int] = {}
    for note in notes:
        for tag in note.tags:
            tag_lower = tag.lower()
            if tag_lower not in tag_counts:
                tag_counts[tag_lower] = 0
            tag_counts[tag_lower] += 1

    # Sort
    sort_key, ascending = _parse_sort(args.sort if args.sort else "name")
    items = list(tag_counts.items())
    if sort_key == "name":
        items.sort(key=lambda x: x[0], reverse=not ascending)
    elif sort_key == "note-count":
        items.sort(key=lambda x: x[1], reverse=not ascending)

    fmt = args.format or "name"
    if fmt == "json":
        result = [{"name": name, "note_count": count} for name, count in items]
        print(json.dumps(result, indent=2))
    else:
        for name, count in items:
            print(name)


def cmd_graph(args: argparse.Namespace) -> None:
    notebook_root = resolve_notebook(args.notebook_dir, os.environ.get("ZK_NOTEBOOK_DIR"))
    config = read_config_toml(notebook_root / ".zk" / "config.toml")

    notes = load_notes(notebook_root, config)
    all_by_path = {n.path: n for n in notes}

    # Apply named filter
    if args.filter:
        filter_cfg = config.get("filter", {}).get(args.filter)
        if filter_cfg is None:
            print(f"zmini: error: unknown filter '{args.filter}'", file=sys.stderr)
            sys.exit(1)
        if "tag" in filter_cfg:
            if not args.tag:
                args.tag = [str(filter_cfg["tag"])]
        if "exclude" in filter_cfg:
            if not args.exclude:
                args.exclude = [str(filter_cfg["exclude"])]

    # Filter notes (using list logic)
    content_cache: dict[str, str] = {}
    if args.match:
        for n in notes:
            content_cache[n.path] = _read_note_body(notebook_root, n.path)

    filtered_notes = []
    for note in notes:
        if not _match_text(note, content_cache, notebook_root,
                           args.match or [], args.match_strategy):
            continue
        if args.tag:
            combined = "|".join(args.tag) if len(args.tag) > 1 else args.tag[0]
            if not evaluate_tag_filter(note.tags, combined):
                continue
        if args.exclude:
            excluded = False
            for ex in args.exclude:
                ex_clean = ex.replace("\\", "/").rstrip("/")
                if note.path == ex_clean or note.path.startswith(ex_clean + "/"):
                    excluded = True
                    break
            if excluded:
                continue
        filtered_notes.append(note)

    filtered_paths = {n.path for n in filtered_notes}

    # Build nodes
    nodes = []
    for n in filtered_notes:
        nodes.append({"path": n.path, "title": n.title})

    # Build edges (only between filtered notes)
    edges = []
    seen_edges = set()
    for n in filtered_notes:
        for lnk in n.links:
            target = lnk
            # Try both with and without .md extension
            if target not in filtered_paths:
                target_md = target if target.endswith(".md") else target + ".md"
                if target_md in filtered_paths:
                    target = target_md
                elif target.endswith(".md") and target[:-3] in filtered_paths:
                    target = target[:-3]
                else:
                    continue

            edge_key = (n.path, target)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({"source": n.path, "target": target})

    result = {"nodes": nodes, "edges": edges}
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zmini",
        description="Compact Zettelkasten note-taking assistant",
    )
    parser.add_argument("--notebook-dir", dest="notebook_dir", default=None,
                        help="Explicit notebook directory")

    sub = parser.add_subparsers(dest="command", required=True)

    # ---- init ----
    p_init = sub.add_parser("init", help="Create a notebook")
    p_init.add_argument("DIR", nargs="?", default=None,
                        help="Directory to initialize (default: current directory)")
    p_init.set_defaults(func=cmd_init)

    # ---- new ----
    p_new = sub.add_parser("new", help="Create a note")
    p_new.add_argument("--title", default=None, help="Note title")
    p_new.add_argument("--id", default=None, help="ID prefix")
    p_new.add_argument("--dir", default=None, help="Subdirectory within notebook")
    p_new.add_argument("--filename", default=None, help="Explicit filename (overrides template)")
    p_new.add_argument("--print-path", action="store_true", help="Print created path")
    p_new.add_argument("--interactive", action="store_true", help="Read body from stdin")
    p_new.set_defaults(func=cmd_new)

    # ---- list ----
    p_list = sub.add_parser("list", help="List notes")
    p_list.add_argument("--format", default="short",
                        choices=["short", "json", "jsonl", "path", "title"],
                        help="Output format (default: short)")
    p_list.add_argument("--match", action="append", default=None,
                        help="Case-insensitive search (repeatable)")
    p_list.add_argument("--match-strategy", default="exact", choices=["exact", "re"],
                        help="Match strategy (default: exact)")
    p_list.add_argument("--tag", action="append", default=None,
                        help="Tag filter expression (repeatable; combined with OR)")
    p_list.add_argument("--link-to", action="append", default=None,
                        help="Filter notes linking to target")
    p_list.add_argument("--linked-by", action="append", default=None,
                        help="Filter notes linked by source")
    p_list.add_argument("--recursive", action="store_true",
                        help="Follow links transitively for link filters")
    p_list.add_argument("--max-distance", type=int, default=None,
                        help="Maximum recursive link traversal depth")
    p_list.add_argument("--orphan", action="store_true",
                        help="Notes with no incoming links")
    p_list.add_argument("--missing-backlink", action="store_true",
                        help="Notes that don't link back to notes linking to them")
    p_list.add_argument("--exclude", action="append", default=None,
                        help="Exclude path prefixes (repeatable)")
    p_list.add_argument("--limit", type=int, default=None,
                        help="Maximum results")
    p_list.add_argument("--sort", default="path",
                        help="Sort key with optional +/- prefix (default: path)")
    p_list.add_argument("--filter", default=None,
                        help="Named filter from config")
    p_list.set_defaults(func=cmd_list)

    # ---- tag list ----
    p_tag = sub.add_parser("tag", help="Tag commands")
    p_tag_sub = p_tag.add_subparsers(dest="tag_command", required=True)

    p_tag_list = p_tag_sub.add_parser("list", help="List tags")
    p_tag_list.add_argument("--format", default="name", choices=["name", "json"],
                            help="Output format (default: name)")
    p_tag_list.add_argument("--sort", default="name",
                            help="Sort key with optional +/- prefix (default: name)")
    p_tag_list.set_defaults(func=cmd_tag_list)

    # ---- graph ----
    p_graph = sub.add_parser("graph", help="Export note-link graph")
    p_graph.add_argument("--format", default="json", choices=["json"],
                         help="Output format (default: json)")
    p_graph.add_argument("--match", action="append", default=None,
                         help="Case-insensitive search (repeatable)")
    p_graph.add_argument("--match-strategy", default="exact", choices=["exact", "re"],
                         help="Match strategy (default: exact)")
    p_graph.add_argument("--tag", action="append", default=None,
                         help="Tag filter expression (repeatable)")
    p_graph.add_argument("--exclude", action="append", default=None,
                         help="Exclude path prefixes (repeatable)")
    p_graph.add_argument("--filter", default=None,
                         help="Named filter from config")
    p_graph.set_defaults(func=cmd_graph)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
