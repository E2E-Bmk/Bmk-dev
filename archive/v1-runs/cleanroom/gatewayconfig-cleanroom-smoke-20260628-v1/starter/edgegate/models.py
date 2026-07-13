class EdgeGateError(Exception):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


KINDS = ("upstream", "service", "plugin_config", "global_rule", "route")
