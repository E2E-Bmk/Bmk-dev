from __future__ import annotations

import warnings

import pytest

import chardet
from chardet import EncodingEra, LanguageFilter, UniversalDetector


GIF = bytes.fromhex(
    "47494638396101000100800100000000ffffff21f90401000001002c00000000010001000002024c01003b"
)
JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb0084000302020a0a080a"
    "08080a0808080808080808080808080808080808080807080808080808080808"
    "08080708080a0808080809090907080d0d0a080d07080908"
)
MP4 = bytes.fromhex(
    "00000020667479706d703432000000006d7034326d70343169736f6d61766331"
    "00002e306d6f6f760000006c6d76686400000000d1ea271ed1ea271e00000258"
    "0000478c00010000010000000000000000000000000100000000000000000000"
)


def assert_binary(data: bytes, mime_type: str | None = None) -> None:
    result = chardet.detect(data)
    assert result["encoding"] is None
    if mime_type is not None:
        assert result["mime_type"] == mime_type


def assert_ascii(data: bytes, confidence: float = 1.0) -> None:
    result = chardet.detect(data)
    assert result["encoding"] == "ascii"
    assert result["confidence"] == confidence
    assert result["mime_type"] == "text/plain"


def test_detect_binary_gif_signature() -> None:
    assert_binary(GIF, "image/gif")


def test_detect_binary_jpeg_signature() -> None:
    assert_binary(JPEG, "image/jpeg")


def test_detect_binary_mp4_signature() -> None:
    assert_binary(MP4, "video/mp4")


def test_detect_binary_gif_with_all_encoding_eras() -> None:
    result = chardet.detect(GIF, encoding_era=EncodingEra.ALL, prefer_superset=True)
    assert result["encoding"] is None
    assert result["mime_type"] == "image/gif"


def test_detect_binary_jpeg_with_all_encoding_eras() -> None:
    result = chardet.detect(JPEG, encoding_era=EncodingEra.ALL, prefer_superset=True)
    assert result["encoding"] is None
    assert result["mime_type"] == "image/jpeg"


def test_detect_binary_mp4_with_all_encoding_eras() -> None:
    result = chardet.detect(MP4, encoding_era=EncodingEra.ALL, prefer_superset=True)
    assert result["encoding"] is None
    assert result["mime_type"] == "video/mp4"


def test_streaming_gif_matches_direct_detection() -> None:
    detector = UniversalDetector()
    detector.feed(GIF)
    assert detector.close() == chardet.detect(GIF)


def test_streaming_jpeg_matches_direct_detection() -> None:
    detector = UniversalDetector()
    detector.feed(JPEG)
    assert detector.close() == chardet.detect(JPEG)


def test_streaming_mp4_matches_direct_detection() -> None:
    detector = UniversalDetector()
    detector.feed(MP4)
    assert detector.close() == chardet.detect(MP4)


def test_detect_returns_four_field_dictionary() -> None:
    result = chardet.detect(b"Hello world")
    assert isinstance(result, dict)
    assert set(result) == {"encoding", "confidence", "language", "mime_type"}


def test_detect_ascii_returns_full_confidence() -> None:
    assert_ascii(b"Hello world")


def test_detect_utf8_bom_returns_compatibility_name() -> None:
    result = chardet.detect(b"\xef\xbb\xbfHello")
    assert result["encoding"] == "UTF-8-SIG"
    assert result["confidence"] == 1.0


def test_detect_utf8_multibyte_text() -> None:
    result = chardet.detect("Héllo wörld café".encode())
    assert result["encoding"] == "utf-8"


def test_detect_empty_uses_utf8_fallback() -> None:
    result = chardet.detect(b"")
    assert result["encoding"] == "utf-8"
    assert result["confidence"] == 0.10
    assert result["mime_type"] == "text/plain"


def test_detect_accepts_modern_web_encoding_era() -> None:
    assert chardet.detect(b"Hello world", encoding_era=EncodingEra.MODERN_WEB)["encoding"] is not None


def test_modern_web_era_excludes_legacy_greek_encoding() -> None:
    text = (
        "Η Αθήνα είναι η πρωτεύουσα και μεγαλύτερη πόλη της Ελλάδας. "
        "Η πόλη έχει μακρά ιστορία που εκτείνεται πάνω από τρεις χιλιετίες."
    ).encode("iso-8859-7")
    modern = chardet.detect(text, encoding_era=EncodingEra.MODERN_WEB)
    all_eras = chardet.detect(text, encoding_era=EncodingEra.ALL)
    assert all_eras["encoding"] == "ISO-8859-7"
    assert modern["encoding"].lower() != "iso-8859-7"


