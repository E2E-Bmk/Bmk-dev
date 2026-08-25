mod functions {
use evalexpr::{error::*, *};
#[allow(unused_imports)]
use std::convert::TryFrom;

#[test]
fn test_functions() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    context
        .set_function(
            "sub2".to_string(),
            Function::new(|argument| {
                if let Value::Int(int) = argument {
                    Ok(Value::Int(int - 2))
                } else if let Value::Float(float) = argument {
                    Ok(Value::Float(float - 2.0))
                } else {
                    Err(EvalexprError::expected_number(argument.clone()))
                }
            }),
        )
        .unwrap();
    context
        .set_value("five".to_string(), Value::Int(5))
        .unwrap();

    assert_eq!(eval_with_context("sub2 5", &context), Ok(Value::Int(3)));
    assert_eq!(eval_with_context("sub2(5)", &context), Ok(Value::Int(3)));
    assert_eq!(eval_with_context("sub2 five", &context), Ok(Value::Int(3)));
    assert_eq!(eval_with_context("sub2(five)", &context), Ok(Value::Int(3)));
    assert_eq!(
        eval_with_context("sub2(3) + five", &context),
        Ok(Value::Int(6))
    );
}

#[test]
fn test_n_ary_functions() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    context
        .set_function(
            "sub2".into(),
            Function::new(|argument| {
                if let Value::Int(int) = argument {
                    Ok(Value::Int(int - 2))
                } else if let Value::Float(float) = argument {
                    Ok(Value::Float(float - 2.0))
                } else {
                    Err(EvalexprError::expected_number(argument.clone()))
                }
            }),
        )
        .unwrap();
    context
        .set_function(
            "avg".into(),
            Function::new(|argument| {
                let arguments = argument.as_tuple()?;
                arguments[0].as_number()?;
                arguments[1].as_number()?;

                if let (Value::Int(a), Value::Int(b)) = (&arguments[0], &arguments[1]) {
                    Ok(Value::Int((a + b) / 2))
                } else {
                    Ok(Value::Float(
                        (arguments[0].as_float()? + arguments[1].as_float()?) / 2.0,
                    ))
                }
            }),
        )
        .unwrap();
    context
        .set_function(
            "muladd".into(),
            Function::new(|argument| {
                let arguments = argument.as_tuple()?;
                arguments[0].as_number()?;
                arguments[1].as_number()?;
                arguments[2].as_number()?;

                if let (Value::Int(a), Value::Int(b), Value::Int(c)) =
                    (&arguments[0], &arguments[1], &arguments[2])
                {
                    Ok(Value::Int(a * b + c))
                } else {
                    Ok(Value::Float(
                        arguments[0].as_float()? * arguments[1].as_float()?
                            + arguments[2].as_float()?,
                    ))
                }
            }),
        )
        .unwrap();
    context
        .set_function(
            "count".into(),
            Function::new(|arguments| match arguments {
                Value::Tuple(tuple) => Ok(Value::from_int(
                    tuple.len() as <DefaultNumericTypes as EvalexprNumericTypes>::Int
                )),
                Value::Empty => Ok(Value::from_int(0)),
                _ => Ok(Value::from_int(1)),
            }),
        )
        .unwrap();
    context
        .set_value("five".to_string(), Value::Int(5))
        .unwrap();
    context
        .set_function("function_four".into(), Function::new(|_| Ok(Value::Int(4))))
        .unwrap();

    assert_eq!(eval_with_context("avg(7, 5)", &context), Ok(Value::Int(6)));
    assert_eq!(
        eval_with_context("avg(sub2 5, 5)", &context),
        Ok(Value::Int(4))
    );
    assert_eq!(
        eval_with_context("sub2(avg(3, 6))", &context),
        Ok(Value::Int(2))
    );
    assert_eq!(
        eval_with_context("sub2 avg(3, 6)", &context),
        Ok(Value::Int(2))
    );
    assert_eq!(
        eval_with_context("muladd(3, 6, -4)", &context),
        Ok(Value::Int(14))
    );
    assert_eq!(eval_with_context("count()", &context), Ok(Value::Int(0)));
    assert_eq!(
        eval_with_context("count((1, 2, 3))", &context),
        Ok(Value::Int(3))
    );
    assert_eq!(
        eval_with_context("count(3, 5.5, 2)", &context),
        Ok(Value::Int(3))
    );
    assert_eq!(eval_with_context("count 5", &context), Ok(Value::Int(1)));
    assert_eq!(
        eval_with_context("function_four()", &context),
        Ok(Value::Int(4))
    );
}

#[test]
fn test_capturing_functions() {
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

    assert_eq!(eval_with_context("mult_3 2", &context), Ok(Value::Int(6)));
    assert_eq!(eval_with_context("mult_3(3)", &context), Ok(Value::Int(9)));
    assert_eq!(
        eval_with_context("mult_3(function_four())", &context),
        Ok(Value::Int(12))
    );
}
}
