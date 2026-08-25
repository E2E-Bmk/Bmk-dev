"""Spec2Repo mutation patch: swap doit failure/error exit codes (1↔2).

Loaded via a .pth file in site-packages before any user code.
Idempotent — safe to import more than once.
"""
import importlib
import sys


def _apply():
    try:
        from doit import runner
    except ImportError:
        return

    if getattr(runner, "_s2r_patched", False):
        return

    runner.FAILURE = 2
    runner.ERROR = 1
    runner._s2r_patched = True


_apply()
