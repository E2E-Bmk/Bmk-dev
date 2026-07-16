# Spec2Repo oracle - integration tests for beancount-ledger-fullrepro-002
from __future__ import annotations

import datetime as dt
import io
import textwrap
from decimal import Decimal
from pathlib import Path

import pytest

import beancount as bn
from beancount import api as bn_api


def write_ledger(tmp_path: Path, name: str, contents: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")
    return path


def test_load_file_returns_entries_errors_and_options(tmp_path):
    ledger = write_ledger(tmp_path, "main.bean", """
        option "title" "My Ledger"
        option "operating_currency" "USD"
        2020-01-01 open Assets:Cash USD
        2020-01-01 open Income:Salary USD
        2020-01-02 * "Acme" "Paycheck" #income ^pay
          Assets:Cash    10 USD
          Income:Salary -10 USD
        2020-01-03 balance Assets:Cash 10 USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    assert options["title"] == "My Ledger"
    assert options["operating_currency"] == ["USD"]
    assert [type(entry).__name__ for entry in entries] == ["Open", "Open", "Transaction", "Balance"]
    txn = next(bn.filter_txns(entries))
    assert txn.payee == "Acme"
    assert txn.tags == frozenset({"income"})
    assert txn.links == frozenset({"pay"})


def test_load_file_resolves_relative_includes_and_aggregates_options(tmp_path):
    write_ledger(tmp_path, "included.bean", """
        option "operating_currency" "CAD"
        2020-01-01 open Assets:Bank CAD
    """)
    main = write_ledger(tmp_path, "main.bean", """
        option "operating_currency" "USD"
        include "included.bean"
        2020-01-01 open Assets:Cash USD
    """)
    entries, errors, options = bn.load_file(str(main))
    assert errors == []
    assert sorted(entry.account for entry in entries if hasattr(entry, "account")) == ["Assets:Bank", "Assets:Cash"]
    assert options["operating_currency"] == ["USD", "CAD"]
    assert {Path(path).name for path in options["include"]} == {"main.bean", "included.bean"}


def test_load_file_reports_missing_include_as_error(tmp_path):
    main = write_ledger(tmp_path, "main.bean", 'include "missing.bean"\n')
    entries, errors, options = bn.load_file(str(main))
    assert entries == []
    assert len(errors) == 1
    assert errors[0].entry is None
    assert "missing.bean" in errors[0].message
    assert "filename" in errors[0].source


def test_load_file_balance_validation_error_contains_entry(tmp_path):
    ledger = write_ledger(tmp_path, "bad_balance.bean", """
        2020-01-01 open Assets:Cash USD
        2020-01-02 balance Assets:Cash 1 USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert [type(entry).__name__ for entry in entries] == ["Open", "Balance"]
    assert len(errors) == 1
    assert type(errors[0].entry).__name__ == "Balance"
    assert errors[0].entry.account == "Assets:Cash"
    assert errors[0].source["lineno"] == 2


def test_load_doc_decorator_supplies_parsed_ledger_to_function():
    seen = {}

    @bn.load_doc()
    def sample(self, entries, errors, options):
        """
        2020-01-01 open Assets:Cash USD
        """
        seen["types"] = [type(entry).__name__ for entry in entries]
        seen["errors"] = errors
        seen["filename"] = options["filename"]

    sample(object())
    assert seen["types"] == ["Open"]
    assert seen["errors"] == []
    assert seen["filename"] == "<string>"


def test_load_doc_expect_errors_accepts_invalid_docstring():
    seen = {}

    @bn.load_doc(expect_errors=True)
    def sample(self, entries, errors, options):
        """
        2020-01-01 open assets:bad USD
        """
        seen["entries"] = entries
        seen["errors"] = errors

    sample(object())
    assert seen["entries"] == []
    assert len(seen["errors"]) >= 1


def test_loader_plugin_can_append_directive_via_public_contract(tmp_path, monkeypatch):
    plugin = write_ledger(tmp_path, "myplugin.py", """
        import beancount as bn
        __plugins__ = ("add_note",)

        def add_note(entries, options_map):
            note = bn.Note(bn.new_metadata("plugin", 1), entries[0].date, "Assets:Cash", "plugin note", None, None)
            return list(entries) + [note], []
    """)
    assert plugin.exists()
    monkeypatch.syspath_prepend(str(tmp_path))
    ledger = write_ledger(tmp_path, "main.bean", """
        plugin "myplugin"
        2020-01-01 open Assets:Cash USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    assert [type(entry).__name__ for entry in entries] == ["Open", "Note"]
    assert entries[1].comment == "plugin note"


def test_plugin_import_failure_is_returned_as_load_error(tmp_path):
    ledger = write_ledger(tmp_path, "main.bean", """
        plugin "missing_public_surface_plugin"
        2020-01-01 open Assets:Cash USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert [type(entry).__name__ for entry in entries] == ["Open"]
    assert len(errors) == 1
    assert "missing_public_surface_plugin" in errors[0].message


def test_realize_builds_tree_and_account_postings_from_loaded_entries(tmp_path):
    ledger = write_ledger(tmp_path, "main.bean", """
        2020-01-01 open Assets:Cash USD
        2020-01-01 open Income:Salary USD
        2020-01-02 * "Acme" "Paycheck"
          Assets:Cash    10 USD
          Income:Salary -10 USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    root = bn.realize(entries)
    assert root.account == ""
    assert root["Assets"]["Cash"].account == "Assets:Cash"
    assert root["Assets"]["Cash"].balance.reduce(bn.get_units).get_currency_units("USD") == bn.Amount(bn.D("10"), "USD")
    assert len(root["Income"]["Salary"].txn_postings) == 2


def test_realize_min_accounts_creates_empty_requested_accounts():
    root = bn.realize([], min_accounts=["Assets:Cash"], compute_balance=True)
    assert root["Assets"]["Cash"].account == "Assets:Cash"
    assert root["Assets"]["Cash"].balance.is_empty()


def test_same_day_ordering_balance_before_transaction_and_close_last(tmp_path):
    ledger = write_ledger(tmp_path, "same_day.bean", """
        2020-01-02 * "Later" "Txn"
          Assets:Cash  0 USD
          Equity:Opening-Balances
        2020-01-02 close Assets:Cash
        2020-01-02 balance Assets:Cash 0 USD
        2020-01-01 open Assets:Cash USD
        2020-01-01 open Equity:Opening-Balances USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    assert [type(entry).__name__ for entry in entries] == ["Open", "Open", "Balance", "Transaction", "Close"]


def test_configured_root_account_names_affect_parsing_and_signs(tmp_path):
    ledger = write_ledger(tmp_path, "custom_roots.bean", """
        option "name_assets" "Actif"
        option "name_income" "Revenu"
        2020-01-01 open Actif:Cash CAD
        2020-01-01 open Revenu:Salary CAD
        2020-01-02 * "Pay" "Salary"
          Actif:Cash      1 CAD
          Revenu:Salary  -1 CAD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    account_types = bn.get_account_types(options)
    assert account_types.assets == "Actif"
    assert bn.get_account_sign("Actif:Cash", account_types) == 1
    assert bn.get_account_sign("Revenu:Salary", account_types) == -1
    assert sorted(bn.get_accounts(entries)) == ["Actif:Cash", "Revenu:Salary"]


def test_booking_enum_exposes_public_methods():
    assert [item.name for item in bn.Booking] == [
        "STRICT",
        "STRICT_WITH_SIZE",
        "NONE",
        "AVERAGE",
        "FIFO",
        "LIFO",
        "HIFO",
    ]
    assert bn.Booking.STRICT.name == "STRICT"
    assert bn.Booking.AVERAGE.value == "AVERAGE"


def test_inventory_split_average_and_only_position_behavior():
    inventory = bn.Inventory.from_string("2 HOOL {5 USD, 2020-01-01}, 3 HOOL {7 USD, 2020-01-03}, -1 USD")
    assert sorted(inventory.split()) == ["HOOL", "USD"]
    averaged = inventory.average()
    assert averaged.get_currency_units("HOOL") == bn.Amount(bn.D("5"), "HOOL")
    only = bn.Inventory.from_string("9 USD")
    assert only.get_only_position() == bn.Position.from_string("9 USD")
    assert bn.Inventory().get_only_position() is None
    with pytest.raises(AssertionError):
        inventory.get_only_position()


def test_inventory_add_position_and_add_inventory_accumulate_units():
    left = bn.Inventory()
    left.add_position(bn.Position.from_string("2 USD"))
    left.add_position(bn.Position.from_string("3 CAD"))
    right = bn.Inventory.from_string("4 USD, -3 CAD")
    returned = left.add_inventory(right)
    assert returned is left
    assert left.get_currency_units("USD") == bn.Amount(bn.D("6"), "USD")
    assert left.get_currency_units("CAD") == bn.Amount(bn.D("0"), "CAD")


def test_inventory_reduce_does_not_mutate_original_inventory():
    inventory = bn.Inventory.from_string("2 HOOL {5 USD}, 3 USD")
    reduced = inventory.reduce(bn.get_cost)
    assert reduced.get_currency_units("USD") == bn.Amount(bn.D("13"), "USD")
    assert inventory.get_currency_units("HOOL") == bn.Amount(bn.D("2"), "HOOL")


def test_price_map_duplicate_dates_keep_later_price_and_add_inverse():
    prices = [
        bn.Price(bn.new_metadata("p", 1), dt.date(2020, 1, 1), "HOOL", bn.Amount(bn.D("10"), "USD")),
        bn.Price(bn.new_metadata("p", 2), dt.date(2020, 1, 1), "HOOL", bn.Amount(bn.D("11"), "USD")),
    ]
    price_map = bn.build_price_map(prices)
    assert price_map.forward_pairs == [("HOOL", "USD")]
    assert bn.get_price(price_map, ("HOOL", "USD"), dt.date(2020, 1, 1)) == (dt.date(2020, 1, 1), bn.D("11"))
    inverse_date, inverse_rate = bn.get_price(price_map, ("USD", "HOOL"), dt.date(2020, 1, 1))
    assert inverse_date == dt.date(2020, 1, 1)
    assert inverse_rate == bn.D("1") / bn.D("11")


def test_get_weight_uses_cost_before_price_and_price_without_cost():
    with_cost = bn.Posting(
        "Assets:Broker",
        bn.Amount(bn.D("2"), "HOOL"),
        bn.Cost(bn.D("5"), "USD", None, None),
        bn.Amount(bn.D("99"), "CAD"),
        None,
        None,
    )
    priced = bn.Posting("Assets:Broker", bn.Amount(bn.D("2"), "HOOL"), None, bn.Amount(bn.D("7"), "CAD"), None, None)
    plain = bn.Posting("Assets:Cash", bn.Amount(bn.D("3"), "USD"), None, None, None, None)
    assert bn.get_weight(with_cost) == bn.Amount(bn.D("10"), "USD")
    assert bn.get_weight(priced) == bn.Amount(bn.D("14"), "CAD")
    assert bn.get_weight(plain) == bn.Amount(bn.D("3"), "USD")


def test_get_value_infers_value_currency_from_cost_or_price():
    price_map = bn.build_price_map([
        bn.Price(bn.new_metadata("p", 1), dt.date(2020, 1, 2), "HOOL", bn.Amount(bn.D("12"), "USD")),
        bn.Price(bn.new_metadata("p", 2), dt.date(2020, 1, 2), "HOOL", bn.Amount(bn.D("8"), "CAD")),
    ])
    costed = bn.Position.from_string("2 HOOL {5 USD, 2020-01-01}")
    priced = bn.Posting("Assets:Broker", bn.Amount(bn.D("2"), "HOOL"), None, bn.Amount(bn.D("8"), "CAD"), None, None)
    assert bn.get_value(costed, price_map, dt.date(2020, 1, 2)) == bn.Amount(bn.D("24"), "USD")
    assert bn.get_value(priced, price_map, dt.date(2020, 1, 2)) == bn.Amount(bn.D("16"), "CAD")


def test_directive_namespace_contains_public_directive_classes():
    for name in ["Open", "Close", "Commodity", "Pad", "Balance", "Transaction", "Note", "Event", "Query", "Price", "Document", "Custom"]:
        assert getattr(bn.dtypes, name) is getattr(bn, name)


def test_note_event_query_document_and_custom_fields_are_public():
    meta = bn.new_metadata("ledger.bean", 1)
    note = bn.Note(meta, dt.date(2020, 1, 1), "Assets:Cash", "hello", frozenset({"tag"}), frozenset({"link"}))
    event = bn.Event(meta, dt.date(2020, 1, 2), "location", "office")
    query = bn.Query(meta, dt.date(2020, 1, 3), "cash", "SELECT account")
    document = bn.Document(meta, dt.date(2020, 1, 4), "Assets:Cash", "/tmp/doc.pdf", frozenset({"doc"}), None)
    custom = bn.Custom(meta, dt.date(2020, 1, 5), "public", [bn.Amount(bn.D("1"), "USD")])
    assert note.comment == "hello"
    assert event.type == "location" and event.description == "office"
    assert query.name == "cash" and query.query_string == "SELECT account"
    assert document.filename.endswith("doc.pdf")
    assert custom.type == "public" and custom.values[0] == bn.Amount(bn.D("1"), "USD")


def test_get_account_open_close_keeps_first_lifecycle_directives():
    first_open = bn.Open(bn.new_metadata("ledger.bean", 1), dt.date(2020, 1, 1), "Assets:Cash", ["USD"], None)
    second_open = bn.Open(bn.new_metadata("ledger.bean", 2), dt.date(2020, 1, 2), "Assets:Cash", ["CAD"], None)
    first_close = bn.Close(bn.new_metadata("ledger.bean", 3), dt.date(2020, 1, 3), "Assets:Cash")
    second_close = bn.Close(bn.new_metadata("ledger.bean", 4), dt.date(2020, 1, 4), "Assets:Cash")
    lifecycle = bn.get_account_open_close([second_open, second_close, first_open, first_close])
    assert lifecycle["Assets:Cash"] == [first_open, first_close]


def test_load_file_duplicate_include_is_reported_as_load_error(tmp_path):
    write_ledger(tmp_path, "part.bean", "2020-01-01 open Assets:Cash USD\n")
    main = write_ledger(tmp_path, "main.bean", """
        include "part.bean"
        include "part.bean"
    """)
    entries, errors, options = bn.load_file(str(main))
    assert [type(entry).__name__ for entry in entries] == ["Open"]
    assert len(errors) == 1
    assert "Duplicate" in errors[0].message or "already" in errors[0].message


def test_load_file_unmatched_include_glob_is_returned_as_error(tmp_path):
    main = write_ledger(tmp_path, "main.bean", 'include "missing-*.bean"\n')
    entries, errors, options = bn.load_file(str(main))
    assert entries == []
    assert len(errors) == 1
    assert "missing-*.bean" in errors[0].message


def test_plugin_exception_is_converted_to_load_error(tmp_path, monkeypatch):
    write_ledger(tmp_path, "badplugin.py", """
        __plugins__ = ("explode",)

        def explode(entries, options_map):
            raise RuntimeError("boom from plugin")
    """)
    monkeypatch.syspath_prepend(str(tmp_path))
    ledger = write_ledger(tmp_path, "main.bean", """
        plugin "badplugin"
        2020-01-01 open Assets:Cash USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert [type(entry).__name__ for entry in entries] == ["Open"]
    assert len(errors) == 1
    assert "boom from plugin" in errors[0].message


def test_plugin_systemexit_is_allowed_to_propagate(tmp_path, monkeypatch):
    write_ledger(tmp_path, "exitplugin.py", """
        __plugins__ = ("stop",)

        def stop(entries, options_map):
            raise SystemExit(7)
    """)
    monkeypatch.syspath_prepend(str(tmp_path))
    ledger = write_ledger(tmp_path, "main.bean", """
        plugin "exitplugin"
        2020-01-01 open Assets:Cash USD
    """)
    with pytest.raises(SystemExit) as excinfo:
        bn.load_file(str(ledger))
    assert excinfo.value.code == 7


def test_realize_stores_account_attached_directives_and_pad_on_both_accounts():
    meta = bn.new_metadata("ledger.bean", 1)
    entries = [
        bn.Open(meta, dt.date(2020, 1, 1), "Assets:Cash", ["USD"], None),
        bn.Open(meta, dt.date(2020, 1, 1), "Equity:Opening-Balances", ["USD"], None),
        bn.Pad(meta, dt.date(2020, 1, 2), "Assets:Cash", "Equity:Opening-Balances"),
        bn.Note(meta, dt.date(2020, 1, 3), "Assets:Cash", "hello", None, None),
    ]
    root = bn.realize(entries)
    cash_kinds = [type(item).__name__ for item in root["Assets"]["Cash"].txn_postings]
    equity_kinds = [type(item).__name__ for item in root["Equity"]["Opening-Balances"].txn_postings]
    assert cash_kinds == ["Open", "Pad", "Note"]
    assert equity_kinds == ["Open", "Pad"]


def test_realize_compute_balance_false_preserves_postings_without_balance(tmp_path):
    ledger = write_ledger(tmp_path, "main.bean", """
        2020-01-01 open Assets:Cash USD
        2020-01-01 open Income:Salary USD
        2020-01-02 * "Pay" "Salary"
          Assets:Cash    10 USD
          Income:Salary -10 USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    root = bn.realize(entries, compute_balance=False)
    assert len(root["Assets"]["Cash"].txn_postings) == 2
    assert root["Assets"]["Cash"].balance.is_empty()


def test_load_file_parses_note_event_query_price_and_custom(tmp_path):
    ledger = write_ledger(tmp_path, "objects.bean", f'''
        2020-01-01 open Assets:Cash USD
        2020-01-02 note Assets:Cash "remember" #tag ^link
        2020-01-03 event "location" "office"
        2020-01-04 query "cash" "SELECT account"
        2020-01-05 price HOOL 10 USD
        2020-01-07 custom "public" 1 USD
    ''')
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    assert [type(entry).__name__ for entry in entries] == ["Open", "Note", "Event", "Query", "Price", "Custom"]
    assert entries[1].tags == frozenset({"tag"})
    assert entries[2].type == "location"
    assert entries[3].name == "cash"
    assert entries[4].amount == bn.Amount(bn.D("10"), "USD")
    assert entries[5].values[0].value == bn.Amount(bn.D("1"), "USD")


def test_load_file_raw_plugin_mode_skips_standard_balance_validation(tmp_path):
    ledger = write_ledger(tmp_path, "raw.bean", """
        option "plugin_processing_mode" "raw"
        2020-01-01 open Assets:Cash USD
        2020-01-02 balance Assets:Cash 1 USD
    """)
    entries, errors, options = bn.load_file(str(ledger))
    assert errors == []
    assert options["plugin_processing_mode"] == "raw"
    assert [type(entry).__name__ for entry in entries] == ["Open", "Balance"]


def test_price_lookup_is_as_of_requested_date():
    prices = [
        bn.Price(bn.new_metadata("p", 1), dt.date(2020, 1, 1), "HOOL", bn.Amount(bn.D("10"), "USD")),
        bn.Price(bn.new_metadata("p", 2), dt.date(2020, 1, 5), "HOOL", bn.Amount(bn.D("15"), "USD")),
    ]
    price_map = bn.build_price_map(prices)
    assert bn.get_price(price_map, ("HOOL", "USD"), dt.date(2020, 1, 3)) == (dt.date(2020, 1, 1), bn.D("10"))
    assert bn.get_price(price_map, ("HOOL", "USD"), dt.date(2020, 1, 5)) == (dt.date(2020, 1, 5), bn.D("15"))


def test_realized_transaction_postings_preserve_parent_transaction():
    meta = bn.new_metadata("ledger.bean", 1)
    posting = bn.Posting("Assets:Cash", bn.Amount(bn.D("1"), "USD"), None, None, None, None)
    txn = bn.Transaction(meta, dt.date(2020, 1, 1), bn.FLAG_OKAY, None, "One", None, None, [posting])
    root = bn.realize([txn])
    (txn_posting,) = root["Assets"]["Cash"].txn_postings
    assert txn_posting.txn is txn
    assert txn_posting.posting is posting
