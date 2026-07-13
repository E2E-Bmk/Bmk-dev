# Requirement Map

Rubric: `task/minikv-realrepo-submit/rubric.json`

Status: `revised-after-independent-judge-verdict/fairness-cascade-trimmed`

## Requirements

| Requirement | Public packet section | Rubric IDs |
| --- | --- | --- |
| `REQ-string-ops` | String and Scalar Operations | `MKVU001`, `MKVU002`, `MKVU003`, `MKVU004`, `MKVU016`, `MKVS001`, `MKVS002`, `MKVS003`, `MKVS004`, `MKVS005`, `MKVS007` |
| `REQ-bulk-ops` | Bulk Operations | `MKVU005`, `MKVS006` |
| `REQ-list-ops` | List Operations | `MKVU006`, `MKVU007`, `MKVU008`, `MKVU009`, `MKVU016`, `MKVS001`, `MKVS002`, `MKVS003`, `MKVS004`, `MKVS005`, `MKVS006` |
| `REQ-set-ops` | Set Operations | `MKVU010`, `MKVU011`, `MKVU012`, `MKVU016`, `MKVS001`, `MKVS002`, `MKVS003`, `MKVS004`, `MKVS005`, `MKVS006`, `MKVS007` |
| `REQ-hash-ops` | Hash Operations | `MKVU013`, `MKVU014`, `MKVU015`, `MKVU016`, `MKVS001`, `MKVS002`, `MKVS003`, `MKVS004`, `MKVS005`, `MKVS006` |
| `REQ-key-mgmt` | Key Management | `MKVU017`, `MKVU018`, `MKVS003`, `MKVS004`, `MKVS005`, `MKVS006`, `MKVS007` |
| `REQ-errors` | Error Behavior | `MKVU004`, `MKVU009`, `MKVU012`, `MKVU015`, `MKVS002`, `MKVS005` |

## Redesign Diagnosis

Canonical fact source: one live key table with value, type tag, and optional expiry metadata.

Derived public views:

- direct read/write/existence/delete/counter APIs;
- list, set, and hash projections;
- mutable returned set and dict views;
- expiry and flush lifecycle behavior;
- persisted save/load representation.

The previous system layer mostly re-ran short feature workflows. The invariant-v2 revision improved this, but an independent fairness judge found that the numeric gap was still dominated by two unit-visible roots: counter auto-creation and missing-key `lrange`. The current revision keeps those behaviors in unit/local tests and trims them out of system scoring unless a separate downstream projection diverges.

The revised system layer now asserts that direct reads, type-specific views, error atomicity, expiry, delete/reuse/flush, mutable views, and persistence all agree after mixed operations. System counter checks start from an existing numeric key, and flush/delete checks validate fresh type reuse rather than repeating missing-list semantics.

## Current Score Evidence After Fairness Revision

| Agent | Unit | System | Gap | Report |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | `doc/score_reports/score_report_reference_fairness_revision.json` |
| Codex subagent | 100.00% | 100.00% | 0.00pp | `doc/score_reports/score_report_codex_subagent_001_fairness_revision.json` |
| OpenHands + DeepSeek V4 | 77.78% | 100.00% | -22.22pp | `doc/score_reports/score_report_openhands_deepseek_v4_pro_001_fairness_revision.json` |
| DeepSeek V4 direct | 94.44% | 85.71% | 8.73pp | `doc/score_reports/score_report_deepseek_v4_pro_001_fairness_revision.json` |

The previous invariant-v2 reports remain useful audit artifacts but are stale for acceptance gating. After cascade trimming, no stored candidate shows a fair unit-over-system gap above 15pp. The remaining direct DeepSeek system failure is a true downstream projection mismatch: `kv_mset` stores list/set/dict values without sharing the direct `kv_set` type-detection path, so typed views and persistence disagree. The OpenHands failures are now confined to unit/local behavior.
