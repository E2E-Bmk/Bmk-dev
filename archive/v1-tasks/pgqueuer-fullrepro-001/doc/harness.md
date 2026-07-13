# PgQueueLedger Harness

Run the hidden executable scorer from outside the candidate workspace:

```powershell
python task\pgqueuer-fullrepro-001\scoring\run_executable_checks.py `
  --solution-dir runs\pgqueuer-fullrepro-001\solution-reference `
  --json-out runs\pgqueuer-fullrepro-001\score_report_reference_v2_repair.json
```

Candidate agents must see only:

- `candidate_task/public_packet.md`
- `candidate_task/starter/`
- an empty `solution/` directory

Hidden assets stay outside the cleanroom:

- `rubric.json`
- `doc/requirement_map.md`
- `scoring/`
- reference solution
- score reports
- prior traces

The first strict model run is forbidden until the reference solution scores
100% and a fairness judge approves the repaired scorer.
