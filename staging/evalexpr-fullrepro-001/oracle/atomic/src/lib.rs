// Oracle atomic tests for the evalexpr reconstruction task.
#![cfg(test)]
#![allow(clippy::all)]
use evalexpr::{error::*, *};
use std::convert::TryFrom;

#[test]
fn test_unary_examples() {
    assert_eq!(eval("3"), Ok(Value::Int(3)));
    assert_eq!(eval("3.3"), Ok(Value::Float(3.3)));
    assert_eq!(eval("true"), Ok(Value::Boolean(true)));
    assert_eq!(eval("false"), Ok(Value::Boolean(false)));
    assert_eq!(
        eval("blub"),
        Err(EvalexprError::VariableIdentifierNotFound(
            "blub".to_string()
        ))
    );
    assert_eq!(eval("-3"), Ok(Value::Int(-3)));
    assert_eq!(eval("-3.6"), Ok(Value::Float(-3.6)));
    assert_eq!(eval("----3"), Ok(Value::Int(3)));
    assert_eq!(eval("1e0"), Ok(Value::Float(1.0)));
    assert_eq!(eval("1e-0"), Ok(Value::Float(1.0)));
    assert_eq!(eval("10e3"), Ok(Value::Float(10000.0)));
    assert_eq!(eval("10e+3"), Ok(Value::Float(10000.0)));
    assert_eq!(eval("10e-3"), Ok(Value::Float(0.01)));
}

#[test]
fn test_binary_examples() {
    assert_eq!(eval("1+3"), Ok(Value::Int(4)));
    assert_eq!(eval("3+1"), Ok(Value::Int(4)));
    assert_eq!(eval("3-5"), Ok(Value::Int(-2)));
    assert_eq!(eval("5-3"), Ok(Value::Int(2)));
    assert_eq!(eval("5 / 4"), Ok(Value::Int(1)));
    assert_eq!(eval("5 *3"), Ok(Value::Int(15)));
    assert_eq!(eval("1.0+3"), Ok(Value::Float(4.0)));
    assert_eq!(eval("3.0+1"), Ok(Value::Float(4.0)));
    assert_eq!(eval("3-5.0"), Ok(Value::Float(-2.0)));
    assert_eq!(eval("5-3.0"), Ok(Value::Float(2.0)));
    assert_eq!(eval("5 / 4.0"), Ok(Value::Float(1.25)));
    assert_eq!(eval("5.0 *3"), Ok(Value::Float(15.0)));
    assert_eq!(eval("5.0 *-3"), Ok(Value::Float(-15.0)));
    assert_eq!(eval("5.0 *- 3"), Ok(Value::Float(-15.0)));
    assert_eq!(eval("5.0 * -3"), Ok(Value::Float(-15.0)));
    assert_eq!(eval("5.0 * - 3"), Ok(Value::Float(-15.0)));
    assert_eq!(eval("-5.0 *-3"), Ok(Value::Float(15.0)));
    assert_eq!(eval("3+-1"), Ok(Value::Int(2)));
    assert_eq!(eval("-3-5"), Ok(Value::Int(-8)));
    assert_eq!(eval("-5--3"), Ok(Value::Int(-2)));
    assert_eq!(eval("5e2--3"), Ok(Value::Float(503.0)));
    assert_eq!(eval("-5e-2--3"), Ok(Value::Float(2.95)));
}

#[test]
fn test_arithmetic_precedence_examples() {
    assert_eq!(eval("1+3-2"), Ok(Value::Int(2)));
    assert_eq!(eval("3+1*5"), Ok(Value::Int(8)));
    assert_eq!(eval("2*3-5"), Ok(Value::Int(1)));
    assert_eq!(eval("5-3/3"), Ok(Value::Int(4)));
    assert_eq!(eval("5 / 4*2"), Ok(Value::Int(2)));
    assert_eq!(eval("1-5 *3/15"), Ok(Value::Int(0)));
    assert_eq!(eval("15/7/2.0"), Ok(Value::Float(1.0)));
    assert_eq!(eval("15.0/7/2"), Ok(Value::Float(15.0 / 7.0 / 2.0)));
    assert_eq!(eval("15.0/-7/2"), Ok(Value::Float(15.0 / -7.0 / 2.0)));
    assert_eq!(eval("-15.0/7/2"), Ok(Value::Float(-15.0 / 7.0 / 2.0)));
    assert_eq!(eval("-15.0/7/-2"), Ok(Value::Float(-15.0 / 7.0 / -2.0)));
}

