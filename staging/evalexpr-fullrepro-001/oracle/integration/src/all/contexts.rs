mod contexts {
use evalexpr::{error::*, *};
#[allow(unused_imports)]
use std::convert::TryFrom;

#[test]
fn test_with_context() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    context
        .set_value("tr".into(), Value::Boolean(true))
        .unwrap();
    context
        .set_value("fa".into(), Value::Boolean(false))
        .unwrap();
    context.set_value("five".into(), Value::Int(5)).unwrap();
    context.set_value("six".into(), Value::Int(6)).unwrap();
    context.set_value("half".into(), Value::Float(0.5)).unwrap();
    context.set_value("zero".into(), Value::Int(0)).unwrap();

    assert_eq!(eval_with_context("tr", &context), Ok(Value::Boolean(true)));
    assert_eq!(eval_with_context("fa", &context), Ok(Value::Boolean(false)));
    assert_eq!(
        eval_with_context("tr && false", &context),
        Ok(Value::Boolean(false))
    );
    assert_eq!(
        eval_with_context("five + six", &context),
        Ok(Value::Int(11))
    );
    assert_eq!(
        eval_with_context("five * half", &context),
        Ok(Value::Float(2.5))
    );
    assert_eq!(
        eval_with_context("five < six && true", &context),
        Ok(Value::Boolean(true))
    );

    assert_eq!(context.remove_value("half"), Ok(Some(Value::Float(0.5))));
    assert_eq!(context.remove_value("zero"), Ok(Some(Value::Int(0))));
    assert_eq!(context.remove_value("zero"), Ok(None));
    assert_eq!(
        eval_with_context("zero", &context),
        Err(EvalexprError::VariableIdentifierNotFound(
            "zero".to_string()
        ))
    );
}

#[test]
fn test_empty_context() {
    let mut context = EmptyContext::<DefaultNumericTypes>::default();
    assert_eq!(context.get_value("abc"), None);
    assert_eq!(
        context.call_function("abc", &Value::Empty),
        Err(EvalexprError::FunctionIdentifierNotFound("abc".to_owned()))
    );
    assert_eq!(
        eval_with_context("max(1,3)", &context),
        Err(EvalexprError::FunctionIdentifierNotFound(String::from(
            "max"
        )))
    );
    assert_eq!(context.set_builtin_functions_disabled(true), Ok(()));
    assert_eq!(
        context.set_builtin_functions_disabled(false),
        Err(EvalexprError::BuiltinFunctionsCannotBeEnabled)
    )
}

#[test]
fn test_empty_context_with_builtin_functions() {
    let mut context = EmptyContextWithBuiltinFunctions::<DefaultNumericTypes>::default();
    assert_eq!(context.get_value("abc"), None);
    assert_eq!(
        context.call_function("abc", &Value::Empty),
        Err(EvalexprError::FunctionIdentifierNotFound("abc".to_owned()))
    );
    assert_eq!(eval_with_context("max(1,3)", &context), Ok(Value::Int(3)));
    assert_eq!(context.set_builtin_functions_disabled(false), Ok(()));
    assert_eq!(
        context.set_builtin_functions_disabled(true),
        Err(EvalexprError::BuiltinFunctionsCannotBeDisabled)
    );
}

