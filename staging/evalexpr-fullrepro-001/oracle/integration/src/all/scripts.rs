mod scripts {
use evalexpr::*;
#[allow(unused_imports)]
use std::convert::TryFrom;

#[test]
fn test_assignment() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    assert_eq!(
        eval_empty_with_context_mut("int = 3", &mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        eval_empty_with_context_mut("float = 2.0", &mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        eval_empty_with_context_mut("tuple = (1,1)", &mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        eval_empty_with_context_mut("empty = ()", &mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        eval_empty_with_context_mut("boolean = false", &mut context),
        Ok(EMPTY_VALUE)
    );

    assert_eq!(eval_int_with_context("int", &context), Ok(3));
    assert_eq!(eval_float_with_context("float", &context), Ok(2.0));
    assert_eq!(
        eval_tuple_with_context("tuple", &context),
        Ok(vec![Value::from_int(1), Value::from_int(1)])
    );
    assert_eq!(eval_empty_with_context("empty", &context), Ok(EMPTY_VALUE));
    assert_eq!(eval_boolean_with_context("boolean", &context), Ok(false));

    assert_eq!(
        eval_empty_with_context_mut("b = a = 5", &mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(eval_empty_with_context("b", &context), Ok(EMPTY_VALUE));
}

#[test]
fn test_expression_chaining() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    assert_eq!(
        eval_int_with_context_mut("a = 5; a = a + 2; a", &mut context),
        Ok(7)
    );
}

#[test]
fn test_strings() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    assert_eq!(eval("\"string\""), Ok(Value::from("string")));
    assert_eq!(
        eval_with_context_mut("a = \"a string\"", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_boolean_with_context("a == \"a string\"", &context),
        Ok(true)
    );
    assert_eq!(eval("\"a\" + \"b\""), Ok(Value::from("ab")));
    assert_eq!(eval("\"a\" > \"b\""), Ok(Value::from(false)));
    assert_eq!(eval("\"a\" < \"b\""), Ok(Value::from(true)));
    assert_eq!(eval("\"a\" >= \"b\""), Ok(Value::from(false)));
    assert_eq!(eval("\"a\" <= \"b\""), Ok(Value::from(true)));
    assert_eq!(eval("\"a\" >= \"a\""), Ok(Value::from(true)));
    assert_eq!(eval("\"a\" <= \"a\""), Ok(Value::from(true)));
    assert_eq!(eval("\"xa\" > \"xb\""), Ok(Value::from(false)));
    assert_eq!(eval("\"xa\" < \"xb\""), Ok(Value::from(true)));
    assert_eq!(eval("\"{}\" != \"{}\""), Ok(Value::from(false)));
    assert_eq!(eval("\"{}\" == \"{}\""), Ok(Value::from(true)));
}

#[test]
fn test_operator_assignments() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    assert_eq!(eval_empty_with_context_mut("a = 5", &mut context), Ok(()));
    assert_eq!(eval_empty_with_context_mut("a += 5", &mut context), Ok(()));
    assert_eq!(eval_empty_with_context_mut("a -= 5", &mut context), Ok(()));
    assert_eq!(eval_empty_with_context_mut("a *= 5", &mut context), Ok(()));
    assert_eq!(eval_empty_with_context_mut("b = 5.0", &mut context), Ok(()));
    assert_eq!(eval_empty_with_context_mut("b /= 5", &mut context), Ok(()));
    assert_eq!(eval_empty_with_context_mut("b %= 5", &mut context), Ok(()));
    assert_eq!(eval_empty_with_context_mut("b ^= 5", &mut context), Ok(()));
    assert_eq!(
        eval_empty_with_context_mut("c = true", &mut context),
        Ok(())
    );
    assert_eq!(
        eval_empty_with_context_mut("c &&= false", &mut context),
        Ok(())
    );
    assert_eq!(
        eval_empty_with_context_mut("c ||= true", &mut context),
        Ok(())
    );

    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    assert_eq!(eval_int_with_context_mut("a = 5; a", &mut context), Ok(5));
    assert_eq!(eval_int_with_context_mut("a += 3; a", &mut context), Ok(8));
    assert_eq!(eval_int_with_context_mut("a -= 5; a", &mut context), Ok(3));
    assert_eq!(eval_int_with_context_mut("a *= 5; a", &mut context), Ok(15));
    assert_eq!(
        eval_float_with_context_mut("b = 5.0; b", &mut context),
        Ok(5.0)
    );
    assert_eq!(
        eval_float_with_context_mut("b /= 2; b", &mut context),
        Ok(2.5)
    );
    assert_eq!(
        eval_float_with_context_mut("b %= 2; b", &mut context),
        Ok(0.5)
    );
    assert_eq!(
        eval_float_with_context_mut("b ^= 2; b", &mut context),
        Ok(0.25)
    );
    assert_eq!(
        eval_boolean_with_context_mut("c = true; c", &mut context),
        Ok(true)
    );
    assert_eq!(
        eval_boolean_with_context_mut("c &&= false; c", &mut context),
        Ok(false)
    );
    assert_eq!(
        eval_boolean_with_context_mut("c ||= true; c", &mut context),
        Ok(true)
    );
}

#[test]
fn test_variable_assignment_and_iteration() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    eval_with_context_mut("a = 5; b = 5.0", &mut context).unwrap();

    let mut variables: Vec<_> = context.iter_variables().collect();
    variables.sort_unstable_by(|(name_a, _), (name_b, _)| name_a.cmp(name_b));
    assert_eq!(
        variables,
        vec![
            ("a".to_string(), Value::from_int(5)),
            ("b".to_string(), Value::from_float(5.0))
        ],
    );

    let mut variables: Vec<_> = context.iter_variable_names().collect();
    variables.sort_unstable();
    assert_eq!(variables, vec!["a".to_string(), "b".to_string()],);
}
}
