# Spec2Repo oracle - atomic tests for beancount-ledger-fullrepro-002
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


def test_root_api_exports_match_api_module():
    assert bn.Amount is bn_api.Amount
    assert bn.Transaction is bn_api.Transaction
    assert bn.load_file is bn_api.load_file
    assert bn.account is bn_api.account
    assert bn.amount is bn_api.amount
    assert bn.dtypes.Transaction is bn.Transaction


def test_decimal_constructor_normalizes_public_inputs():
    assert bn.D(None) == Decimal("0")
    assert bn.D("") == Decimal("0")
    assert bn.D("1,234.50") == Decimal("1234.50")
    assert bn.D("1 234.50") == Decimal("1234.50")
    with pytest.raises(ValueError):
        bn.D("not-a-number")


def test_amount_parsing_comparison_and_boolean_behavior():
    amount = bn.Amount.from_string("10.50 USD")
    assert amount == bn.Amount(Decimal("10.50"), "USD")
    assert str(amount) == "10.50 USD"
    assert bool(bn.Amount(Decimal("1"), "USD")) is True
    assert bool(bn.Amount(Decimal("0"), "USD")) is False
    assert sorted([bn.Amount(bn.D("2"), "CAD"), bn.Amount(bn.D("1"), "CAD")]) == [
        bn.Amount(bn.D("1"), "CAD"),
        bn.Amount(bn.D("2"), "CAD"),
    ]
    with pytest.raises(ValueError):
        bn.Amount.from_string("10")


def test_position_from_string_and_value_helpers():
    position = bn.Position.from_string("2 HOOL {5 USD, 2020-01-01}")
    assert position.units == bn.Amount(bn.D("2"), "HOOL")
    assert bn.get_units(position) == bn.Amount(bn.D("2"), "HOOL")
    assert bn.get_cost(position) == bn.Amount(bn.D("10"), "USD")
    assert position.currency_pair() == ("HOOL", "USD")


def test_account_helpers_component_semantics():
    account = bn.account.join("Assets", "Bank", "Checking")
    assert account == "Assets:Bank:Checking"
    assert bn.account.split(account) == ["Assets", "Bank", "Checking"]
    assert bn.account.parent(account) == "Assets:Bank"
    assert bn.account.leaf(account) == "Checking"
    assert bn.account.sans_root(account) == "Bank:Checking"
    assert bn.account.root(2, account) == "Assets:Bank"
    assert bn.account.has_component(account, "Bank")
    assert not bn.account.has_component(account, "Ban")
    assert bn.account.commonprefix(["Assets:Bank:Checking", "Assets:Bank:Savings"]) == "Assets:Bank"
    assert list(bn.account.parents(account)) == ["Assets:Bank:Checking", "Assets:Bank", "Assets"]
    assert bn.account.parent_matcher("Assets:Bank")("Assets:Bank:Checking")


def test_account_type_helpers_default_signs_and_sorting():
    options = {"name_assets": "Assets", "name_liabilities": "Liabilities", "name_equity": "Equity", "name_income": "Income", "name_expenses": "Expenses"}
    account_types = bn.get_account_types(options)
    assert bn.get_account_type("Assets:Cash") == "Assets"
    assert bn.is_balance_sheet_account("Assets:Cash", account_types)
    assert bn.is_income_statement_account("Income:Salary", account_types)
    assert bn.is_inverted_account("Liabilities:Card", account_types)
    assert bn.get_account_sign("Assets:Cash", account_types) == 1
    assert bn.get_account_sign("Income:Salary", account_types) == -1
    assert bn.get_account_sort_key(account_types, "Assets:Cash") < bn.get_account_sort_key(account_types, "Income:Salary")


def test_directive_objects_metadata_and_filter_txns():
    meta = bn.new_metadata("ledger.bean", 7, {"source": "unit"})
    txn = bn.Transaction(meta, dt.date(2020, 1, 2), bn.FLAG_OKAY, "Payee", "Narration", frozenset({"tag"}), frozenset({"link"}), [])
    open_entry = bn.Open(meta, dt.date(2020, 1, 1), "Assets:Cash", ["USD"], None)
    assert meta == {"filename": "ledger.bean", "lineno": 7, "source": "unit"}
    assert txn.payee == "Payee"
    assert txn.tags == frozenset({"tag"})
    assert list(bn.filter_txns([open_entry, txn])) == [txn]


