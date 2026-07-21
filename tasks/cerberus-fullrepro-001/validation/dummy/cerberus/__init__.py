from types import SimpleNamespace


class SchemaError(Exception):
    pass


class DocumentError(Exception):
    pass


class _Registry:
    def add(self, *args, **kwargs):
        return None

    def extend(self, *args, **kwargs):
        return None

    def clear(self):
        return None


class Validator:
    def __init__(self, schema=None, *args, **kwargs):
        self.schema = schema
        self.document = None
        self.errors = {"dummy": ["not implemented"]}

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("dummy implementation")

    validate = __call__

    def normalized(self, *args, **kwargs):
        raise NotImplementedError("dummy implementation")

    def validated(self, *args, **kwargs):
        raise NotImplementedError("dummy implementation")


schema_registry = _Registry()
rules_set_registry = _Registry()
errors = SimpleNamespace()
