# MiniAptly Source Notes

MiniAptly is inspired by aptly's public archive-management lifecycle, especially mirrors/local repositories, snapshots, published repositories, publish switching, cleanup, recovery, and graph/report surfaces.

Sources used for product semantics:

- https://www.aptly.info/doc/overview/
- https://www.aptly.info/doc/aptly/publish/switch/
- https://www.aptly.info/doc/aptly/snapshot/drop/
- https://manpages.debian.org/testing/aptly/aptly.1.en.html

The task intentionally does not clone aptly's implementation, Go APIs, real Debian package format, GPG signing, network mirrors, compression, or exact CLI. It uses an aptly-inspired simplified archive lifecycle to reduce known-pattern and forced-standard risk while preserving public multi-projection state.
