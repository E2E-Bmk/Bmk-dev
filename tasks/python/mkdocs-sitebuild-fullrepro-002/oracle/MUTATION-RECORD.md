# Mutation record

The clean pinned upstream provides ordinary MkDocs configuration, files,
pages, navigation, search, build, and error behavior but has no recoverable
publication records.  The synthetic product adds one coherent recovery mode
without changing ordinary builds or public call signatures.

| Family | Upstream rule | Synthetic rule | Owners | Roots |
|---|---|---|---|---|
| generation ownership | builds have no durable generation | normalized config and sources jointly own a reusable monotonic generation | C,D | A07,A08,I05,I08,I14,S01,S02,S04,S08,S10 |
| acknowledged discovery | each build rediscovers current files | sorted deltas are retained until the exact generation is acknowledged | D | A08,I05,I06,I09,I12,S01,S03,S04,S06,S07,S09,S10 |
| lineage | Page identity is build-local | page IDs survive edit/reopen and transfer only through declared rename | L | A09,I06,I07,I13,S01,S05,S07,S10 |
| publication transaction | clean build writes destination directly | generation-owned prepare, visible publication, and stale fencing are distinct | P | A10,I06,I08,I09,I10,I11,I12,I13,S01-S10 |
| search receipts | search JSON has no recovery receipt | artifact and semantic records bind search to acknowledged page/publication lineage | S | A11,I07,I09,I13,S02,S05,S08,S09,S10 |
| outbox recovery | plugin completion has no durable exactly-once journal | stable events survive delivery failure and retry without duplication | O | A12,I09,I11,I14,S03,S06,S08,S10 |
| owner integrity | history may be recomputed from current inputs | existing owner/checksum corruption fails and does not rewrite other owners | C,D,L,P,S,O | I12,S07,S10 |

The portfolio covers 26/36 roots (72.22%) across all six substantial surfaces.
No one abstraction satisfies more than half of the mutation roots.  The public
rules are implementable with JSON journals, SQLite, or another local durable
store and are coherent with an offline documentation publisher.

M1 must pass every root.  M2 must pass exactly A01-A06 and I01-I04.  The
behavior-empty control must pass none.  Any other M2 vector is an incomplete
impact declaration and blocks freeze.

