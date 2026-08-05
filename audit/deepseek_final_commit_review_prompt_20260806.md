# Final commit review request

Review the final local benchmark publication branch as an independent auditor.
The branch is intended for comparison with the independent GitHub branches,
not with the team's own `LiandZhang` branch. Use only the supplied evidence.
Return one JSON object with these keys:

```json
{
  "verdict": "PASS" | "CONDITIONAL_PASS" | "NOT_QUALIFIED",
  "blocking_issues": [],
  "non_blocking_issues": [],
  "checks": {},
  "recommendation": "..."
}
```

Answer these questions explicitly in `checks`:

1. Are there exactly 50 selected task directories and do they have the common
   packet files and referenced replay files claimed by the manifest?
2. Does the package appear structurally compatible with the independent
   branches (`main`, `beta`, `repo_status`, `codex/transitions-fullrepro-001`,
   `sync-from-release-and-fix-gates`, and non-mirrored upload content), while
   excluding the team's own `LiandZhang` branch and its 21 mirrored tasks?
3. Do any supplied local replays, pytest/oracle files, logs, or metadata prove
   a trusted black-box candidate score? Treat same-process replays as
   construction evidence only.
4. Is there an external signed Stage 4 isolation attestation, independent
   runner record, or promotion/judge record in the package?
5. Is it correct to call the branch `ARTIFACT_ONLY`, and is it incorrect to
   call any task `QUALIFIED` based on this package?

Be conservative. A structurally valid packet may pass upload review while
still being `NOT_QUALIFIED` for trusted Stage 4. Do not invent missing
evidence, and do not treat the existence of hidden-looking oracle files in the
same repository as proof of trust.
