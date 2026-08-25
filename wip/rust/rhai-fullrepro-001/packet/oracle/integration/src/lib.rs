use rhai::grain::{Compiler, Program, Vm};
use rhai::module_resolvers::StaticModuleResolver;
use rhai::{eval_file, run_file, CallFnOptions, Dynamic, Engine, EvalAltResult, Module, Scope, INT};
use std::fs;

fn temp_script(name: &str, text: &str) -> std::path::PathBuf {
    let path = std::env::temp_dir().join(format!("rhai_oracle_{}_{}.rhai", name, std::process::id()));
    fs::write(&path, text).unwrap();
    path
}

/// Verifies: RHAI-EVAL-005, RHAI-INV-002
#[test]
fn eval_with_scope_returns_value_and_preserves_mutation() {
    let engine = Engine::new();
    let mut scope = Scope::new();
    scope.push("x", 40 as INT);
    let value: INT = engine.eval_with_scope(&mut scope, "x += 2; x").unwrap();
    assert_eq!(value, 42);
    assert_eq!(scope.get_value::<INT>("x"), Some(42));
}

/// Verifies: RHAI-EVAL-006, RHAI-INV-002
#[test]
fn run_with_scope_preserves_side_effects() {
    let engine = Engine::new();
    let mut scope = Scope::new();
    scope.push("x", 1 as INT);
    engine.run_with_scope(&mut scope, "x = x + 41;").unwrap();
    assert_eq!(scope.get_value::<INT>("x"), Some(42));
}

/// Verifies: RHAI-COMP-001, RHAI-INV-001
#[test]
fn compiled_ast_matches_text_evaluation() {
    let engine = Engine::new();
    let source = "let x = 6; x * 7";
    let ast = engine.compile(source).unwrap();
    let text = engine.eval::<INT>(source).unwrap();
    let compiled = engine.eval_ast::<INT>(&ast).unwrap();
    assert_eq!(text, 42);
    assert_eq!(compiled, text);
}

/// Verifies: RHAI-COMP-003, RHAI-INV-003
#[test]
fn compile_with_constant_scope_rejects_assignment_to_constant() {
    let engine = Engine::new();
    let mut scope = Scope::new();
    scope.push_constant("answer", 42 as INT);
    let ast = engine.compile_with_scope(&scope, "answer = 0").unwrap();
    let err = engine.run_ast_with_scope(&mut scope, &ast).unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorAssignmentToConstant(..)));
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-CALL-001
#[test]
fn call_fn_loads_ast_and_returns_converted_value() {
    let engine = Engine::new();
    let ast = engine.compile("fn double(x) { x * 2 }").unwrap();
    let value: INT = engine.call_fn(&mut Scope::new(), &ast, "double", (21 as INT,)).unwrap();
    assert_eq!(value, 42);
}

/// Verifies: RHAI-CALL-001
#[test]
fn call_fn_rewinds_temporary_declarations_by_default() {
    let engine = Engine::new();
    let ast = engine.compile("fn make() { let hidden = 42; hidden }").unwrap();
    let mut scope = Scope::new();
    assert_eq!(engine.call_fn::<INT>(&mut scope, &ast, "make", ()).unwrap(), 42);
    assert!(!scope.contains("hidden"));
}

/// Verifies: RHAI-CALL-002
#[test]
fn call_fn_option_can_preserve_declarations() {
    let engine = Engine::new();
    let ast = engine.compile("fn make() { let hidden = 42; hidden }").unwrap();
    let mut scope = Scope::new();
    let options = CallFnOptions::new().rewind_scope(false);
    assert_eq!(engine.call_fn_with_options::<INT>(options, &mut scope, &ast, "make", ()).unwrap(), 42);
    assert_eq!(scope.get_value::<INT>("hidden"), Some(42));
}

/// Verifies: RHAI-CALL-002
#[test]
fn call_fn_option_searches_native_namespace() {
    let mut engine = Engine::new();
    engine.register_fn("host_add", |x: INT, y: INT| x + y);
    let ast = engine.compile("fn placeholder() { 0 }").unwrap();
    let mut scope = Scope::new();
    let options = CallFnOptions::new().in_all_namespaces(true);
    let value: INT = engine.call_fn_with_options(options, &mut scope, &ast, "host_add", (20 as INT, 22 as INT)).unwrap();
    assert_eq!(value, 42);
}

