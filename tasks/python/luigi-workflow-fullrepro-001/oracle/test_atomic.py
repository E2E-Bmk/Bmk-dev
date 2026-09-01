"""Spec2Repo oracle – atomic tests for luigi-workflow-fullrepro-001.

Each test verifies a single public API entry and a single behaviour point.
"""
import datetime as dt
import pathlib
import warnings

import pytest

from conftest import Flavor, run_script


# ═══════════════════════════════════════════════════════════════════
# Parameter types: parse / serialize
# ═══════════════════════════════════════════════════════════════════

def test_parameter_parse_returns_string():
    import luigi

    assert luigi.Parameter().parse("xyz") == "xyz"
    assert luigi.StrParameter().serialize(42) == "42"


def test_int_parameter_parse_valid_and_reject_invalid():
    import luigi

    assert luigi.IntParameter().parse("77") == 77
    with pytest.raises(ValueError):
        luigi.IntParameter().parse("nope")


def test_float_parameter_parse_valid_and_reject_invalid():
    import luigi

    assert luigi.FloatParameter().parse("2.718") == pytest.approx(2.718)
    with pytest.raises(ValueError):
        luigi.FloatParameter().parse("bad")


def test_bool_parameter_case_insensitive_and_reject_unknown():
    import luigi

    p = luigi.BoolParameter()
    assert p.parse("True") is True
    assert p.parse("FALSE") is False
    assert p.parse("true") is True
    with pytest.raises(ValueError):
        p.parse("maybe")


def test_date_parameter_parse_and_serialize_round_trip():
    import luigi

    dp = luigi.DateParameter()
    assert dp.parse("2025-03-15") == dt.date(2025, 3, 15)
    assert dp.serialize(dt.date(2025, 3, 15)) == "2025-03-15"


def test_month_year_parameter_parse_and_serialize():
    import luigi

    mp = luigi.MonthParameter()
    assert mp.parse("2025-04") == dt.date(2025, 4, 1)
    assert mp.serialize(dt.date(2025, 4, 1)) == "2025-04"

    yp = luigi.YearParameter()
    assert yp.parse("2025") == dt.date(2025, 1, 1)
    assert yp.serialize(dt.date(2025, 1, 1)) == "2025"


def test_date_hour_minute_second_parse_documented_shapes():
    import luigi

    assert luigi.DateHourParameter().parse("2025-04-20T09") == dt.datetime(
        2025, 4, 20, 9
    )
    assert luigi.DateMinuteParameter().parse("2025-04-20T0915") == dt.datetime(
        2025, 4, 20, 9, 15
    )
    assert luigi.DateSecondParameter().parse("2025-04-20T091530") == dt.datetime(
        2025, 4, 20, 9, 15, 30
    )


def test_date_parameter_invalid_format_raises_value_error():
    import luigi

    with pytest.raises(ValueError):
        luigi.DateParameter().parse("20/04/2025")
    with pytest.raises(ValueError):
        luigi.DateHourParameter().parse("2025-04-20")


# ═══════════════════════════════════════════════════════════════════
# Collection parameters
# ═══════════════════════════════════════════════════════════════════

def test_list_parameter_parse_json_array():
    import luigi

    result = luigi.ListParameter().parse("[10, 20, 30]")
    assert tuple(result) == (10, 20, 30)


def test_dict_parameter_parse_json_object():
    import luigi

    parsed = luigi.DictParameter().parse('{"alpha": 1, "beta": 2}')
    assert dict(parsed) == {"alpha": 1, "beta": 2}


def test_tuple_parameter_parse_json_and_reject_plain_string():
    import luigi

    assert luigi.TupleParameter().parse("[3, 4]") == (3, 4)
    with pytest.raises(ValueError):
        luigi.TupleParameter().parse("not-json")


# ═══════════════════════════════════════════════════════════════════
# Enum parameters
# ═══════════════════════════════════════════════════════════════════

def test_enum_parameter_parse_serialize_reject_unknown():
    import luigi

    p = luigi.EnumParameter(enum=Flavor)
    assert p.parse("VANILLA") is Flavor.VANILLA
    assert p.serialize(Flavor.CHOCOLATE) == "CHOCOLATE"
    with pytest.raises((ValueError, KeyError)):
        p.parse("MINT")


