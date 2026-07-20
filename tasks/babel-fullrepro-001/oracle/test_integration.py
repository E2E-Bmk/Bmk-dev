from __future__ import annotations

import pytest

from babel.messages.catalog import Message, TranslationError
from babel.messages.checkers import python_format


def assert_format_valid(message_id: str | tuple[str, str], translation: str | tuple[str, ...]) -> None:
    message = Message(message_id, translation)
    assert message.check() == []


def assert_format_invalid(message_id: str | tuple[str, str], translation: str | tuple[str, ...]) -> None:
    message = Message(message_id, translation)
    errors = message.check()
    assert any(isinstance(error, TranslationError) for error in errors)


def test_message_detects_percent_format_placeholders() -> None:
    valid = [
        "foo %d bar",
        "foo %s bar",
        "foo %r bar",
        "foo %(name).1f",
        "foo %(name)06d",
        "foo %(name)*.*f",
    ]
    assert all(Message(value).python_format for value in valid)
    assert Message("ordinary text").python_format is False


def test_message_detects_brace_format_placeholders() -> None:
    invalid = ["", "foo", "{", "}", "{} {", "{{}}"]
    valid = ["{}", "foo {name}", "foo {name!r}", "foo {name!r:10.2f}"]
    assert all(not Message(value).python_brace_format for value in invalid)
    assert all(Message(value).python_brace_format for value in valid)


def test_percent_checker_rejects_missing_singular_placeholder() -> None:
    assert_format_invalid("foo %s", "foo")


def test_percent_checker_rejects_missing_plural_placeholder() -> None:
    assert_format_invalid(("foo %s", "bar"), ("foo", "bar"))


def test_percent_checker_rejects_placeholder_only_in_plural_id() -> None:
    assert_format_invalid(("foo", "bar %s"), ("foo", "bar"))


def test_percent_checker_accepts_plain_translation() -> None:
    assert_format_valid("foo", "foo")


def test_percent_checker_allows_translation_to_add_placeholder_for_plain_id() -> None:
    assert_format_valid("foo", "foo %s")


def test_percent_checker_allows_empty_translation() -> None:
    assert_format_valid("foo %s", "")


def test_percent_checker_rejects_mixed_positional_and_named_placeholders() -> None:
    assert_format_invalid("%s %(foo)s", "%s %(foo)s")


def test_percent_checker_rejects_incompatible_missing_placeholder() -> None:
    assert_format_invalid("foo %s", "foo")


def test_percent_checker_rejects_different_placeholder_kinds() -> None:
    assert_format_invalid("%s", "%(foo)s")


def test_percent_checker_accepts_two_plain_strings() -> None:
    assert_format_valid("foo", "foo")


def test_percent_checker_accepts_extra_placeholder_for_plain_source() -> None:
    assert_format_valid("foo", "foo %s")


def test_percent_checker_accepts_reordered_compatible_placeholder() -> None:
    message = Message("%s foo", "foo %s")
    python_format(None, message)
    assert message.check() == []
