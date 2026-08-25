from __future__ import annotations

from pathlib import Path

from tests.support import (
    acknowledged_publication,
    entries_for,
    expect_error,
    native_api,
    records,
    temporary_root,
    workflow_api,
)


def test_i01_settings_author_cross_view():
    api = native_api()
    settings = api.read_settings(override={"AUTHOR_URL": "contributors/{slug}/", "AUTHOR_SAVE_AS": "contributor-pages/{slug}.html"})
    author = api.Author("Amber Editor", settings)
    assert author.url == "contributors/amber-editor/"
    assert author.save_as == "contributor-pages/amber-editor.html"
    assert author.as_dict()["slug"] == author.slug == "amber-editor"


def test_i02_taxonomy_namespace_cross_view():
    api = native_api()
    with temporary_root("pelican-v6-i02-") as name:
        path = Path(name) / "settings.py"
        path.write_text("CATEGORY_URL='topics/{slug}/'\nTAG_URL='labels/{slug}/'\n", encoding="utf-8")
        settings = api.read_settings(path=str(path), override={"CATEGORY_SAVE_AS": "topic-files/{slug}.html", "TAG_SAVE_AS": "label-files/{slug}.html"})
        category = api.Category("Shared Copper", settings)
        tag = api.Tag("Shared Copper", settings)
    assert category.slug == tag.slug == "shared-copper"
    assert category.url != tag.url and category.save_as != tag.save_as


def test_i03_slug_path_author_handoff():
    api = native_api()
    settings = api.read_settings(override={"AUTHOR_URL": "people/{slug}/", "AUTHOR_SAVE_AS": "people/{slug}/index.html"})
    expected_slug = api.slugify("Silver Curator", ((" ", "-"),))
    author = api.Author("Silver Curator", settings)
    projected = api.path_to_url(api.posixize_path(author.save_as))
    assert author.slug == expected_slug
    assert author.url == f"people/{expected_slug}/"
    assert projected == f"people/{expected_slug}/index.html"


def test_i04_cli_settings_completion():
    api = native_api()
    args = api.parse_arguments(["-e", 'SITENAME="Typed Ridge"', 'DEFAULT_LANG="nl"', "RELATIVE_URLS=true"])
    partial = api.get_config(args)
    completed = api.read_settings(override={key: partial[key] for key in ("SITENAME", "DEFAULT_LANG", "RELATIVE_URLS")})
    assert completed["SITENAME"] == "Typed Ridge" and completed["DEFAULT_LANG"] == "nl"
    assert completed["RELATIVE_URLS"] is True and "OUTPUT_PATH" in completed


def test_i05_paginator_rule_projection():
    api = native_api()
    settings = api.read_settings(override={"DEFAULT_ORPHANS": 0})
    paginator = api.Paginator("ore", "archive/{number}/", ["tin", "iron", "gold", "zinc", "lead"], settings, per_page=2)
    rule = api.PaginationRule(2, "archive/{number}/", "archive-pages/{number}.html")
    projected = [(number, rule.URL.format(number=number), rule.SAVE_AS.format(number=number), paginator.page(number).object_list) for number in paginator.page_range if number >= rule.min_page]
    assert projected == [(2, "archive/2/", "archive-pages/2.html", ["gold", "zinc"]), (3, "archive/3/", "archive-pages/3.html", ["lead"])]


def test_i06_settings_taxonomy_consistency():
    api = native_api()
    settings = api.read_settings(override={
        "AUTHOR_URL": "owners/{slug}/", "AUTHOR_SAVE_AS": "owner-files/{slug}.html",
        "CATEGORY_URL": "groups/{slug}/", "CATEGORY_SAVE_AS": "group-files/{slug}.html",
        "TAG_URL": "facets/{slug}/", "TAG_SAVE_AS": "facet-files/{slug}.html",
    })
    values = [api.Author("North Star", settings), api.Category("North Star", settings), api.Tag("North Star", settings)]
    assert {value.slug for value in values} == {"north-star"}
    assert [value.url for value in values] == ["owners/north-star/", "groups/north-star/", "facets/north-star/"]
    assert len({value.save_as for value in values}) == 3


