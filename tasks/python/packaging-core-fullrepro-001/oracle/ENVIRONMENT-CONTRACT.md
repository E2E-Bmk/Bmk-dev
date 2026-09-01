# Environment contract

- Python 3.11+; UTF-8 source; no network, subprocess, clock, randomness, or filesystem persistence is required.
- The candidate directory is source blank before the solver writes it and must contain the complete importable `packaging` package.
- Evaluation imports only candidate-contained `packaging.*` modules. The reference profile may attach its private federation implementation to the pinned clean reference package.
- Semantic calls may raise documented validation errors. Setup/import/signature/provenance failures, warnings, or outer root timeouts invalidate a run; other exceptions raised after a root enters its semantic call are ordinary failures.
- Roots are isolated processes and may execute in natural, reverse, or fixed-permuted order.
