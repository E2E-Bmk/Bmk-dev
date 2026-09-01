from __future__ import annotations

import copy
import importlib


def api():
    return importlib.import_module("traitlets.workspace")


def model_class():
    import traitlets as t

    class Model(t.HasTraits):
        raw = t.Int(1).tag(config=True)
        limit = t.Int(20).tag(config=True)
        normalized = t.Int(2).tag(config=True)
        title = t.Unicode("base").tag(config=True)
        mode = t.Enum(("cold", "hot"), default_value="cold").tag(config=True)
        secret = t.Unicode("seed")
        ceiling = t.Int(100)

        @t.validate("normalized")
        def _normalized(self, proposal):
            value = proposal["value"]
            if value < 0 or value > self.limit or value > self.ceiling:
                raise t.TraitError("normalized outside limit")
            return value

    return Model


NAMES = ("raw", "limit", "normalized", "title", "mode")
DEPENDENCIES = {"normalized": ("raw",), "title": ("normalized",)}


def workspace(path, owner=None, workspace_id="workspace"):
    owner = model_class()() if owner is None else owner
    return api().ConfigWorkspace(path, owner, workspace_id, NAMES, DEPENDENCIES)


def leased(workspace, owner="alice", operation_id="lease"):
    return workspace.lease_view(owner, operation_id=operation_id)


def publish(workspace, layers, *, owner="alice", plan_id="plan", lease_id="lease", commit_id="commit"):
    lease = leased(workspace, owner, lease_id)
    plan = workspace.plan(plan_id, layers, lease=lease)
    revision = workspace.commit(plan, lease, owner, operation_id=commit_id)
    return revision, lease, plan


def raises(error, function):
    try:
        function()
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


def isolated(value):
    return copy.deepcopy(value)