def test_detect_respects_max_bytes() -> None:
    result = chardet.detect(b"Hello world" * 100_000, max_bytes=100)
    assert result["encoding"] is not None
    assert result["confidence"] > 0


def test_detect_all_returns_nonempty_list() -> None:
    result = chardet.detect_all(b"Hello world")
    assert isinstance(result, list)
    assert result


def test_detect_all_is_sorted_by_descending_confidence() -> None:
    results = chardet.detect_all("Héllo wörld".encode())
    confidences = [result["confidence"] for result in results]
    assert confidences == sorted(confidences, reverse=True)


def test_detect_all_returns_four_field_dictionaries() -> None:
    for result in chardet.detect_all(b"Hello world"):
        assert set(result) == {"encoding", "confidence", "language", "mime_type"}


def test_detect_all_top_matches_detect_for_ascii() -> None:
    assert chardet.detect_all(b"Hello world")[0] == chardet.detect(b"Hello world")


def test_detect_all_top_matches_detect_for_utf8() -> None:
    data = "Héllo wörld café résumé".encode()
    assert chardet.detect_all(data)[0] == chardet.detect(data)


def test_detect_all_top_matches_detect_for_bom() -> None:
    data = b"\xef\xbb\xbfHello"
    assert chardet.detect_all(data)[0] == chardet.detect(data)


def test_version_is_nonempty_and_starts_with_digit() -> None:
    assert isinstance(chardet.__version__, str)
    assert chardet.__version__
    assert chardet.__version__[0].isdigit()


def test_legacy_rename_default_keeps_ascii_name() -> None:
    assert chardet.detect(b"Hello world")["encoding"] == "ascii"


def test_legacy_rename_false_keeps_ascii_name() -> None:
    assert chardet.detect(b"Hello world", should_rename_legacy=False)["encoding"] == "ascii"


def test_legacy_rename_true_maps_ascii_to_windows_1252() -> None:
    result = chardet.detect(
        b"Hello world", should_rename_legacy=True, encoding_era=EncodingEra.ALL
    )
    assert result["encoding"] == "Windows-1252"


def test_legacy_rename_default_with_all_eras_keeps_ascii() -> None:
    result = chardet.detect(b"Hello world", encoding_era=EncodingEra.ALL)
    assert result["encoding"] == "ascii"


def test_detect_all_legacy_rename_true_maps_ascii() -> None:
    result = chardet.detect_all(b"Hello world", should_rename_legacy=True)
    assert result[0]["encoding"] == "Windows-1252"


def test_detect_all_legacy_rename_false_keeps_ascii() -> None:
    result = chardet.detect_all(b"Hello world", should_rename_legacy=False)
    assert result[0]["encoding"] == "ascii"


def test_streaming_legacy_rename_true_maps_ascii() -> None:
    detector = UniversalDetector(should_rename_legacy=True)
    detector.feed(b"Hello world, this is enough ASCII data for detection. " * 2)
    assert detector.close()["encoding"] == "Windows-1252"


def test_streaming_legacy_rename_false_keeps_ascii() -> None:
    detector = UniversalDetector(should_rename_legacy=False)
    detector.feed(b"Hello world, this is enough ASCII data for detection. " * 2)
    assert detector.close()["encoding"] == "ascii"


def test_compatibility_name_maps_euc_jis_to_euc_jp() -> None:
    text = "東京は日本の首都です。人口は約1400万人で、世界最大の都市圏を形成しています。"
    assert chardet.detect(text.encode("euc_jp"))["encoding"] == "EUC-JP"


def test_detect_all_default_filters_low_confidence_results() -> None:
    data = "Héllo wörld café résumé".encode()
    unfiltered = chardet.detect_all(data, ignore_threshold=True)
    filtered = chardet.detect_all(data, ignore_threshold=False)
    assert len(filtered) <= len(unfiltered)
    assert all(result["confidence"] > chardet.MINIMUM_THRESHOLD for result in filtered)


def test_detect_all_ignore_threshold_returns_candidates() -> None:
    assert chardet.detect_all("Héllo wörld café résumé".encode(), ignore_threshold=True)


def test_detect_all_threshold_falls_back_when_everything_is_low() -> None:
    assert chardet.detect_all(b"", ignore_threshold=False)


def test_non_all_language_filter_emits_deprecation_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        UniversalDetector(lang_filter=LanguageFilter.CJK)
    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "lang_filter" in str(caught[0].message)


