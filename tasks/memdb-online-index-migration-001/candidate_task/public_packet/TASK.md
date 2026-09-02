# Implementation Request

Implement the online atomic secondary-index migration extension described in `SPEC.md` for the provided `github.com/hashicorp/go-memdb` source tree.

Preserve all existing behavior. Add the documented public API and error values, perform complete atomic backfill, retain old MVCC schema generations, provide the specified watch notifications, and serialize migration consistently with ordinary writers.

Run `gofmt` and the relevant Go build and tests before finishing.