/// Verifies: RHAI-NATIVE-001, RHAI-INV-004
#[test]
fn registered_native_function_works_in_text_and_ast() {
    let mut engine = Engine::new();
    engine.register_fn("triple", |x: INT| x * 3);
    let source = "triple(14)";
    let ast = engine.compile(source).unwrap();
    assert_eq!(engine.eval::<INT>(source).unwrap(), 42);
    assert_eq!(engine.eval_ast::<INT>(&ast).unwrap(), 42);
}

/// Verifies: RHAI-NATIVE-002
#[test]
fn raw_function_can_read_dynamic_arguments() {
    let mut engine = Engine::new();
    engine.register_raw_fn("sum_raw", [std::any::TypeId::of::<INT>(), std::any::TypeId::of::<INT>()], |_, args| {
        let b = args[1].as_int().unwrap();
        let a = args[0].as_int().unwrap();
        Ok(Dynamic::from(a + b))
    });
    assert_eq!(engine.eval::<INT>("sum_raw(20, 22)").unwrap(), 42);
}

/// Verifies: RHAI-MOD-002, RHAI-MOD-007, RHAI-INV-005
#[test]
fn static_module_exposes_qualified_variable() {
    let mut module = Module::new();
    module.set_var("answer", 42 as INT);
    module.build_index();
    let mut engine = Engine::new();
    engine.register_static_module("facts", module.into());
    assert_eq!(engine.eval::<INT>("facts::answer").unwrap(), 42);
}

/// Verifies: RHAI-MOD-004, RHAI-MOD-007, RHAI-INV-005
#[test]
fn static_module_exposes_nested_submodule_variable() {
    let mut child = Module::new();
    child.set_var("answer", 42 as INT);
    let mut root = Module::new();
    root.set_sub_module("child", child);
    root.build_index();
    let mut engine = Engine::new();
    engine.register_static_module("facts", root.into());
    assert_eq!(engine.eval::<INT>("facts::child::answer").unwrap(), 42);
}

