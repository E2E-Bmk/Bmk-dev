import json
import os
import textwrap

import pytest

from traitlets import (
    Any,
    Bool,
    CBool,
    CBytes,
    CFloat,
    CInt,
    CRegExp,
    CUnicode,
    Callable,
    CaselessStrEnum,
    Complex,
    Dict,
    DottedObjectName,
    Enum,
    Float,
    FuzzyEnum,
    HasTraits,
    Instance,
    Int,
    Integer,
    List,
    ObjectName,
    Set,
    TCPAddress,
    This,
    TraitError,
    Tuple,
    Type,
    Unicode,
    Union,
    Bunch,
    default,
    directional_link,
    import_item,
    link,
    observe,
    signature_has_traits,
    validate,
)

from traitlets.config import Application, Config, Configurable, MultipleInstanceError
from traitlets.config.application import boolean_flag
from traitlets.config.loader import (
    ArgumentError,
    ConfigFileNotFound,
    JSONFileConfigLoader,
    KVArgParseConfigLoader,
    LazyConfigValue,
    PyFileConfigLoader,
)


class IntegerModel(HasTraits):
    value = Integer()


class Worker(Configurable):
    enabled = Bool(False, help="enable worker").tag(config=True)
    label = Unicode("default", help="worker label").tag(config=True)
    count = Int(0, help="worker count").tag(config=True)
    plain = Unicode("plain")


class MiniApp(Application):
    classes = [Worker]
    aliases = {"label": "Worker.label", "count": "Worker.count"}
    flags = {"enable-worker": ({"Worker": {"enabled": True}}, "enable worker")}


def clear_application_tree(cls=Application):
    cls.clear_instance()
    for subclass in cls.__subclasses__():
        clear_application_tree(subclass)
