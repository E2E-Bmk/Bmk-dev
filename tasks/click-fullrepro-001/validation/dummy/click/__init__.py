class _Dummy:
    def __init__(self, *args, **kwargs):
        self.name = None
        self.params = []

    def __call__(self, *args, **kwargs):
        return _Dummy()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __getattr__(self, name):
        return _Dummy()


class Command(_Dummy):
    pass


class Group(_Dummy):
    pass


class Argument(_Dummy):
    pass


class Option(_Dummy):
    pass


class Context(_Dummy):
    pass


class BadParameter(Exception):
    pass


class Tuple(_Dummy):
    pass


class File(_Dummy):
    pass


class Path(_Dummy):
    pass


UUID = _Dummy()
INT = _Dummy()
FLOAT = _Dummy()
BOOL = _Dummy()
STRING = _Dummy()
Choice = _Dummy


def _empty(*args, **kwargs):
    return _Dummy()


command = _empty
group = _empty
argument = _empty
option = _empty
echo = _empty
pass_context = _empty
get_current_context = _empty
