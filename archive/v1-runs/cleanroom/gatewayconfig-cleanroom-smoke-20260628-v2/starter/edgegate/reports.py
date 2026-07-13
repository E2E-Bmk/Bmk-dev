def config_report(gateway) -> dict:
    raise NotImplementedError


def runtime_report(gateway) -> dict:
    raise NotImplementedError


def audit_report(gateway, include_deleted: bool = False) -> list[dict]:
    raise NotImplementedError
