from pathlib import Path

import pytest


WORKFLOW_GRAMMAR = """
Workflow:
    project=Project
    states+=State
    events*=Event
    transitions*=Transition
;
Project: 'project' name=ID version=INT;
State: 'state' name=ID initial?='initial';
Event: 'event' name=ID code=INT;
Transition:
    'transition' name=ID
    'from' source=[State]
    'to' target=[State]
    'on' event=[Event]
    action=Action
;
Action: SendAction | LogAction;
SendAction: 'send' message=STRING;
LogAction: 'log' label=ID;
"""


WORKFLOW_MODEL = """
project Demo 1
state draft initial
state review
state done
event submit 10
event approve 20
transition t_submit from draft to review on submit send "notify"
transition t_approve from review to done on approve log audit
"""


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


@pytest.fixture
def workflow_metamodel():
    from textx import metamodel_from_str

    return metamodel_from_str(WORKFLOW_GRAMMAR)


@pytest.fixture
def workflow_model(workflow_metamodel):
    return workflow_metamodel.model_from_str(WORKFLOW_MODEL)


@pytest.fixture
def workflow_files(tmp_path: Path):
    grammar_file = tmp_path / "workflow.tx"
    model_file = tmp_path / "sample.workflow"
    grammar_file.write_text(WORKFLOW_GRAMMAR, encoding="utf-8")
    model_file.write_text(WORKFLOW_MODEL, encoding="utf-8")
    return grammar_file, model_file


@pytest.fixture
def clean_textx_registrations():
    from textx import clear_generator_registrations, clear_language_registrations

    clear_language_registrations()
    clear_generator_registrations()
    yield
    clear_language_registrations()
    clear_generator_registrations()
