from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from jedi import Project


APP_SOURCE = dedent(
    '''\
    """Application module."""
    from lib import Greeter, make_greeter

    person = make_greeter("Ada")
    message = person.greet("Hi")
    repeat = make_greeter
    '''
)

LIB_SOURCE = dedent(
    '''\
    """Library module."""
    class Greeter:
        """Greets a person."""
        def __init__(self, name: str = "Ada"):
            self.name = name

        def greet(self, prefix: str = "Hello") -> str:
            """Return a greeting."""
            return f"{prefix}, {self.name}"

    def make_greeter(name: str = "Ada") -> Greeter:
        """Build a greeter."""
        return Greeter(name)
    '''
)

CALC_SOURCE = dedent(
    '''\
    def total():
        first = 1
        second = 2
        result = first + second
        return result
    '''
)


def namespace_greet(name: str = "Ada", count: int = 1) -> str:
    return name * count


@pytest.fixture
def project_tree(tmp_path):
    root = tmp_path / "sample_project"
    root.mkdir()
    app = root / "app.py"
    lib = root / "lib.py"
    calc = root / "calc.py"
    app.write_text(APP_SOURCE, encoding="utf-8")
    lib.write_text(LIB_SOURCE, encoding="utf-8")
    calc.write_text(CALC_SOURCE, encoding="utf-8")
    project = Project(root, sys_path=[str(root)], smart_sys_path=False)
    return {
        "root": root,
        "app": app,
        "lib": lib,
        "calc": calc,
        "project": project,
    }


@pytest.fixture
def app_script(project_tree):
    from jedi import Script

    return Script(path=project_tree["app"], project=project_tree["project"])


@pytest.fixture
def lib_script(project_tree):
    from jedi import Script

    return Script(path=project_tree["lib"], project=project_tree["project"])


@pytest.fixture
def signature_script(project_tree):
    from jedi import Script

    code = dedent(
        '''\
        def greet(name: str = "Ada", count: int = 1) -> str:
            return name
        greet("A",
        '''
    ).rstrip("\n")
    return Script(
        code,
        path=project_tree["root"] / "signature.py",
        project=project_tree["project"],
    )


@pytest.fixture
def interpreter_namespace():
    return {"message": "hello", "greet": namespace_greet}


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): public atomic behaviors used by an integration test",
    )
