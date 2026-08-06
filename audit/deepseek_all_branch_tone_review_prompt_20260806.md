# All-branch requirements and tone audit review

Return valid JSON only with keys `verdict`, `blocking_issues`,
`non_blocking_issues`, `verified_claims`, `disputed_claims`, and
`recommendation`.

Review the supplied audit of all cached Bmk-dev branches and the current
LiandZhang50 branch. Check:

1. whether the branch matrix correctly distinguishes current normative rules
   from beta/codex/upload/LiandZhang historical conventions;
2. whether the required-file and oracle-layout statements are supported;
3. whether the README, AGENTS, REPO_STATUS, CANDIDATES, skill, and spec tone
   comparison is fair and does not turn style heuristics into hard gates;
4. whether the current 50's `ARTIFACT_ONLY` wording is more evidence-correct
   than historical `QUALIFIED` wording;
5. whether the report identifies any material omissions or overclaims.

Be conservative. Treat the supplied branch/style audit as machine evidence,
and distinguish historical convention from the current sync standard. Do not
upgrade any task to QUALIFIED merely because another branch uses that label.
