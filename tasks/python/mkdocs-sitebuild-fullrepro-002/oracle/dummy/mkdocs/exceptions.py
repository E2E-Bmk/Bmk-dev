class MkDocsException(Exception):
    pass


class Abort(MkDocsException):
    exit_code = 9


class ConfigurationError(MkDocsException):
    pass


class BuildError(MkDocsException):
    pass


class PluginError(BuildError):
    pass

