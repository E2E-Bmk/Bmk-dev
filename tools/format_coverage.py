"""Convert coverage.json to an agent-readable gap report with source context."""
import json
import sys
from pathlib import Path


def format_gaps(coverage_json: Path, source_root: Path, modules: list[str], context_lines: int = 6) -> str:
    data = json.loads(coverage_json.read_text())
    sections = []

    for rel_path, filedata in sorted(data["files"].items()):
        # Only report on requested modules
        norm = rel_path.replace("\\", "/")
        if modules and not any(norm.endswith(m) for m in modules):
            continue

        missing_branches = filedata.get("missing_branches", [])
        missing_lines = filedata.get("missing_lines", [])
        if not missing_branches and not missing_lines:
            continue

        src_file = source_root / rel_path
        if not src_file.exists():
            continue
        source = src_file.read_text(encoding="utf-8", errors="replace").splitlines()

        branch_lines = {b[0] for b in missing_branches}
        covered_pct = filedata.get("summary", {}).get("percent_covered", 0)

        file_sections = [f"\n## {rel_path}  (covered: {covered_pct:.0f}%)"]

        reported = set()
        for from_line, to_line in sorted(missing_branches):
            if from_line in reported:
                continue
            reported.add(from_line)
            start = max(0, from_line - 4)
            end = min(len(source), from_line + context_lines)
            snippet = "\n".join(
                f"{'>>>' if i + 1 == from_line else '   '} {i+1:4d}  {line}"
                for i, line in enumerate(source[start:end], start=start)
            )
            dest = "exit/exception" if to_line < 0 else f"line {to_line}"
            file_sections.append(f"\nUncovered branch: line {from_line} → {dest}\n{snippet}")

        sections.append("\n".join(file_sections))

    if not sections:
        return "No coverage gaps found in specified modules."
    return "\n\n" + "=" * 60 + "\n".join(sections)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: format_coverage.py <coverage.json> <source_root> [module1 module2 ...]")
        sys.exit(1)
    cov_path = Path(sys.argv[1])
    src_root = Path(sys.argv[2])
    mods = sys.argv[3:] if len(sys.argv) > 3 else []
    print(format_gaps(cov_path, src_root, mods))
