mod generated {
use evalexpr::*;

#[test]
fn generated_math_consts_context_default_bindings() {
    let context: HashMapContext<DefaultNumericTypes> = math_consts_context!().unwrap();
    assert_eq!(
        context.get_value("PI"),
        Some(&Value::Float(core::f64::consts::PI))
    );
    assert_eq!(
        context.get_value("LN_10"),
        Some(&Value::Float(core::f64::consts::LN_10))
    );
    assert_eq!(
        context.get_value("FRAC_PI_4"),
        Some(&Value::Float(core::f64::consts::FRAC_PI_4))
    );
    let product = eval_float_with_context("SQRT_2 * SQRT_2", &context).unwrap();
    assert!((product - 2.0).abs() < 1e-12);
}

#[test]
fn generated_math_consts_context_selected_names_only() {
    let context: HashMapContext<DefaultNumericTypes> = math_consts_context!(E, LN_2).unwrap();
    assert_eq!(
        context.get_value("E"),
        Some(&Value::Float(core::f64::consts::E))
    );
    assert_eq!(
        context.get_value("LN_2"),
        Some(&Value::Float(core::f64::consts::LN_2))
    );
    assert_eq!(context.get_value("PI"), None);
    assert_eq!(
        eval_with_context("PI", &context),
        Err(EvalexprError::VariableIdentifierNotFound("PI".into()))
    );
}

#[test]
fn generated_cross_view_agreement_on_one_expression() {
    let source = "7 * 6 - 13";
    let direct = eval(source).unwrap();
    assert_eq!(direct, Value::Int(29));
    assert_eq!(eval_int(source), Ok(29));

    let tree = build_operator_tree::<DefaultNumericTypes>(source).unwrap();
    assert_eq!(tree.eval().unwrap(), direct);
    assert_eq!(tree.eval_int(), Ok(29));

    let context = HashMapContext::<DefaultNumericTypes>::new();
    assert_eq!(eval_with_context(source, &context).unwrap(), direct);
    assert_eq!(tree.eval_with_context(&context).unwrap(), direct);
}

#[test]
fn generated_precompiled_tree_recomputes_under_mutated_context() {
    let tree = build_operator_tree::<DefaultNumericTypes>("a * 3 + b").unwrap();
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    context.set_value("a".into(), Value::Int(4)).unwrap();
    context.set_value("b".into(), Value::Int(9)).unwrap();
    assert_eq!(tree.eval_with_context(&context), Ok(Value::Int(21)));
    assert_eq!(tree.eval_int_with_context(&context), Ok(21));

    context.set_value("a".into(), Value::Int(11)).unwrap();
    assert_eq!(tree.eval_with_context(&context), Ok(Value::Int(42)));

    eval_with_context_mut("b = a - 2", &mut context).unwrap();
    assert_eq!(context.get_value("b"), Some(&Value::Int(9)));
    assert_eq!(tree.eval_with_context(&context), Ok(Value::Int(42)));
}

#[test]
fn generated_typed_shortcut_error_agrees_with_tree_shortcut() {
    let direct = eval_int("4.25");
    assert_eq!(
        direct,
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(4.25)
        })
    );
    let tree = build_operator_tree::<DefaultNumericTypes>("4.25").unwrap();
    assert_eq!(tree.eval_int(), direct);
}
}
