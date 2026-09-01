# Environment contract

- Python 3.12
- pytest 9.x is used only by the evaluator
- implementation dependencies: Python standard library only
- supported host: Windows or POSIX with local stream sockets or a loopback TCP fallback
- network access is not required
- all synchronization in the contract is observable through public barriers,
  lifecycle waits, or completion operations; timing assumptions are not part of
  the contract

