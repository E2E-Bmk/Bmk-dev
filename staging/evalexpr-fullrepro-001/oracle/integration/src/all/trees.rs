mod trees {
use evalexpr::*;
#[allow(unused_imports)]
use std::convert::TryFrom;

#[test]
fn test_iterators() {
    let tree =
        build_operator_tree::<DefaultNumericTypes>("writevar = 5 + 3 + fun(4) + var").unwrap();
    let mut iter = tree.iter_identifiers();
    assert_eq!(iter.next(), Some("writevar"));
    assert_eq!(iter.next(), Some("fun"));
    assert_eq!(iter.next(), Some("var"));
    assert_eq!(iter.next(), None);

    let mut iter = tree.iter_variable_identifiers();
    assert_eq!(iter.next(), Some("writevar"));
    assert_eq!(iter.next(), Some("var"));
    assert_eq!(iter.next(), None);

    let mut iter = tree.iter_read_variable_identifiers();
    assert_eq!(iter.next(), Some("var"));
    assert_eq!(iter.next(), None);

    let mut iter = tree.iter_write_variable_identifiers();
    assert_eq!(iter.next(), Some("writevar"));
    assert_eq!(iter.next(), None);

    let mut iter = tree.iter_function_identifiers();
    assert_eq!(iter.next(), Some("fun"));
    assert_eq!(iter.next(), None);
}

#[test]
fn test_node_mutable_access() {
    let mut node = build_operator_tree::<DefaultNumericTypes>("5").unwrap();
    assert_eq!(node.children_mut().len(), 1);
    assert!(matches!(*node.operator_mut(), Operator::RootNode));
}

#[test]
fn assignment_lhs_is_identifier() {
    let tree = build_operator_tree::<DefaultNumericTypes>("a = 1").unwrap();
    assert_eq!(
        tree.iter_write_variable_identifiers().collect::<Vec<_>>(),
        vec!["a"]
    );
    assert_eq!(tree.iter_read_variable_identifiers().next(), None);

    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    tree.eval_with_context_mut(&mut context).unwrap();
    assert_eq!(context.get_value("a"), Some(&Value::Int(1)));
}

#[test]
fn test_long_expression_i89() {
    let tree = build_operator_tree::<DefaultNumericTypes>(
        "x*0.2*5/4+x*2*4*1*1*1*1*1*1*1+7*math::sin(y)-z/math::sin(3.0/2.0/(1-x*4*1*1*1*1))",
    )
    .unwrap();
    let x = 0.0;
    let y: <DefaultNumericTypes as EvalexprNumericTypes>::Float = 3.0;
    let z = 4.0;
    let context = context_map! {
        "x" => float 0.0,
        "y" => float 3.0,
        "z" => float 4.0
    }
    .unwrap();
    let expected = x * 0.2 * 5.0 / 4.0
        + x * 2.0 * 4.0 * 1.0 * 1.0 * 1.0 * 1.0 * 1.0 * 1.0 * 1.0
        + 7.0 * y.sin()
        - z / (3.0 / 2.0 / (1.0 - x * 4.0 * 1.0 * 1.0 * 1.0 * 1.0)).sin();
    let actual: <DefaultNumericTypes as EvalexprNumericTypes>::Float =
        tree.eval_float_with_context(&context).unwrap();
    assert!(
        (expected - actual).abs() < expected.abs().min(actual.abs()) * 1e-12,
        "expected: {}, actual: {}",
        expected,
        actual
    );
}
}
