#!/usr/bin/env python3
"""MiniZK: a compact Markdown notebook command line assistant."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


DEFAULT_CONFIG = """[note]
default_title = "Untitled"
filename = "{{id}}-{{slug title}}"

[format.markdown]
hashtags = true
colon_tags = true
"""


class ZMiniError(Exception):
    pass


@dataclass
class Config:
    default_title: str = "Untitled"
    filename: str = "{{id}}-{{slug title}}"
    hashtags: bool = True
    colon_tags: bool = True
    filters: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class RawLink:
    target: str
    kind: str


@dataclass
class Note:
    path: str
    full_path: Path
    title: str
    body: str
    tags: set[str]
    raw_links: list[RawLink]
    links: list[str] = field(default_factory=list)
    created: float = 0.0
    modified: float = 0.0

    @property
    def word_count(self) -> int:
        return len(re.findall(r"\b[\w'-]+\b", self.body, flags=re.UNICODE))

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "tags": sorted(self.tags),
            "links": sorted(dict.fromkeys(self.links)),
            "word_count": self.word_count,
        }


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def normalize_rel(path: str | Path) -> str:
    text = str(path).replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    if not text:
        return ""
    parts: list[str] = []
    for part in PurePosixPath(text).parts:
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def strip_link_suffix(target: str) -> str:
    target = target.strip()
    if "|" in target:
        target = target.split("|", 1)[0].strip()
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    return target


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[-\s_]+", "-", value).strip("-")
    return value or "note"


def unquote_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_scalar_or_list(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [unquote_scalar(part.strip()) for part in inner.split(",")]
    if "," in value:
        return [unquote_scalar(part.strip()) for part in value.split(",") if part.strip()]
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    return unquote_scalar(value)


def parse_simple_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item_match = re.match(r"^\s*-\s*(.+?)\s*$", line)
        if item_match and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(unquote_scalar(item_match.group(1)))
            continue
        key_match = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$", line)
        if key_match:
            current_key = key_match.group(1).replace("-", "_")
            value = key_match.group(2)
            data[current_key] = [] if value == "" else parse_scalar_or_list(value)
        else:
            current_key = None
    return data


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    first_line_end = text.find("\n")
    if first_line_end not in (3, 4):
        return {}, text
    closing = re.search(r"(?m)^---\s*$", text[first_line_end + 1 :])
    if not closing:
        return {}, text
    start = first_line_end + 1
    end = start + closing.start()
    body_start = start + closing.end()
    if body_start < len(text) and text[body_start] == "\n":
        body_start += 1
    return parse_simple_yaml(text[start:end]), text[body_start:]


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_tag(tag: Any) -> str:
    text = str(tag).strip()
    if text.startswith("#"):
        text = text[1:]
    if text.startswith(":") and text.endswith(":"):
        text = text[1:-1]
    return text.strip().lower()


def read_config(root: Path) -> Config:
    cfg = Config()
    path = root / ".zk" / "config.toml"
    if not path.exists():
        return cfg
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ZMiniError(f"failed to read config: {exc}") from exc

    note = raw.get("note", {})
    if isinstance(note, dict):
        cfg.default_title = str(note.get("default_title", cfg.default_title))
        cfg.filename = str(note.get("filename", cfg.filename))
    fmt = raw.get("format", {}).get("markdown", {}) if isinstance(raw.get("format"), dict) else {}
    if isinstance(fmt, dict):
        cfg.hashtags = bool(fmt.get("hashtags", cfg.hashtags))
        cfg.colon_tags = bool(fmt.get("colon_tags", cfg.colon_tags))
    filters = raw.get("filter", {})
    if isinstance(filters, dict):
        cfg.filters = {str(name): value for name, value in filters.items() if isinstance(value, dict)}
    return cfg


def find_notebook(start: Path, explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not (root / ".zk").is_dir():
            raise ZMiniError(f"not a notebook: {root}")
        return root
    env_dir = os.environ.get("ZK_NOTEBOOK_DIR")
    if env_dir:
        root = Path(env_dir).expanduser().resolve()
        if not (root / ".zk").is_dir():
            raise ZMiniError(f"not a notebook: {root}")
        return root
    cur = start.resolve()
    while True:
        if (cur / ".zk").is_dir():
            return cur
        if cur.parent == cur:
            raise ZMiniError("no notebook found; run 'zmini.py init' first")
        cur = cur.parent


def markdown_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if ".zk" in rel_parts:
            continue
        if path.suffix.lower() in (".md", ".markdown"):
            yield path


def extract_title(frontmatter: dict[str, Any], body: str, path: Path) -> str:
    title = frontmatter.get("title")
    if title:
        return str(title).strip()
    for line in body.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return path.stem


def extract_tags(frontmatter: dict[str, Any], body: str, cfg: Config) -> set[str]:
    tags: set[str] = set()
    for key in ("tags", "keywords"):
        for value in as_list(frontmatter.get(key)):
            tag = normalize_tag(value)
            if tag:
                tags.add(tag)
    if cfg.hashtags:
        for match in re.finditer(r"(?<![\w/])#([A-Za-z0-9][A-Za-z0-9_/-]*)", body):
            tag = normalize_tag(match.group(1))
            if tag:
                tags.add(tag)
    if cfg.colon_tags:
        for match in re.finditer(r"(?<!\S):([A-Za-z0-9][A-Za-z0-9_/-]*):", body):
            tag = normalize_tag(match.group(1))
            if tag:
                tags.add(tag)
    return tags


def extract_links(body: str) -> list[RawLink]:
    links: list[RawLink] = []
    for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", body):
        target = strip_link_suffix(match.group(1))
        if target and not re.match(r"^[a-z][a-z0-9+.-]*:", target, flags=re.I):
            links.append(RawLink(target, "markdown"))
    for match in re.finditer(r"\[\[([^\]]+)\]\]", body):
        target = strip_link_suffix(match.group(1))
        if target:
            links.append(RawLink(target, "wiki"))
    return links


def load_notes(root: Path, cfg: Config) -> list[Note]:
    notes: list[Note] = []
    for path in sorted(markdown_files(root), key=lambda p: normalize_rel(p.relative_to(root)).lower()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = split_frontmatter(text)
        stat = path.stat()
        notes.append(
            Note(
                path=normalize_rel(path.relative_to(root)),
                full_path=path,
                title=extract_title(frontmatter, body, path),
                body=body,
                tags=extract_tags(frontmatter, body, cfg),
                raw_links=extract_links(body),
                created=stat.st_ctime,
                modified=stat.st_mtime,
            )
        )
    resolve_all_links(notes)
    return notes


def build_indexes(notes: list[Note]) -> dict[str, dict[str, list[str]]]:
    by_path: dict[str, list[str]] = {}
    by_stem: dict[str, list[str]] = {}
    by_title: dict[str, list[str]] = {}
    by_id: dict[str, list[str]] = {}
    for note in notes:
        by_path.setdefault(note.path.lower(), []).append(note.path)
        by_stem.setdefault(Path(note.path).stem.lower(), []).append(note.path)
        by_title.setdefault(note.title.lower(), []).append(note.path)
        first = Path(note.path).stem.split("-", 1)[0]
        if first:
            by_id.setdefault(first.lower(), []).append(note.path)
    return {"path": by_path, "stem": by_stem, "title": by_title, "id": by_id}


def unique_match(candidates: list[str]) -> str | None:
    unique = sorted(dict.fromkeys(candidates))
    return unique[0] if len(unique) == 1 else None


def resolve_target(raw: str, source_path: str | None, notes: list[Note]) -> str | None:
    indexes = build_indexes(notes)
    target = strip_link_suffix(raw)
    if not target:
        return None
    target_norm = normalize_rel(target)
    source_dir = normalize_rel(PurePosixPath(source_path).parent) if source_path else ""
    candidate_paths: list[str] = []

    def add_path_candidate(value: str) -> None:
        value = normalize_rel(value)
        if value:
            candidate_paths.append(value)
            if not PurePosixPath(value).suffix:
                candidate_paths.append(value + ".md")

    if "/" in target_norm or "\\" in target or PurePosixPath(target_norm).suffix:
        add_path_candidate(target_norm)
        if source_dir:
            add_path_candidate(f"{source_dir}/{target_norm}")
    else:
        add_path_candidate(target_norm)
        if source_dir:
            add_path_candidate(f"{source_dir}/{target_norm}")

    for candidate in candidate_paths:
        match = unique_match(indexes["path"].get(candidate.lower(), []))
        if match:
            return match

    lowered = target.strip().lower()
    match = unique_match(indexes["title"].get(lowered, []))
    if match:
        return match
    match = unique_match(indexes["stem"].get(lowered, []))
    if match:
        return match
    match = unique_match(indexes["id"].get(lowered, []))
    if match:
        return match

    prefix_matches = [
        note.path for note in notes if Path(note.path).stem.lower().startswith(lowered + "-")
    ]
    return unique_match(prefix_matches)


def resolve_cli_target(value: str, notes: list[Note]) -> str:
    match = resolve_target(value, None, notes)
    if not match:
        raise ZMiniError(f"missing linked target: {value}")
    return match


def resolve_all_links(notes: list[Note]) -> None:
    for note in notes:
        resolved: list[str] = []
        for link in note.raw_links:
            match = resolve_target(link.target, note.path, notes)
            resolved.append(match if match else normalize_rel(link.target))
        note.links = resolved


def graph_maps(notes: list[Note]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    note_paths = {note.path for note in notes}
    outgoing = {note.path: {link for link in note.links if link in note_paths} for note in notes}
    incoming = {note.path: set() for note in notes}
    for source, targets in outgoing.items():
        for target in targets:
            incoming.setdefault(target, set()).add(source)
    return outgoing, incoming


def parse_sort(value: str | None, default: str) -> tuple[str, bool]:
    text = value or default
    reverse = False
    if text.startswith("-"):
        reverse = True
        text = text[1:]
    elif text.startswith("+"):
        text = text[1:]
    return text, reverse


def tag_expr_matches(tags: set[str], expr: str) -> bool:
    alternatives = re.split(r"\s+(?:OR|or)\s+|\|", expr)
    for alt in alternatives:
        alt = alt.strip()
        if not alt:
            continue
        tokens = [t for t in re.split(r"[\s,]+", alt) if t]
        negate_next = False
        ok = True
        saw_condition = False
        for token in tokens:
            upper = token.upper()
            if upper == "AND":
                continue
            if upper == "NOT":
                negate_next = True
                continue
            negated = negate_next or token.startswith("-")
            negate_next = False
            name = token[1:] if token.startswith("-") else token
            name = normalize_tag(name)
            if not name:
                continue
            saw_condition = True
            has_tag = name in tags
            if (not negated and not has_tag) or (negated and has_tag):
                ok = False
                break
        if ok and saw_condition:
            return True
    return False


def apply_named_filters(args: argparse.Namespace, cfg: Config) -> None:
    names = getattr(args, "filters", None) or []
    for name in names:
        if name not in cfg.filters:
            raise ZMiniError(f"unknown filter: {name}")
        data = cfg.filters[name]
        for tag in as_list(data.get("tag")):
            args.tags.append(str(tag))
        for exclude in as_list(data.get("exclude")):
            args.exclude.append(str(exclude))
        for match in as_list(data.get("match")):
            args.matches.append(str(match))


def compile_matchers(args: argparse.Namespace) -> list[re.Pattern[str] | str]:
    matchers: list[re.Pattern[str] | str] = []
    for value in args.matches:
        if args.match_strategy == "re":
            try:
                matchers.append(re.compile(value, flags=re.I))
            except re.error as exc:
                raise ZMiniError(f"invalid regex: {exc}") from exc
        else:
            matchers.append(value.lower())
    return matchers


def exclude_note(path: str, excludes: list[str]) -> bool:
    for item in excludes:
        prefix = normalize_rel(item)
        if prefix and (path == prefix or path.startswith(prefix.rstrip("/") + "/")):
            return True
    return False


def reachable_from(start: str, adjacency: dict[str, set[str]], max_distance: int | None) -> set[str]:
    seen: set[str] = set()
    frontier: list[tuple[str, int]] = [(start, 0)]
    while frontier:
        current, dist = frontier.pop(0)
        if max_distance is not None and dist >= max_distance:
            continue
        for nxt in sorted(adjacency.get(current, set())):
            if nxt in seen or nxt == start:
                continue
            seen.add(nxt)
            frontier.append((nxt, dist + 1))
    return seen


def filter_notes(notes: list[Note], args: argparse.Namespace, cfg: Config) -> list[Note]:
    apply_named_filters(args, cfg)
    matchers = compile_matchers(args)
    outgoing, incoming = graph_maps(notes)
    current = list(notes)

    if args.exclude:
        current = [note for note in current if not exclude_note(note.path, args.exclude)]

    for expr in args.tags:
        current = [note for note in current if tag_expr_matches(note.tags, expr)]

    for matcher in matchers:
        if isinstance(matcher, str):
            current = [
                note
                for note in current
                if matcher in (note.title + "\n" + note.body).lower()
            ]
        else:
            current = [
                note
                for note in current
                if matcher.search(note.title) or matcher.search(note.body)
            ]

    max_distance = args.max_distance
    if args.link_to:
        target = resolve_cli_target(args.link_to, notes)
        if args.recursive:
            wanted = reachable_from(target, incoming, max_distance)
        else:
            wanted = incoming.get(target, set())
        current = [note for note in current if note.path in wanted]

    if args.linked_by:
        source = resolve_cli_target(args.linked_by, notes)
        if args.recursive:
            wanted = reachable_from(source, outgoing, max_distance)
        else:
            wanted = outgoing.get(source, set())
        current = [note for note in current if note.path in wanted]

    if args.orphan:
        current = [note for note in current if not incoming.get(note.path)]

    if args.missing_backlink:
        missing: set[str] = set()
        for source, targets in outgoing.items():
            for target in targets:
                if source not in outgoing.get(target, set()):
                    missing.add(target)
        current = [note for note in current if note.path in missing]

    key_name, reverse = parse_sort(args.sort, "path")
    sorters = {
        "path": lambda note: note.path.lower(),
        "title": lambda note: note.title.lower(),
        "created": lambda note: note.created,
        "modified": lambda note: note.modified,
        "word-count": lambda note: note.word_count,
    }
    if key_name not in sorters:
        raise ZMiniError(f"invalid sort key: {key_name}")
    current.sort(key=sorters[key_name], reverse=reverse)

    if args.limit is not None:
        current = current[: max(0, args.limit)]
    return current


def write_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.dir or ".").expanduser().resolve()
    zk = root / ".zk"
    (zk / "templates").mkdir(parents=True, exist_ok=True)
    cfg_path = zk / "config.toml"
    if not cfg_path.exists():
        cfg_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return 0


def render_filename(template: str, title: str, note_id: str) -> str:
    name = template
    name = name.replace("{{id}}", note_id)
    name = re.sub(r"{{\s*slug\s+title\s*}}", slugify(title), name)
    name = name.replace("{{title}}", title)
    if not PurePosixPath(name).suffix:
        name += ".md"
    return normalize_rel(name)


def cmd_new(args: argparse.Namespace) -> int:
    root = find_notebook(Path.cwd(), args.notebook_dir)
    cfg = read_config(root)
    title = args.title or cfg.default_title
    note_id = args.id or _dt.datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = normalize_rel(args.filename) if args.filename else render_filename(cfg.filename, title, note_id)
    if args.dir:
        filename = normalize_rel(f"{normalize_rel(args.dir)}/{filename}")
    target = (root / filename).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ZMiniError("output path must stay inside notebook") from exc
    if target.exists():
        raise ZMiniError(f"output path already exists: {normalize_rel(target.relative_to(root))}")
    target.parent.mkdir(parents=True, exist_ok=True)
    body = sys.stdin.read() if args.interactive else ""
    content = f"# {title}\n\n"
    if body:
        content += body
        if not content.endswith("\n"):
            content += "\n"
    target.write_text(content, encoding="utf-8")
    if args.print_path:
        print(normalize_rel(target.relative_to(root)))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = find_notebook(Path.cwd(), args.notebook_dir)
    cfg = read_config(root)
    notes = filter_notes(load_notes(root, cfg), args, cfg)
    if args.format == "json":
        write_json([note.to_json() for note in notes])
    elif args.format == "jsonl":
        for note in notes:
            write_json(note.to_json())
    elif args.format == "path":
        for note in notes:
            print(note.path)
    elif args.format == "title":
        for note in notes:
            print(note.title)
    else:
        for note in notes:
            print(f"{note.path}\t{note.title}")
    return 0


def cmd_tag_list(args: argparse.Namespace) -> int:
    root = find_notebook(Path.cwd(), args.notebook_dir)
    cfg = read_config(root)
    counts: dict[str, int] = {}
    for note in load_notes(root, cfg):
        for tag in note.tags:
            counts[tag] = counts.get(tag, 0) + 1
    key_name, reverse = parse_sort(args.sort, "name")
    if key_name == "name":
        items = sorted(counts.items(), key=lambda item: item[0], reverse=reverse)
    elif key_name == "note-count":
        if reverse:
            items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        else:
            items = sorted(counts.items(), key=lambda item: (item[1], item[0]))
    else:
        raise ZMiniError(f"invalid sort key: {key_name}")
    if args.format == "json":
        write_json([{"name": name, "note_count": count} for name, count in items])
    else:
        for name, _count in items:
            print(name)
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    root = find_notebook(Path.cwd(), args.notebook_dir)
    cfg = read_config(root)
    all_notes = load_notes(root, cfg)
    notes = filter_notes(all_notes, args, cfg)
    selected = {note.path for note in notes}
    nodes = [{"path": note.path, "title": note.title} for note in notes]
    edges: list[dict[str, str]] = []
    for note in notes:
        for target in sorted(dict.fromkeys(note.links)):
            if target in selected:
                edges.append({"source": note.path, "target": target})
    write_json({"nodes": nodes, "edges": edges})
    return 0


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--filter", dest="filters", action="append", default=[])
    parser.add_argument("--match", dest="matches", action="append", default=[])
    parser.add_argument("--match-strategy", choices=["exact", "re"], default="exact")
    parser.add_argument("--tag", dest="tags", action="append", default=[])
    parser.add_argument("--link-to")
    parser.add_argument("--linked-by")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--max-distance", type=int)
    parser.add_argument("--orphan", action="store_true")
    parser.add_argument("--missing-backlink", action="store_true")
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sort")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zmini.py", allow_abbrev=False)
    parser.add_argument("--notebook-dir")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init")
    init_p.add_argument("dir", nargs="?")
    init_p.set_defaults(func=cmd_init)

    new_p = sub.add_parser("new")
    new_p.add_argument("--title")
    new_p.add_argument("--id")
    new_p.add_argument("--dir")
    new_p.add_argument("--filename")
    new_p.add_argument("--print-path", action="store_true")
    new_p.add_argument("--interactive", action="store_true")
    new_p.set_defaults(func=cmd_new)

    list_p = sub.add_parser("list")
    list_p.add_argument("--format", choices=["short", "json", "jsonl", "path", "title"], default="short")
    add_filter_args(list_p)
    list_p.set_defaults(func=cmd_list)

    tag_p = sub.add_parser("tag")
    tag_sub = tag_p.add_subparsers(dest="tag_command", required=True)
    tag_list_p = tag_sub.add_parser("list")
    tag_list_p.add_argument("--format", choices=["name", "json"], default="name")
    tag_list_p.add_argument("--sort")
    tag_list_p.set_defaults(func=cmd_tag_list)

    graph_p = sub.add_parser("graph")
    graph_p.add_argument("--format", choices=["json"], default="json")
    add_filter_args(graph_p)
    graph_p.set_defaults(func=cmd_graph)
    return parser


def preprocess_argv(argv: list[str]) -> list[str]:
    """Let value options accept practical values that begin with '-'."""
    value_options = {
        "--notebook-dir",
        "--title",
        "--id",
        "--dir",
        "--filename",
        "--format",
        "--match",
        "--match-strategy",
        "--tag",
        "--link-to",
        "--linked-by",
        "--max-distance",
        "--exclude",
        "--limit",
        "--sort",
        "--filter",
    }
    flag_options = {"--print-path", "--interactive", "--recursive", "--orphan", "--missing-backlink"}
    known_options = value_options | flag_options
    result: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in value_options and i + 1 < len(argv):
            nxt = argv[i + 1]
            if nxt.startswith("-") and nxt not in known_options and "=" not in token:
                result.append(f"{token}={nxt}")
                i += 2
                continue
        result.append(token)
        i += 1
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    clean_argv = preprocess_argv(list(sys.argv[1:] if argv is None else argv))
    args = parser.parse_args(clean_argv)
    try:
        return int(args.func(args) or 0)
    except ZMiniError as exc:
        eprint(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
