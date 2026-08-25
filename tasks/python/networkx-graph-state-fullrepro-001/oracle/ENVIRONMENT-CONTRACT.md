# Environment contract

- Reference repository: `https://github.com/networkx/networkx.git`.
- Pinned commit: `d8081795e1344c576590b214c2e4f264b5e87244`.
- Pinned tree: `11e304e0ac731258355dc09836229d8bbf2655ac`.
- Reference version: `3.7rc0.dev0`.
- Runtime: CPython 3.12 or newer, standard library plus the pinned NetworkX
  source; no network installation is performed.
- The candidate owns `networkx.workspace`; ordinary NetworkX modules may be
  implemented directly or loaded from the declared pinned runtime.
- Evaluator-created workspace directories are private to each semantic root.
  State must be durable across a new Python object opened on the same path.
- UTF-8 source, regular files only; symlinks and evaluator-path dependencies
  are forbidden.