/// Verifies: RHAI-RES-002, RHAI-INV-005
#[test]
fn resolver_import_exposes_module_variable() {
    let mut module = Module::new();
    module.set_var("answer", 42 as INT);
    let mut resolver = StaticModuleResolver::new();
    resolver.insert("facts", module);
    let mut engine = Engine::new();
    engine.set_module_resolver(resolver);
    assert_eq!(engine.eval::<INT>(r#"import "facts" as f; f::answer"#).unwrap(), 42);
}

/// Verifies: RHAI-COMP-005, RHAI-INV-005
#[test]
fn self_contained_ast_keeps_resolved_module_after_resolver_change() {
    let mut module = Module::new();
    module.set_var("answer", 42 as INT);
    let mut resolver = StaticModuleResolver::new();
    resolver.insert("facts", module);
    let mut engine = Engine::new();
    engine.set_module_resolver(resolver);
    let scope = Scope::new();
    let ast = engine.compile_into_self_contained(&scope, r#"import "facts" as f; f::answer"#).unwrap();
    engine.set_module_resolver(StaticModuleResolver::new());
    assert_eq!(engine.eval_ast::<INT>(&ast).unwrap(), 42);
}

/// Verifies: RHAI-FILE-001
#[test]
fn eval_file_reads_script_and_returns_value() {
    let path = temp_script("eval", "40 + 2");
    assert_eq!(eval_file::<INT>(&path).unwrap(), 42);
    let _ = fs::remove_file(path);
}

/// Verifies: RHAI-FILE-001
#[test]
fn run_file_executes_side_effect_script() {
    let path = temp_script("run", "40 + 2");
    assert!(run_file(&path).is_ok());
    assert_eq!(eval_file::<INT>(&path).unwrap(), 42);
    let _ = fs::remove_file(path);
}

/// Verifies: RHAI-FILE-001
#[test]
fn engine_compile_file_sets_executable_ast() {
    let path = temp_script("compile", "40 + 2");
    let engine = Engine::new();
    let ast = engine.compile_file(path.clone()).unwrap();
    assert_eq!(engine.eval_ast::<INT>(&ast).unwrap(), 42);
    let _ = fs::remove_file(path);
}

/// Verifies: RHAI-FILE-002
#[test]
fn missing_file_reports_system_error() {
    let engine = Engine::new();
    let err = engine.eval_file::<INT>(std::path::PathBuf::from("/tmp/rhai_oracle_missing_no_such_file.rhai")).unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorSystem(..)));
}

/// Verifies: RHAI-INV-001, RHAI-GRAIN-003
#[test]
fn grain_program_matches_ast_evaluation_result() {
    let engine = Engine::new();
    let mut ast_scope = Scope::new();
    let mut vm_scope = Scope::new();
    ast_scope.push("x", 40 as INT);
    vm_scope.push("x", 40 as INT);
    let ast = engine.compile("x += 2; x").unwrap();
    let expected: INT = engine.eval_ast_with_scope(&mut ast_scope, &ast).unwrap();
    let program = Compiler::new().compile(&ast);
    let actual = Vm::new(&engine).eval_with_scope(&mut vm_scope, &program).unwrap();
    assert_eq!(expected, 42);
    assert_eq!(actual.as_int().unwrap(), expected);
    assert_eq!(vm_scope.get_value::<INT>("x"), ast_scope.get_value::<INT>("x"));
}

/// Verifies: RHAI-GRAIN-006, RHAI-INV-007
#[test]
fn grain_written_program_reads_back_with_same_result() {
    let engine = Engine::new();
    let ast = engine.compile("let x = 20; x * 2 + 2").unwrap();
    let program = Compiler::new().compile(&ast);
    let bytes = program.write().unwrap();
    let loaded = Program::read(&bytes).unwrap();
    assert_eq!(Vm::new(&engine).eval(&program).unwrap().as_int().unwrap(), 42);
    assert_eq!(Vm::new(&engine).eval(&loaded).unwrap().as_int().unwrap(), 42);
}

/// Verifies: RHAI-NATIVE-004, RHAI-INV-006
#[test]
fn custom_type_display_matches_text_ast_and_grain_views() {
    #[derive(Clone)]
    struct Marker;

    let mut engine = Engine::new();
    engine.register_type_with_name::<Marker>("MarkerName");
    engine.register_fn("marker", || Marker);

    let source = "type_of(marker())";
    let ast = engine.compile(source).unwrap();
    let program = Compiler::new().compile(&ast);

    assert_eq!(engine.eval::<String>(source).unwrap(), "MarkerName");
    assert_eq!(engine.eval_ast::<String>(&ast).unwrap(), "MarkerName");
    assert_eq!(Vm::new(&engine).eval(&program).unwrap().into_string().unwrap(), "MarkerName");
}

/// Verifies: RHAI-NATIVE-004, RHAI-GRAIN-006, RHAI-INV-006, RHAI-INV-007
#[test]
fn custom_type_display_survives_program_artifact_read() {
    #[derive(Clone)]
    struct ArtifactMarker;

    let mut engine = Engine::new();
    engine.register_type_with_name::<ArtifactMarker>("ArtifactMarkerName");
    engine.register_fn("artifact_marker", || ArtifactMarker);

    let ast = engine.compile("type_of(artifact_marker())").unwrap();
    let program = Compiler::new().compile(&ast);
    let bytes = program.write().unwrap();
    let loaded = Program::read(&bytes).unwrap();

    assert_eq!(Vm::new(&engine).eval(&program).unwrap().into_string().unwrap(), "ArtifactMarkerName");
    assert_eq!(Vm::new(&engine).eval(&loaded).unwrap().into_string().unwrap(), "ArtifactMarkerName");
}

/// Verifies: RHAI-GRAIN-006, RHAI-GRAIN-009, RHAI-INV-007
#[test]
fn grain_read_program_preserves_scope_mutations() {
    let engine = Engine::new();
    let ast = engine.compile("x += 2; x").unwrap();
    let program = Compiler::new().compile(&ast);
    let bytes = program.write().unwrap();
    let loaded = Program::read(&bytes).unwrap();

    let mut original_scope = Scope::new();
    original_scope.push("x", 40 as INT);
    let mut loaded_scope = Scope::new();
    loaded_scope.push("x", 40 as INT);

    assert_eq!(Vm::new(&engine).eval_with_scope(&mut original_scope, &program).unwrap().as_int().unwrap(), 42);
    assert_eq!(Vm::new(&engine).eval_with_scope(&mut loaded_scope, &loaded).unwrap().as_int().unwrap(), 42);
    assert_eq!(loaded_scope.get_value::<INT>("x"), original_scope.get_value::<INT>("x"));
}

/// Verifies: RHAI-GRAIN-006, RHAI-GRAIN-009, RHAI-ERR-001, RHAI-INV-007
#[test]
fn grain_read_program_preserves_public_error_family() {
    let engine = Engine::new();
    let ast = engine.compile("40 / 0").unwrap();
    let program = Compiler::new().compile(&ast);
    let bytes = program.write().unwrap();
    let loaded = Program::read(&bytes).unwrap();

    let original = Vm::new(&engine).eval(&program).unwrap_err();
    let read_back = Vm::new(&engine).eval(&loaded).unwrap_err();

    assert!(matches!(*original, EvalAltResult::ErrorArithmetic(..)));
    assert!(matches!(*read_back, EvalAltResult::ErrorArithmetic(..)));
}

/// Verifies: RHAI-GRAIN-009, RHAI-INV-008
#[test]
fn stripped_program_fault_trace_resolves_with_sidecar() {
    let engine = Engine::new();
    let ast = engine.compile("let denominator = 0;\n40 / denominator").unwrap();
    let program = Compiler::new().compile(&ast);
    let stripped = program.write_stripped().unwrap();
    let loaded = Program::read(&stripped.artifact).unwrap();

    let mut vm = Vm::new(&engine);
    let err = vm.eval(&loaded).unwrap_err();
    let trace = vm.fault_trace();
    let sites = stripped.sidecar.resolve(&trace);

    assert!(err.position().is_none());
    assert!(!trace.is_empty());
    assert!(sites.iter().any(|site| site.is_some()));
}

/// Verifies: RHAI-GRAIN-009, RHAI-INV-008
#[test]
fn stripped_program_accepts_own_sidecar_and_rejects_unrelated_sidecar() {
    let engine = Engine::new();
    let first = Compiler::new().compile(&engine.compile("let a = 1;\nlet b = 2;\na + b").unwrap());
    let second = Compiler::new().compile(&engine.compile("let a = 1;\n\nlet b = 2;\na + b").unwrap());

    let first_stripped = first.write_stripped().unwrap();
    let second_stripped = second.write_stripped().unwrap();
    assert_ne!(first_stripped.sidecar.debug_id, second_stripped.sidecar.debug_id);

    let mut reattached = Program::read(&first_stripped.artifact).unwrap();
    reattached.attach_positions(&first_stripped.sidecar).unwrap();
    assert!(Program::read(&first_stripped.artifact).is_ok());

    let mut mismatched = Program::read(&first_stripped.artifact).unwrap();
    assert!(mismatched.attach_positions(&second_stripped.sidecar).is_err());
}

/// Verifies: RHAI-GRAIN-009, RHAI-CALL-001
#[test]
fn grain_vm_call_fn_matches_engine_call_fn() {
    let engine = Engine::new();
    let ast = engine.compile("fn double(x) { x * 2 }").unwrap();
    let program = Compiler::new().compile(&ast);
    let expected: INT = engine.call_fn(&mut Scope::new(), &ast, "double", (21 as INT,)).unwrap();
    let actual: INT = Vm::new(&engine).call_fn(&mut Scope::new(), &program, "double", (21 as INT,)).unwrap();
    assert_eq!(expected, 42);
    assert_eq!(actual, expected);
}

/// Verifies: RHAI-GRAIN-003, RHAI-INV-003
#[test]
fn grain_assignment_to_constant_matches_engine_error_family() {
    let engine = Engine::new();
    let ast = engine.compile("answer = 0").unwrap();
    let program = Compiler::new().compile(&ast);
    let mut scope = Scope::new();
    scope.push_constant("answer", 42 as INT);
    let err = Vm::new(&engine).run_with_scope(&mut scope, &program).unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorAssignmentToConstant(..)));
    assert_eq!(scope.get_value::<INT>("answer"), Some(42));
}

