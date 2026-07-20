class _DummyValue:
    pass


class FileIO:
    def __init__(self, *args, **kwargs):
        self.path = _DummyValue()

    def read(self):
        return _DummyValue()

    def get_last_modified(self):
        return _DummyValue()


class KnownContentFileIO(FileIO):
    pass