def test_getters_report_accounts_and_lifecycle():
    open_entry = bn.Open(bn.new_metadata("x", 1), dt.date(2020, 1, 1), "Assets:Cash", ["USD"], None)
    close_entry = bn.Close(bn.new_metadata("x", 2), dt.date(2020, 1, 3), "Assets:Cash")
    posting = bn.Posting("Income:Salary", bn.Amount(bn.D("-1"), "USD"), None, None, None, None)
    txn = bn.Transaction(bn.new_metadata("x", 2), dt.date(2020, 1, 2), bn.FLAG_OKAY, None, "Income", None, None, [posting])
    assert bn.get_accounts([open_entry, txn, close_entry]) == {"Assets:Cash", "Income:Salary"}
    assert bn.get_account_open_close([open_entry, close_entry])["Assets:Cash"] == [open_entry, close_entry]


def test_inventory_operations_preserve_lots_and_currencies():
    inventory = bn.Inventory.from_string("2 HOOL {5 USD}, 3 USD")
    assert inventory.currencies() == {"HOOL", "USD"}
    assert inventory.cost_currencies() == {"USD"}
    assert ("HOOL", "USD") in inventory.currency_pairs()
    assert ("USD", None) in inventory.currency_pairs()
    assert inventory.get_currency_units("USD") == bn.Amount(bn.D("3"), "USD")
    reduced = inventory.reduce(bn.get_units)
    assert reduced.get_currency_units("HOOL") == bn.Amount(bn.D("2"), "HOOL")
    assert reduced.get_currency_units("USD") == bn.Amount(bn.D("3"), "USD")


def test_inventory_add_amount_aggregates_and_removes_zero_lots():
    inventory = bn.Inventory()
    prior, _ = inventory.add_amount(bn.Amount(bn.D("5"), "USD"))
    assert prior is None
    assert inventory.get_currency_units("USD") == bn.Amount(bn.D("5"), "USD")
    prior, _ = inventory.add_amount(bn.Amount(bn.D("-5"), "USD"))
    assert prior is not None
    assert inventory.get_currency_units("USD") == bn.Amount(bn.D("0"), "USD")
    assert inventory.is_empty()


def test_inventory_bool_requires_explicit_empty_check():
    with pytest.raises(NotImplementedError):
        bool(bn.Inventory())


def test_price_map_lookup_latest_inverse_and_identity():
    entries = [
        bn.Price(bn.new_metadata("p", 1), dt.date(2020, 1, 1), "HOOL", bn.Amount(bn.D("10"), "USD")),
        bn.Price(bn.new_metadata("p", 2), dt.date(2020, 1, 2), "HOOL", bn.Amount(bn.D("12"), "USD")),
    ]
    price_map = bn.build_price_map(entries)
    assert bn.get_price(price_map, ("HOOL", "USD"), dt.date(2020, 1, 1)) == (dt.date(2020, 1, 1), bn.D("10"))
    assert bn.get_latest_price(price_map, "HOOL/USD") == (dt.date(2020, 1, 2), bn.D("12"))
    assert bn.get_price(price_map, ("USD", "USD")) == (None, bn.D("1"))
    assert bn.get_price(price_map, ("MISSING", "USD")) == (None, None)


def test_conversion_helpers_use_prices_or_return_original_amount():
    price_map = bn.build_price_map([
        bn.Price(bn.new_metadata("p", 1), dt.date(2020, 1, 1), "HOOL", bn.Amount(bn.D("10"), "USD")),
        bn.Price(bn.new_metadata("p", 2), dt.date(2020, 1, 1), "USD", bn.Amount(bn.D("2"), "CAD")),
    ])
    assert bn.convert_amount(bn.Amount(bn.D("3"), "HOOL"), "USD", price_map, dt.date(2020, 1, 1)) == bn.Amount(bn.D("30"), "USD")
    assert bn.convert_amount(bn.Amount(bn.D("3"), "HOOL"), "CAD", price_map, dt.date(2020, 1, 1), via=("USD",)) == bn.Amount(bn.D("60"), "CAD")
    unchanged = bn.Amount(bn.D("3"), "HOOL")
    assert bn.convert_amount(unchanged, "EUR", price_map, dt.date(2020, 1, 1)) == unchanged


