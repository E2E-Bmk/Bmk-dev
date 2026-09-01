from __future__ import annotations

from pathlib import Path

from tests.support import entries_for, expect_error, native_api, records, temporary_root, workflow_api


def test_a01_public_surface():
    api = native_api()
    assert all(value is not None for value in (api.Pelican, api.get_config, api.parse_arguments, api.Readers, api.Author, api.Category, api.Tag, api.Paginator, api.PaginationRule))
    assert api.signals.article_generator_finalized is api.plugin_signals.article_generator_finalized
    assert api.signals.content_object_init is api.plugin_signals.content_object_init


def test_a02_default_settings():
    api = native_api()
    assert api.DEFAULT_CONFIG.get("DEFAULT_LANG") == "en"
    assert api.DEFAULT_CONFIG.get("RELATIVE_URLS") is False


def test_a03_effective_settings():
    api = native_api()
    settings = api.read_settings(override={"SITENAME": "Copper Observatory"})
    assert settings["SITENAME"] == "Copper Observatory"
    assert settings["DEFAULT_LANG"] == "en"
    assert "OUTPUT_PATH" in settings


def test_a04_settings_precedence():
    api = native_api()
    with temporary_root("pelican-v6-a04-") as name:
        path = Path(name) / "settings.py"
        path.write_text("SITENAME = 'File Site'\nDEFAULT_LANG = 'pt'\n", encoding="utf-8")
        settings = api.read_settings(path=str(path), override={"SITENAME": "Override Site"})
    assert settings["SITENAME"] == "Override Site"
    assert settings["DEFAULT_LANG"] == "pt"
    assert "OUTPUT_PATH" in settings


def test_a05_slug_policy():
    api = native_api()
    assert api.slugify("Q__R", (("__", "-"), ("-", "x"))) == "qxr"
    assert api.slugify("Copper Field") == "copper field"
    assert api.slugify("Copper Field", preserve_case=True) == "Copper Field"


def test_a06_path_url_projection():
    api = native_api()
    path = api.posixize_path("ore\\copper/report.txt")
    url = api.path_to_url("ore\\copper/report.txt")
    assert "\\" not in path and path.endswith("ore/copper/report.txt")
    assert "\\" not in url and url.endswith("ore/copper/report.txt")


def test_a07_public_date_parser():
    api = native_api()
    value = api.get_date("2033-07-08 09:10")
    assert (value.year, value.month, value.day, value.hour) == (2033, 7, 8, 9)
    try:
        api.get_date("not a calendar value")
    except Exception as exc:
        assert type(exc).__name__ != "AssertionError"
    else:
        raise AssertionError("invalid date was accepted")


def _wrapper(kind: str):
    api = native_api()
    settings = api.read_settings(override={
        "AUTHOR_URL": "people/{slug}/", "AUTHOR_SAVE_AS": "people-files/{slug}.html",
        "CATEGORY_URL": "subjects/{slug}/", "CATEGORY_SAVE_AS": "subject-files/{slug}.html",
        "TAG_URL": "marks/{slug}/", "TAG_SAVE_AS": "mark-files/{slug}.html",
    })
    cls, text, url, save = {
        "author": (api.Author, "Copper Writer", "people/copper-writer/", "people-files/copper-writer.html"),
        "category": (api.Category, "Copper Study", "subjects/copper-study/", "subject-files/copper-study.html"),
        "tag": (api.Tag, "Copper Mark", "marks/copper-mark/", "mark-files/copper-mark.html"),
    }[kind]
    value = cls(text, settings)
    return value, url, save


def test_a08_author_projection():
    value, url, save = _wrapper("author")
    projection = value.as_dict()
    assert (value.slug, value.url, value.save_as) == ("copper-writer", url, save)
    assert projection["name"] == value.name and projection["slug"] == value.slug


def test_a09_category_projection():
    value, url, save = _wrapper("category")
    projection = value.as_dict()
    assert (value.slug, value.url, value.save_as) == ("copper-study", url, save)
    assert projection["name"] == value.name and projection["slug"] == value.slug


def test_a10_tag_projection():
    value, url, save = _wrapper("tag")
    projection = value.as_dict()
    assert (value.slug, value.url, value.save_as) == ("copper-mark", url, save)
    assert projection["name"] == value.name and projection["slug"] == value.slug


def test_a11_paginator_arithmetic():
    api = native_api()
    settings = api.read_settings(override={"DEFAULT_ORPHANS": 0})
    paginator = api.Paginator("items", "pages/{number}/", list("abcdefg"), settings, per_page=3)
    assert paginator.count == 7 and paginator.num_pages == 3
    assert list(paginator.page_range) == [1, 2, 3]
    assert [paginator.page(number).object_list for number in (1, 2, 3)] == [list("abc"), list("def"), ["g"]]


def test_a12_pagination_rule():
    api = native_api()
    rule = api.PaginationRule(3, "browse/{number}/", "browse-files/{number}.html")
    assert rule.min_page == 3
    assert rule.URL == "browse/{number}/" and rule.SAVE_AS == "browse-files/{number}.html"
    assert rule.URL != rule.SAVE_AS


