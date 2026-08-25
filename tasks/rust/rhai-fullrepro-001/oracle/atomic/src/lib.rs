use rhai::grain::{Compiler, Program, Vm};
use rhai::grain::format::WriteError;
use rhai::module_resolvers::{DummyModuleResolver, StaticModuleResolver};
use rhai::{eval, run, Dynamic, Engine, EvalAltResult, Module, ModuleResolver, Scope, INT};

/// Verifies: RHAI-EVAL-003, RHAI-EVAL-004
#[test]
fn free_eval_returns_typed_integer() {
    let value: INT = eval("40 + 2").unwrap();
    assert_eq!(value, 42);
}

/// Verifies: RHAI-EVAL-003, RHAI-EVAL-006
#[test]
fn free_run_accepts_side_effect_script() {
    assert!(run("let x = 1; x += 41;").is_ok());
    assert_eq!(eval::<INT>("40 + 2").unwrap(), 42);
}

/// Verifies: RHAI-EVAL-001, RHAI-EVAL-004
#[test]
fn engine_eval_converts_string_result() {
    let engine = Engine::new();
    let value: String = engine.eval(r#""rhai" + "-" + "script""#).unwrap();
    assert_eq!(value, "rhai-script");
}

/// Verifies: RHAI-EVAL-001, RHAI-EVAL-004
#[test]
fn engine_eval_converts_boolean_result() {
    let engine = Engine::new();
    let value: bool = engine.eval("40 < 42 && 10 >= 10").unwrap();
    assert!(value);
}

/// Verifies: RHAI-EVAL-008
#[test]
fn eval_expression_accepts_single_expression() {
    let engine = Engine::new();
    let value: INT = engine.eval_expression("(6 * 7) - 1").unwrap();
    assert_eq!(value, 41);
}

/// Verifies: RHAI-EVAL-009
#[test]
fn eval_expression_rejects_statement_body() {
    let engine = Engine::new();
    let err = engine.eval_expression::<INT>("let x = 1; x").unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorParsing(..)));
}

/// Verifies: RHAI-EVAL-007
#[test]
fn eval_reports_output_type_mismatch() {
    let engine = Engine::new();
    let err = engine.eval::<String>("42").unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorMismatchOutputType(..)));
}

/// Verifies: RHAI-EVAL-007
#[test]
fn eval_invalid_syntax_reports_parsing_error() {
    let engine = Engine::new();
    let err = engine.eval::<INT>("let = 42").unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorParsing(..)));
}

/// Verifies: RHAI-COMP-001
#[test]
fn compile_invalid_syntax_returns_parse_error() {
    let engine = Engine::new();
    assert!(engine.compile("let = 42").is_err());
}

/// Verifies: RHAI-COMP-001
#[test]
fn compile_returns_reusable_ast() {
    let engine = Engine::new();
    let ast = engine.compile("let x = 20; x + 22").unwrap();
    assert_eq!(engine.eval_ast::<INT>(&ast).unwrap(), 42);
    assert_eq!(engine.eval_ast::<INT>(&ast).unwrap(), 42);
}

/// Verifies: RHAI-COMP-002
#[test]
fn compile_expression_returns_expression_ast() {
    let engine = Engine::new();
    let ast = engine.compile_expression("21 * 2").unwrap();
    assert_eq!(engine.eval_ast::<INT>(&ast).unwrap(), 42);
}

/// Verifies: RHAI-COMP-004
#[test]
fn compile_scripts_concatenates_segments_without_separators() {
    let engine = Engine::new();
    let scope = Scope::new();
    let ast = engine.compile_scripts_with_scope(&scope, ["let x = 40;", "x + 2"]).unwrap();
    assert_eq!(engine.eval_ast::<INT>(&ast).unwrap(), 42);
}

/// Verifies: RHAI-SCOPE-001
#[test]
fn scope_new_is_empty() {
    let scope = Scope::new();
    assert_eq!(scope.len(), 0);
    assert!(scope.is_empty());
}