#[test]
fn test_hashmap_context_type_safety() {
    let mut context: HashMapContext<DefaultNumericTypes> =
        context_map! {"a" => int 5, "b" => float 5.0}.unwrap();
    assert_eq!(
        eval_with_context_mut("a = 4", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_with_context_mut("a = 4.0", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(4.0)
        })
    );
    assert_eq!(
        eval_with_context_mut("a += 4.0", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(8.0)
        })
    );
    assert_eq!(
        eval_with_context_mut("a -= 4.0", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(0.0)
        })
    );
    assert_eq!(
        eval_with_context_mut("a *= 4.0", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(16.0)
        })
    );
    assert_eq!(
        eval_with_context_mut("a /= 4.0", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(1.0)
        })
    );
    assert_eq!(
        eval_with_context_mut("a %= 4.0", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(0.0)
        })
    );
    assert_eq!(
        eval_with_context_mut("a ^= 4.0", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(256.0)
        })
    );

    assert_eq!(
        eval_with_context_mut("b = 4.0", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_with_context_mut("b = 4", &mut context),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        eval_with_context_mut("b += 4", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_with_context_mut("b -= 4", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_with_context_mut("b *= 4", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_with_context_mut("b /= 4", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_with_context_mut("b %= 4", &mut context),
        Ok(Value::Empty)
    );
    assert_eq!(
        eval_with_context_mut("b ^= 4", &mut context),
        Ok(Value::Empty)
    );
}

#[test]
fn test_hashmap_context_clone() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    // this variable is captured by the function
    let three = 3;
    context
        .set_function(
            "mult_3".into(),
            Function::new(move |argument| {
                if let Value::Int(int) = argument {
                    Ok(Value::Int(int * three))
                } else if let Value::Float(float) = argument {
                    Ok(Value::Float(
                        float * three as <DefaultNumericTypes as EvalexprNumericTypes>::Float,
                    ))
                } else {
                    Err(EvalexprError::expected_number(argument.clone()))
                }
            }),
        )
        .unwrap();

    let four = 4;
    context
        .set_function(
            "function_four".into(),
            Function::new(move |_| Ok(Value::Int(four))),
        )
        .unwrap();
    context
        .set_value("variable_five".into(), Value::from_int(5))
        .unwrap();
    let context = context;
    #[allow(clippy::redundant_clone)]
    let cloned_context = context.clone();

    assert_eq!(
        cloned_context.get_value("variable_five"),
        Some(&Value::from_int(5))
    );
    assert_eq!(
        eval_with_context("mult_3 2", &cloned_context),
        Ok(Value::Int(6))
    );
    assert_eq!(
        eval_with_context("mult_3(3)", &cloned_context),
        Ok(Value::Int(9))
    );
    assert_eq!(
        eval_with_context("mult_3(function_four())", &cloned_context),
        Ok(Value::Int(12))
    );
}

#[test]
fn test_clear() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    context.set_value("abc".into(), "def".into()).unwrap();
    assert_eq!(context.get_value("abc"), Some(&("def".into())));
    context.clear_functions();
    assert_eq!(context.get_value("abc"), Some(&("def".into())));
    context.clear_variables();
    assert_eq!(context.get_value("abc"), None);

    context
        .set_function(
            "abc".into(),
            Function::new(|input| Ok(Value::Int(input.as_int()? + 1))),
        )
        .unwrap();
    assert_eq!(
        eval_with_context("abc(5)", &context).unwrap(),
        Value::Int(6)
    );
    context.clear_variables();
    assert_eq!(
        eval_with_context("abc(5)", &context).unwrap(),
        Value::Int(6)
    );
    context.clear_functions();
    assert!(eval_with_context("abc(5)", &context).is_err());

    context
        .set_value("five".into(), Value::from_int(5))
        .unwrap();
    context
        .set_function(
            "abc".into(),
            Function::new(|input| Ok(Value::Int(input.as_int()? + 1))),
        )
        .unwrap();
    assert_eq!(
        eval_with_context("abc(five)", &context).unwrap(),
        Value::Int(6)
    );
    context.clear();
    assert!(context.get_value("five").is_none());
    assert!(eval_with_context("abc(5)", &context).is_err());
}

#[test]
fn test_iter_empty_contexts() {
    assert_eq!(
        EmptyContext::<DefaultNumericTypes>::default()
            .iter_variables()
            .next(),
        None
    );
    assert_eq!(
        EmptyContext::<DefaultNumericTypes>::default()
            .iter_variable_names()
            .next(),
        None
    );
    assert_eq!(
        EmptyContextWithBuiltinFunctions::<DefaultNumericTypes>::default()
            .iter_variables()
            .next(),
        None
    );
    assert_eq!(
        EmptyContextWithBuiltinFunctions::<DefaultNumericTypes>::default()
            .iter_variable_names()
            .next(),
        None
    );
}

#[test]
fn test_empty_context_builtin_functions() {
    assert!(EmptyContext::<DefaultNumericTypes>::default().are_builtin_functions_disabled());
    assert!(
        !EmptyContextWithBuiltinFunctions::<DefaultNumericTypes>::default()
            .are_builtin_functions_disabled()
    );
}

#[test]
fn test_builtin_functions_context() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    // Builtin functions are enabled by default for HashMapContext.
    assert_eq!(
        eval_with_context("max(1,3)", &context),
        Ok(Value::from_int(3))
    );
    // Disabling builtin function in Context.
    context.set_builtin_functions_disabled(true).unwrap();
    // Builtin functions are disabled and using them returns an error.
    assert_eq!(
        eval_with_context("max(1,3)", &context),
        Err(EvalexprError::FunctionIdentifierNotFound(String::from(
            "max"
        )))
    );
}
}
