from __future__ import annotations

import os


if os.environ.get("AUTHLIB_SYNTHETIC_REFERENCE_PATCH") == "1":
    from reference_patch import apply

    apply()