def test_all_language_filter_emits_no_deprecation_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        UniversalDetector(lang_filter=LanguageFilter.ALL)
    assert not [item for item in caught if issubclass(item.category, DeprecationWarning)]


def test_detect_rejects_boolean_max_bytes() -> None:
    with pytest.raises(ValueError):
        chardet.detect(b"Hello", max_bytes=True)


def test_public_detection_identifies_plain_ascii() -> None:
    assert_ascii(b"Hello, world! 123")


def test_public_detection_identifies_ascii_whitespace() -> None:
    assert_ascii(b"Hello\n\tworld\r\n")


def test_public_detection_does_not_label_high_byte_as_ascii() -> None:
    assert chardet.detect(b"Hello \x80 world")["encoding"] != "ascii"


def test_public_detection_does_not_label_utf8_multibyte_as_ascii() -> None:
    assert chardet.detect("Héllo".encode())["encoding"] == "utf-8"


def test_public_detection_empty_input_is_not_ascii() -> None:
    assert chardet.detect(b"")["encoding"] == "utf-8"


def test_public_detection_identifies_single_ascii_byte() -> None:
    assert_ascii(b"A")


def test_public_detection_identifies_all_printable_ascii() -> None:
    assert_ascii(bytes(range(0x20, 0x7F)))


def test_public_detection_does_not_label_dense_nulls_as_ascii() -> None:
    assert chardet.detect(b"Hello\x00\x00rld")["encoding"] != "ascii"


def test_public_detection_identifies_null_separated_paths() -> None:
    data = (
        b"/home/user/documents/report.txt\x00"
        b"/home/user/documents/notes.txt\x00"
        b"/home/user/downloads/image.png\x00"
        b"/home/user/music/song.mp3\x00"
    )
    assert_ascii(data, 0.99)


def test_public_detection_accepts_ascii_at_five_percent_null_boundary() -> None:
    assert_ascii(b"abcdefghij\x00klmnopqrs", 0.99)


def test_public_detection_rejects_ascii_above_null_boundary() -> None:
    assert chardet.detect(b"abcdefghij\x00klmnopqr")["encoding"] != "ascii"


def test_public_detection_rejects_ascii_with_high_null_fraction() -> None:
    assert chardet.detect(b"ab\x00cd\x00ef\x00gh\x00ij\x00")["encoding"] != "ascii"


def test_public_detection_rejects_ascii_with_null_and_high_byte() -> None:
    assert chardet.detect(b"Hello\x00\x80World")["encoding"] != "ascii"


def test_public_detection_pure_ascii_retains_full_confidence() -> None:
    assert_ascii(b"Hello, world!")


def test_empty_input_is_text_not_binary() -> None:
    result = chardet.detect(b"")
    assert result["encoding"] == "utf-8"
    assert result["mime_type"] == "text/plain"


def test_plain_ascii_is_text_not_binary() -> None:
    assert_ascii(b"Hello, world!")


def test_newlines_and_tabs_are_text_not_binary() -> None:
    assert_ascii(b"Hello\n\tworld\r\n")


def test_all_null_bytes_are_binary() -> None:
    assert_binary(b"\x00" * 100, "application/octet-stream")


def test_high_null_concentration_is_binary() -> None:
    assert_binary(b"Hello" + b"\x00" * 10 + b"world" * 10, "application/octet-stream")


def test_single_null_in_large_text_is_not_binary() -> None:
    result = chardet.detect(b"a" * 500 + b"\x00" + b"b" * 500)
    assert result["encoding"] == "ascii"
    assert result["mime_type"] == "text/plain"


def test_control_characters_indicate_binary() -> None:
    assert_binary(b"\x01\x02\x03\x04\x05\x06\x07\x08" * 20, "application/octet-stream")


def test_few_control_characters_in_large_text_are_not_binary() -> None:
    result = chardet.detect(b"Normal text " * 100 + b"\x01")
    assert result["encoding"] is not None
    assert result["mime_type"] == "text/plain"


def test_jpeg_magic_is_binary() -> None:
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 50 + bytes(range(256))
    assert_binary(data, "image/jpeg")


def test_utf8_text_is_not_binary() -> None:
    result = chardet.detect("Héllo wörld".encode())
    assert result["encoding"] == "utf-8"
    assert result["mime_type"] == "text/plain"


def test_max_bytes_ignores_binary_tail() -> None:
    text = b"clean text " * 100
    result = chardet.detect(text + b"\x00" * 1000, max_bytes=len(text))
    assert result["encoding"] == "ascii"