/// Verifies: RHAI-SCOPE-001
#[test]
fn scope_with_capacity_starts_empty() {
    let scope = Scope::with_capacity(8);
    assert_eq!(scope.len(), 0);
    assert!(scope.is_empty());
}

/// Verifies: RHAI-SCOPE-002, RHAI-SCOPE-007
#[test]
fn scope_push_makes_value_visible() {
    let mut scope = Scope::new();
    scope.push("answer", 42 as INT);
    assert!(scope.contains("answer"));
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-SCOPE-003
#[test]
fn scope_push_constant_marks_value_read_only() {
    let mut scope = Scope::new();
    scope.push_constant("answer", 42 as INT);
    assert_eq!(scope.is_constant("answer"), Some(true));
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-SCOPE-004, RHAI-SCOPE-007
#[test]
fn scope_lookup_uses_latest_shadowing_entry() {
    let mut scope = Scope::new();
    scope.push("answer", 1 as INT).push("answer", 42 as INT);
    assert_eq!(scope.len(), 2);
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-SCOPE-005
#[test]
fn scope_pop_removes_last_entry() {
    let mut scope = Scope::new();
    scope.push("a", 1 as INT).push("b", 2 as INT);
    scope.pop();
    assert!(scope.contains("a"));
    assert!(!scope.contains("b"));
}

/// Verifies: RHAI-SCOPE-006
#[test]
#[should_panic]
fn scope_pop_empty_panics() {
    Scope::new().pop();
}

/// Verifies: RHAI-SCOPE-008
#[test]
fn scope_set_or_push_updates_mutable_visible_value() {
    let mut scope = Scope::new();
    scope.push("answer", 1 as INT);
    scope.set_or_push("answer", 42 as INT);
    assert_eq!(scope.len(), 1);
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-SCOPE-008
#[test]
fn scope_set_or_push_shadows_constant() {
    let mut scope = Scope::new();
    scope.push_constant("answer", 1 as INT);
    scope.set_or_push("answer", 42 as INT);
    assert_eq!(scope.len(), 2);
    assert_eq!(scope.is_constant("answer"), Some(false));
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-SCOPE-009
#[test]
fn scope_set_value_adds_absent_name() {
    let mut scope = Scope::new();
    scope.set_value("answer", 42 as INT);
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-SCOPE-009
#[test]
#[should_panic]
fn scope_set_value_on_constant_panics() {
    let mut scope = Scope::new();
    scope.push_constant("answer", 1 as INT);
    scope.set_value("answer", 42 as INT);
}

/// Verifies: RHAI-SCOPE-010
#[test]
fn scope_clone_visible_keeps_only_visible_names() {
    let mut scope = Scope::new();
    scope.push("x", 1 as INT).push("x", 42 as INT).push_constant("y", 7 as INT);
    let cloned = scope.clone_visible();
    assert_eq!(cloned.len(), 2);
    assert_eq!(cloned.get_value::<INT>("x"), Some(42));
    assert_eq!(cloned.is_constant("y"), Some(true));
}

/// Verifies: RHAI-MOD-001
#[test]
fn module_new_starts_without_variables() {
    let mut module = Module::new();
    assert!(!module.contains_var("answer"));
    module.set_var("answer", 42 as INT);
    assert!(module.contains_var("answer"));
}

/// Verifies: RHAI-MOD-002
#[test]
fn module_variable_round_trips_dynamic_value() {
    let mut module = Module::new();
    module.set_var("answer", Dynamic::from(42 as INT));
    assert!(module.contains_var("answer"));
    assert_eq!(module.get_var_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-MOD-004
#[test]
fn module_submodule_is_reachable() {
    let mut root = Module::new();
    let mut child = Module::new();
    child.set_var("value", 42 as INT);
    root.set_sub_module("child", child);
    assert!(root.contains_sub_module("child"));
    assert_eq!(root.get_sub_module("child").unwrap().get_var_value::<INT>("value"), Some(42));
}

/// Verifies: RHAI-MOD-005
#[test]
fn module_build_index_marks_module_indexed() {
    let mut module = Module::new();
    module.set_var("answer", 42 as INT);
    module.build_index();
    assert!(module.is_indexed());
}

/// Verifies: RHAI-RES-002
#[test]
fn static_module_resolver_projects_inserted_paths() {
    let mut resolver = StaticModuleResolver::new();
    let mut module = Module::new();
    module.set_var("answer", 42 as INT);
    resolver.insert("math", module);
    assert!(resolver.contains_path("math"));
    assert_eq!(resolver.len(), 1);
    assert_eq!(resolver.paths().collect::<Vec<_>>(), vec!["math"]);
}

/// Verifies: RHAI-RES-002
#[test]
fn static_module_resolver_remove_updates_map() {
    let mut resolver = StaticModuleResolver::new();
    resolver.insert("math", Module::new());
    assert!(resolver.remove("math").is_some());
    assert!(resolver.is_empty());
}

/// Verifies: RHAI-RES-001
#[test]
fn dummy_module_resolver_rejects_paths() {
    let resolver = DummyModuleResolver::new();
    let engine = Engine::new();
    let err = resolver.resolve(&engine, None, "missing", rhai::Position::NONE).unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorModuleNotFound(..)));
}

/// Verifies: RHAI-NATIVE-001
#[test]
fn registered_function_is_visible_to_eval() {
    let mut engine = Engine::new();
    engine.register_fn("add_one", |x: INT| x + 1);
    assert_eq!(engine.eval::<INT>("add_one(41)").unwrap(), 42);
}

/// Verifies: RHAI-NATIVE-003, RHAI-NATIVE-004
#[test]
fn registered_type_name_is_visible_to_type_of() {
    #[derive(Clone)]
    struct Marker;
    let mut engine = Engine::new();
    engine.register_type_with_name::<Marker>("MarkerName");
    engine.register_fn("marker", || Marker);
    assert_eq!(engine.eval::<String>("type_of(marker())").unwrap(), "MarkerName");
}

/// Verifies: RHAI-GRAIN-001, RHAI-GRAIN-002
#[test]
fn grain_compiler_produces_program() {
    let engine = Engine::new();
    let ast = engine.compile("40 + 2").unwrap();
    let program = Compiler::new().compile(&ast);
    assert!(program.max_stack() > 0);
}

/// Verifies: RHAI-GRAIN-008, RHAI-GRAIN-009
#[test]
fn grain_vm_eval_returns_dynamic_value() {
    let engine = Engine::new();
    let ast = engine.compile("40 + 2").unwrap();
    let program = Compiler::new().compile(&ast);
    let value = Vm::new(&engine).eval(&program).unwrap();
    assert_eq!(value.as_int().unwrap(), 42);
}

/// Verifies: RHAI-GRAIN-004, RHAI-GRAIN-005, RHAI-GRAIN-007
#[test]
fn grain_residual_program_refuses_artifact_write() {
    let engine = Engine::new();
    let ast = engine.compile("eval(\"40 + 2\")").unwrap();
    let program = Compiler::new().compile(&ast);
    assert!(program.residual_count() > 0);
    assert!(matches!(program.write(), Err(WriteError::HasResiduals { .. })));
}

/// Verifies: RHAI-GRAIN-006
#[test]
fn grain_program_write_and_read_round_trip_bytes() {
    let engine = Engine::new();
    let ast = engine.compile("let x = 40; x + 2").unwrap();
    let program = Compiler::new().compile(&ast);
    let bytes = program.write().unwrap();
    let loaded = Program::read(&bytes).unwrap();
    let value = Vm::new(&engine).eval(&loaded).unwrap();
    assert_eq!(value.as_int().unwrap(), 42);
}
