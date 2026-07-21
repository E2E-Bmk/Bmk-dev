#!/usr/bin/env python3
import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path


TARGET_FILES = {
    "minidynaconf-realrepo-001": "minidynaconf.py",
    "miniredis-realrepo-submit": "miniredis.py",
    "minikv-realrepo-submit": "minikv.py",
    "minimarkdown-realrepo-001": "minimarkdown.py",
    "minipackaging-realrepo-001": "minipackaging.py",
    "minitemplate-realrepo-submit": "minitemplate.py",
}


def load_config(path):
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text)


def extract_code(text, filename):
    pattern = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
    blocks = pattern.findall(text)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    marker = f"# {filename}"
    if marker in text:
        return text[text.index(marker):].strip() + "\n"
    return text.strip() + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True, choices=sorted(TARGET_FILES))
    parser.add_argument("--prd", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--response-json", type=Path, required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)
    filename = TARGET_FILES[args.task_id]
    prd = args.prd.read_text(encoding="utf-8")
    prompt = f"""You are implementing a benchmark candidate from a public product packet only.

Rules:
- Do not assume hidden tests.
- Use only Python 3.11 standard library.
- Return one complete Python source file for {filename}.
- Do not include explanations outside the code block.

Public packet:

{prd}
"""
    body = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": "You are a careful coding agent. Produce complete, runnable code."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "stream": False,
    }
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw_body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {raw_body[:2000]}")

    data = json.loads(raw)
    args.response_json.parent.mkdir(parents=True, exist_ok=True)
    args.response_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    content = data["choices"][0]["message"]["content"]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / filename).write_text(extract_code(content, filename), encoding="utf-8")
    print(args.out_dir / filename)


if __name__ == "__main__":
    raise SystemExit(main())
