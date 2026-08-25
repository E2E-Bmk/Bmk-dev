mod shortcuts {
use evalexpr::{error::*, *};
#[allow(unused_imports)]
use std::convert::TryFrom;

#[test]
fn test_shortcut_functions() {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    context
        .set_value("string".into(), Value::from("a string"))
        .unwrap();

    assert_eq!(eval_string("\"3.3\""), Ok("3.3".to_owned()));
    assert_eq!(
        eval_string("3.3"),
        Err(EvalexprError::ExpectedString {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        eval_string("3..3"),
        Err(EvalexprError::VariableIdentifierNotFound("3..3".to_owned()))
    );
    assert_eq!(
        eval_string_with_context("string", &context),
        Ok("a string".to_owned())
    );
    assert_eq!(
        eval_string_with_context("3.3", &context),
        Err(EvalexprError::ExpectedString {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        eval_string_with_context("3..3", &context),
        Err(EvalexprError::VariableIdentifierNotFound("3..3".to_owned()))
    );
    assert_eq!(
        eval_string_with_context_mut("string", &mut context),
        Ok("a string".to_string())
    );
    assert_eq!(
        eval_string_with_context_mut("3.3", &mut context),
        Err(EvalexprError::ExpectedString {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        eval_string_with_context_mut("3..3", &mut context),
        Err(EvalexprError::VariableIdentifierNotFound("3..3".to_owned()))
    );

    assert_eq!(eval_float("3.3"), Ok(3.3));
    assert_eq!(
        eval_float("33"),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        eval_float("asd()"),
        Err(EvalexprError::FunctionIdentifierNotFound("asd".to_owned()))
    );
    assert_eq!(eval_float_with_context("3.3", &context), Ok(3.3));
    assert_eq!(
        eval_float_with_context("33", &context),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        eval_float_with_context("asd)", &context),
        Err(EvalexprError::UnmatchedRBrace)
    );
    assert_eq!(eval_float_with_context_mut("3.3", &mut context), Ok(3.3));
    assert_eq!(
        eval_float_with_context_mut("33", &mut context),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        eval_float_with_context_mut("asd(", &mut context),
        Err(EvalexprError::UnmatchedLBrace)
    );

    assert_eq!(eval_int("3"), Ok(3));
    assert_eq!(
        eval_int("3.3"),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        eval_int("(,);."),
        Err(EvalexprError::VariableIdentifierNotFound(".".to_owned()))
    );
    assert_eq!(eval_int_with_context("3", &context), Ok(3));
    assert_eq!(
        eval_int_with_context("3.3", &context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        eval_int_with_context("(,);.", &context),
        Err(EvalexprError::VariableIdentifierNotFound(".".to_owned()))
    );
    assert_eq!(eval_int_with_context_mut("3", &mut context), Ok(3));
    assert_eq!(
        eval_int_with_context_mut("3.3", &mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        eval_int_with_context_mut("(,);.", &mut context),
        Err(EvalexprError::VariableIdentifierNotFound(".".to_owned()))
    );

    assert_eq!(eval_number("3"), Ok(3.0));
    assert_eq!(
        eval_number("true"),
        Err(EvalexprError::ExpectedNumber {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        eval_number("abc"),
        Err(EvalexprError::VariableIdentifierNotFound("abc".to_owned()))
    );
    assert_eq!(eval_number_with_context("3.5", &context), Ok(3.5));
    assert_eq!(eval_number_with_context("3", &context), Ok(3.0));
    assert_eq!(
        eval_number_with_context("true", &context),
        Err(EvalexprError::ExpectedNumber {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        eval_number_with_context("abc", &context),
        Err(EvalexprError::VariableIdentifierNotFound("abc".to_owned()))
    );
    assert_eq!(eval_number_with_context_mut("3.5", &mut context), Ok(3.5));
    assert_eq!(eval_number_with_context_mut("3", &mut context), Ok(3.0));
    assert_eq!(
        eval_number_with_context_mut("true", &mut context),
        Err(EvalexprError::ExpectedNumber {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        eval_number_with_context_mut("abc", &mut context),
        Err(EvalexprError::VariableIdentifierNotFound("abc".to_owned()))
    );

    assert_eq!(eval_boolean("true"), Ok(true));
    assert_eq!(
        eval_boolean("4"),
        Err(EvalexprError::ExpectedBoolean {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        eval_boolean("trueee"),
        Err(EvalexprError::VariableIdentifierNotFound(
            "trueee".to_owned()
        ))
    );
    assert_eq!(eval_boolean_with_context("true", &context), Ok(true));
    assert_eq!(
        eval_boolean_with_context("4", &context),
        Err(EvalexprError::ExpectedBoolean {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        eval_boolean_with_context("trueee", &context),
        Err(EvalexprError::VariableIdentifierNotFound(
            "trueee".to_owned()
        ))
    );
    assert_eq!(
        eval_boolean_with_context_mut("true", &mut context),
        Ok(true)
    );
    assert_eq!(
        eval_boolean_with_context_mut("4", &mut context),
        Err(EvalexprError::ExpectedBoolean {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        eval_boolean_with_context_mut("trueee", &mut context),
        Err(EvalexprError::VariableIdentifierNotFound(
            "trueee".to_owned()
        ))
    );

    assert_eq!(eval_tuple("3,3"), Ok(vec![Value::Int(3), Value::Int(3)]));
    assert_eq!(
        eval_tuple("33"),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        eval_tuple("3a3"),
        Err(EvalexprError::VariableIdentifierNotFound("3a3".to_owned()))
    );
    assert_eq!(
        eval_tuple_with_context("3,3", &context),
        Ok(vec![Value::Int(3), Value::Int(3)])
    );
    assert_eq!(
        eval_tuple_with_context("33", &context),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        eval_tuple_with_context("3a3", &context),
        Err(EvalexprError::VariableIdentifierNotFound("3a3".to_owned()))
    );
    assert_eq!(
        eval_tuple_with_context_mut("3,3", &mut context),
        Ok(vec![Value::Int(3), Value::Int(3)])
    );
    assert_eq!(
        eval_tuple_with_context_mut("33", &mut context),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        eval_tuple_with_context_mut("3a3", &mut context),
        Err(EvalexprError::VariableIdentifierNotFound("3a3".to_owned()))
    );

    assert_eq!(eval_empty(""), Ok(EMPTY_VALUE));
    assert_eq!(eval_empty("()"), Ok(EMPTY_VALUE));
    assert_eq!(
        eval_empty("(,)"),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Tuple(vec![Value::Empty, Value::Empty])
        })
    );
    assert_eq!(
        eval_empty("xaq"),
        Err(EvalexprError::VariableIdentifierNotFound("xaq".to_owned()))
    );
    assert_eq!(eval_empty_with_context("", &context), Ok(EMPTY_VALUE));
    assert_eq!(eval_empty_with_context("()", &context), Ok(EMPTY_VALUE));
    assert_eq!(
        eval_empty_with_context("(,)", &context),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Tuple(vec![Value::Empty, Value::Empty])
        })
    );
    assert_eq!(
        eval_empty_with_context("xaq", &context),
        Err(EvalexprError::VariableIdentifierNotFound("xaq".to_owned()))
    );
    assert_eq!(
        eval_empty_with_context_mut("", &mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        eval_empty_with_context_mut("()", &mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        eval_empty_with_context_mut("(,)", &mut context),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Tuple(vec![Value::Empty, Value::Empty])
        })
    );
    assert_eq!(
        eval_empty_with_context_mut("xaq", &mut context),
        Err(EvalexprError::VariableIdentifierNotFound("xaq".to_owned()))
    );

    // With detour via build_operator_tree

    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("\"3.3\"")
            .unwrap()
            .eval_string(),
        Ok("3.3".to_owned())
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3.3")
            .unwrap()
            .eval_string(),
        Err(EvalexprError::ExpectedString {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3..3")
            .unwrap()
            .eval_string(),
        Err(EvalexprError::VariableIdentifierNotFound("3..3".to_owned()))
    );
    assert_eq!(
        build_operator_tree("string")
            .unwrap()
            .eval_string_with_context(&context),
        Ok("a string".to_owned())
    );
    assert_eq!(
        build_operator_tree("3.3")
            .unwrap()
            .eval_string_with_context(&context),
        Err(EvalexprError::ExpectedString {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        build_operator_tree("3..3")
            .unwrap()
            .eval_string_with_context(&context),
        Err(EvalexprError::VariableIdentifierNotFound("3..3".to_owned()))
    );
    assert_eq!(
        build_operator_tree("string")
            .unwrap()
            .eval_string_with_context_mut(&mut context),
        Ok("a string".to_string())
    );
    assert_eq!(
        build_operator_tree("3.3")
            .unwrap()
            .eval_string_with_context_mut(&mut context),
        Err(EvalexprError::ExpectedString {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        build_operator_tree("3..3")
            .unwrap()
            .eval_string_with_context_mut(&mut context),
        Err(EvalexprError::VariableIdentifierNotFound("3..3".to_owned()))
    );

    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3.3")
            .unwrap()
            .eval_float(),
        Ok(3.3)
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("33")
            .unwrap()
            .eval_float(),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("asd()")
            .unwrap()
            .eval_float(),
        Err(EvalexprError::FunctionIdentifierNotFound("asd".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3.3")
            .unwrap()
            .eval_float_with_context(&context),
        Ok(3.3)
    );
    assert_eq!(
        build_operator_tree("33")
            .unwrap()
            .eval_float_with_context(&context),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        build_operator_tree("asd")
            .unwrap()
            .eval_float_with_context(&context),
        Err(EvalexprError::VariableIdentifierNotFound("asd".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3.3")
            .unwrap()
            .eval_float_with_context_mut(&mut context),
        Ok(3.3)
    );
    assert_eq!(
        build_operator_tree("33")
            .unwrap()
            .eval_float_with_context_mut(&mut context),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        build_operator_tree("asd")
            .unwrap()
            .eval_float_with_context_mut(&mut context),
        Err(EvalexprError::VariableIdentifierNotFound("asd".to_owned()))
    );

    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3")
            .unwrap()
            .eval_int(),
        Ok(3)
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3.3")
            .unwrap()
            .eval_int(),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("(,);.")
            .unwrap()
            .eval_int(),
        Err(EvalexprError::VariableIdentifierNotFound(".".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3")
            .unwrap()
            .eval_int_with_context(&context),
        Ok(3)
    );
    assert_eq!(
        build_operator_tree("3.3")
            .unwrap()
            .eval_int_with_context(&context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        build_operator_tree("(,);.")
            .unwrap()
            .eval_int_with_context(&context),
        Err(EvalexprError::VariableIdentifierNotFound(".".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3")
            .unwrap()
            .eval_int_with_context_mut(&mut context),
        Ok(3)
    );
    assert_eq!(
        build_operator_tree("3.3")
            .unwrap()
            .eval_int_with_context_mut(&mut context),
        Err(EvalexprError::ExpectedInt {
            actual: Value::Float(3.3)
        })
    );
    assert_eq!(
        build_operator_tree("(,);.")
            .unwrap()
            .eval_int_with_context_mut(&mut context),
        Err(EvalexprError::VariableIdentifierNotFound(".".to_owned()))
    );

    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3")
            .unwrap()
            .eval_number(),
        Ok(3.0)
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("true")
            .unwrap()
            .eval_number(),
        Err(EvalexprError::ExpectedNumber {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("abc")
            .unwrap()
            .eval_number(),
        Err(EvalexprError::VariableIdentifierNotFound("abc".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3")
            .unwrap()
            .eval_number_with_context(&context),
        Ok(3.0)
    );
    assert_eq!(
        build_operator_tree("true")
            .unwrap()
            .eval_number_with_context(&context),
        Err(EvalexprError::ExpectedNumber {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        build_operator_tree("abc")
            .unwrap()
            .eval_number_with_context(&context),
        Err(EvalexprError::VariableIdentifierNotFound("abc".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3")
            .unwrap()
            .eval_number_with_context_mut(&mut context),
        Ok(3.0)
    );
    assert_eq!(
        build_operator_tree("true")
            .unwrap()
            .eval_number_with_context_mut(&mut context),
        Err(EvalexprError::ExpectedNumber {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        build_operator_tree("abc")
            .unwrap()
            .eval_number_with_context_mut(&mut context),
        Err(EvalexprError::VariableIdentifierNotFound("abc".to_owned()))
    );

    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("true")
            .unwrap()
            .eval_boolean(),
        Ok(true)
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("4")
            .unwrap()
            .eval_boolean(),
        Err(EvalexprError::ExpectedBoolean {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("trueee")
            .unwrap()
            .eval_boolean(),
        Err(EvalexprError::VariableIdentifierNotFound(
            "trueee".to_owned()
        ))
    );
    assert_eq!(
        build_operator_tree("true")
            .unwrap()
            .eval_boolean_with_context(&context),
        Ok(true)
    );
    assert_eq!(
        build_operator_tree("4")
            .unwrap()
            .eval_boolean_with_context(&context),
        Err(EvalexprError::ExpectedBoolean {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        build_operator_tree("trueee")
            .unwrap()
            .eval_boolean_with_context(&context),
        Err(EvalexprError::VariableIdentifierNotFound(
            "trueee".to_owned()
        ))
    );
    assert_eq!(
        build_operator_tree("true")
            .unwrap()
            .eval_boolean_with_context_mut(&mut context),
        Ok(true)
    );
    assert_eq!(
        build_operator_tree("4")
            .unwrap()
            .eval_boolean_with_context_mut(&mut context),
        Err(EvalexprError::ExpectedBoolean {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        build_operator_tree("trueee")
            .unwrap()
            .eval_boolean_with_context_mut(&mut context),
        Err(EvalexprError::VariableIdentifierNotFound(
            "trueee".to_owned()
        ))
    );

    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3,3")
            .unwrap()
            .eval_tuple(),
        Ok(vec![Value::Int(3), Value::Int(3)])
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("33")
            .unwrap()
            .eval_tuple(),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("3a3")
            .unwrap()
            .eval_tuple(),
        Err(EvalexprError::VariableIdentifierNotFound("3a3".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3,3")
            .unwrap()
            .eval_tuple_with_context(&context),
        Ok(vec![Value::Int(3), Value::Int(3)])
    );
    assert_eq!(
        build_operator_tree("33")
            .unwrap()
            .eval_tuple_with_context(&context),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        build_operator_tree("3a3")
            .unwrap()
            .eval_tuple_with_context(&context),
        Err(EvalexprError::VariableIdentifierNotFound("3a3".to_owned()))
    );
    assert_eq!(
        build_operator_tree("3,3")
            .unwrap()
            .eval_tuple_with_context_mut(&mut context),
        Ok(vec![Value::Int(3), Value::Int(3)])
    );
    assert_eq!(
        build_operator_tree("33")
            .unwrap()
            .eval_tuple_with_context_mut(&mut context),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(33)
        })
    );
    assert_eq!(
        build_operator_tree("3a3")
            .unwrap()
            .eval_tuple_with_context_mut(&mut context),
        Err(EvalexprError::VariableIdentifierNotFound("3a3".to_owned()))
    );

    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("")
            .unwrap()
            .eval_empty(),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("()")
            .unwrap()
            .eval_empty(),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("(,)")
            .unwrap()
            .eval_empty(),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Tuple(vec![Value::Empty, Value::Empty])
        })
    );
    assert_eq!(
        build_operator_tree::<DefaultNumericTypes>("xaq")
            .unwrap()
            .eval_empty(),
        Err(EvalexprError::VariableIdentifierNotFound("xaq".to_owned()))
    );
    assert_eq!(
        build_operator_tree("")
            .unwrap()
            .eval_empty_with_context(&context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        build_operator_tree("()")
            .unwrap()
            .eval_empty_with_context(&context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        build_operator_tree("(,)")
            .unwrap()
            .eval_empty_with_context(&context),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Tuple(vec![Value::Empty, Value::Empty])
        })
    );
    assert_eq!(
        build_operator_tree("xaq")
            .unwrap()
            .eval_empty_with_context(&context),
        Err(EvalexprError::VariableIdentifierNotFound("xaq".to_owned()))
    );
    assert_eq!(
        build_operator_tree("")
            .unwrap()
            .eval_empty_with_context_mut(&mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        build_operator_tree("()")
            .unwrap()
            .eval_empty_with_context_mut(&mut context),
        Ok(EMPTY_VALUE)
    );
    assert_eq!(
        build_operator_tree("(,)")
            .unwrap()
            .eval_empty_with_context_mut(&mut context),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Tuple(vec![Value::Empty, Value::Empty])
        })
    );
    assert_eq!(
        build_operator_tree("xaq")
            .unwrap()
            .eval_empty_with_context_mut(&mut context),
        Err(EvalexprError::VariableIdentifierNotFound("xaq".to_owned()))
    );
}
}
