#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path


def slug(text):
    text = re.sub(r"[^A-Za-z0-9]+", "-", text.lower()).strip("-")
    return text or "note"


def read_config(nb):
    config = {"filters": {}, "note": {}, "colon_tags": True}
    path = nb / ".zk" / "config.toml"
    if not path.exists():
        return config
    section = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        if section == "note":
            config["note"][key] = value
        elif section.startswith("filter."):
            name = section.split(".", 1)[1]
            config["filters"].setdefault(name, {})[key] = value
        elif section == "format.markdown" and key == "colon_tags":
            config["colon_tags"] = value.lower() == "true"
    return config


def init_notebook(path):
    nb = Path(path or ".").resolve()
    (nb / ".zk" / "templates").mkdir(parents=True, exist_ok=True)
    cfg = nb / ".zk" / "config.toml"
    if not cfg.exists():
        cfg.write_text("", encoding="utf-8")
    return nb


def find_notebook(global_dir):
    if global_dir:
        nb = Path(global_dir).resolve()
        if not (nb / ".zk").exists():
            raise RuntimeError("notebook not found")
        return nb
    env = os.environ.get("ZK_NOTEBOOK_DIR")
    if env:
        nb = Path(env).resolve()
        if not (nb / ".zk").exists():
            raise RuntimeError("notebook not found")
        return nb
    cur = Path.cwd().resolve()
    for path in [cur, *cur.parents]:
        if (path / ".zk").exists():
            return path
    raise RuntimeError("notebook not found: missing .zk")


def parse_frontmatter(text):
    data = {}
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            fm = text[4:end].strip()
            body = text[end + 4 :]
            for raw in fm.splitlines():
                if ":" not in raw:
                    continue
                key, value = [part.strip() for part in raw.split(":", 1)]
                if value.startswith("[") and value.endswith("]"):
                    items = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
                    data[key] = items
                else:
                    data[key] = value.strip('"').strip("'")
    return data, body


def extract_title(path, fm, body):
    if fm.get("title"):
        return str(fm["title"])
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def extract_tags(fm, text, colon_tags=True):
    tags = set()
    for key in ("tags", "keywords"):
        value = fm.get(key)
        if isinstance(value, list):
            tags.update(str(v).strip() for v in value if str(v).strip())
        elif isinstance(value, str) and value:
            tags.add(value)
    tags.update(m.group(1) for m in re.finditer(r"(?<!\w)#([A-Za-z0-9_/-]+)", text))
    if colon_tags:
        tags.update(m.group(1) for m in re.finditer(r":([A-Za-z0-9_/-]+):", text))
    return sorted(tags)


def extract_links(text):
    links = []
    links.extend(m.group(2) for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text))
    links.extend(m.group(1) for m in re.finditer(r"\[\[([^\]]+)\]\]", text))
    return links


def word_count(text):
    return len(re.findall(r"[A-Za-z0-9_]+", text))


def load_notes(nb):
    config = read_config(nb)
    notes = []
    for path in sorted(nb.rglob("*.md")):
        if ".zk" in path.parts:
            continue
        rel = path.relative_to(nb).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(text)
        notes.append(
            {
                "path": rel,
                "title": extract_title(path, fm, body),
                "tags": extract_tags(fm, text, config["colon_tags"]),
                "links": extract_links(text),
                "word_count": word_count(body),
                "body": body,
                "text": text,
                "mtime": path.stat().st_mtime,
                "ctime": path.stat().st_ctime,
            }
        )
    resolve_links(notes)
    return notes


def resolve_target(notes, target):
    target = str(target).strip()
    target_low = target.lower()
    for note in notes:
        path = note["path"]
        stem = Path(path).stem
        if path.lower() == target_low or path.lower().endswith("/" + target_low):
            return path
        if stem.lower() == target_low or stem.split("-", 1)[0].lower() == target_low:
            return path
        if note["title"].lower() == target_low:
            return path
    return target


def resolve_links(notes):
    for note in notes:
        note["resolved_links"] = [resolve_target(notes, link) for link in note["links"]]


def apply_tag_expr(notes, expr):
    if not expr:
        return notes
    clauses = [c.strip() for c in expr.split(",") if c.strip()]
    result = notes
    for clause in clauses:
        upper = clause.upper()
        if upper.startswith("NOT ") or clause.startswith("-"):
            tag = clause[4:].strip() if upper.startswith("NOT ") else clause[1:].strip()
            result = [n for n in result if tag not in n["tags"]]
        elif " OR " in upper or "|" in clause:
            parts = re.split(r"\s+OR\s+|\|", clause, flags=re.I)
            wanted = {p.strip() for p in parts if p.strip()}
            result = [n for n in result if wanted & set(n["tags"])]
        else:
            wanted = {p.strip() for p in clause.split() if p.strip()}
            if len(wanted) == 1 and "," not in clause:
                result = [n for n in result if next(iter(wanted)) in n["tags"]]
            else:
                result = [n for n in result if wanted <= set(n["tags"])]
    return result


