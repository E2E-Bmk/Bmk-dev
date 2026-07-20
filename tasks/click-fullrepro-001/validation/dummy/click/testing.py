class CliRunner:
    def invoke(self, *args, **kwargs):
        return None

    def isolated_filesystem(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Result:
    pass
