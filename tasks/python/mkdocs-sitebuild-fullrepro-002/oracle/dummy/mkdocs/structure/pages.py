from __future__ import annotations

from mkdocs.exceptions import BuildError


class Page:
    def __init__(self, title, file, config):
        self.title = title
        self.file = file
        self.meta = {}
        self.content = ""
        self.toc = []

    def read_source(self, config):
        raise BuildError("behavior-empty page reader")

    def render(self, config, files):
        raise BuildError("behavior-empty page renderer")

