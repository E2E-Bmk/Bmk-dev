# MkDocs v14 root design

Status: pre-freeze qualification design.  Counts are case-native: 12 Atomic,
14 Integration, and 10 System/E2E roots.

## Atomic

| ID | Owner | Independent behavior | Mutation |
|---|---|---|---|
| A01 | Q | typed config load, override, mapping/attribute agreement | no |
| A02 | F | Markdown/static destination and URL mapping | no |
| A03 | F | collection replacement, removal, typed subsets | no |
| A04 | A | metadata/source/render/TOC lifecycle | no |
| A05 | N | nav identity, parentage, adjacency, external links | no |
| A06 | E | public exception inheritance and exit status | no |
| A07 | C | normalized config generation record | yes |
| A08 | D | sorted discovery change set and pending acknowledgement | yes |
| A09 | L | stable page identity with revision advance | yes |
| A10 | P | prepare is non-visible and idempotent | yes |
| A11 | S | search artifact and semantic receipt record | yes |
| A12 | O | stable unique delivered event records | yes |

## Integration

| ID | Owners | Seam | Atomic prerequisites | Mutation |
|---|---|---|---|---|
| I01 | Q+B | effective destination produces complete basic site | A01 | no |
| I02 | F+A+B | URL policy agrees across file, link, and output | A02,A04 | no |
| I03 | A+N+X+B | title/location/heading agree with search | A04,A05 | no |
| I04 | Q+E+B | strict diagnostic changes success category | A01,A06 | no |
| I05 | C+D | one input change advances one shared generation | A07,A08 | yes |
| I06 | D+L+P | edit change, lineage revision, and publication agree | A08,A09,A10 | yes |
| I07 | D+L+S | declared rename transfers identity into search | A08,A09,A11 | yes |
| I08 | C+P | prepared generation later publishes without renumbering | A07,A10 | yes |
| I09 | D+P+S+O | identical retry completes acknowledgement in order | A08,A10,A11,A12 | yes |
| I10 | C+P | stale expected generation fences visible bytes | A07,A10 | yes |
| I11 | P+O | post-publication delivery failure retries exactly once | A10,A12 | yes |
| I12 | D+P | corrupted owner fails without changing visibility | A08,A10 | yes |
| I13 | L+P+S | search acknowledgement carries page lineage receipt | A09,A10,A11 | yes |
| I14 | C+O | plugin-set change creates one config event | A07,A12 | yes |

## System/E2E

| ID | Owners crossed | Workflow | Atomic prerequisites | Mutation |
|---|---|---|---|---|
| S01 | C+D+L+P | fresh-process edit and reopen | A07,A08,A09,A10 | yes |
| S02 | C+P+S | prepare in one process, publish in another | A07,A10,A11 | yes |
| S03 | D+P+O | delivery failure and fresh-process retry | A08,A10,A12 | yes |
| S04 | C+D+P | competing stale writer is fenced | A07,A08,A10 | yes |
| S05 | D+L+P+S | rename, publication, and search identity | A08,A09,A10,A11 | yes |
| S06 | D+P+O | unacknowledged conflict then same-generation recovery | A08,A10,A12 | yes |
| S07 | D+L+P | owner corruption, exact restore, reopen | A08,A09,A10 | yes |
| S08 | C+P+S+O | plugin-set change, failed delivery, recovery | A07,A10,A11,A12 | yes |
| S09 | D+P+S | clean republish removes stale output and receipts | A08,A10,A11 | yes |
| S10 | C+D+L+P+S+O | full prepare/publish/edit/rename/retry workflow | A07,A08,A09,A10,A11,A12 | yes |

## Independence and shortcut audit

The six synthetic Atomic roots each read a different durable record and can
fail independently.  No record contributes more than 6 of the 26 mutation
roots.  System roots require persistent reopen, ownership handoff, or recovery;
they cannot be satisfied by a single in-memory renderer.  Parameter variants
remain inside their owning root.  Composition scoring conditions on the listed
Atomic prerequisites and reports primitive-cascade exclusions separately.