#[test]
fn test_braced_examples() {
    assert_eq!(eval("(1)"), Ok(Value::Int(1)));
    assert_eq!(eval("( 1.0 )"), Ok(Value::Float(1.0)));
    assert_eq!(eval("( true)"), Ok(Value::Boolean(true)));
    assert_eq!(eval("( -1 )"), Ok(Value::Int(-1)));
    assert_eq!(eval("-(1)"), Ok(Value::Int(-1)));
    assert_eq!(eval("-(1 + 3) * 7"), Ok(Value::Int(-28)));
    assert_eq!(eval("(1 * 1) - 3"), Ok(Value::Int(-2)));
    assert_eq!(eval("4 / (2 * 2)"), Ok(Value::Int(1)));
    assert_eq!(eval("7/(7/(7/(7/(7/(7)))))"), Ok(Value::Int(1)));
}

#[test]
fn test_mod_examples() {
    assert_eq!(eval("1 % 4"), Ok(Value::Int(1)));
    assert_eq!(eval("6 % 4"), Ok(Value::Int(2)));
    assert_eq!(eval("1 % 4 + 2"), Ok(Value::Int(3)));
}

#[test]
fn test_pow_examples() {
    assert_eq!(eval("1 ^ 4"), Ok(Value::Float(1.0)));
    assert_eq!(
        eval("6 ^ 4"),
        Ok(Value::Float(
            (6.0 as <DefaultNumericTypes as EvalexprNumericTypes>::Float).powf(4.0)
        ))
    );
    assert_eq!(eval("1 ^ 4 + 2"), Ok(Value::Float(3.0)));
    assert_eq!(eval("2 ^ (4 + 2)"), Ok(Value::Float(64.0)));
}

#[test]
fn test_boolean_examples() {
    assert_eq!(eval("true && false"), Ok(Value::Boolean(false)));
    assert_eq!(
        eval("true && false || true && true"),
        Ok(Value::Boolean(true))
    );
    assert_eq!(eval("5 > 4 && 1 <= 1"), Ok(Value::Boolean(true)));
    assert_eq!(eval("5.0 <= 4.9 || !(4 > 3.5)"), Ok(Value::Boolean(false)));
}

