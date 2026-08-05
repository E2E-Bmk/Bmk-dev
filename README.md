# Bmk-dev Upload Preparation

This branch preparation tree contains 50 locally constructed task packets.
They are copied into `tasks/<task-id>/` for structural review and remain
`ARTIFACT_ONLY` until candidate evaluation and judge evidence are complete.

Task-local `logs/` files referenced by `task.json` are included so the local
replay metadata is not dangling. Publication copies use redacted host paths
and refreshed SHA-256 bindings; they are not trusted Stage 4 evidence.

See `UPLOAD_PREP_STATUS.md` and `UPLOAD_PREP_MANIFEST.json` for the exact
promotion blockers.