def test_real_account_child_constraints_are_enforced():
    root = bn.RealAccount("")
    root["Assets"] = bn.RealAccount("Assets")
    assert root["Assets"].account == "Assets"
    with pytest.raises(KeyError):
        root[""] = bn.RealAccount("")
    with pytest.raises(ValueError):
        root["Cash"] = object()
    with pytest.raises(ValueError):
        root["Cash"] = bn.RealAccount("Assets:Bank")


def test_format_entry_omits_source_metadata_and_sorts_tags_links():
    meta = bn.new_metadata("ledger.bean", 3, {"note": "kept", "__private": "hidden"})
    txn = bn.Transaction(meta, dt.date(2020, 1, 2), bn.FLAG_OKAY, "Payee", "Narration", frozenset({"z", "a"}), frozenset({"b", "a"}), [])
    rendered = bn.format_entry(txn)
    assert 'note: "kept"' in rendered
    assert "filename" not in rendered
    assert "__private" not in rendered
    assert '#a #z' in rendered
    assert '^a ^b' in rendered


def test_print_entry_and_print_entries_write_public_syntax():
    open_entry = bn.Open(bn.new_metadata("ledger.bean", 1), dt.date(2020, 1, 1), "Assets:Cash", ["USD"], None)
    first = io.StringIO()
    bn.print_entry(open_entry, file=first)
    assert "2020-01-01 open Assets:Cash" in first.getvalue()
    output = io.StringIO()
    bn.print_entries([open_entry], file=output)
    assert "2020-01-01 open Assets:Cash" in output.getvalue()
    with pytest.raises(AssertionError):
        bn.print_entries(tuple([open_entry]), file=io.StringIO())


def test_account_validation_helpers_accept_components_and_reject_bad_names():
    assert bn.account.is_valid_root("Assets")
    assert bn.account.is_valid_leaf("Cash")
    assert bn.account.is_valid("Assets:Cash")
    assert not bn.account.is_valid_root("assets")
    assert not bn.account.is_valid("Assets:cash")
    assert bn.account.parent("Assets") == ""


def test_amount_negation_and_currency_first_sorting():
    usd = bn.Amount(bn.D("2"), "USD")
    cad = bn.Amount(bn.D("100"), "CAD")
    assert -usd == bn.Amount(bn.D("-2"), "USD")
    assert sorted([usd, cad]) == [cad, usd]


def test_position_arithmetic_preserves_lot_cost():
    position = bn.Position.from_string("2 HOOL {5 USD, 2020-01-01}")
    assert -position == bn.Position.from_string("-2 HOOL {5 USD, 2020-01-01}")
    assert abs(-position) == position
    assert position * bn.D("3") == bn.Position.from_string("6 HOOL {5 USD, 2020-01-01}")
    with pytest.raises(ValueError):
        bn.Position.from_string("not a position")


def test_get_accounts_includes_pad_note_document_and_balance_accounts():
    meta = bn.new_metadata("ledger.bean", 1)
    entries = [
        bn.Pad(meta, dt.date(2020, 1, 1), "Assets:Cash", "Equity:Opening-Balances"),
        bn.Balance(meta, dt.date(2020, 1, 2), "Assets:Cash", bn.Amount(bn.D("0"), "USD"), None, None),
        bn.Note(meta, dt.date(2020, 1, 3), "Expenses:Food", "note", None, None),
        bn.Document(meta, dt.date(2020, 1, 4), "Assets:Cash", "/tmp/doc.pdf", None, None),
    ]
    assert bn.get_accounts(entries) == {"Assets:Cash", "Equity:Opening-Balances", "Expenses:Food"}


def test_format_entry_write_source_emits_source_comment():
    entry = bn.Open(bn.new_metadata("ledger.bean", 12), dt.date(2020, 1, 1), "Assets:Cash", ["USD"], None)
    rendered = bn.format_entry(entry, write_source=True)
    assert "; source: ledger.bean:12:" in rendered
    assert "2020-01-01 open Assets:Cash" in rendered


def test_tags_and_links_store_without_markers_and_print_with_markers():
    txn = bn.Transaction(
        bn.new_metadata("ledger.bean", 1),
        dt.date(2020, 1, 1),
        bn.FLAG_OKAY,
        None,
        "Tagged",
        frozenset({"tag"}),
        frozenset({"link"}),
        [],
    )
    assert txn.tags == frozenset({"tag"})
    assert txn.links == frozenset({"link"})
    rendered = bn.format_entry(txn)
    assert "#tag" in rendered
    assert "^link" in rendered