def test_enum_list_parameter_comma_separated_round_trip():
    import luigi

    p = luigi.EnumListParameter(enum=Flavor)
    assert p.parse("CHOCOLATE,STRAWBERRY") == (Flavor.CHOCOLATE, Flavor.STRAWBERRY)
    assert p.serialize((Flavor.STRAWBERRY, Flavor.VANILLA)) == "STRAWBERRY,VANILLA"


# ═══════════════════════════════════════════════════════════════════
# Constrained parameters
# ═══════════════════════════════════════════════════════════════════

def test_numerical_parameter_enforces_bounds_and_requires_var_type():
    import luigi
    from luigi.parameter import ParameterException

    p = luigi.NumericalParameter(var_type=int, min_value=0, max_value=10)
    assert p.parse("5") == 5
    with pytest.raises(ValueError):
        p.parse("10")
    with pytest.raises(ParameterException):
        luigi.NumericalParameter()


def test_choice_parameter_accepts_rejects_and_missing_choices():
    import luigi
    from luigi.parameter import ParameterException

    p = luigi.ChoiceParameter(choices=["alpha", "beta"])
    assert p.parse("alpha") == "alpha"
    with pytest.raises(ValueError):
        p.parse("gamma")
    with pytest.raises(ParameterException):
        luigi.ChoiceParameter()


def test_choice_list_parameter_order_duplicates_empty_reject():
    import luigi

    p = luigi.ChoiceListParameter(choices=["p", "q"])
    assert p.parse("p,q,p") == ("p", "q", "p")
    assert p.parse("") == ()
    with pytest.raises(ValueError):
        p.parse("p,r")


# ═══════════════════════════════════════════════════════════════════
# Path parameter
# ═══════════════════════════════════════════════════════════════════

def test_path_parameter_parse_normalize_exists_check(tmp_path):
    import luigi

    present = tmp_path / "exists.txt"
    present.write_text("ok", encoding="utf-8")

    pp = luigi.PathParameter(exists=True)
    assert pp.parse(str(present)) == str(present)
    assert pp.normalize(str(present)) == present
    with pytest.raises(ValueError):
        pp.normalize(str(tmp_path / "missing.txt"))

    plain = luigi.PathParameter()
    assert plain.normalize("rel/path.txt") == pathlib.Path("rel/path.txt")


# ═══════════════════════════════════════════════════════════════════
# Optional parameters
# ═══════════════════════════════════════════════════════════════════

def test_optional_parameter_parse_empty_serialize_none():
    import luigi

    assert luigi.OptionalParameter().parse("") is None
    assert luigi.OptionalIntParameter().parse("") is None
    assert luigi.OptionalBoolParameter().parse("") is None
    assert luigi.OptionalFloatParameter().parse("1.5") == 1.5
    assert luigi.OptionalParameter().serialize(None) == ""


