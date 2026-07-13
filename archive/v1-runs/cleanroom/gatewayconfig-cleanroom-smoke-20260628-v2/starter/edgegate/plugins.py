def merge_plugins(global_rules, service, plugin_config, route) -> dict:
    raise NotImplementedError


def apply_plugins(plan: dict, request: dict, upstream_selected: bool = True) -> dict:
    raise NotImplementedError
