"""Shared helpers for whoosh oracle tests."""

from whoosh import index
from whoosh.fields import (
    BOOLEAN,
    ID,
    KEYWORD,
    NUMERIC,
    STORED,
    TEXT,
    Schema,
)


def make_index(tmp_path, name=None):
    """Create a standard multi-field index in a subdirectory of tmp_path."""
    directory = tmp_path / (name or "index")
    directory.mkdir()
    schema = Schema(
        path=ID(stored=True, unique=True),
        body=TEXT(stored=True),
        tags=KEYWORD(stored=True, commas=True, lowercase=True),
        note=STORED,
        number=NUMERIC(stored=True),
        flag=BOOLEAN(stored=True),
    )
    return directory, index.create_in(str(directory), schema, indexname=name)


def add_two(ix):
    """Add two reference documents to the index."""
    with ix.writer() as writer:
        writer.add_document(
            path="a", body="alpha beta", tags="Red,Blue",
            note="first", number=1, flag=True,
        )
        writer.add_document(
            path="b", body="beta gamma", tags="Blue",
            note="second", number=2, flag=False,
        )


def paths(ix, query, **kwargs):
    """Search and return the set of 'path' stored values from all hits."""
    with ix.searcher() as searcher:
        return {hit["path"] for hit in searcher.search(query, limit=None, **kwargs)}
