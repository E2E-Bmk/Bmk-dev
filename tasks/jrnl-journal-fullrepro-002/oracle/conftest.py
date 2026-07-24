"""Shared fixtures, helpers, and constants for jrnl oracle tests."""
import json
import subprocess
import sys
from datetime import datetime

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): integration test depends on named atomic tests",
    )


TIMEFORMAT = "%Y-%m-%d %H:%M"
TAGSYMBOLS = "#@"
DEFAULT_HOUR = 9
DEFAULT_MINUTE = 0


def make_config(path=None, **overrides):
    """Build a journal config dict with sensible defaults."""
    config = {
        "encrypt": False,
        "timeformat": TIMEFORMAT,
        "tagsymbols": TAGSYMBOLS,
        "default_hour": DEFAULT_HOUR,
        "default_minute": DEFAULT_MINUTE,
        "highlight": False,
        "linewrap": 79,
        "indent_character": "|",
        "colors": {"body": "none", "date": "none", "tags": "none", "title": "none"},
    }
    if path is not None:
        config["journal"] = str(path)
    config.update(overrides)
    return config


def make_journal(path=None, **overrides):
    """Create a Journal instance (not opened, no file I/O)."""
    from jrnl.journals import Journal

    return Journal(**make_config(path, **overrides))


def make_populated(path=None):
    """Create a journal with two sample entries (Alpha #work, Beta #home starred)."""
    journal = make_journal(path)
    journal.new_entry("Alpha #work\nFirst body", date=datetime(2024, 1, 1, 9))
    second = journal.new_entry("Beta #home\nSecond body", date=datetime(2024, 1, 2, 10))
    second.starred = True
    return journal


def write_cli_config(tmp_path, journals):
    """Write a YAML config file suitable for CLI invocations and return its Path."""
    import jrnl

    config_path = tmp_path / "jrnl.yaml"
    journal_lines = [f"  {name}: {json.dumps(str(p))}" for name, p in journals.items()]
    config_path.write_text(
        "\n".join(
            [
                f"version: {json.dumps(jrnl.__version__)}",
                "journals:",
                *journal_lines,
                "editor: ''",
                "encrypt: false",
                "template: false",
                f"default_hour: {DEFAULT_HOUR}",
                f"default_minute: {DEFAULT_MINUTE}",
                f"timeformat: '{TIMEFORMAT}'",
                f"tagsymbols: '{TAGSYMBOLS}'",
                "highlight: false",
                "linewrap: 79",
                "indent_character: '|'",
                "colors:",
                "  body: none",
                "  date: none",
                "  tags: none",
                "  title: none",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def run_cli(config, *args):
    """Run ``python -m jrnl`` with the given config file and CLI arguments."""
    return subprocess.run(
        [sys.executable, "-m", "jrnl", "--config-file", str(config), *args],
        text=True,
        capture_output=True,
    )
