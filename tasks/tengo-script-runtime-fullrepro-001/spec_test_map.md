# Spec Test Map — Tengo v1

| Node range | Clauses | Source | Focus |
|---|---|---|---|
| `atomic::TestTGO001`–`TestTGO007` | `TGO-001`–`TGO-005` | generated | scalar expressions, comparisons, short circuit, conditional |
| `atomic::TestTGO008`–`TestTGO015` | `TGO-004`, `TGO-008`, `TGO-010` | generated | arrays, maps, builtins, functions |
| `atomic::TestTGO016`–`TestTGO021` | `TGO-013`–`TGO-017` | generated | Go/object conversion and recursive count |
| `atomic::TestTGO022`–`TestTGO027` | `TGO-018`–`TGO-023` | generated | variables, script lifecycle, errors, modules |
| `atomic::TestTGO028`–`TestTGO030` | `TGO-024`, `TGO-026`, `TGO-012` | generated | limits, cancellation, object truth/type |
| `integration::TestTGO031`–`TestTGO035` | `TGO-027`–`TGO-032` | generated | parity, rerun, views, clone isolation |
| `integration::TestTGO036`–`TestTGO040` | `TGO-033`–`TGO-036` | generated | closure, recursion, loops, mutation, variadics |
| `integration::TestTGO041`–`TestTGO044` | `TGO-037`–`TGO-040` | generated | builtin/source/nested modules and Go callables |
| `integration::TestTGO045`–`TestTGO050` | `TGO-029`, `TGO-041`–`TGO-045`, `TGO-011` | generated | error boundaries, cancellation recovery, concurrency, immutable/error values |
| `atomic::TestTGO051`–`TestTGO055` | `TGO-001`, `TGO-004`, `TGO-013`, `TGO-016`, `TGO-021` | generated | bitwise operations, slicing, conversions, module-map merge |
| `integration::TestTGO056`–`TestTGO060` | `TGO-025`, `TGO-033`, `TGO-035`, `TGO-038`, `TGO-039`, `TGO-044` | generated | loop/closure composition, source exports, limits, merged modules |