#[test]
fn test_builtin_functions() {
    // Log
    assert_eq!(eval("math::ln(2.718281828459045)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("math::log(9, 9)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("math::log2(2)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("math::log10(10)"), Ok(Value::Float(1.0)));
    // Powers
    assert_eq!(
        eval("math::exp(2)"),
        Ok(Value::Float(
            (2.0 as <DefaultNumericTypes as EvalexprNumericTypes>::Float).exp()
        ))
    );
    assert_eq!(
        eval("math::exp2(2)"),
        Ok(Value::Float(
            (2.0 as <DefaultNumericTypes as EvalexprNumericTypes>::Float).exp2()
        ))
    );
    assert_eq!(
        eval("math::pow(1.5, 1.3)"),
        Ok(Value::Float(
            (1.5 as <DefaultNumericTypes as EvalexprNumericTypes>::Float).powf(1.3)
        ))
    );
    // Cos
    assert_eq!(eval("math::cos(0)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("math::acos(1)"), Ok(Value::Float(0.0)));
    assert_eq!(eval("math::cosh(0)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("math::acosh(1)"), Ok(Value::Float(0.0)));
    // Sin
    assert_eq!(eval("math::sin(0)"), Ok(Value::Float(0.0)));
    assert_eq!(eval("math::asin(0)"), Ok(Value::Float(0.0)));
    assert_eq!(eval("math::sinh(0)"), Ok(Value::Float(0.0)));
    assert_eq!(eval("math::asinh(0)"), Ok(Value::Float(0.0)));
    // Tan
    assert_eq!(eval("math::tan(0)"), Ok(Value::Float(0.0)));
    assert_eq!(eval("math::atan(0)"), Ok(Value::Float(0.0)));
    assert_eq!(eval("math::tanh(0)"), Ok(Value::Float(0.0)));
    assert_eq!(eval("math::atanh(0)"), Ok(Value::Float(0.0)));
    assert_eq!(
        eval("math::atan2(1.2, -5.5)"),
        Ok(Value::Float(
            (1.2 as <DefaultNumericTypes as EvalexprNumericTypes>::Float).atan2(-5.5)
        ))
    );
    // Root
    assert_eq!(eval("math::sqrt(25)"), Ok(Value::Float(5.0)));
    assert_eq!(eval("math::cbrt(8)"), Ok(Value::Float(2.0)));
    // Hypotenuse
    assert_eq!(
        eval("math::hypot(8.2, 1.1)"),
        Ok(Value::Float(
            (8.2 as <DefaultNumericTypes as EvalexprNumericTypes>::Float).hypot(1.1)
        ))
    );
    // Rounding
    assert_eq!(eval("floor(1.1)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("floor(1.9)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("round(1.1)"), Ok(Value::Float(1.0)));
    assert_eq!(eval("round(1.5)"), Ok(Value::Float(2.0)));
    assert_eq!(eval("round(2.5)"), Ok(Value::Float(3.0)));
    assert_eq!(eval("round(1.9)"), Ok(Value::Float(2.0)));
    assert_eq!(eval("ceil(1.1)"), Ok(Value::Float(2.0)));
    assert_eq!(eval("ceil(1.9)"), Ok(Value::Float(2.0)));
    assert_eq!(eval("math::is_nan(1.0/0.0)"), Ok(Value::Boolean(false)));
    assert_eq!(eval("math::is_nan(0.0/0.0)"), Ok(Value::Boolean(true)));
    assert_eq!(eval("math::is_finite(1.0/0.0)"), Ok(Value::Boolean(false)));
    assert_eq!(eval("math::is_finite(0.0/0.0)"), Ok(Value::Boolean(false)));
    assert_eq!(eval("math::is_finite(0.0)"), Ok(Value::Boolean(true)));
    assert_eq!(
        eval("math::is_infinite(0.0/0.0)"),
        Ok(Value::Boolean(false))
    );
    assert_eq!(eval("math::is_infinite(1.0/0.0)"), Ok(Value::Boolean(true)));
    assert_eq!(eval("math::is_normal(1.0/0.0)"), Ok(Value::Boolean(false)));
    assert_eq!(eval("math::is_normal(0)"), Ok(Value::Boolean(false)));
    // Absolute
    assert_eq!(eval("math::abs(15.4)"), Ok(Value::Float(15.4)));
    assert_eq!(eval("math::abs(-15.4)"), Ok(Value::Float(15.4)));
    assert_eq!(eval("math::abs(15)"), Ok(Value::Int(15)));
    assert_eq!(eval("math::abs(-15)"), Ok(Value::Int(15)));
    // Other
    assert_eq!(eval("typeof(4.0, 3)"), Ok(Value::String("tuple".into())));
    assert_eq!(eval("typeof(4.0)"), Ok(Value::String("float".into())));
    assert_eq!(eval("typeof(4)"), Ok(Value::String("int".into())));
    assert_eq!(eval("typeof(\"\")"), Ok(Value::String("string".into())));
    assert_eq!(eval("typeof(true)"), Ok(Value::String("boolean".into())));
    assert_eq!(eval("typeof()"), Ok(Value::String("empty".into())));
    assert_eq!(eval("min(4.0, 3)"), Ok(Value::Int(3)));
    assert_eq!(eval("max(4.0, 3)"), Ok(Value::Float(4.0)));
    assert_eq!(eval("len(\"foobar\")"), Ok(Value::Int(6)));
    assert_eq!(eval("len(\"a\", \"b\")"), Ok(Value::Int(2)));
    //Contians
    assert_eq!(
        eval("contains(1, 2, 3)"),
        Err(EvalexprError::expected_fixed_len_tuple(
            2,
            Value::Tuple(vec![Value::Int(1), Value::Int(2), Value::Int(3)])
        ))
    );
    assert_eq!(
        eval("contains((\"foo\", \"bar\"), \"bar\")"),
        Ok(Value::Boolean(true))
    );
    assert_eq!(
        eval("contains((\"foo\", \"bar\"), \"buzz\")"),
        Ok(Value::Boolean(false)),
    );
    assert_eq!(
        eval("contains(\"foo\", \"bar\")"),
        Err(EvalexprError::expected_tuple(Value::String("foo".into())))
    );
    assert_eq!(
        eval("contains((\"foo\", \"bar\", 123), 123)"),
        Ok(Value::Boolean(true))
    );
    assert_eq!(
        eval("contains((\"foo\", \"bar\"), (\"buzz\", \"bazz\"))"),
        Err(EvalexprError::type_error(
            Value::Tuple(vec![
                Value::String("buzz".into()),
                Value::String("bazz".into())
            ]),
            vec![
                ValueType::String,
                ValueType::Int,
                ValueType::Float,
                ValueType::Boolean
            ]
        ))
    );
    //Contains Any
    assert_eq!(
        eval("contains_any(1, 2, 3)"),
        Err(EvalexprError::expected_fixed_len_tuple(
            2,
            Value::Tuple(vec![Value::Int(1), Value::Int(2), Value::Int(3)])
        ))
    );
    assert_eq!(
        eval("contains_any((\"foo\", \"bar\"), (\"bar\", \"buzz\"))"),
        Ok(Value::Boolean(true))
    );
    assert_eq!(
        eval("contains_any((\"foo\", \"bar\"), (\"buzz\", \"bazz\"))"),
        Ok(Value::Boolean(false)),
    );
    assert_eq!(
        eval("contains_any((1,2,3), (3,4,5))"),
        Ok(Value::Boolean(true))
    );
    assert_eq!(
        eval("contains_any((1,2,3), (4,5,6))"),
        Ok(Value::Boolean(false))
    );
    assert_eq!(
        eval("contains_any((true, false, true, true), (false, false, false))"),
        Ok(Value::Boolean(true))
    );
    assert_eq!(
        eval("contains_any(\"foo\", \"bar\")"),
        Err(EvalexprError::expected_tuple(Value::String("foo".into())))
    );
    assert_eq!(
        eval("contains_any((\"foo\", \"bar\"), \"buzz\")"),
        Err(EvalexprError::expected_tuple(Value::String("buzz".into())))
    );
    assert_eq!(
        eval("contains_any((\"foo\", \"bar\"), (\"buzz\", (1, 2, 3)))"),
        Err(EvalexprError::type_error(
            Value::Tuple(vec![Value::Int(1), Value::Int(2), Value::Int(3)]),
            vec![
                ValueType::String,
                ValueType::Int,
                ValueType::Float,
                ValueType::Boolean
            ]
        ))
    );
    // String
    assert_eq!(
        eval("str::to_lowercase(\"FOOBAR\")"),
        Ok(Value::from("foobar"))
    );
    assert_eq!(
        eval("str::to_uppercase(\"foobar\")"),
        Ok(Value::from("FOOBAR"))
    );
    assert_eq!(
        eval("str::trim(\"  foo  bar \")"),
        Ok(Value::from("foo  bar"))
    );
    assert_eq!(
        eval("str::from(\"a\")"),
        Ok(Value::String(String::from("a")))
    );
    assert_eq!(eval("str::from(1.0)"), Ok(Value::String(String::from("1"))));
    assert_eq!(
        eval("str::from(4.2)"),
        Ok(Value::String(String::from("4.2")))
    );
    assert_eq!(eval("str::from(1)"), Ok(Value::String(String::from("1"))));
    assert_eq!(
        eval("str::from(true)"),
        Ok(Value::String(String::from("true")))
    );
    assert_eq!(
        eval(r#"str::from((1, "foo", , false))"#),
        Ok(Value::String(String::from(r#"(1, "foo", (), false)"#)))
    );
    assert_eq!(
        eval("str::from(true)"),
        Ok(Value::String(String::from("true")))
    );
    assert_eq!(
        eval("str::from(1, 2, 3)"),
        Ok(Value::String(String::from("(1, 2, 3)")))
    );
    assert_eq!(eval("str::from()"), Ok(Value::String(String::from("()"))));
    assert_eq!(
        eval("str::substring(\"foobar\", 3)"),
        Ok(Value::String(String::from("bar")))
    );
    assert_eq!(
        eval("str::substring(\"foobar\", 3, 3)"),
        Ok(Value::String(String::from("")))
    );
    assert_eq!(
        eval("str::substring(\"foobar\", 3, 4)"),
        Ok(Value::String(String::from("b")))
    );
    assert!(eval("str::substring()").is_err());
    assert!(eval("str::substring(\"foobar\")").is_err());
    assert!(eval("str::substring(\"foobar\", 2, 1)").is_err());
    assert!(eval("str::substring(\"foobar\", 99999)").is_err());
    assert!(eval("str::substring(\"foobar\", -1)").is_err());
    assert!(eval("str::substring(\"foobar\", 0, -1)").is_err());
    assert!(eval("str::substring(\"foobar\", 0, 1, 1)").is_err());
    // Bitwise
    assert_eq!(eval("bitand(5, -1)"), Ok(Value::Int(5)));
    assert_eq!(eval("bitand(6, 5)"), Ok(Value::Int(4)));
    assert_eq!(eval("bitor(5, -1)"), Ok(Value::Int(-1)));
    assert_eq!(eval("bitor(6, 5)"), Ok(Value::Int(7)));
    assert_eq!(eval("bitxor(5, -1)"), Ok(Value::Int(-6)));
    assert_eq!(eval("bitxor(6, 5)"), Ok(Value::Int(3)));
    assert_eq!(eval("bitnot(5)"), Ok(Value::Int(-6)));
    assert_eq!(eval("bitnot(-1)"), Ok(Value::Int(0)));
    assert_eq!(eval("shl(5, 1)"), Ok(Value::Int(10)));
    assert_eq!(eval("shl(-6, 5)"), Ok(Value::Int(-192)));
    assert_eq!(eval("shr(5, 1)"), Ok(Value::Int(2)));
    assert_eq!(eval("shr(-6, 5)"), Ok(Value::Int(-1)));
    assert_eq!(eval("if(true, -6, 5)"), Ok(Value::Int(-6)));
    assert_eq!(eval("if(false, -6, 5)"), Ok(Value::Int(5)));
    assert_eq!(
        eval("if(2-1==1, \"good\", 0)"),
        Ok(Value::String(String::from("good")))
    );
}

#[test]
fn test_errors() {
    assert_eq!(
        eval("-true"),
        Err(EvalexprError::expected_number(Value::Boolean(true)))
    );
    assert_eq!(
        eval("1-true"),
        Err(EvalexprError::expected_number(Value::Boolean(true)))
    );
    assert_eq!(
        eval("true-"),
        Err(EvalexprError::WrongOperatorArgumentAmount {
            actual: 1,
            expected: 2,
        })
    );
    assert_eq!(eval("!(()true)"), Err(EvalexprError::AppendedToLeafNode));
    assert_eq!(
        eval("math::is_nan(\"xxx\")"),
        Err(EvalexprError::ExpectedNumber {
            actual: Value::String("xxx".to_string())
        })
    );
}

#[test]
fn test_no_panic() {
    assert!(eval(&format!(
        "{} + {}",
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX,
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX
    ))
    .is_err());
    assert!(eval(&format!(
        "-{} - {}",
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX,
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX
    ))
    .is_err());
    assert!(eval(&format!(
        "-(-{} - 1)",
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX
    ))
    .is_err());
    assert!(eval(&format!(
        "{} * {}",
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX,
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX
    ))
    .is_err());
    assert!(eval(&format!(
        "{} / {}",
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX,
        0
    ))
    .is_err());
    assert!(eval(&format!(
        "{} % {}",
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX,
        0
    ))
    .is_err());
    assert!(eval(&format!(
        "{} ^ {}",
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX,
        <DefaultNumericTypes as EvalexprNumericTypes>::Int::MAX
    ))
    .is_ok());
    assert!(eval("if").is_err());
    assert!(eval("if()").is_err());
    assert!(eval("if(true, 1)").is_err());
    assert!(eval("if(false, 2)").is_err());
    assert!(eval("if(1,1,1)").is_err());
    assert!(eval("if(true,1,1,1)").is_err());
}

#[test]
fn test_whitespace() {
    assert!(eval_boolean("2 < = 3").is_err());
}

#[test]
fn test_string_escaping() {
    assert_eq!(
        eval("\"\\\"str\\\\ing\\\"\""),
        Ok(Value::from("\"str\\ing\""))
    );
}

#[test]
fn test_tuple_definitions() {
    assert_eq!(eval_empty("()"), Ok(()));
    assert_eq!(eval_int("(3)"), Ok(3));
    assert_eq!(
        eval_tuple("(3, 4)"),
        Ok(vec![Value::from_int(3), Value::from_int(4)])
    );
    assert_eq!(
        eval_tuple("2, (5, 6)"),
        Ok(vec![
            Value::from_int(2),
            Value::from(vec![Value::from_int(5), Value::from_int(6)])
        ])
    );
    assert_eq!(
        eval_tuple("1, 2"),
        Ok(vec![Value::from_int(1), Value::from_int(2)])
    );
    assert_eq!(
        eval_tuple("1, 2, 3, 4"),
        Ok(vec![
            Value::from_int(1),
            Value::from_int(2),
            Value::from_int(3),
            Value::from_int(4)
        ])
    );
    assert_eq!(
        eval_tuple("(1, 2, 3), 5, 6, (true, false, 0)"),
        Ok(vec![
            Value::from(vec![
                Value::from_int(1),
                Value::from_int(2),
                Value::from_int(3)
            ]),
            Value::from_int(5),
            Value::from_int(6),
            Value::from(vec![
                Value::from(true),
                Value::from(false),
                Value::from_int(0)
            ])
        ])
    );
    assert_eq!(
        eval_tuple("1, (2)"),
        Ok(vec![Value::from_int(1), Value::from_int(2)])
    );
    assert_eq!(
        eval_tuple("1, ()"),
        Ok(vec![Value::from_int(1), Value::from(())])
    );
    assert_eq!(
        eval_tuple("1, ((2))"),
        Ok(vec![Value::from_int(1), Value::from_int(2)])
    );
}

#[test]
fn test_implicit_context() {
    assert_eq!(
        eval("a = 2 + 4 * 2; b = -5 + 3 * 5; a == b"),
        Ok(Value::from(true))
    );
    assert_eq!(
        eval_boolean("a = 2 + 4 * 2; b = -5 + 3 * 5; a == b"),
        Ok(true)
    );
    assert_eq!(eval_int("a = 2 + 4 * 2; b = -5 + 3 * 5; a - b"), Ok(0));
    assert_eq!(
        eval_float("a = 2 + 4 * 2; b = -5 + 3 * 5; a - b + 0.5"),
        Ok(0.5)
    );
    assert_eq!(eval_number("a = 2 + 4 * 2; b = -5 + 3 * 5; a - b"), Ok(0.0));
    assert_eq!(eval_empty("a = 2 + 4 * 2; b = -5 + 3 * 5;"), Ok(()));
    assert_eq!(
        eval_tuple("a = 2 + 4 * 2; b = -5 + 3 * 5; a, b + 0.5"),
        Ok(vec![Value::from_int(10), Value::from_float(10.5)])
    );
    assert_eq!(
        eval_string("a = \"xyz\"; b = \"abc\"; c = a + b; c"),
        Ok("xyzabc".to_string())
    );
}

#[test]
fn test_type_errors_in_binary_operators() {
    // Only addition supports incompatible types, all others work only on numbers or only on booleans.
    // So only addition requires the more fancy error message.
    assert!(matches!(
        eval("4 + \"abc\""),
        Err(EvalexprError::WrongTypeCombination { actual, .. })
            if actual == vec![ValueType::Int, ValueType::String]
    ));
    assert!(matches!(
        eval("\"abc\" + 4"),
        Err(EvalexprError::WrongTypeCombination { actual, .. })
            if actual == vec![ValueType::String, ValueType::Int]
    ));
}

#[test]
fn test_error_constructors() {
    assert_eq!(
        eval("a = true + \"4\""),
        Err(EvalexprError::ExpectedNumberOrString {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        eval("a = true && \"4\""),
        Err(EvalexprError::ExpectedBoolean {
            actual: Value::from("4")
        })
    );
    assert_eq!(
        eval_tuple("4"),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(4)
        })
    );
    assert_eq!(
        Value::Tuple(vec![Value::<DefaultNumericTypes>::Int(4), Value::Int(5)])
            .as_fixed_len_tuple(3),
        Err(EvalexprError::ExpectedFixedLengthTuple {
            expected_length: 3,
            actual: Value::Tuple(vec![Value::Int(4), Value::Int(5)])
        })
    );
    assert_eq!(
        eval_empty("4"),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Int(4)
        })
    );
    assert!(matches!(
        eval("&"),
        Err(EvalexprError::UnmatchedPartialToken { .. })
    ));
}

#[test]
fn test_same_operator_chains() {
    #![allow(clippy::eq_op)]
    assert_eq!(
        eval("3.0 / 3.0 / 3.0 / 3.0"),
        Ok(Value::from_float(3.0 / 3.0 / 3.0 / 3.0))
    );
    assert_eq!(
        eval("3.0 - 3.0 - 3.0 - 3.0"),
        Ok(Value::from_float(3.0 - 3.0 - 3.0 - 3.0))
    );
}

#[test]
fn test_value_type() {
    assert_eq!(
        ValueType::from(&Value::<DefaultNumericTypes>::String(String::new())),
        ValueType::String
    );
    assert_eq!(
        ValueType::from(&Value::<DefaultNumericTypes>::Float(0.0)),
        ValueType::Float
    );
    assert_eq!(
        ValueType::from(&Value::<DefaultNumericTypes>::Int(0)),
        ValueType::Int
    );
    assert_eq!(
        ValueType::from(&Value::<DefaultNumericTypes>::Boolean(true)),
        ValueType::Boolean
    );
    assert_eq!(
        ValueType::from(&Value::<DefaultNumericTypes>::Tuple(Vec::new())),
        ValueType::Tuple
    );
    assert_eq!(
        ValueType::from(&Value::<DefaultNumericTypes>::Empty),
        ValueType::Empty
    );

    assert_eq!(
        Value::<DefaultNumericTypes>::String(String::new()).as_float(),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::String(String::new())
        })
    );
    assert_eq!(Value::<DefaultNumericTypes>::Float(0.0).as_float(), Ok(0.0));
    assert_eq!(
        Value::<DefaultNumericTypes>::Int(0).as_float(),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Int(0)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Boolean(true).as_float(),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Tuple(Vec::new()).as_float(),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Tuple(Vec::new())
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Empty.as_float(),
        Err(EvalexprError::ExpectedFloat {
            actual: Value::Empty
        })
    );

    assert_eq!(
        Value::<DefaultNumericTypes>::String(String::new()).as_tuple(),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::String(String::new())
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Float(0.0).as_tuple(),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Float(0.0)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Int(0).as_tuple(),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(0)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Boolean(true).as_tuple(),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Tuple(Vec::new()).as_tuple(),
        Ok(Vec::new())
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Empty.as_tuple(),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Empty
        })
    );

    assert_eq!(
        Value::<DefaultNumericTypes>::String(String::new()).as_fixed_len_tuple(0),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::String(String::new())
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Float(0.0).as_fixed_len_tuple(0),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Float(0.0)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Int(0).as_fixed_len_tuple(0),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Int(0)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Boolean(true).as_fixed_len_tuple(0),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Tuple(Vec::new()).as_fixed_len_tuple(0),
        Ok(Vec::new())
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Empty.as_fixed_len_tuple(0),
        Err(EvalexprError::ExpectedTuple {
            actual: Value::Empty
        })
    );

    assert_eq!(
        Value::<DefaultNumericTypes>::String(String::new()).as_empty(),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::String(String::new())
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Float(0.0).as_empty(),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Float(0.0)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Int(0).as_empty(),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Int(0)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Boolean(true).as_empty(),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Boolean(true)
        })
    );
    assert_eq!(
        Value::<DefaultNumericTypes>::Tuple(Vec::new()).as_empty(),
        Err(EvalexprError::ExpectedEmpty {
            actual: Value::Tuple(Vec::new())
        })
    );
    assert_eq!(Value::<DefaultNumericTypes>::Empty.as_empty(), Ok(()));
}

#[test]
fn test_parenthese_combinations() {
    // These are from issue #94
    assert_eq!(
        eval("123(1*2)"),
        Err(EvalexprError::MissingOperatorOutsideOfBrace)
    );
    assert_eq!(
        eval("1()"),
        Err(EvalexprError::MissingOperatorOutsideOfBrace)
    );
    assert_eq!(
        eval("1()()()()"),
        Err(EvalexprError::MissingOperatorOutsideOfBrace)
    );
    assert_eq!(
        eval("1()()()(9)()()"),
        Err(EvalexprError::MissingOperatorOutsideOfBrace)
    );
    assert_eq!(
        eval_with_context("a+100(a*2)", &context_map! {"a" => int 4}.unwrap()),
        Err(EvalexprError::<DefaultNumericTypes>::MissingOperatorOutsideOfBrace)
    );
    assert_eq!(eval_int("(((1+2)*(3+4)+(5-(6)))/((7-8)))"), Ok(-20));
    assert_eq!(eval_int("(((((5)))))"), Ok(5));
}

#[test]
fn test_try_from() {
    #![allow(clippy::redundant_clone)]

    let value = Value::<DefaultNumericTypes>::String("abc".to_string());
    assert_eq!(String::try_from(value.clone()), Ok("abc".to_string()));
    assert_eq!(
        bool::try_from(value.clone()),
        Err(EvalexprError::ExpectedBoolean {
            actual: value.clone()
        })
    );
    assert_eq!(
        TupleType::try_from(value.clone()),
        Err(EvalexprError::ExpectedTuple {
            actual: value.clone()
        })
    );
    assert_eq!(
        EmptyType::try_from(value.clone()),
        Err(EvalexprError::ExpectedEmpty {
            actual: value.clone()
        })
    );

    let value = Value::<DefaultNumericTypes>::Float(1.3);
    assert_eq!(
        String::try_from(value.clone()),
        Err(EvalexprError::ExpectedString {
            actual: value.clone()
        })
    );
    assert_eq!(
        bool::try_from(value.clone()),
        Err(EvalexprError::ExpectedBoolean {
            actual: value.clone()
        })
    );
    assert_eq!(
        TupleType::try_from(value.clone()),
        Err(EvalexprError::ExpectedTuple {
            actual: value.clone()
        })
    );
    assert_eq!(
        EmptyType::try_from(value.clone()),
        Err(EvalexprError::ExpectedEmpty {
            actual: value.clone()
        })
    );

    let value = Value::<DefaultNumericTypes>::Int(13);
    assert_eq!(
        String::try_from(value.clone()),
        Err(EvalexprError::ExpectedString {
            actual: value.clone()
        })
    );
    assert_eq!(
        bool::try_from(value.clone()),
        Err(EvalexprError::ExpectedBoolean {
            actual: value.clone()
        })
    );
    assert_eq!(
        TupleType::try_from(value.clone()),
        Err(EvalexprError::ExpectedTuple {
            actual: value.clone()
        })
    );
    assert_eq!(
        EmptyType::try_from(value.clone()),
        Err(EvalexprError::ExpectedEmpty {
            actual: value.clone()
        })
    );

    let value = Value::<DefaultNumericTypes>::Boolean(true);
    assert_eq!(
        String::try_from(value.clone()),
        Err(EvalexprError::ExpectedString {
            actual: value.clone()
        })
    );
    assert_eq!(bool::try_from(value.clone()), Ok(true));
    assert_eq!(
        TupleType::try_from(value.clone()),
        Err(EvalexprError::ExpectedTuple {
            actual: value.clone()
        })
    );
    assert_eq!(
        EmptyType::try_from(value.clone()),
        Err(EvalexprError::ExpectedEmpty {
            actual: value.clone()
        })
    );

    let value =
        Value::<DefaultNumericTypes>::Tuple(vec![Value::Int(1), Value::String("abc".to_string())]);
    assert_eq!(
        String::try_from(value.clone()),
        Err(EvalexprError::ExpectedString {
            actual: value.clone()
        })
    );
    assert_eq!(
        bool::try_from(value.clone()),
        Err(EvalexprError::ExpectedBoolean {
            actual: value.clone()
        })
    );
    assert_eq!(
        TupleType::try_from(value.clone()),
        Ok(vec![Value::Int(1), Value::String("abc".to_string())])
    );
    assert_eq!(
        EmptyType::try_from(value.clone()),
        Err(EvalexprError::ExpectedEmpty {
            actual: value.clone()
        })
    );

    let value = Value::<DefaultNumericTypes>::Empty;
    assert_eq!(
        String::try_from(value.clone()),
        Err(EvalexprError::ExpectedString {
            actual: value.clone()
        })
    );
    assert_eq!(
        bool::try_from(value.clone()),
        Err(EvalexprError::ExpectedBoolean {
            actual: value.clone()
        })
    );
    assert_eq!(
        TupleType::try_from(value.clone()),
        Err(EvalexprError::ExpectedTuple {
            actual: value.clone()
        })
    );
    assert_eq!(EmptyType::try_from(value.clone()), Ok(()));
}

#[test]
fn test_negative_power() {
    assert_eq!(eval("3^-2"), Ok(Value::Float(1.0 / 9.0)));
    assert_eq!(eval("3^(-2)"), Ok(Value::Float(1.0 / 9.0)));
    assert_eq!(eval("-3^2"), Ok(Value::Float(-9.0)));
    assert_eq!(eval("-(3)^2"), Ok(Value::Float(-9.0)));
    assert_eq!(eval("(-3)^-2"), Ok(Value::Float(1.0 / 9.0)));
    assert_eq!(eval("-(3^-2)"), Ok(Value::Float(-1.0 / 9.0)));
}

#[test]
fn test_hex() {
    assert_eq!(eval("0x3"), Ok(Value::Int(3)));
    assert_eq!(eval("0xFF"), Ok(Value::Int(255)));
    assert_eq!(eval("-0xFF"), Ok(Value::Int(-255)));
    assert_eq!(
        eval("0x"),
        // The "VariableIdentifierNotFound" error is what evalexpr currently returns,
        // but ideally it would return more specific errors for "illegal" literals.
        Err(EvalexprError::VariableIdentifierNotFound("0x".into()))
    );
}

#[test]
fn test_binary() {
    assert_eq!(eval("0b11"), Ok(Value::Int(3)));
    assert_eq!(eval("0b0101"), Ok(Value::Int(5)));
    assert_eq!(eval("0b11111111"), Ok(Value::Int(255)));
    assert_eq!(eval("-0b11111111"), Ok(Value::Int(-255)));
    assert_eq!(
        eval("0b2"),
        // See `test_hex`.
        Err(EvalexprError::VariableIdentifierNotFound("0b2".into()))
    );
}

#[test]
fn test_octal() {
    assert_eq!(eval("0o12"), Ok(Value::Int(10)));
    assert_eq!(eval("0o3"), Ok(Value::Int(3)));
    assert_eq!(eval("0o377"), Ok(Value::Int(255)));
    assert_eq!(eval("-0o377"), Ok(Value::Int(-255)));
    assert_eq!(
        eval("0o8"),
        // See `test_hex`.
        Err(EvalexprError::VariableIdentifierNotFound("0o8".into()))
    );
}

#[test]
fn test_broken_string() {
    assert_eq!(
        eval(r#""abc" == "broken string"#),
        Err(EvalexprError::UnmatchedDoubleQuote)
    );
}

#[test]
fn test_comments() {
    assert_eq!(
        eval(
            "
            // input
            a = 1;  // assignment
            // output
            a + 2  // add"
        ),
        Ok(Value::Int(3))
    );

    assert_eq!(
        eval("0 /*"),
        Err(EvalexprError::CustomMessage(
            "unmatched inline comment".into()
        ))
    );

    assert_eq!(
        eval("1 % 4 + /*inline comment*/ 6 /*END*/"),
        Ok(Value::Int(7))
    );

    assert_eq!(
        eval("/* begin */ 10 /* middle */ + 5 /* end */ + 6 // DONE"),
        Ok(Value::Int(21))
    );
}

#[test]
fn test_compare_different_numeric_types() {
    assert_eq!(eval("1 < 2.0"), Ok(true.into()));
    assert_eq!(eval("1 >= 2"), Ok(false.into()));
    assert_eq!(eval("1 >= 2.0"), Ok(false.into()));
}

#[test]
fn test_escape_sequences() {
    assert_eq!(
        eval("\"\\x\""),
        Err(EvalexprError::IllegalEscapeSequence("\\x".to_string()))
    );
    assert_eq!(
        eval("\"\\"),
        Err(EvalexprError::IllegalEscapeSequence("\\".to_string()))
    );
}


#[test]
fn test_unmatched_partial_tokens() {
    assert!(matches!(
        eval("|"),
        Err(EvalexprError::UnmatchedPartialToken { .. })
    ));
}
