from __future__ import annotations


class File:
    def __init__(self, path, src_dir, dest_dir, use_directory_urls, dest_uri=None):
        self.src_uri = str(path)
        self.dest_uri = str(path)
        self.url = str(path)
        self.page = None

    def is_css(self):
        return False


class Files:
    def __init__(self, files=None):
        self._files = list(files or [])

    @property
    def src_uris(self):
        return [item.src_uri for item in self._files]

    def append(self, value):
        self._files.append(value)

    def remove(self, value):
        self._files.remove(value)

    def get_file_from_path(self, path):
        return next((item for item in self._files if item.src_uri == path), None)


def get_files(config):
    return Files()

