from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Literal, Optional

import pytest


@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 80


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    tags: List[str] = field(default_factory=lambda: ["dev"])
    enabled: bool = True
    mode: Literal["dev", "prod"] = "dev"
    required: str = "???"


@dataclass
class OptionalConfig:
    count: Optional[int] = None
    label: str = "ready"


class Color(Enum):
    RED = "red"
    BLUE = "blue"


@dataclass
class EnumConfig:
    color: Color = Color.RED


@dataclass
class CollectionConfig:
    numbers: List[int] = field(default_factory=lambda: [1])
    mapping: Dict[str, int] = field(default_factory=lambda: {"one": 1})


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


@pytest.fixture(autouse=True)
def reset_omegaconf_resolvers():
    from omegaconf import OmegaConf

    OmegaConf.clear_resolvers()
    yield
    OmegaConf.clear_resolvers()


@pytest.fixture
def base_config():
    from omegaconf import OmegaConf

    return OmegaConf.create(
        {
            "app": {"name": "demo", "port": 8080},
            "database": {"host": "localhost", "ports": [5432, 5433]},
            "alias": "${app.name}",
            "missing": "???",
        }
    )


@pytest.fixture
def app_config():
    from omegaconf import OmegaConf

    return OmegaConf.structured(AppConfig)


@pytest.fixture
def yaml_text():
    return (
        "name: demo\n"
        "port: 8080\n"
        "features:\n"
        "  - alpha\n"
        "  - beta\n"
    )
