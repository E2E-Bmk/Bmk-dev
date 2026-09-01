from __future__ import annotations


class Link:
    pass


class Section:
    pass


class Navigation:
    def __init__(self):
        self.pages = []
        self.items = []


def get_navigation(files, config):
    return Navigation()

