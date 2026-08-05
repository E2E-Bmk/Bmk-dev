# Independent submission-comparison review

Return valid JSON only with keys `verdict`, `blocking_issues`,
`non_blocking_issues`, `verified_claims`, `disputed_claims`, and
`recommendation`.

Review the supplied comparison between the previous 21-task LiandZhang branch,
the current 50-task artifact-only branch, and independent peer refs.

Check especially:

1. whether old branch conventions are incorrectly presented as universal hard
   requirements;
2. whether the reported current-validator failures and structural counts are
   supported by the supplied machine output;
3. whether numeric local candidate scores and self-submitted DeepSeek reviews
   can support `QUALIFIED` without an external signature/isolation attestation;
4. whether the current runner exposes oracle/test context to candidate code at
   scoring time and whether the Docker wrapper proves network isolation;
5. whether the current branch is correctly classified as structurally valid
   but `ARTIFACT_ONLY`;
6. whether any statement should be narrowed or corrected before publication.

Treat style heuristics as comparative signals, not semantic proof. Do not infer
missing signatures or attestations. A PASS verdict should mean that the report
is factually supportable, not that either submission is QUALIFIED.
