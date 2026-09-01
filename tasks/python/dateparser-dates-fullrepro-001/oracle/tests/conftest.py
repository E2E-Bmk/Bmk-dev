from __future__ import annotations

import os


if os.environ.get("DATEPARSER_V4_REFERENCE_PATCH") == "1":
    from reference_patch import apply

    apply(os.environ.get("DATEPARSER_V4_CONTROL_MODE"))
