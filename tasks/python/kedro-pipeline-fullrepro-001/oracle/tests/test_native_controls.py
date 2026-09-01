from __future__ import annotations

from pathlib import Path

from .native_support import add_one, api, combine, double, expect, write_config


def test_a01(tmp_path: Path) -> None:
    k = api()
    assert k.pipeline_module.Node is k.Node and k.pipeline_module.Pipeline is k.Pipeline
    assert k.io_module.DataCatalog is k.DataCatalog and k.runner_module.SequentialRunner is k.SequentialRunner


def test_a02(tmp_path: Path) -> None:
    k = api()
    assert k.node(add_one, "x", "y").run({"x": 2}) == {"y": 3}
    assert k.node(combine, {"left": "a", "right": "b"}, "sum").run({"a": 4, "b": 5}) == {"sum": 9}


def test_a03(tmp_path: Path) -> None:
    k = api(); first = k.node(add_one, "raw", "middle", name="first"); second = k.node(double, "middle", "out", name="second")
    pipe = k.Pipeline([second, first])
    assert [node.name for node in pipe.nodes] == ["first", "second"]
    assert pipe.inputs() == {"raw"} and pipe.outputs() == {"out"} and pipe.node_dependencies[second] == {first}


def test_a04(tmp_path: Path) -> None:
    k = api(); base = k.Pipeline([k.node(add_one, "raw", "clean", name="clean", tags="prepare")])
    named = k.pipeline(base, namespace="etl", inputs={"raw"})
    assert named.inputs() == {"raw"} and named.outputs() == {"etl.clean"}
    assert [node.name for node in named.filter(tags={"prepare"}).nodes] == ["etl.clean"]


def test_a05(tmp_path: Path) -> None:
    k = api(); catalog = k.DataCatalog({"seed": k.MemoryDataset(2)}); catalog["raw"] = {"items": [3]}
    assert set(catalog.keys()) == {"seed", "raw"} and isinstance(catalog["raw"], k.MemoryDataset)
    assert catalog.load("raw") == {"items": [3]}; catalog["seed"] = 7; assert catalog.load("seed") == 7


def test_a06(tmp_path: Path) -> None:
    k = api(); data = [{"value": 1}]; dataset = k.MemoryDataset(data, copy_mode="deepcopy"); loaded = dataset.load(); loaded[0]["value"] = 9
    assert dataset.load() == [{"value": 1}] and dataset.exists(); dataset.release(); assert not dataset.exists()
    expect(k.DatasetError, dataset.load)


def test_a07(tmp_path: Path) -> None:
    k = api(); conf = write_config(tmp_path / "conf", value=2)
    params = k.OmegaConfigLoader(str(conf), base_env="base", runtime_params={"value": 8})["parameters"]
    assert params == {"value": 8, "increment": 1}


def test_a08(tmp_path: Path) -> None:
    k = api()
    expect(k.OutputNotUniqueError, lambda: k.Pipeline([k.node(add_one, "a", "same"), k.node(double, "b", "same")]))
    expect(k.CircularDependencyError, lambda: k.Pipeline([k.node(add_one, "right", "left"), k.node(double, "left", "right")]))
    expect(k.DatasetNotFoundError, lambda: k.DataCatalog().load("missing"))


def test_i01(tmp_path: Path) -> None:
    k = api(); pipe = k.Pipeline([k.node(add_one, "seed", "middle", name="first"), k.node(double, "middle", "result", name="second")])
    catalog = k.DataCatalog({"seed": k.MemoryDataset(5)}); result = k.SequentialRunner().run(pipe, catalog)
    assert result["result"].load() == 12 and catalog.load("result") == 12


def test_i02(tmp_path: Path) -> None:
    k = api(); pipe = k.Pipeline([k.node(add_one, "seed", "left"), k.node(double, "seed", "right"), k.node(combine, ["left", "right"], "total")])
    result = k.SequentialRunner().run(pipe, k.DataCatalog({"seed": k.MemoryDataset(4)}))
    assert result["total"].load() == 13


def test_i03(tmp_path: Path) -> None:
    k = api(); base = k.Pipeline([k.node(add_one, "params:value", "result", name="add")]); named = k.pipeline(base, namespace="ns", parameters={"value"})
    result = k.SequentialRunner().run(named, k.DataCatalog({"params:value": k.MemoryDataset(5)}))
    assert named.inputs() == {"params:value"} and result["ns.result"].load() == 6


def test_i04(tmp_path: Path) -> None:
    k = api(); downstream: list[int] = []
    def fail(value: int) -> int: raise RuntimeError(f"boom:{value}")
    pipe = k.Pipeline([k.node(fail, "seed", "middle"), k.node(lambda value: downstream.append(value), "middle", None)])
    expect(RuntimeError, lambda: k.SequentialRunner().run(pipe, k.DataCatalog({"seed": k.MemoryDataset(3)})))
    assert downstream == []


def test_s01(tmp_path: Path) -> None:
    k = api(); conf = write_config(tmp_path / "conf", value=2, increment=3); loader = k.OmegaConfigLoader(str(conf), base_env="base", runtime_params={"value": 7})
    params = loader["parameters"]; catalog = k.DataCatalog.from_config(loader["catalog"]); catalog["params:value"] = params["value"]; catalog["params:increment"] = params["increment"]
    pipe = k.Pipeline([k.node(combine, ["params:value", "params:increment"], "result")]); result = k.SequentialRunner().run(pipe, catalog)
    assert result["result"].load() == 10 and catalog.load("seed") == 4


def test_s02(tmp_path: Path) -> None:
    k = api(); pipe = k.Pipeline([k.node(add_one, "seed", "middle", name="prepare", tags="keep"), k.node(double, "middle", "result", name="train", tags="keep"), k.node(lambda value: str(value), "result", "report", name="report", tags="drop")])
    selected = pipe.filter(tags={"keep"}); catalog = k.DataCatalog({"seed": k.MemoryDataset(2)}); result = k.SequentialRunner().run(selected, catalog)
    assert set(result) == {"result"} and result["result"].load() == 6; catalog.release("result"); assert not catalog.exists("result")
