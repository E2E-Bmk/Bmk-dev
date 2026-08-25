def raises(kind, operation):
    try: operation()
    except kind: return
    raise AssertionError(f"expected {kind.__name__}")


def stores():
    from packaging.federation import LayeredPolicyBook, WitnessGraph, MirrorQuorum, TransparencyLog, CompensationJournal, FederationCoordinator
    policies = LayeredPolicyBook(); witnesses = WitnessGraph(); mirrors = MirrorQuorum(); log = TransparencyLog(); compensations = CompensationJournal()
    return policies, witnesses, mirrors, log, compensations, FederationCoordinator(policies, witnesses, mirrors, log, compensations)


def seeded(owner="acme", release="r1"):
    policies, witnesses, mirrors, log, compensations, coordinator = stores()
    policies.define("baseline", 10, (("core-lib", ">=1,<3", None), ("plug-in", ">=2,<4", "os_name == 'posix'")))
    policies.define("security", 20, (("core_lib", ">=2,<3", None),))
    lease = policies.lease("lease-1", owner, {"os_name":"posix", "python_version":"3.12"}, {"core-lib":("1.9","2.4"), "plug_in":("2.1","3.5")})
    artifacts = ("core.whl", "plugin.whl"); digests = {"core.whl":"d-core", "plugin.whl":"d-plugin"}
    coordinator.stage(release, owner, lease.lease_id, artifacts)
    for artifact, digest in digests.items():
        base = witnesses.add(f"{artifact}:source", owner, artifact + ":source", "src-" + digest, "source")
        witnesses.add(f"{artifact}:a", owner, artifact, digest, "builder-a", (base.claim_id,))
        witnesses.add(f"{artifact}:b", owner, artifact, digest, "builder-b", (base.claim_id,))
    mirrors.observe(owner, "m1", 7, digests); mirrors.observe(owner, "m2", 7, digests)
    return policies, witnesses, mirrors, log, compensations, coordinator, artifacts, digests
