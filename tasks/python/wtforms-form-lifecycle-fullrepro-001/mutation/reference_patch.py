"""Spec2Repo mutation patch: SelectMultipleField.data returns tuple instead of list.

Loaded via a .pth file in site-packages before any user code.
Idempotent — safe to import more than once.
"""
import sys

def _apply():
    import wtforms.fields.choices as _mod

    if getattr(_mod.SelectMultipleField, "_s2r_patched", False):
        return

    _orig_process_formdata = _mod.SelectMultipleField.process_formdata
    _orig_process_data = _mod.SelectMultipleField.process_data

    def _patched_process_formdata(self, valuelist):
        _orig_process_formdata(self, valuelist)
        if isinstance(self.data, list):
            self.data = tuple(self.data)

    def _patched_process_data(self, value):
        _orig_process_data(self, value)
        if isinstance(self.data, list):
            self.data = tuple(self.data)

    _mod.SelectMultipleField.process_formdata = _patched_process_formdata
    _mod.SelectMultipleField.process_data = _patched_process_data
    _mod.SelectMultipleField._s2r_patched = True

_apply()