def test_optional_parameter_warns_on_wrong_type():
    import luigi

    class WTask(luigi.Task):
        v = luigi.OptionalIntParameter(default=None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        t = WTask(v="wrong")
    assert t.v == "wrong"
    assert any("OptionalIntParameter" in str(w.message) for w in caught)


# ═══════════════════════════════════════════════════════════════════
# Task identity
# ═══════════════════════════════════════════════════════════════════

def test_task_family_with_and_without_namespace():
    import luigi

    luigi.namespace("proj")

    class Scoped(luigi.Task):
        pass

    luigi.namespace(None)
    assert Scoped.get_task_family() == "proj.Scoped"

    class Bare(luigi.Task):
        pass

    assert Bare.get_task_family() == "Bare"


def test_class_level_task_namespace_overrides():
    import luigi

    luigi.namespace("outer")

    class Inner(luigi.Task):
        task_namespace = "mine"

    luigi.namespace(None)
    assert Inner.get_task_family() == "mine.Inner"


def test_task_equality_and_hash_by_significant_params():
    import luigi

    class EqT(luigi.Task):
        n = luigi.IntParameter()

    class OtherT(luigi.Task):
        n = luigi.IntParameter()

    a, b, c = EqT(n=8), EqT(n=8), EqT(n=9)
    assert a == b and hash(a) == hash(b)
    assert a != c
    assert a != OtherT(n=8)


def test_insignificant_param_omitted_from_identity():
    import luigi

    class SigT(luigi.Task):
        key = luigi.Parameter()
        tag = luigi.Parameter(default="x", significant=False)

    x = SigT(key="k", tag="a")
    y = SigT(key="k", tag="b")
    assert x == y and hash(x) == hash(y)
    assert x.to_str_params(only_significant=True) == {"key": "k"}


def test_visibility_controls_public_serialization():
    import luigi
    from luigi.parameter import ParameterVisibility

    class VT(luigi.Task):
        pub = luigi.Parameter(default="u", visibility=ParameterVisibility.PUBLIC)
        hid = luigi.Parameter(default="h", visibility=ParameterVisibility.HIDDEN)
        pri = luigi.Parameter(default="p", visibility=ParameterVisibility.PRIVATE)

    t = VT()
    assert (t.pub, t.hid, t.pri) == ("u", "h", "p")
    public = t.to_str_params(only_public=True)
    assert "pub" in public
    assert "pri" not in public


def test_from_str_params_falls_back_to_defaults():
    import luigi

    class FS(luigi.Task):
        count = luigi.IntParameter()
        label = luigi.Parameter(default="fallback")

    t = FS.from_str_params({"count": "12"})
    assert t.count == 12 and t.label == "fallback"


def test_task_repr_shows_family_omits_insignificant():
    import luigi

    class RT(luigi.Task):
        val = luigi.IntParameter()
        note = luigi.Parameter(default="secret", significant=False)

    text = str(RT(val=17))
    assert "RT" in text and "17" in text
    assert "note" not in text and "secret" not in text


# ═══════════════════════════════════════════════════════════════════
# Positional / unknown / missing params
# ═══════════════════════════════════════════════════════════════════

def test_positional_missing_unknown_duplicate_exceptions():
    import luigi
    from luigi.parameter import (
        DuplicateParameterException,
        MissingParameterException,
        UnknownParameterException,
    )

    class PT(luigi.Task):
        v = luigi.IntParameter()

    with pytest.raises(MissingParameterException):
        PT()
    with pytest.raises(UnknownParameterException):
        PT(v=1, extra=2)
    with pytest.raises(DuplicateParameterException):
        PT("1", v=2)
    with pytest.raises(UnknownParameterException):
        PT("1", "2")


# ═══════════════════════════════════════════════════════════════════
# Task lifecycle
# ═══════════════════════════════════════════════════════════════════

def test_task_complete_reflects_output_existence(tmp_path):
    import luigi

    class NoOut(luigi.Task):
        pass

    assert NoOut().complete() is False

    class HasOut(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "done.txt")

    t = HasOut()
    assert t.complete() is False
    pathlib.Path(t.output().path).write_text("ok", encoding="utf-8")
    assert t.complete() is True


def test_task_complete_raises_when_output_has_no_exists(tmp_path):
    import luigi

    class BadOut(luigi.Task):
        def output(self):
            return object()

    with pytest.raises((AttributeError, TypeError)):
        BadOut().complete()


def test_clone_preserves_params_and_overrides():
    import luigi

    class Src(luigi.Task):
        a = luigi.IntParameter()
        b = luigi.Parameter(default="orig")

    class Dst(luigi.Task):
        a = luigi.IntParameter()
        c = luigi.Parameter(default="dst")

    s = Src(a=6, b="x")
    same = s.clone(b="y")
    assert isinstance(same, Src)
    assert same.a == 6
    assert same.b == "y"

    cross = s.clone(Dst, c="z")
    assert isinstance(cross, Dst)
    assert cross.a == 6
    assert cross.c == "z"


def test_external_task_run_is_none_and_incomplete(tmp_path):
    import luigi

    class Ext(luigi.ExternalTask):
        def output(self):
            return luigi.LocalTarget(tmp_path / "ext.txt")

    t = Ext()
    assert t.run is None
    assert t.complete() is False


# ═══════════════════════════════════════════════════════════════════
# LocalTarget
# ═══════════════════════════════════════════════════════════════════

def test_local_target_requires_path_or_is_tmp():
    import luigi

    with pytest.raises(Exception, match="path or is_tmp must be set"):
        luigi.LocalTarget()

    tmp = luigi.LocalTarget(is_tmp=True)
    assert isinstance(tmp.path, str)
    assert tmp.fn == tmp.path
    assert tmp.exists() is False


def test_local_target_path_exists_and_open_read_write(tmp_path):
    import luigi

    fp = tmp_path / "rw.txt"
    t = luigi.LocalTarget(str(fp))
    assert t.path == str(fp)
    assert t.exists() is False

    with t.open("w") as f:
        f.write("content")
    assert t.exists() is True

    with t.open("r") as f:
        assert f.read() == "content"


def test_local_target_write_exception_does_not_commit(tmp_path):
    import luigi

    t = luigi.LocalTarget(tmp_path / "fail.txt")
    with pytest.raises(RuntimeError):
        with t.open("w") as f:
            f.write("partial")
            raise RuntimeError("stop")
    assert t.exists() is False


def test_local_target_invalid_mode_raises(tmp_path):
    import luigi

    t = luigi.LocalTarget(tmp_path / "mode.txt")
    with pytest.raises(Exception, match=r"mode must be 'r' or 'w'"):
        t.open("a")


def test_filesystem_target_temporary_path_commits_and_rolls_back(tmp_path):
    import luigi

    target = luigi.LocalTarget(tmp_path / "commit.txt")
    with target.temporary_path() as tp:
        pathlib.Path(tp).write_text("committed", encoding="utf-8")
    assert pathlib.Path(target.path).read_text(encoding="utf-8") == "committed"

    rolled = luigi.LocalTarget(tmp_path / "rollback.txt")
    with pytest.raises(RuntimeError):
        with rolled.temporary_path() as tp:
            pathlib.Path(tp).write_text("nope", encoding="utf-8")
            raise RuntimeError("abort")
    assert rolled.exists() is False


# ═══════════════════════════════════════════════════════════════════
# Event system
# ═══════════════════════════════════════════════════════════════════

def test_event_handler_register_trigger_and_remove():
    import luigi

    collected = []

    class EvTask(luigi.Task):
        pass

    def handler(val):
        collected.append(val)

    EvTask.event_handler("custom-ev")(handler)
    EvTask().trigger_event("custom-ev", "hit")
    EvTask.remove_event_handler("custom-ev", handler)
    EvTask().trigger_event("custom-ev", "miss")
    assert collected == ["hit"]


# ═══════════════════════════════════════════════════════════════════
# DynamicRequirements
# ═══════════════════════════════════════════════════════════════════

def test_dynamic_requirements_complete_and_custom_complete(tmp_path):
    import luigi

    class DR(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "dr.txt")

    reqs = luigi.DynamicRequirements([DR()])
    assert reqs.complete() is False
    (tmp_path / "dr.txt").write_text("ok", encoding="utf-8")
    assert reqs.complete() is True

    calls = []

    def custom(fn):
        calls.append(fn(DR()))
        return "custom"

    reqs2 = luigi.DynamicRequirements([DR()], custom_complete=custom)
    assert reqs2.complete() == "custom"
    assert calls == [True]


# ═══════════════════════════════════════════════════════════════════
# run() type check
# ═══════════════════════════════════════════════════════════════════

def test_run_rejects_non_sequence_cmdline_args(tmp_path):
    proc = run_script(
        tmp_path,
        """
        import luigi
        try:
            luigi.run(cmdline_args="bad-arg", local_scheduler=True)
        except TypeError:
            print("type-error")
        """,
    )
    assert proc.returncode == 0
    assert "type-error" in proc.stdout


# ═══════════════════════════════════════════════════════════════════
# LuigiStatusCode
# ═══════════════════════════════════════════════════════════════════

def test_luigi_status_code_values_exist():
    import luigi

    codes = [
        luigi.LuigiStatusCode.SUCCESS,
        luigi.LuigiStatusCode.FAILED,
        luigi.LuigiStatusCode.MISSING_EXT,
        luigi.LuigiStatusCode.NOT_RUN,
        luigi.LuigiStatusCode.SCHEDULING_FAILED,
    ]
    assert len(set(codes)) == 5
