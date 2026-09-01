# Upstream checkouts for the four-language WIP tasks

The Stage 1 feasibility work cloned these into `/tmp`, which does not survive a
reboot. Recorded here so any later stage can restore them without re-deriving
the commit from `filter_notes.md`.

| task | repo | commit | current path |
|---|---|---|---|
| `gocty-value-algebra-fullrepro-001` | `zclconf/go-cty` | `0d1eb267373bab24cd0f4d917ab4b8200bb0234a` | `/tmp/feas/go-cty`, `/tmp/s2rprobe/go-cty` |
| `graphql-inspector-schemadiff-fullrepro-001` | `graphql-hive/graphql-inspector` | `7180fcae8260a734d526d66157c1a361c00f04d6` | `/tmp/feasts/graphql-inspector` |
| `guppy-cargo-graph-fullrepro-001` | `guppy-rs/guppy` | `2deddd390245dfa226dc5acf3a46f3d2eb38f2e5` | `/tmp/feas/guppy` |
| `japicmp-binarycompat-fullrepro-001` | `siom79/japicmp` | `5186e1d75e9588e86afb20f5e98f7885093780c4` | `/tmp/feas/japicmp`, `/tmp/b2r/japicmp` |

Restore:

```bash
mkdir -p /tmp/feas && cd /tmp/feas
git clone https://github.com/zclconf/go-cty                 && git -C go-cty            checkout 0d1eb26
git clone https://github.com/guppy-rs/guppy                 && git -C guppy             checkout 2deddd3
git clone https://github.com/siom79/japicmp                 && git -C japicmp           checkout 5186e1d
mkdir -p /tmp/feasts && cd /tmp/feasts
git clone https://github.com/graphql-hive/graphql-inspector && git -C graphql-inspector checkout 7180fca
```

`guppy` and `graphql-inspector` measure ~1.1 GB each on disk only because the
`/tmp` copies carry build artifacts (`target/`, `node_modules/`); a fresh clone
is far smaller and is sufficient for spec writing and test filtering.

The host has network access. The **agent** container does not — see
`spec2repo-agent-container-language` — so nothing here can be fetched from
inside a solve run.