def outgoing_map(notes):
    return {n["path"]: list(n["resolved_links"]) for n in notes}


def incoming_map(notes):
    incoming = {n["path"]: [] for n in notes}
    for note in notes:
        for target in note["resolved_links"]:
            if target in incoming:
                incoming[target].append(note["path"])
    return incoming


def reachable(notes, start, recursive=False, max_distance=None):
    graph = outgoing_map(notes)
    start_path = resolve_target(notes, start)
    found = []
    queue = [(start_path, 0)]
    seen = {start_path}
    while queue:
        cur, dist = queue.pop(0)
        if max_distance is not None and dist >= max_distance:
            continue
        for target in graph.get(cur, []):
            if target in seen:
                continue
            seen.add(target)
            found.append(target)
            if recursive:
                queue.append((target, dist + 1))
    return found


def filter_notes(notes, args, config):
    if getattr(args, "filter", None):
        filt = config["filters"].get(args.filter)
        if filt:
            if "tag" in filt and not getattr(args, "tag", None):
                args.tag = filt["tag"]
            if "exclude" in filt:
                args.exclude = list(getattr(args, "exclude", []) or []) + [filt["exclude"]]
    result = list(notes)
    for prefix in getattr(args, "paths", []) or []:
        result = [n for n in result if n["path"].startswith(prefix) or Path(n["path"]).stem.startswith(prefix)]
    for ex in getattr(args, "exclude", []) or []:
        result = [n for n in result if not n["path"].startswith(ex)]
    strategy = getattr(args, "match_strategy", "exact") or "exact"
    for query in getattr(args, "match", []) or []:
        if strategy == "re":
            rx = re.compile(query, re.I)
            result = [n for n in result if rx.search(n["title"] + "\n" + n["body"])]
        else:
            q = query.lower()
            result = [n for n in result if q in (n["title"] + "\n" + n["body"]).lower()]
    result = apply_tag_expr(result, getattr(args, "tag", None))
    if getattr(args, "link_to", None):
        target = resolve_target(notes, args.link_to)
        if args.recursive:
            incoming = incoming_map(notes)
            maxd = args.max_distance
            found = []
            queue = [(target, 0)]
            seen = {target}
            while queue:
                cur, dist = queue.pop(0)
                if maxd is not None and dist >= maxd:
                    continue
                for source in incoming.get(cur, []):
                    if source in seen:
                        continue
                    seen.add(source)
                    found.append(source)
                    queue.append((source, dist + 1))
            result = [n for n in result if n["path"] in found]
        else:
            result = [n for n in result if target in n["resolved_links"]]
    if getattr(args, "linked_by", None):
        paths = reachable(notes, args.linked_by, args.recursive, args.max_distance)
        result = [n for n in result if n["path"] in paths]
    if getattr(args, "orphan", False):
        incoming = incoming_map(notes)
        result = [n for n in result if not incoming.get(n["path"])]
    if getattr(args, "missing_backlink", False):
        incoming = incoming_map(notes)
        by_path = {n["path"]: n for n in notes}
        missing = []
        for target, sources in incoming_map(notes).items():
            target_links = set(by_path[target]["resolved_links"])
            if any(source not in target_links for source in sources):
                missing.append(target)
        result = [n for n in result if n["path"] in missing]
    return sort_limit(result, args)


def sort_limit(notes, args):
    sort = getattr(args, "sort", None) or "path+"
    desc = sort.endswith("-")
    key = sort[:-1] if sort[-1:] in "+-" else sort
    if key in {"title", "t"}:
        notes.sort(key=lambda n: n["title"].lower(), reverse=desc)
    elif key in {"word-count", "wc"}:
        notes.sort(key=lambda n: n["word_count"], reverse=desc)
    elif key in {"modified", "m"}:
        notes.sort(key=lambda n: n["mtime"], reverse=desc)
    else:
        notes.sort(key=lambda n: n["path"], reverse=desc)
    if getattr(args, "limit", None) is not None:
        notes = notes[: args.limit]
    return notes


