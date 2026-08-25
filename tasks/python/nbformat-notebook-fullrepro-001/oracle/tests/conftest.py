from __future__ import annotations

import hashlib
import json
import os
import re


_reports={}; _collection_order=[]


def pytest_collection_modifyitems(config,items):
    mode=os.environ.get("NBF_GATE_ORDER_MODE","natural")
    if mode=="reverse": items.reverse()
    elif mode=="permuted": items.sort(key=lambda x:hashlib.sha256(x.nodeid.encode()).hexdigest())
    elif mode!="natural": raise RuntimeError(f"unsupported evaluator order mode: {mode}")
    _collection_order[:]=[x.nodeid for x in items]


def pytest_runtest_logreport(report):
    match=re.search(r"test_([ACE]\d\d)_",report.nodeid)
    if match: _reports.setdefault(match.group(1),{})[report.when]=report.outcome
    print(f"GATE_PHASE::{report.when}::{report.outcome}::{report.nodeid}",flush=True)


def pytest_sessionfinish(session,exitstatus):
    destination=os.environ.get("NBF_GATE_PHASE_RECEIPT")
    if destination:
        with open(destination,"w",encoding="utf-8") as stream:
            json.dump({"exitstatus":exitstatus,"order_mode":os.environ.get("NBF_GATE_ORDER_MODE","natural"),"collection_order":_collection_order,"thread_audits":[],"roots":_reports},stream,indent=2,sort_keys=True)


def make_notebook():
    from nbformat import v4
    return v4.new_notebook(metadata={"project":"shoal","cycle":7},cells=[
        v4.new_markdown_cell("# Survey\nNorth inlet",id="survey-note"),
        v4.new_code_cell("depth = 37\ndepth",id="depth-code",execution_count=4,outputs=[v4.new_output("execute_result",execution_count=4,data={"text/plain":"37"})]),
        v4.new_raw_cell("station: amber",id="station-raw"),
    ])


def candidate_env():
    env=os.environ.copy(); candidate=env["NBF_GATE_CANDIDATE"]
    env.update(PYTHONPATH=candidate,PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1")
    return env


def dependencies(tmp_path, notebook=None, label="one"):
    from nbformat._receipts import canonical
    from nbformat.durable_store import DurableStore
    from nbformat.lineage import LineageJournal
    from nbformat.trust_receipts import TrustLedger
    notebook=make_notebook() if notebook is None else notebook
    digest=hashlib.sha256(canonical(notebook)).hexdigest()
    store=DurableStore(tmp_path/f"{label}-store.db")
    store_receipt=store.acquire(f"owner-{label}").commit({"digest":digest})
    lineage=LineageJournal(tmp_path/f"{label}-lineage.db")
    prepared=lineage.prepare(f"stage-{label}",input_digest=digest,output_digest=digest,parents=[store_receipt["receipt_id"]])
    acknowledged=lineage.acknowledge(prepared)
    trust=TrustLedger(tmp_path/f"{label}-trust.db")
    generation=trust.issue_generation(f"key-{label}",f"secret-{label}".encode(),parents=[store_receipt["receipt_id"]])
    signed=trust.sign(notebook,domain=f"domain-{label}",key_id=f"key-{label}",lineage_receipt=acknowledged)
    return {"notebook":notebook,"store":store,"store_receipt":store_receipt,"lineage":lineage,"lineage_prepare":prepared,"lineage_ack":acknowledged,"trust":trust,"generation":generation,"signed":signed}