def test_a13_content_generation_commit():
    api = workflow_api()
    with temporary_root("pelican-v6-a13-") as name:
        store = api.ContentStore(Path(name) / "content")
        receipt = store.ingest(reversed(records()))
        current = store.current()
        assert receipt["generation"] == 1 and receipt["count"] == 2 and not receipt["acknowledged"]
        assert [row["source_id"] for row in current["records"]] == ["opal", "quartz"]
        assert current["digest"] == receipt["digest"] and len(receipt["digest"]) == 64


def test_a14_content_acknowledgement():
    api = workflow_api()
    with temporary_root("pelican-v6-a14-") as name:
        store = api.ContentStore(Path(name) / "content")
        receipt = store.ingest(records())
        expect_error(api.AcknowledgementError, lambda: store.acknowledge(receipt["generation"], "0" * 64))
        acknowledged = store.acknowledge(receipt["generation"], receipt["digest"])
        repeated = store.acknowledge(receipt["generation"], receipt["digest"])
        reopened = api.ContentStore(Path(name) / "content").current()
        assert acknowledged["acknowledged"] and repeated == acknowledged
        assert reopened["acknowledged"] and reopened["digest"] == receipt["digest"]


def test_a15_identity_lineage():
    api = workflow_api()
    with temporary_root("pelican-v6-a15-") as name:
        index = api.IdentityIndex(Path(name) / "identity")
        index.project(1, records(1))
        renamed = index.project(2, records(2))
        current = index.resolve("quartz-field-guide")
        historical = index.resolve("quartz-notes")
        assert current and historical and current["identity"] == historical["identity"] == "content:quartz"
        assert "quartz-notes" in current["aliases"] and renamed["generation"] == 2


def test_a16_identity_stale_fence():
    api = workflow_api()
    with temporary_root("pelican-v6-a16-") as name:
        index = api.IdentityIndex(Path(name) / "identity")
        committed = index.project(4, records())
        expect_error(api.StaleGenerationError, lambda: index.project(3, records(2)))
        assert index.snapshot() == committed


def test_a17_theme_lease():
    api = workflow_api()
    with temporary_root("pelican-v6-a17-") as name:
        index = api.IdentityIndex(Path(name) / "identity")
        identities = index.project(3, records())
        renderer = api.ThemeRenderer(Path(name) / "theme")
        lease = renderer.lease(3, "basalt", identities)
        artifact = renderer.render(lease["token"], "content:quartz", "glint", context_generation=3)
        committed = renderer.commit(lease["token"])
        assert artifact["path"] == "articles/quartz-notes.html"
        assert artifact["generation"] == 3 and "basalt|content:quartz|glint" == artifact["text"]
        assert committed == [artifact]


def test_a18_artifact_recovery():
    api = workflow_api()
    with temporary_root("pelican-v6-a18-") as name:
        publisher = api.ArtifactPublisher(Path(name) / "publisher")
        first = publisher.prepare(1, {"index.html": "old"})
        visible = publisher.promote(first["token"])
        publisher.acknowledge(1, visible["digest"])
        second = publisher.prepare(2, {"index.html": "new", "asset.bin": b"bits"})
        assert publisher.read("index.html") == b"old" and second["state"] == "prepared"
        recovered = api.ArtifactPublisher(Path(name) / "publisher").recover()
        assert recovered["state"] == "recovered-prepared" and publisher.read("index.html") == b"old"


def test_a19_publication_ledger():
    api = workflow_api()
    with temporary_root("pelican-v6-a19-") as name:
        ledger = api.PublicationLedger(Path(name) / "ledger")
        staged = ledger.stage(1, entries_for(records()), page_size=1)
        expect_error(api.AcknowledgementError, lambda: ledger.commit(staged["token"], {"generation": 1, "visible": True, "acknowledged": False}))
        _, receipt = __import__("tests.support", fromlist=["acknowledged_publication"]).acknowledged_publication(Path(name), 1)
        view = ledger.commit(staged["token"], receipt)
        assert [row["source_id"] for row in view["feed"]] == ["quartz", "opal"]
        assert [page["number"] for page in view["pages"]] == [1, 2]


def test_a20_signal_outbox():
    api = workflow_api()
    with temporary_root("pelican-v6-a20-") as name:
        _, receipt = __import__("tests.support", fromlist=["acknowledged_publication"]).acknowledged_publication(Path(name), 1)
        outbox = api.SignalOutbox(Path(name) / "outbox")
        event = outbox.enqueue(1, "site-ready", {"count": 2}, publication_receipt=receipt)
        first = outbox.claim("worker-a")
        assert first and first["token"] == event["token"] and first["attempt"] == 1
        outbox.fail(first["token"], "worker-a")
        second = outbox.claim("worker-b")
        assert second and second["attempt"] == 2
        outbox.ack(second["token"], "worker-b")
        assert not outbox.pending() and [row["event_id"] for row in outbox.delivered()] == ["site-ready"]