/// Verifies: RHAI-GRAIN-005, RHAI-GRAIN-009
#[test]
fn grain_residual_eval_preserves_runtime_value() {
    let engine = Engine::new();
    let ast = engine.compile("eval(\"40 + 2\")").unwrap();
    let program = Compiler::new().compile(&ast);
    assert!(program.residual_count() > 0);
    assert_eq!(Vm::new(&engine).eval(&program).unwrap().as_int().unwrap(), 42);
}

/// Verifies: RHAI-INV-004, RHAI-GRAIN-003
#[test]
fn grain_uses_registered_native_function() {
    let mut engine = Engine::new();
    engine.register_fn("add", |x: INT, y: INT| x + y);
    let ast = engine.compile("add(20, 22)").unwrap();
    let program = Compiler::new().compile(&ast);
    assert_eq!(Vm::new(&engine).eval(&program).unwrap().as_int().unwrap(), 42);
}

/// Verifies: RHAI-INV-002, RHAI-GRAIN-009
#[test]
fn repeated_evaluations_share_scope_state() {
    let engine = Engine::new();
    let ast = engine.compile("x += 1; x").unwrap();
    let program = Compiler::new().compile(&ast);
    let mut scope = Scope::new();
    scope.push("x", 40 as INT);
    assert_eq!(Vm::new(&engine).eval_with_scope(&mut scope, &program).unwrap().as_int().unwrap(), 41);
    assert_eq!(engine.eval_ast_with_scope::<INT>(&mut scope, &ast).unwrap(), 42);
    assert_eq!(scope.get_value::<INT>("x"), Some(42));
}

