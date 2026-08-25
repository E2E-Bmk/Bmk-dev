target clause:   spec.md:100 — "SelectMultipleField must coerce all submitted values to a tuple"
                 spec.md:285 — API Catalog row "Multi-selection choice field coercing to a tuple"
upstream form:   SelectMultipleField.data returns a list. Source: choices.py:523,529 `self.data = list(...)`.
                 Verified on both pinned commit ae8f4b4 and PyPI 3.2.2.
mutated form:    SelectMultipleField.data returns a tuple. Spec now says "to a tuple".
oracle tests:    test_atomic::test_select_multiple_field_coerces_all_values_to_list
                 test_integration::test_select_multiple_preserves_all_values_and_rejects_invalid_members
                 test_integration::test_select_multiple_with_int_coerce_converts_all_values
                 (3 functions / 5 parametrized cases)
implementable:   One expression change per method: `self.data = tuple(...)` instead of `list(...)`.
                 iter_choices uses `in data` membership, which works identically on tuple.
                 populate_obj cascades unchanged. Zero restructuring.
divergent:       Upstream returns list. Injecting `tuple(...)` into upstream and running the
                 unmutated oracle: exactly 5 failed, 97 passed. Zero collateral.
unguessable:     list is the universal default for multi-valued form fields across all Python
                 form libraries (wtforms, Django forms, WTForms-Alchemy). No engineer writes
                 tuple(...) here by convention. The only route to tuple is reading the spec.