def output_notes(notes, fmt):
    if fmt == "json":
        print(json.dumps([{k: n[k] for k in ("path", "title", "tags", "links", "word_count")} for n in notes], ensure_ascii=False))
    elif fmt == "jsonl":
        for n in notes:
            print(json.dumps({k: n[k] for k in ("path", "title", "tags", "links", "word_count")}, ensure_ascii=False))
    elif fmt == "title":
        print("\n".join(n["title"] for n in notes))
    else:
        print("\n".join(n["path"] for n in notes))


def command_new(nb, args):
    config = read_config(nb)
    title = args.title or config["note"].get("default_title") or "Untitled"
    note_id = args.id or "note"
    if args.filename:
        filename = args.filename
    else:
        tmpl = config["note"].get("filename", "{{id}}-{{slug title}}")
        filename = tmpl.replace("{{id}}", note_id).replace("{{slug title}}", slug(title))
        if not filename.endswith(".md"):
            filename += ".md"
    path = nb / (args.dir or "") / filename
    if path.exists():
        raise RuntimeError("output path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = sys.stdin.read() if args.interactive else ""
    if body:
        content = body if title in body else f"# {title}\n{body}"
    else:
        content = f"# {title}\n"
    path.write_text(content, encoding="utf-8")
    if args.print_path:
        print(path)


def command_tag_list(nb, args):
    counts = {}
    for note in load_notes(nb):
        for tag in note["tags"]:
            counts[tag] = counts.get(tag, 0) + 1
    rows = [{"name": tag, "note_count": count} for tag, count in counts.items()]
    sort = args.sort or "name+"
    desc = sort.endswith("-")
    key = sort[:-1] if sort[-1:] in "+-" else sort
    rows.sort(key=lambda r: r["note_count"] if key == "note-count" else r["name"], reverse=desc)
    if args.format == "json":
        print(json.dumps(rows, ensure_ascii=False))
    else:
        print("\n".join(r["name"] for r in rows))


def command_graph(nb, args):
    config = read_config(nb)
    notes = filter_notes(load_notes(nb), args, config)
    selected = {n["path"] for n in notes}
    nodes = [{"path": n["path"], "title": n["title"]} for n in notes]
    edges = []
    for n in notes:
        for target in n["resolved_links"]:
            if target in selected:
                edges.append({"source": n["path"], "target": target})
    print(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False))


def build_parser():
    parser = argparse.ArgumentParser(prog="zmini")
    parser.add_argument("--notebook-dir")
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("directory", nargs="?")
    p_new = sub.add_parser("new")
    p_new.add_argument("--title")
    p_new.add_argument("--id")
    p_new.add_argument("--dir")
    p_new.add_argument("--filename")
    p_new.add_argument("--print-path", action="store_true")
    p_new.add_argument("--interactive", action="store_true")
    p_list = sub.add_parser("list")
    p_list.add_argument("--format", default="short")
    p_list.add_argument("--match", action="append", default=[])
    p_list.add_argument("--match-strategy", default="exact")
    p_list.add_argument("--tag")
    p_list.add_argument("--link-to")
    p_list.add_argument("--linked-by")
    p_list.add_argument("--recursive", action="store_true")
    p_list.add_argument("--max-distance", type=int)
    p_list.add_argument("--orphan", action="store_true")
    p_list.add_argument("--missing-backlink", action="store_true")
    p_list.add_argument("--exclude", action="append", default=[])
    p_list.add_argument("--limit", type=int)
    p_list.add_argument("--sort")
    p_list.add_argument("--filter")
    p_list.add_argument("paths", nargs="*")
    p_tag = sub.add_parser("tag")
    tag_sub = p_tag.add_subparsers(dest="tag_command", required=True)
    p_tag_list = tag_sub.add_parser("list")
    p_tag_list.add_argument("--format", default="name")
    p_tag_list.add_argument("--sort")
    p_graph = sub.add_parser("graph")
    p_graph.add_argument("--format", default="json")
    p_graph.add_argument("--match", action="append", default=[])
    p_graph.add_argument("--match-strategy", default="exact")
    p_graph.add_argument("--tag")
    p_graph.add_argument("--exclude", action="append", default=[])
    p_graph.add_argument("--filter")
    p_graph.add_argument("paths", nargs="*")
    return parser


def main():
    args = build_parser().parse_args()
    try:
        if args.command == "init":
            init_notebook(args.directory)
            return 0
        nb = find_notebook(args.notebook_dir)
        if args.command == "new":
            command_new(nb, args)
        elif args.command == "list":
            output_notes(filter_notes(load_notes(nb), args, read_config(nb)), args.format)
        elif args.command == "tag":
            command_tag_list(nb, args)
        elif args.command == "graph":
            command_graph(nb, args)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
