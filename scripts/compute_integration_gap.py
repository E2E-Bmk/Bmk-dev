"""
Compute the PRECISE Integration Gap for Spec2Repo tasks.

True Integration Gap Event: An integration/e2e test FAILED,
but ALL of its depended atomic tests PASSED.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

TASKS_DIR = Path(r"G:\research\01_agents\swe-e2e\Bmk-dev\tasks")

PRIORITY_TASKS = [
    "httpcore-transport-fullrepro-001",
    "doit-taskrunner-fullrepro-002",
    "dynaconf-settings-fullrepro-001",
    "requests-cache-fullrepro-001",
    "copier-template-fullrepro-001",
    "fsspec-filesystem-fullrepro-001",
    "boltons-coreutils-fullrepro-001",
    "cookiecutter-fullrepro-001",
    "jrnl-journal-fullrepro-002",
    "packaging-core-fullrepro-001",
]

# ---------------------------------------------------------------------------
# Module keyword heuristics per project
# ---------------------------------------------------------------------------

HTTPCORE_MODULE_KEYWORDS = {
    "Pool": ["pool", "connection_pool", "connections_property", "keepalive",
             "idle_connections", "reuse", "distinct"],
    "Connection": ["connection", "http_connection", "handle_request", "stream",
                   "reuses_its_stream", "origin", "available_state"],
    "TLS": ["tls", "https", "ssl", "sni", "secure", "start_tls"],
    "Retry": ["retry", "retries", "backoff", "connect_error"],
    "Backend": ["backend", "tcp_connect", "local_address", "socket_options",
                "unix_domain", "connect_unix"],
    "Request": ["request_line", "url_path", "host_header", "port",
                "headers", "content_length", "chunked", "transfer_encoding",
                "method", "bytes_method", "bytes_content", "mapping_headers",
                "sequence_headers", "request_target"],
    "Response": ["response", "status", "iter_stream", "read", "close",
                 "content", "stream_response"],
    "URL": ["url_from", "url_target", "url_rejects", "options_star"],
    "Proxy": ["proxy"],
    "Trace": ["trace"],
    "ErrorHandling": ["unsupported_protocol", "missing_protocol",
                      "premature_server_disconnect", "invalid_response_header",
                      "remote_protocol_error"],
    "Mock": ["mock_backend", "mock_stream"],
    "Timeout": ["timeout", "connect_timeout", "read_timeout", "write_timeout"],
}

DOIT_MODULE_KEYWORDS = {
    "Action": ["action", "python_action", "command_action", "cmdaction",
               "string_command", "list_command", "create_folder"],
    "Runner": ["run", "execute", "continue_runs", "single_option",
               "always_execute", "run_once"],
    "TaskLoader": ["module_task_loader", "generator_subtasks", "create_after",
                   "pyproject_default", "doit_config"],
    "DepDB": ["dependency", "file_dependency", "result_dep", "calc_dep",
              "config_changed", "up_to_date", "rerun", "implicit_target"],
    "CLI": ["list_status", "list_hides", "help_task", "dumpdb",
            "selecting_by_target", "wildcard_selection", "positional_arguments",
            "default_command", "verbosity"],
    "Clean": ["clean", "forget", "ignore", "reset_dep"],
    "Reporter": ["json_reporter", "reporter"],
    "GetArgs": ["getargs", "save_out", "result_dep", "feeds_getargs"],
    "Setup": ["setup_task", "teardown"],
    "Params": ["params", "option", "get_var", "boolean_inverse"],
}

DYNACONF_MODULE_KEYWORDS = {
    "Settings": ["settings", "envvar", "local_file", "includes",
                 "settings_files", "preload", "python_settings"],
    "Environment": ["environment", "from_env", "setenv", "using_env",
                    "active_env", "comma_separated", "keep_chains"],
    "Merge": ["merge", "nested_access", "global_merge", "merge_marker"],
    "Validator": ["validator", "validate", "cast", "composition",
                  "callable_default", "apply_default"],
    "Token": ["token", "cast_token", "get_token", "read_file_token",
              "string_utility", "format_token", "builtin_cast"],
    "CLI_Dynaconf": ["cli_get", "cli_inspect", "cli_list"],
    "Runtime": ["runtime_set", "runtime_update", "load_file", "fresh_var"],
    "Hook": ["hook", "post_hook", "dynaconf_hooks", "constructor_post"],
    "EnvVar": ["envvar", "prefix", "unprefixed", "ignore_unknown",
               "sysenv_fallback", "auto_cast"],
    "Insert_Del": ["insert_token", "del_token"],
    "History": ["history", "inspect"],
}

REQUESTS_CACHE_MODULE_KEYWORDS = {
    "Session": ["session", "cached_session"],
    "Cache": ["cache", "sqlite", "redis", "mongodb", "gridfs", "dynamodb",
              "filesystem"],
    "Serializer": ["serializer", "bson", "json", "yaml", "pickle"],
    "Expiration": ["expire", "expiration", "stale", "ttl", "max_age"],
    "Filter": ["filter", "allowlist", "denylist", "url_pattern", "param"],
    "Backend": ["backend", "storage"],
    "Request_Match": ["match", "normalize", "ignored_param"],
    "Response_Model": ["response", "cached_response"],
}

COPIER_MODULE_KEYWORDS = {
    "Copy": ["copy", "run_copy", "render", "pretend"],
    "Recopy": ["recopy", "reuses_recorded", "recopy_data", "recopy_pretend"],
    "Settings": ["settings", "load_settings", "defaults", "configuration",
                 "minimum_version", "invalid_settings"],
    "CLI": ["cli_copy", "cli_data", "cli_force", "cli_recopy",
            "cli_pretend", "cli_quiet", "cli_answers", "cli_skip",
            "cli_exclude", "cli_no_cleanup", "cli_help", "cli_refuses"],
    "Question": ["question", "answer", "secret_answer", "defaults_mode",
                 "api_data", "data_file"],
    "Template": ["template", "jinja", "exclude", "subdirectory",
                 "skip_if_exists", "force"],
    "Task": ["task_runs", "skip_tasks", "trust"],
    "Phase": ["phase", "vcsref", "render_during"],
    "Import": ["import_surface", "error_namespace"],
}

FSSPEC_MODULE_KEYWORDS = {
    "Registry": ["factory", "register", "unknown_protocol", "public_exports",
                 "protocols"],
    "MemoryFS": ["memory_write", "memory_global", "memory_path",
                 "memory_text", "memory_mkdir", "memory_cat",
                 "memory_pipe", "memory_touch", "memory_find",
                 "memory_walk", "memory_copy", "memory_recursive",
                 "memory_transaction"],
    "LocalFS": ["local_auto_mkdir", "local_copy_move"],
    "OpenFile": ["openfile", "open_text", "open_files", "open_local",
                 "open_files_context"],
    "FSMap": ["fsmap", "get_mapper", "getitems", "pop_clear",
              "value_conversion", "leading_slash"],
    "DirFS": ["dirfs", "relative_view", "listing_detail", "find_walk",
              "rejects_paths", "non_local"],
    "ZipFS": ["zip_write", "zip_find", "zip_chained", "zip_missing",
              "zip_member"],
    "CacheFS": ["simplecache", "wholefilecache", "cache_read",
                "transaction_defers", "transaction_rollback"],
    "CrossView": ["cross_view", "copy_between", "url_token",
                  "url_to_fs", "get_fs_token"],
    "Find": ["find_exact", "du_and_find", "withdirs", "maxdepth"],
}

BOLTONS_MODULE_KEYWORDS = {
    "iterutils": ["iter", "chunk", "flatten", "unique", "windowed",
                  "partition", "bucketize", "first"],
    "strutils": ["str", "string", "slugify", "html", "strip", "indent",
                 "camel", "snake"],
    "dictutils": ["dict", "ordered", "merge", "subdict", "remap",
                  "frozen_dict"],
    "funcutils": ["func", "wraps", "partial", "memoize", "cache"],
    "typeutils": ["type", "classproperty", "issubclass", "make_sentinel"],
    "setutils": ["set", "indexed", "complement"],
    "fileutils": ["file", "atomic", "mkdir", "copy_tree"],
    "timeutils": ["time", "date", "parse", "format", "relative"],
    "cacheutils": ["cache", "lru", "lri", "threshold"],
    "jsonutils": ["json", "ordered_json"],
    "tableutils": ["table", "input", "render"],
    "statsutils": ["stats", "mean", "median", "variance"],
    "debugutils": ["debug", "trace", "pdb"],
    "queueutils": ["queue", "priority", "heap"],
}

COOKIECUTTER_MODULE_KEYWORDS = {
    "Template": ["template", "generate", "render"],
    "Config": ["config", "user_config", "default_config"],
    "Prompt": ["prompt", "choice", "no_input"],
    "Repository": ["repository", "clone", "zip", "abbreviation"],
    "Hook": ["hook", "pre_generate", "post_generate"],
    "Output": ["output", "overwrite", "skip"],
    "Extension": ["extension", "jinja"],
    "Context": ["context", "extra_context"],
}

JRNL_MODULE_KEYWORDS = {
    "Entry": ["entry", "title", "body", "tag", "date", "star"],
    "Journal": ["journal", "write", "read", "load", "save"],
    "Encrypt": ["encrypt", "decrypt", "password", "keyring"],
    "Config": ["config", "yaml", "default"],
    "Export": ["export", "markdown", "json", "text", "fancy", "xml"],
    "Search": ["search", "filter", "contains", "tag_filter"],
    "CLI": ["cli", "parse", "args", "command"],
    "Plugin": ["plugin", "import", "format"],
    "Edit": ["edit", "delete"],
    "Time": ["time", "date", "parse_date"],
}

PACKAGING_MODULE_KEYWORDS = {
    "Version": ["version", "parse", "release", "pre", "post", "dev",
                "epoch", "public", "base", "major", "minor", "micro"],
    "Specifier": ["specifier", "contains", "filter", "compatible",
                  "arbitrary", "prereleases"],
    "Requirement": ["requirement", "extras", "url", "marker"],
    "Marker": ["marker", "evaluate", "environment", "default_environment"],
    "Tag": ["tag", "platform", "interpreter", "abi", "sys_tags",
            "compatible_tags"],
    "Utils": ["canonicalize", "normalize", "parse_wheel", "parse_sdist"],
    "Metadata": ["metadata", "raw", "from_email"],
}

PROJECT_KEYWORDS = {
    "httpcore-transport-fullrepro-001": HTTPCORE_MODULE_KEYWORDS,
    "doit-taskrunner-fullrepro-002": DOIT_MODULE_KEYWORDS,
    "dynaconf-settings-fullrepro-001": DYNACONF_MODULE_KEYWORDS,
    "requests-cache-fullrepro-001": REQUESTS_CACHE_MODULE_KEYWORDS,
    "copier-template-fullrepro-001": COPIER_MODULE_KEYWORDS,
    "fsspec-filesystem-fullrepro-001": FSSPEC_MODULE_KEYWORDS,
    "boltons-coreutils-fullrepro-001": BOLTONS_MODULE_KEYWORDS,
    "cookiecutter-fullrepro-001": COOKIECUTTER_MODULE_KEYWORDS,
    "jrnl-journal-fullrepro-002": JRNL_MODULE_KEYWORDS,
    "packaging-core-fullrepro-001": PACKAGING_MODULE_KEYWORDS,
}


def normalize_test_name(taxonomy_key: str) -> str:
    """Extract the bare test function name from a taxonomy_key."""
    parts = taxonomy_key.split("::")
    name = parts[-1] if "::" in taxonomy_key else taxonomy_key.split(".")[-1]
    return name


def identify_modules(test_name: str, module_keywords: dict) -> set:
    """Identify which modules a test depends on based on keyword matching."""
    name_lower = test_name.lower()
    modules = set()
    for module, keywords in module_keywords.items():
        for kw in keywords:
            if kw.lower() in name_lower:
                modules.add(module)
                break
    return modules


def load_taxonomy(task_dir: Path) -> dict:
    """Load taxonomy.jsonl and return {normalized_test_name: layer}."""
    taxonomy = {}
    tax_file = task_dir / "taxonomy.jsonl"
    if not tax_file.exists():
        return taxonomy
    with open(tax_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            key = entry.get("taxonomy_key", "")
            layer = entry.get("layer", "unknown")
            norm_name = normalize_test_name(key)
            taxonomy[norm_name] = layer
    return taxonomy


def load_test_outcomes(task_dir: Path, taxonomy: dict) -> dict:
    """Load score_result.json and return {normalized_test_name: 'passed'|'failed'}.

    Handles two formats:
    1. grouped_results → json_report.tests (most tasks)
    2. failed_nodeids flat list (boltons-style)
    """
    outcomes = {}
    score_file = task_dir / "score_result.json"
    if not score_file.exists():
        return outcomes
    with open(score_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    grouped = data.get("grouped_results", {})
    if grouped:
        for test_file, file_data in grouped.items():
            jr = file_data.get("json_report", {})
            tests = jr.get("tests", [])
            for t in tests:
                nodeid = t.get("nodeid", "")
                outcome = t.get("outcome", "unknown")
                norm_name = normalize_test_name(nodeid)
                outcomes[norm_name] = outcome
    else:
        failed_nodeids = data.get("failed_nodeids", [])
        failed_names = set()
        for nid in failed_nodeids:
            norm = normalize_test_name(nid)
            failed_names.add(norm)

        for test_name in taxonomy.keys():
            if test_name in failed_names:
                outcomes[test_name] = "failed"
            else:
                outcomes[test_name] = "passed"

    return outcomes


def analyze_task(task_name: str) -> dict:
    task_dir = TASKS_DIR / task_name
    taxonomy = load_taxonomy(task_dir)
    outcomes = load_test_outcomes(task_dir, taxonomy)

    module_keywords = PROJECT_KEYWORDS.get(task_name, {})

    atomics = {}
    integ_e2e = {}

    for test_name, layer in taxonomy.items():
        outcome = outcomes.get(test_name, None)
        if outcome is None:
            continue
        if layer == "atomic":
            atomics[test_name] = outcome
        elif layer in ("integration", "system_e2e"):
            integ_e2e[test_name] = {"outcome": outcome, "layer": layer}

    total_integ_e2e = len(integ_e2e)
    failed_integ_e2e = {k: v for k, v in integ_e2e.items() if v["outcome"] == "failed"}
    total_failed = len(failed_integ_e2e)

    atomic_modules = defaultdict(list)
    for test_name, outcome in atomics.items():
        modules = identify_modules(test_name, module_keywords)
        for m in modules:
            atomic_modules[m].append((test_name, outcome))

    true_gap_events = []
    noise_events = []

    for test_name, info in failed_integ_e2e.items():
        dep_modules = identify_modules(test_name, module_keywords)

        if not dep_modules:
            dep_modules = {"_unclassified_"}

        all_depended_atomics_passed = True
        depended_atomics = []
        any_depended_atomic_found = False

        for m in dep_modules:
            if m in atomic_modules:
                for atomic_name, atomic_outcome in atomic_modules[m]:
                    any_depended_atomic_found = True
                    depended_atomics.append((atomic_name, atomic_outcome))
                    if atomic_outcome != "passed":
                        all_depended_atomics_passed = False

        if not any_depended_atomic_found:
            all_depended_atomics_passed = True

        if all_depended_atomics_passed:
            true_gap_events.append({
                "test": test_name,
                "layer": info["layer"],
                "dep_modules": dep_modules,
                "depended_atomics": depended_atomics,
            })
        else:
            failed_atomics = [(a, o) for a, o in depended_atomics if o != "passed"]
            noise_events.append({
                "test": test_name,
                "layer": info["layer"],
                "dep_modules": dep_modules,
                "failed_atomics": failed_atomics,
            })

    strong_gaps = [e for e in true_gap_events if len(e['depended_atomics']) > 0]
    weak_gaps = [e for e in true_gap_events if len(e['depended_atomics']) == 0]

    gap_rate = len(true_gap_events) / total_integ_e2e * 100 if total_integ_e2e > 0 else 0
    strong_gap_rate = len(strong_gaps) / total_integ_e2e * 100 if total_integ_e2e > 0 else 0
    noise_rate = len(noise_events) / total_integ_e2e * 100 if total_integ_e2e > 0 else 0

    return {
        "task": task_name,
        "total_integ_e2e": total_integ_e2e,
        "total_failed": total_failed,
        "true_gap_count": len(true_gap_events),
        "strong_gap_count": len(strong_gaps),
        "weak_gap_count": len(weak_gaps),
        "noise_count": len(noise_events),
        "gap_rate": gap_rate,
        "strong_gap_rate": strong_gap_rate,
        "noise_rate": noise_rate,
        "true_gap_events": true_gap_events,
        "strong_gaps": strong_gaps,
        "weak_gaps": weak_gaps,
        "noise_events": noise_events,
        "atomics_total": len(atomics),
        "atomics_passed": sum(1 for o in atomics.values() if o == "passed"),
        "atomics_failed": sum(1 for o in atomics.values() if o != "passed"),
        "integ_passed": sum(1 for v in integ_e2e.values() if v["outcome"] == "passed"),
    }


def main():
    results = []

    for task_name in PRIORITY_TASKS:
        task_dir = TASKS_DIR / task_name
        tax_file = task_dir / "taxonomy.jsonl"
        score_file = task_dir / "score_result.json"

        if not tax_file.exists() or not score_file.exists():
            print(f"SKIP {task_name}: missing taxonomy.jsonl or score_result.json")
            continue

        r = analyze_task(task_name)
        results.append(r)

        print(f"\n### {task_name}")
        print(f"Atomic tests: {r['atomics_total']} (passed={r['atomics_passed']}, failed={r['atomics_failed']})")
        print(f"Total integration+e2e tests: {r['total_integ_e2e']}")
        print(f"  Passed: {r['integ_passed']}")
        print(f"  Failed integration+e2e tests: {r['total_failed']}")
        print(f"True Gap Events (all depended atomics passed): {r['true_gap_count']}")
        print(f"  Strong (verified atomics > 0 all passed): {r['strong_gap_count']}")
        print(f"  Weak (no matching atomics found):          {r['weak_gap_count']}")
        print(f"Noise (component itself broken): {r['noise_count']}")
        print(f"")
        print(f"True Integration Gap Rate: {r['gap_rate']:.1f}% (strong only: {r['strong_gap_rate']:.1f}%)")
        print(f"Noise Rate: {r['noise_rate']:.1f}%")

        if r['true_gap_events']:
            print(f"\nExamples of True Gap Events:")
            for ev in r['true_gap_events'][:5]:
                mods = ", ".join(sorted(ev['dep_modules']))
                n_atomics = len(ev['depended_atomics'])
                print(f"  - {ev['test']} [layer={ev['layer']}]")
                print(f"    depends on modules: {{{mods}}}")
                print(f"    depended atomics ({n_atomics}): ALL PASSED")

        if r['noise_events']:
            print(f"\nNoise examples (component broken):")
            for ev in r['noise_events'][:3]:
                mods = ", ".join(sorted(ev['dep_modules']))
                fa = [(a, o) for a, o in ev['failed_atomics']]
                print(f"  - {ev['test']} [layer={ev['layer']}]")
                print(f"    depends on modules: {{{mods}}}")
                print(f"    FAILED atomics: {fa}")

    print("\n\n" + "=" * 100)
    print("SUMMARY TABLE (sorted by Gap Rate descending)")
    print("=" * 100)

    results.sort(key=lambda x: x["gap_rate"], reverse=True)

    header = f"{'Task':<45} {'I+E Tot':>7} {'I+E Fl':>6} {'Gap':>4} {'Strng':>5} {'Weak':>5} {'Noise':>5} {'GapR%':>6} {'StrgR%':>7} {'Top Gap Pattern'}"
    print(header)
    print("-" * 140)

    for r in results:
        top_patterns = set()
        for ev in r['true_gap_events'][:5]:
            for m in ev['dep_modules']:
                if m != "_unclassified_":
                    top_patterns.add(m)
        top_str = ", ".join(sorted(top_patterns)[:3]) if top_patterns else "N/A"

        print(f"{r['task']:<45} {r['total_integ_e2e']:>7} {r['total_failed']:>6} {r['true_gap_count']:>4} {r['strong_gap_count']:>5} {r['weak_gap_count']:>5} {r['noise_count']:>5} {r['gap_rate']:>5.1f}% {r['strong_gap_rate']:>6.1f}% {top_str}")

    total_ie = sum(r['total_integ_e2e'] for r in results)
    total_fail = sum(r['total_failed'] for r in results)
    total_gap = sum(r['true_gap_count'] for r in results)
    total_strong = sum(r['strong_gap_count'] for r in results)
    total_weak = sum(r['weak_gap_count'] for r in results)
    total_noise = sum(r['noise_count'] for r in results)
    agg_rate = total_gap / total_ie * 100 if total_ie > 0 else 0
    agg_strong = total_strong / total_ie * 100 if total_ie > 0 else 0

    print("-" * 140)
    print(f"{'AGGREGATE':<45} {total_ie:>7} {total_fail:>6} {total_gap:>4} {total_strong:>5} {total_weak:>5} {total_noise:>5} {agg_rate:>5.1f}% {agg_strong:>6.1f}%")

    # Paper-ready condensed table
    print("\n\n" + "=" * 100)
    print("PAPER TABLE 1: True Integration Gap (sorted by Gap Rate)")
    print("=" * 100)
    ph = f"{'Task':<40} {'|I+E|':>5} {'Fail':>5} {'TrueGap':>8} {'GapRate':>8} {'Precision':>10} {'TopPattern'}"
    print(ph)
    print("-" * 100)

    for r in results:
        if r['total_integ_e2e'] == 0:
            continue
        top_patterns = set()
        for ev in r['true_gap_events'][:5]:
            for m in ev['dep_modules']:
                if m != "_unclassified_":
                    top_patterns.add(m)
        top_str = ", ".join(sorted(top_patterns)[:2]) if top_patterns else "-"
        precision = r['true_gap_count'] / r['total_failed'] * 100 if r['total_failed'] > 0 else 0
        print(f"{r['task']:<40} {r['total_integ_e2e']:>5} {r['total_failed']:>5} {r['true_gap_count']:>8} {r['gap_rate']:>7.1f}% {precision:>9.1f}% {top_str}")

    print("-" * 100)
    agg_prec = total_gap / total_fail * 100 if total_fail > 0 else 0
    print(f"{'AGGREGATE':<40} {total_ie:>5} {total_fail:>5} {total_gap:>8} {agg_rate:>7.1f}% {agg_prec:>9.1f}%")

    # Also dump raw JSON for further analysis
    output_path = TASKS_DIR.parent / "analysis" / "integration_gap_precise.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