def test_i07_ingest_identity_handoff():
    api = workflow_api()
    with temporary_root("pelican-v6-i07-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        receipt = store.ingest(records())
        snapshot = api.IdentityIndex(root / "identity").project(receipt["generation"], store.current()["records"])
        assert snapshot["generation"] == receipt["generation"]
        assert {row["source_id"] for row in snapshot["identities"]} == {"opal", "quartz"}
        assert receipt["digest"] == store.current()["digest"]


def test_i08_ingest_expected_generation_retry():
    api = workflow_api()
    with temporary_root("pelican-v6-i08-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        first = store.ingest(records())
        store.acknowledge(first["generation"], first["digest"])
        expect_error(api.StaleGenerationError, lambda: store.ingest(records(2), expected_generation=0))
        assert store.current()["generation"] == 1 and store.current()["acknowledged"]
        second = store.ingest(records(2), expected_generation=1)
        assert second["generation"] == 2 and not second["acknowledged"]


def test_i09_identity_alias_resolution():
    api = workflow_api()
    with temporary_root("pelican-v6-i09-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        index = api.IdentityIndex(root / "identity")
        one = store.ingest(records(1))
        index.project(one["generation"], store.current()["records"])
        two = store.ingest(records(2), expected_generation=1)
        index.project(two["generation"], store.current()["records"])
        current = index.resolve("quartz-field-guide")
        old = index.resolve("quartz-notes")
        assert current and old and current["identity"] == old["identity"]
        assert current["slug"] == old["slug"] == "quartz-field-guide"


def test_i10_identity_taxonomy_namespaces():
    api = workflow_api()
    with temporary_root("pelican-v6-i10-") as name:
        root = Path(name)
        rows = records()
        rows[0]["category"] = "Field"
        rows[0]["tags"] = ["Field"]
        store = api.ContentStore(root / "content")
        receipt = store.ingest(rows)
        index = api.IdentityIndex(root / "identity")
        snapshot = index.project(receipt["generation"], store.current()["records"])
        matches = [row for row in snapshot["identities"] if row["source_id"] == "quartz"]
        assert matches
        quartz = matches[0]
        expect_error(api.StaleGenerationError, lambda: index.project(1, rows))
        assert quartz["category"] == "Field" and quartz["tags"] == ["Field"]
        assert index.snapshot() == snapshot


def test_i11_identity_theme_context():
    api = workflow_api()
    with temporary_root("pelican-v6-i11-") as name:
        root = Path(name)
        index = api.IdentityIndex(root / "identity")
        identities = index.project(5, records())
        renderer = api.ThemeRenderer(root / "theme")
        lease = renderer.lease(5, "granite", identities)
        artifact = renderer.render(lease["token"], "content:opal", "opal text", context_generation=5)
        assert artifact["identity"] == "content:opal" and artifact["generation"] == identities["generation"]
        assert artifact["path"] == "articles/opal-dispatch.html"
        committed = renderer.commit(lease["token"])
        assert committed and committed[0] == artifact


def test_i12_new_lease_fences_old_context():
    api = workflow_api()
    with temporary_root("pelican-v6-i12-") as name:
        root = Path(name)
        index = api.IdentityIndex(root / "identity")
        first_identities = index.project(2, records())
        renderer = api.ThemeRenderer(root / "theme")
        first = renderer.lease(2, "granite", first_identities)
        second_identities = index.project(3, records(2))
        second = renderer.lease(3, "granite-v2", second_identities)
        expect_error(api.StaleGenerationError, lambda: renderer.render(first["token"], "content:quartz", "old", context_generation=2))
        current = renderer.render(second["token"], "content:quartz", "new", context_generation=3)
        assert current["path"] == "articles/quartz-field-guide.html" and current["generation"] == 3


def test_i13_ingest_feed_generation():
    api = workflow_api()
    with temporary_root("pelican-v6-i13-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        content = store.ingest(records())
        _, publication = acknowledged_publication(root, content["generation"])
        ledger = api.PublicationLedger(root / "ledger")
        staged = ledger.stage(content["generation"], entries_for(store.current()["records"]), page_size=2)
        committed = ledger.commit(staged["token"], publication)
        assert committed["generation"] == store.current()["generation"]
        assert [row["source_id"] for row in committed["feed"]] == ["quartz", "opal"]
        assert len(committed["pages"]) == 1


def test_i14_identity_alias_feed_link():
    api = workflow_api()
    with temporary_root("pelican-v6-i14-") as name:
        root = Path(name)
        index = api.IdentityIndex(root / "identity")
        index.project(1, records())
        identities = index.project(2, records(2))
        _, publication = acknowledged_publication(root, 2)
        ledger = api.PublicationLedger(root / "ledger")
        stage = ledger.stage(2, entries_for(records(2), identities), page_size=3)
        view = ledger.commit(stage["token"], publication)
        matches = [row for row in view["feed"] if row["source_id"] == "quartz"]
        assert matches
        quartz = matches[0]
        assert quartz["url"] == "articles/quartz-field-guide.html"
        historical = index.resolve("quartz-notes")
        assert historical is not None and historical["identity"] == "content:quartz"


def test_i15_pagination_replacement():
    api = workflow_api()
    with temporary_root("pelican-v6-i15-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        ledger = api.PublicationLedger(root / "ledger")
        first_prepare = publisher.prepare(1, {"index.html": "one"})
        first_visible = publisher.promote(first_prepare["token"])
        first_ack = publisher.acknowledge(1, first_visible["digest"])
        first_stage = ledger.stage(1, entries_for(records()), page_size=1)
        first_view = ledger.commit(first_stage["token"], first_ack)
        second_prepare = publisher.prepare(2, {"index.html": "two"})
        second_visible = publisher.promote(second_prepare["token"])
        second_ack = publisher.acknowledge(2, second_visible["digest"])
        rows = [records(2)[0]]
        second_stage = ledger.stage(2, entries_for(rows), page_size=4)
        assert ledger.view() == first_view and len(first_view["pages"]) == 2
        second_view = ledger.commit(second_stage["token"], second_ack)
        assert second_view["generation"] == 2 and len(second_view["pages"]) == 1
        assert [row["source_id"] for row in second_view["feed"]] == ["quartz"]


def test_i16_render_prepare_visibility():
    api = workflow_api()
    with temporary_root("pelican-v6-i16-") as name:
        root = Path(name)
        identities = api.IdentityIndex(root / "identity").project(1, records())
        renderer = api.ThemeRenderer(root / "theme")
        lease = renderer.lease(1, "dune", identities)
        artifact = renderer.render(lease["token"], "content:quartz", "vein", context_generation=1)
        artifacts = renderer.commit(lease["token"])
        publisher = api.ArtifactPublisher(root / "publisher")
        prepared = publisher.prepare(1, {row["path"]: row["text"] for row in artifacts})
        assert publisher.read(artifact["path"]) is None
        visible = publisher.promote(prepared["token"])
        assert visible["generation"] == artifact["generation"]
        assert publisher.read(artifact["path"]) == artifact["text"].encode()


def test_i17_prepared_crash_does_not_advance_ledger():
    api = workflow_api()
    with temporary_root("pelican-v6-i17-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        first = publisher.prepare(1, {"index.html": "committed"})
        first_visible = publisher.promote(first["token"])
        first_ack = publisher.acknowledge(1, first_visible["digest"])
        ledger = api.PublicationLedger(root / "ledger")
        first_stage = ledger.stage(1, entries_for(records()), page_size=2)
        ledger.commit(first_stage["token"], first_ack)
        second_stage = ledger.stage(2, entries_for(records(2)), page_size=1)
        publisher.prepare(2, {"index.html": "uncommitted"})
        assert publisher.read("index.html") == b"committed"
        publisher.recover()
        expect_error(api.AcknowledgementError, lambda: ledger.commit(second_stage["token"], {"generation": 2, "visible": False, "acknowledged": False}))
        assert ledger.view()["generation"] == 1 and publisher.read("index.html") == b"committed"


def test_i18_publication_enqueues_signal():
    api = workflow_api()
    with temporary_root("pelican-v6-i18-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        prepared = publisher.prepare(4, {"index.html": "ready"})
        visible = publisher.promote(prepared["token"])
        outbox = api.SignalOutbox(root / "outbox")
        expect_error(api.AcknowledgementError, lambda: outbox.enqueue(4, "visible-only", {}, publication_receipt=visible))
        acknowledged = publisher.acknowledge(4, visible["digest"])
        event = outbox.enqueue(4, "ready", {"digest": visible["digest"]}, publication_receipt=acknowledged)
        assert event["generation"] == 4 and event["state"] == "pending"
        assert [row["event_id"] for row in outbox.pending()] == ["ready"]


def test_i19_signal_retry_exactly_once():
    api = workflow_api()
    with temporary_root("pelican-v6-i19-") as name:
        root = Path(name)
        _, receipt = acknowledged_publication(root, 2)
        outbox = api.SignalOutbox(root / "outbox")
        original = outbox.enqueue(2, "feed-ready", {"generation": 2}, publication_receipt=receipt)
        duplicate = outbox.enqueue(2, "feed-ready", {"different": True}, publication_receipt=receipt)
        first = outbox.claim("one")
        assert first is not None
        outbox.fail(first["token"], "one")
        second = outbox.claim("two")
        assert second is not None
        delivered = outbox.ack(second["token"], "two")
        repeated = outbox.ack(second["token"], "two")
        assert original["token"] == duplicate["token"] == delivered["token"]
        assert second["attempt"] == 2 and repeated == delivered and len(outbox.delivered()) == 1


def test_i20_signal_worker_ownership():
    api = workflow_api()
    with temporary_root("pelican-v6-i20-") as name:
        root = Path(name)
        _, receipt = acknowledged_publication(root, 3)
        outbox = api.SignalOutbox(root / "outbox")
        outbox.enqueue(3, "owned", {}, publication_receipt=receipt)
        claim = outbox.claim("worker-citrine")
        assert claim is not None
        expect_error(api.OwnershipError, lambda: outbox.fail(claim["token"], "worker-amber"))
        expect_error(api.OwnershipError, lambda: outbox.ack(claim["token"], "worker-amber"))
        pending = outbox.pending()
        assert pending and pending[0]["worker"] == "worker-citrine"
        outbox.ack(claim["token"], "worker-citrine")
        assert len(outbox.delivered()) == 1


def test_i21_acknowledged_ingest_reopen():
    api = workflow_api()
    with temporary_root("pelican-v6-i21-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        receipt = store.ingest(records())
        acknowledged = store.acknowledge(receipt["generation"], receipt["digest"])
        reopened = api.ContentStore(root / "content")
        index = api.IdentityIndex(root / "identity")
        snapshot = index.project(reopened.current()["generation"], reopened.current()["records"])
        assert reopened.current()["acknowledged"] and reopened.current()["digest"] == acknowledged["digest"]
        assert snapshot["generation"] == acknowledged["generation"]


def test_i22_reopen_stale_ingest_fence():
    api = workflow_api()
    with temporary_root("pelican-v6-i22-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        first = store.ingest(records())
        store.acknowledge(1, first["digest"])
        reopened = api.ContentStore(root / "content")
        expect_error(api.StaleGenerationError, lambda: reopened.ingest(records(2), expected_generation=0))
        identity = api.IdentityIndex(root / "identity").project(1, reopened.current()["records"])
        assert reopened.current()["generation"] == 1 and identity["generation"] == 1


def test_i23_reopen_theme_fence():
    api = workflow_api()
    with temporary_root("pelican-v6-i23-") as name:
        root = Path(name)
        index = api.IdentityIndex(root / "identity")
        identities = index.project(6, records())
        renderer = api.ThemeRenderer(root / "theme")
        lease = renderer.lease(6, "night", identities)
        renderer.render(lease["token"], "content:opal", "night body", context_generation=6)
        reopened = api.ThemeRenderer(root / "theme")
        newer = reopened.lease(7, "dawn", identities)
        expect_error(api.StaleGenerationError, lambda: reopened.render(lease["token"], "content:opal", "stale", context_generation=6))
        current = reopened.render(newer["token"], "content:opal", "fresh", context_generation=7)
        assert current["generation"] == 7 and current["text"].startswith("dawn|")


def test_i24_reopen_promoted_recovery():
    api = workflow_api()
    with temporary_root("pelican-v6-i24-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        first = publisher.prepare(1, {"index.html": "before"})
        old = publisher.promote(first["token"])
        publisher.acknowledge(1, old["digest"])
        second = publisher.prepare(2, {"index.html": "after"})
        promoted = publisher.promote(second["token"])
        reopened = api.ArtifactPublisher(root / "publisher")
        recovered = reopened.recover()
        ledger = api.PublicationLedger(root / "ledger")
        staged = ledger.stage(2, entries_for(records(2)), page_size=2)
        acknowledged = reopened.acknowledge(2, promoted["digest"])
        view = ledger.commit(staged["token"], acknowledged)
        assert recovered["state"] == "recovered-promoted" and reopened.read("index.html") == b"after"
        assert view["generation"] == 2


def test_i25_rename_render_current_identity():
    api = workflow_api()
    with temporary_root("pelican-v6-i25-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        index = api.IdentityIndex(root / "identity")
        one = store.ingest(records())
        index.project(1, store.current()["records"])
        store.ingest(records(2), expected_generation=1)
        identities = index.project(2, store.current()["records"])
        renderer = api.ThemeRenderer(root / "theme")
        lease = renderer.lease(2, "renamed", identities)
        artifact = renderer.render(lease["token"], "content:quartz", "new body", context_generation=2)
        assert artifact["path"] == "articles/quartz-field-guide.html"
        historical = index.resolve("quartz-notes")
        assert historical is not None and historical["identity"] == artifact["identity"]


def test_i26_stale_feed_stage_rejected():
    api = workflow_api()
    with temporary_root("pelican-v6-i26-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        first = publisher.prepare(1, {"index.html": "one"})
        first_visible = publisher.promote(first["token"])
        first_ack = publisher.acknowledge(1, first_visible["digest"])
        ledger = api.PublicationLedger(root / "ledger")
        stale_stage = ledger.stage(1, entries_for(records()), page_size=1)
        first_view = ledger.commit(stale_stage["token"], first_ack)
        second = publisher.prepare(2, {"index.html": "two"})
        second_visible = publisher.promote(second["token"])
        second_ack = publisher.acknowledge(2, second_visible["digest"])
        old_token = ledger.stage(2, entries_for(records(2)), page_size=1)
        current_token = ledger.stage(3, entries_for(records(2)), page_size=2)
        expect_error(api.OwnershipError, lambda: ledger.commit(old_token["token"], second_ack))
        expect_error(api.StaleGenerationError, lambda: ledger.commit(current_token["token"], second_ack))
        assert ledger.view() == first_view


def test_i27_publication_ack_failure_recovery():
    api = workflow_api()
    with temporary_root("pelican-v6-i27-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        prepared = publisher.prepare(9, {"index.html": "nine"})
        visible = publisher.promote(prepared["token"])
        expect_error(api.AcknowledgementError, lambda: publisher.acknowledge(9, "f" * 64))
        outbox = api.SignalOutbox(root / "outbox")
        expect_error(api.AcknowledgementError, lambda: outbox.enqueue(9, "bad-ack", {}, publication_receipt=visible))
        recovered = api.ArtifactPublisher(root / "publisher").recover()
        acknowledged = publisher.acknowledge(9, visible["digest"])
        assert recovered["visible"]["digest"] == acknowledged["digest"] and publisher.read("index.html") == b"nine"


def test_i28_outbox_reopen_claim_recovery():
    api = workflow_api()
    with temporary_root("pelican-v6-i28-") as name:
        root = Path(name)
        _, receipt = acknowledged_publication(root, 8)
        outbox = api.SignalOutbox(root / "outbox")
        event = outbox.enqueue(8, "restart-event", {"g": 8}, publication_receipt=receipt)
        claimed = outbox.claim("lost-worker")
        assert claimed is not None
        assert claimed["attempt"] == 1 and claimed["token"] == event["token"]
        reopened = api.SignalOutbox(root / "outbox")
        retry = reopened.claim("recovery-worker")
        assert retry is not None
        assert retry["attempt"] == 2 and retry["token"] == event["token"]
        reopened.ack(retry["token"], "recovery-worker")
        assert len(reopened.delivered()) == 1 and not reopened.pending()


def test_s01_ingest_identity_render_publish():
    api = workflow_api()
    with temporary_root("pelican-v6-s01-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        receipt = store.ingest(records())
        identities = api.IdentityIndex(root / "identity").project(receipt["generation"], store.current()["records"])
        renderer = api.ThemeRenderer(root / "theme")
        lease = renderer.lease(receipt["generation"], "ridge", identities)
        artifacts = [renderer.render(lease["token"], row["identity"], row["source_id"], context_generation=receipt["generation"]) for row in identities["identities"]]
        renderer.commit(lease["token"])
        publisher = api.ArtifactPublisher(root / "publisher")
        prepared = publisher.prepare(receipt["generation"], {row["path"]: row["text"] for row in artifacts})
        assert all(publisher.read(row["path"]) is None for row in artifacts)
        visible = publisher.promote(prepared["token"])
        acknowledged = publisher.acknowledge(receipt["generation"], visible["digest"])
        assert acknowledged["acknowledged"] and all(publisher.read(row["path"]) for row in artifacts)


def test_s02_publish_crash_feed_recovery():
    api = workflow_api()
    with temporary_root("pelican-v6-s02-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        prepared = publisher.prepare(2, {"index.html": "durable two"})
        visible = publisher.promote(prepared["token"])
        recovered = api.ArtifactPublisher(root / "publisher").recover()
        assert recovered["state"] == "recovered-promoted" and publisher.read("index.html") == b"durable two"
        acknowledged = publisher.acknowledge(2, visible["digest"])
        ledger = api.PublicationLedger(root / "ledger")
        stage = ledger.stage(2, entries_for(records(2)), page_size=1)
        view = ledger.commit(stage["token"], acknowledged)
        assert view["generation"] == 2 and len(view["pages"]) == 2


def test_s03_regeneration_stale_fencing():
    api = workflow_api()
    with temporary_root("pelican-v6-s03-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        index = api.IdentityIndex(root / "identity")
        first = store.ingest(records())
        ids1 = index.project(1, store.current()["records"])
        renderer = api.ThemeRenderer(root / "theme")
        lease1 = renderer.lease(1, "old", ids1)
        second = store.ingest(records(2), expected_generation=1)
        ids2 = index.project(2, store.current()["records"])
        lease2 = renderer.lease(2, "new", ids2)
        expect_error(api.StaleGenerationError, lambda: store.ingest(records(), expected_generation=1))
        expect_error(api.StaleGenerationError, lambda: renderer.render(lease1["token"], "content:quartz", "stale", context_generation=1))
        current = renderer.render(lease2["token"], "content:quartz", "fresh", context_generation=2)
        assert second["generation"] == current["generation"] == 2 and current["path"].endswith("quartz-field-guide.html")


def test_s04_taxonomy_rename_publication_lineage():
    api = workflow_api()
    with temporary_root("pelican-v6-s04-") as name:
        root = Path(name)
        index = api.IdentityIndex(root / "identity")
        index.project(1, records())
        identities = index.project(2, records(2))
        renderer = api.ThemeRenderer(root / "theme")
        lease = renderer.lease(2, "lineage", identities)
        artifact = renderer.render(lease["token"], "content:quartz", "renamed", context_generation=2)
        publisher = api.ArtifactPublisher(root / "publisher")
        prepared = publisher.prepare(2, {artifact["path"]: artifact["text"]})
        visible = publisher.promote(prepared["token"])
        acknowledged = publisher.acknowledge(2, visible["digest"])
        ledger = api.PublicationLedger(root / "ledger")
        stage = ledger.stage(2, entries_for(records(2), identities), page_size=2)
        view = ledger.commit(stage["token"], acknowledged)
        assert publisher.read("articles/quartz-field-guide.html") is not None
        historical = index.resolve("quartz-notes")
        assert historical is not None and historical["identity"] == "content:quartz"
        assert view["feed"] and view["feed"][0]["url"] == "articles/quartz-field-guide.html"


def test_s05_feed_pagination_generation_swap():
    api = workflow_api()
    with temporary_root("pelican-v6-s05-") as name:
        root = Path(name)
        publisher = api.ArtifactPublisher(root / "publisher")
        ledger = api.PublicationLedger(root / "ledger")
        p1 = publisher.prepare(1, {"index.html": "g1"})
        v1 = publisher.promote(p1["token"])
        a1 = publisher.acknowledge(1, v1["digest"])
        s1 = ledger.stage(1, entries_for(records()), page_size=1)
        ledger.commit(s1["token"], a1)
        p2 = publisher.prepare(2, {"index.html": "g2"})
        v2 = publisher.promote(p2["token"])
        a2 = publisher.acknowledge(2, v2["digest"])
        next_rows = [records(2)[0], {**records(2)[1], "status": "hidden"}]
        s2 = ledger.stage(2, entries_for(next_rows), page_size=3)
        assert ledger.view()["generation"] == 1 and len(ledger.view()["pages"]) == 2
        view = ledger.commit(s2["token"], a2)
        assert view["generation"] == 2 and len(view["feed"]) == 1 and len(view["pages"]) == 1


def test_s06_publication_signal_retry_reopen():
    api = workflow_api()
    with temporary_root("pelican-v6-s06-") as name:
        root = Path(name)
        _, publication = acknowledged_publication(root, 5)
        outbox = api.SignalOutbox(root / "outbox")
        event = outbox.enqueue(5, "generation-five", {"generation": 5}, publication_receipt=publication)
        first = outbox.claim("worker-one")
        assert first is not None
        outbox.fail(first["token"], "worker-one")
        second = outbox.claim("worker-two")
        assert second is not None
        assert second["attempt"] == 2
        reopened = api.SignalOutbox(root / "outbox")
        third = reopened.claim("worker-three")
        assert third is not None
        assert third["token"] == event["token"] and third["attempt"] == 3
        reopened.ack(third["token"], "worker-three")
        duplicate = reopened.enqueue(5, "generation-five", {"ignored": True}, publication_receipt=publication)
        assert duplicate["token"] == event["token"] and len(reopened.delivered()) == 1


def test_s07_failure_then_clean_retry():
    api = workflow_api()
    with temporary_root("pelican-v6-s07-") as name:
        root = Path(name)
        index = api.IdentityIndex(root / "identity")
        ids1 = index.project(1, records())
        renderer = api.ThemeRenderer(root / "theme")
        stale = renderer.lease(1, "stale", ids1)
        ids2 = index.project(2, records(2))
        current = renderer.lease(2, "current", ids2)
        expect_error(api.StaleGenerationError, lambda: renderer.render(stale["token"], "content:quartz", "wrong", context_generation=1))
        artifact = renderer.render(current["token"], "content:quartz", "right", context_generation=2)
        publisher = api.ArtifactPublisher(root / "publisher")
        publisher.prepare(1, {"discarded.html": "discard"})
        assert publisher.read("discarded.html") is None
        publisher.recover()
        prepared = publisher.prepare(2, {artifact["path"]: artifact["text"]})
        visible = publisher.promote(prepared["token"])
        acknowledged = publisher.acknowledge(2, visible["digest"])
        assert acknowledged["acknowledged"] and publisher.read(artifact["path"]) == artifact["text"].encode()


def test_s08_six_owner_restart_workflow():
    api = workflow_api()
    with temporary_root("pelican-v6-s08-") as name:
        root = Path(name)
        store = api.ContentStore(root / "content")
        content = store.ingest(records(2))
        store.acknowledge(content["generation"], content["digest"])
        identities = api.IdentityIndex(root / "identity").project(content["generation"], store.current()["records"])
        renderer = api.ThemeRenderer(root / "theme")
        lease = renderer.lease(content["generation"], "summit", identities)
        rendered = [renderer.render(lease["token"], row["identity"], row["source_id"], context_generation=content["generation"]) for row in identities["identities"]]
        renderer.commit(lease["token"])
        publisher = api.ArtifactPublisher(root / "publisher")
        prepared = publisher.prepare(content["generation"], {row["path"]: row["text"] for row in rendered})
        visible = publisher.promote(prepared["token"])
        api.ArtifactPublisher(root / "publisher").recover()
        publication = publisher.acknowledge(content["generation"], visible["digest"])
        ledger = api.PublicationLedger(root / "ledger")
        stage = ledger.stage(content["generation"], entries_for(store.current()["records"], identities), page_size=1)
        view = ledger.commit(stage["token"], publication)
        outbox = api.SignalOutbox(root / "outbox")
        event = outbox.enqueue(content["generation"], "site-complete", {"feed": len(view["feed"])}, publication_receipt=publication)
        claimed = outbox.claim("worker-before-restart")
        assert claimed is not None
        assert claimed["token"] == event["token"]
        reopened = api.SignalOutbox(root / "outbox")
        retry = reopened.claim("worker-after-restart")
        assert retry is not None
        reopened.ack(retry["token"], "worker-after-restart")
        assert api.ContentStore(root / "content").current()["acknowledged"]
        assert api.IdentityIndex(root / "identity").resolve("quartz-field-guide")["identity"] == "content:quartz"
        assert api.ArtifactPublisher(root / "publisher").read("articles/quartz-field-guide.html") is not None
        assert api.PublicationLedger(root / "ledger").view()["generation"] == content["generation"]
        assert len(reopened.delivered()) == 1 and retry["attempt"] == 2
