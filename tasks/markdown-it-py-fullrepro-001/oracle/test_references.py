from __future__ import annotations

# Rewritten from tests/test_port/test_references.py at the pinned source revision.
from markdown_it import MarkdownIt

def test_ref_definitions():
    md = MarkdownIt()
    src = '[a]: abc\n\n[b]: xyz\n\n[b]: ijk'
    env = {}
    tokens = md.parse(src, env)
    assert tokens == []
    assert env == {'references': {'A': {'title': '', 'href': 'abc', 'map': [0, 1]}, 'B': {'title': '', 'href': 'xyz', 'map': [2, 3]}}, 'duplicate_refs': [{'href': 'ijk', 'label': 'B', 'map': [4, 5], 'title': ''}]}