/// Verifies: RHAI-COMP-004, RHAI-INV-002
#[test]
fn concatenated_script_segments_run_with_scope() {
    let engine = Engine::new();
    let mut scope = Scope::new();
    scope.push("x", 10 as INT);
    let ast = engine.compile_scripts_with_scope(&scope, ["x += 11;", "x *= 2;", "x"]).unwrap();
    assert_eq!(engine.eval_ast_with_scope::<INT>(&mut scope, &ast).unwrap(), 42);
    assert_eq!(scope.get_value::<INT>("x"), Some(42));
}

/// Verifies: RHAI-EVAL-007, RHAI-CALL-001
#[test]
fn call_fn_missing_function_reports_public_error() {
    let engine = Engine::new();
    let ast = engine.compile("fn present() { 42 }").unwrap();
    let err = engine.call_fn::<INT>(&mut Scope::new(), &ast, "missing", ()).unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorFunctionNotFound(..)));
}

/// Verifies: RHAI-EVAL-007, RHAI-INV-004
#[test]
fn missing_registered_function_reports_public_error() {
    let engine = Engine::new();
    let err = engine.eval::<INT>("missing_fn(1)").unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorFunctionNotFound(..)));
}

/// Verifies: RHAI-EVAL-007, RHAI-INV-005
#[test]
fn missing_module_reports_public_error() {
    let engine = Engine::new();
    let err = engine.eval::<INT>(r#"import "absent" as a; a::x"#).unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorModuleNotFound(..)));
}

/// Verifies: RHAI-EVAL-007
#[test]
fn missing_variable_reports_public_error() {
    let engine = Engine::new();
    let err = engine.eval::<INT>("unknown_value + 1").unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorVariableNotFound(..)));
}

/// Verifies: RHAI-EVAL-007
#[test]
fn wrong_runtime_operand_reports_data_type_error() {
    let engine = Engine::new();
    let err = engine.eval::<INT>(r#""not a number" - 1"#).unwrap_err();
    assert!(matches!(*err, EvalAltResult::ErrorMismatchDataType(..) | EvalAltResult::ErrorFunctionNotFound(..)));
}

/// Verifies: RHAI-MOD-002, RHAI-MOD-004
#[test]
fn module_merge_preserves_missing_receiver_entries() {
    let mut receiver = Module::new();
    receiver.set_var("kept", 40 as INT);
    let mut donor = Module::new();
    donor.set_var("added", 2 as INT);
    receiver.fill_with(&donor);
    assert_eq!(receiver.get_var_value::<INT>("kept"), Some(40));
    assert_eq!(receiver.get_var_value::<INT>("added"), Some(2));
}