def test_exactly_one_percent_control_bytes_is_not_binary() -> None:
    result = chardet.detect(b"a" * 99 + b"\x01")
    assert result["encoding"] is not None
    assert result["mime_type"] == "text/plain"


def test_above_one_percent_control_bytes_is_binary() -> None:
    assert_binary(b"a" * 98 + b"\x01\x02", "application/octet-stream")


def test_utf8_bom_precedes_statistical_detection() -> None:
    assert chardet.detect(b"\xef\xbb\xbfHello")["encoding"] == "UTF-8-SIG"


def test_utf16_little_endian_bom() -> None:
    assert chardet.detect(b"\xff\xfeH\x00e\x00l\x00l\x00o\x00")["encoding"] == "UTF-16"


def test_utf16_big_endian_bom() -> None:
    assert chardet.detect(b"\xfe\xff\x00H\x00e\x00l\x00l\x00o")["encoding"] == "UTF-16"


def test_utf32_little_endian_bom() -> None:
    assert chardet.detect(b"\xff\xfe\x00\x00H\x00\x00\x00")["encoding"] == "UTF-32"


def test_utf32_big_endian_bom() -> None:
    assert chardet.detect(b"\x00\x00\xfe\xff\x00\x00\x00H")["encoding"] == "UTF-32"


def test_plain_text_has_no_bom_result() -> None:
    assert chardet.detect(b"Hello, world!")["encoding"] == "ascii"


def test_empty_input_has_no_bom_result() -> None:
    assert chardet.detect(b"")["encoding"] == "utf-8"


def test_partial_utf8_bom_is_not_treated_as_bom() -> None:
    assert chardet.detect(b"\xef")["encoding"] != "UTF-8-SIG"
    assert chardet.detect(b"\xef\xbb")["encoding"] != "UTF-8-SIG"


def test_utf32_little_endian_is_checked_before_utf16() -> None:
    data = b"\xff\xfe\x00\x00H\x00\x00\x00"
    assert chardet.detect(data)["encoding"] == "UTF-32"


def test_bare_utf32_little_endian_bom_is_valid() -> None:
    assert chardet.detect(b"\xff\xfe\x00\x00")["encoding"] == "UTF-32"


def test_ebcdic_text_is_not_misdetected_as_gb18030() -> None:
    data = "Hello World, this is a test of EBCDIC encoding.".encode("cp037")
    result = chardet.detect(data, encoding_era=EncodingEra.ALL, compat_names=False)
    assert result["encoding"] != "gb18030"


def test_latin_text_is_not_misdetected_as_cp932() -> None:
    data = "Héllo wörld, tëst dàta wïth äccénts.".encode("iso-8859-1")
    result = chardet.detect(data, encoding_era=EncodingEra.ALL, compat_names=False)
    assert result["encoding"] != "cp932"


def test_real_japanese_remains_a_cjk_candidate() -> None:
    data = "これはテストです。日本語のテキストです。".encode("shift_jis")
    result = chardet.detect(data, encoding_era=EncodingEra.ALL, compat_names=False)
    assert result["encoding"] in {"shift_jis_2004", "cp932"}


def test_real_chinese_remains_a_cjk_candidate() -> None:
    data = "这是一个测试。中文文本应该被正确检测。".encode("gb18030")
    result = chardet.detect(data, encoding_era=EncodingEra.ALL, compat_names=False)
    assert result["encoding"] in {"gb18030", "big5hkscs", "cp949", "euc_kr"}


def test_real_korean_remains_a_cjk_candidate() -> None:
    data = "이것은 테스트입니다. 한국어 텍스트입니다.".encode("euc-kr")
    result = chardet.detect(data, encoding_era=EncodingEra.ALL, compat_names=False)
    assert result["encoding"] in {"cp949", "euc_kr", "gb18030", "johab"}


def test_german_macroman_is_not_misdetected_as_cjk() -> None:
    text = "München ist die Hauptstadt Bayerns. Größe, Qualität und schöne Straßen prägen die Stadt. " * 10
    result = chardet.detect(
        text.encode("mac_roman"), encoding_era=EncodingEra.ALL, compat_names=False
    )
    assert result["encoding"] not in {
        "gb18030",
        "big5hkscs",
        "cp932",
        "cp949",
        "euc_jis_2004",
        "euc_kr",
        "shift_jis_2004",
        "johab",
        "hz",
        "iso2022_jp_2",
        "iso2022_kr",
    }
