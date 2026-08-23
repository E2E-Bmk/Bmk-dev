# Validator Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`validator` is a reflective Go validation library that applies declarative tag rules to individual values, structs, nested collections, and maps. A reusable `Validate` instance owns registered rules and naming policies, while each validation call returns structured errors that expose rule, field, namespace, type, value, and parameter projections.

The installable module is `github.com/go-playground/validator/v10`. The selected interface covers the core in-process validation engine and requires no network service or persistent storage.

## Non-Goals

- This specification does not require locale translation packages or translator registration.
- This specification does not require filesystem, DNS, socket-resolution, cryptocurrency-address, country-code, or checksum validation tags.
- This specification does not define exact human-readable formatting for the aggregate `ValidationErrors.Error` string.
- This specification does not define internal reflection caches, parser nodes, goroutine layout, or source-file organization.

## Representative Workflows

The first workflow validates a request model and inspects structured errors.

```go
type Request struct {
    Name  string `validate:"required,min=3"`
    Email string `validate:"required,email"`
}

v := validator.New()
err := v.Struct(Request{Name: "ab", Email: "bad"})
for _, fe := range err.(validator.ValidationErrors) {
    fmt.Println(fe.Field(), fe.Tag(), fe.Param())
}
```

The second workflow composes naming, custom field validation, and structure-level validation on one reusable engine.

```go
v := validator.New()
v.RegisterTagNameFunc(func(sf reflect.StructField) string {
    return strings.SplitN(sf.Tag.Get("json"), ",", 2)[0]
})
_ = v.RegisterValidation("even", func(fl validator.FieldLevel) bool {
    return fl.Field().Int()%2 == 0
})
v.RegisterStructValidation(func(sl validator.StructLevel) {
    account := sl.Current().Interface().(Account)
    if account.Start > account.End {
        sl.ReportError(account.End, "End", "End", "afterstart", "")
    }
}, Account{})
err := v.Struct(Account{Count: 3, Start: 9, End: 2})
```

## Value Rules and Tag Expressions

Value validation parses comma-separated rule chains and applies them from left to right. Rule parameters follow `=` and alternatives within one rule use the library's documented separators.

**Presence and conditional execution.** When the `required` rule receives a zero value, nil pointer, nil interface, nil slice, or nil map, validation must fail with tag `required`. When `omitempty` receives an empty value, the remaining rules in that chain must be skipped. When `omitnil` receives a nil value, the remaining rules must be skipped, while a non-nil pointer to a zero value must continue through the chain.

**Size and ordering.** The `len`, `min`, `max`, `eq`, `ne`, `gt`, `gte`, `lt`, and `lte` rules must compare strings by rune count, collections by element count, numeric values numerically, and time-compatible values by their documented ordering. If the parameter is not valid for the reflected kind, then validation must fail or panic consistently rather than silently accepting the value.

**Membership and text.** The `oneof`, `oneofci`, `noneof`, `noneofci`, `contains`, `containsany`, `excludes`, `startswith`, `endswith`, `lowercase`, `uppercase`, `alpha`, `alphanum`, `numeric`, and `boolean` rules must apply their named membership or lexical predicate. `oneofci` and `noneofci` must compare strings without case sensitivity.

**Structured formats.** The `email`, `url`, `ip`, `ipv4`, `ipv6`, `cidr`, `uuid`, `uuid4`, `json`, `base64`, `datetime`, and `timezone` rules must accept valid values of their named formats and reject malformed values. The `datetime` parameter must be interpreted as a Go time layout.

**Alternatives and aliases.** When rules are separated with `|`, validation must succeed if at least one alternative succeeds. When all alternatives fail, `FieldError.Tag` must expose the joined alternative expression. When `RegisterAlias` maps an alias to a rule expression, the alias must behave as that expression while `Tag` reports the alias and `ActualTag` reports the underlying failing expression.

## Structures, Fields, and Collections

Structure validation traverses exported fields recursively and connects tag evaluation to stable field and namespace metadata.

**Recursive structures.** When `Struct` or `StructCtx` receives a struct or a non-nil pointer to a struct, all selected exported fields must be validated and nested structs must be traversed. When a nested field is excluded by `-`, it must not be validated. When `required` is enabled for non-pointer structs through `WithRequiredStructEnabled`, a zero-valued nested struct marked `required` must fail.

**Field selection.** `StructPartial` and `StructPartialCtx` must validate only named fields, including dotted nested paths. `StructExcept` and `StructExceptCtx` must validate every eligible field except the named paths. `StructFiltered` and `StructFilteredCtx` must call the filter with namespace bytes and skip fields for which the filter returns true.

**Cross-field conditions.** The `eqfield`, `nefield`, `gtfield`, `gtefield`, `ltfield`, and `ltefield` rules must compare the current field with another field in the same structure. The `required_if`, `required_unless`, `required_with`, `required_with_all`, `required_without`, and `required_without_all` families must determine presence from the referenced fields. The corresponding `excluded_*` families must reject a present current field when their condition is satisfied.

**Collection traversal.** When `dive` follows a rule chain, subsequent rules must be applied to each slice or array element and each map value. When `keys` and `endkeys` occur inside a map dive, rules between them must validate keys and rules after them must validate values. An element failure must preserve its index or map key in the returned namespace.

**Map rules.** `ValidateMap` and `ValidateMapCtx` accept data and a parallel rules map. String leaves must be treated as tag expressions, nested rule maps must recurse into nested data maps, successful fields must be absent from the result, and failed fields must map to validation errors or nested result maps.

## Registration and Callback Semantics

Registration extends a validator instance with user-defined field, type, and structure behaviors.

**Field callbacks.** `RegisterValidation` and `RegisterValidationCtx` accept a tag and callback. If the tag is empty or the callback is nil, registration must return an error. If the tag uses reserved names or separator characters, registration must panic. When the registered tag is evaluated, `FieldLevel` must expose the current field, field names, tag, parameter, and sibling lookup operations. Context-aware validation must receive the exact context passed to the validation entry point.

**Custom type projection.** When `RegisterCustomTypeFunc` associates a projector with one or more concrete types, validation rules must evaluate the projected value. If no projector is registered for a type, normal reflection behavior must remain unchanged.

**Structure callbacks.** When `RegisterStructValidation` or `RegisterStructValidationCtx` associates a callback with a structure type, the callback must run during structure validation. `StructLevel` must expose top, parent, current, validator, and error-reporting operations. Errors reported through `ReportError` must join ordinary field errors in the returned `ValidationErrors`; context-aware callbacks must receive the exact supplied context.

**Rule overlays.** When `RegisterStructValidationMapRules` supplies field-to-tag mappings for a structure type, those mappings must take precedence over validation tags for the named fields. Registrations affect subsequent calls on that `Validate` instance and must not mutate separately created instances.

## Error Metadata and Naming

Validation failures are observable through typed errors and field-level metadata rather than through exact aggregate message text.

**Error classification.** When validation succeeds, each entry point must return nil. When a valid value fails one or more rules, it must return `ValidationErrors`. Each failing field contributes a `FieldError`. When an entry point receives an unsupported top-level value, it must return `InvalidValidationError`. If a tag expression is syntactically invalid or names an undefined validator, then validation must panic.

**Field projections.** `FieldError.Tag` returns the exposed failing tag, `ActualTag` returns the underlying rule, `Param` returns its parameter, `Value` returns the rejected value, and `Kind` and `Type` return its reflected kind and type. `StructField` returns the Go field name; `Field` returns the alternate name when a naming function supplies one, otherwise the Go field name.

**Namespaces.** `StructNamespace` must use Go struct field names from the root type through nested fields and collection positions. `Namespace` must use alternate field names where configured while preserving the same path structure. Collection indices and map keys must appear as bracketed path components.

**Naming policy.** `SetTagName` must select the struct tag key from which validation rule expressions are read. `RegisterTagNameFunc` must derive alternate field names from `reflect.StructField`. When the derived alternate name is empty or `-`, field naming must fall back or omit according to the configured option rather than changing which underlying Go field failed.

## State Model

A `Validate` instance owns a tag-name policy, aliases, field callbacks, type projectors, structure callbacks, and structure-rule overlays. Validation calls combine that registry with an input value to produce either nil, `InvalidValidationError`, or `ValidationErrors`. Each `FieldError` projects one failed rule through exposed tag, underlying tag, field names, namespaces, parameter, value, kind, and type. Registration state persists across calls on the same instance and is independent across instances.

## Error Semantics

| Condition | Required response |
|---|---|
| A supported value satisfies every selected rule | Return nil |
| One or more validation rules fail | Return `ValidationErrors` containing `FieldError` entries |
| A structure entry point receives nil or a non-structure top-level value | Return `InvalidValidationError` |
| A tag expression is malformed, uses a missing parameter where required, or names an undefined rule | Panic during validation |
| Registration uses an empty tag or nil callback | `RegisterValidation` or `RegisterValidationCtx` returns a non-nil error |
| Registration uses a reserved name or separator character | Panic during registration |
| A partial/except path names no field | Continue without manufacturing an unrelated validation error |

## Cross-View Invariants

1. A rule failure reported by `Struct` must expose the same tag, parameter, value, kind, and type through its corresponding `FieldError`.
2. Alternate naming must change `Field` and `Namespace` while `StructField` and `StructNamespace` continue to identify the same Go field path.
3. Partial, except, and filtered validation must apply the same rule semantics as full validation to every field they select.
4. A custom field or structure callback failure must participate in the same `ValidationErrors` ordering and namespace model as a built-in rule failure.
5. Collection traversal must connect the failed element's value with the same bracketed index or key in both namespace projections.
6. Alias evaluation must connect the public alias in `Tag` to the failing underlying expression in `ActualTag` without changing success or failure.
7. Context-aware entry points must produce the same validation result as their context-free counterparts when callbacks do not inspect context.
8. Registrations on one `Validate` instance must affect all later relevant entry points on that instance and must not affect another instance.

## Public Interface

### Import Surface

```go
import validator "github.com/go-playground/validator/v10"
```

Exported identifiers in scope are `New`, `Validate`, `Option`, `WithRequiredStructEnabled`, `WithPrivateFieldValidation`, `WithTagNameFuncBlankOmit`, `Func`, `FuncCtx`, `FilterFunc`, `CustomTypeFunc`, `TagNameFunc`, `StructLevelFunc`, `StructLevelFuncCtx`, `FieldLevel`, `StructLevel`, `Valuer`, `InvalidValidationError`, `ValidationErrors`, `ValidationErrorsTranslations`, and `FieldError`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `New` | function | Creates an independent validation engine with options. |
| `Validate` | type | Stores registrations and exposes validation entry points. |
| `Option` | type | Configures a newly created validation engine. |
| `WithRequiredStructEnabled` | function | Enables required checks for non-pointer structures. |
| `WithPrivateFieldValidation` | function | Enables traversal of non-exported structure fields. |
| `WithTagNameFuncBlankOmit` | function | Changes handling of blank alternate field names. |
| `Func`, `FuncCtx` | function types | Define custom field validation callbacks. |
| `FilterFunc` | function type | Selects namespaces to skip during filtered validation. |
| `CustomTypeFunc` | function type | Projects custom types into validation values. |
| `TagNameFunc` | function type | Derives alternate field names. |
| `StructLevelFunc`, `StructLevelFuncCtx` | function types | Define structure-level validation callbacks. |
| `FieldLevel` | interface | Exposes the current field-validation context. |
| `StructLevel` | interface | Exposes the current structure-validation context. |
| `Valuer` | interface | Projects a validation value through a `Value` method. |
| `InvalidValidationError` | error type | Reports an unsupported top-level validation input. |
| `ValidationErrors` | error collection | Holds all field failures from one validation call. |
| `ValidationErrorsTranslations` | map type | Holds translated error strings keyed by namespace. |
| `FieldError` | interface | Exposes structured metadata for one failed field rule. |

`Validate` provides configuration methods `SetTagName`, `RegisterTagNameFunc`, `RegisterAlias`, `RegisterValidation`, `RegisterValidationCtx`, `RegisterStructValidation`, `RegisterStructValidationCtx`, `RegisterStructValidationMapRules`, and `RegisterCustomTypeFunc`. It provides entry points `Struct`, `StructCtx`, `StructFiltered`, `StructFilteredCtx`, `StructPartial`, `StructPartialCtx`, `StructExcept`, `StructExceptCtx`, `Var`, `VarCtx`, `VarWithValue`, `VarWithValueCtx`, `VarWithKey`, `VarWithKeyCtx`, `ValidateMap`, and `ValidateMapCtx`.

### CLI Entry Points

There is no console script for this package. `go run` command-package use is not supported. Programmatic use is through Go imports.

## Appendix A: Environment

The working environment runs Go 1.26 on Linux without network access. The Go standard library is available. The core selected interface requires no third-party runtime behavior. The project must declare module metadata in `go.mod` at the project root with module path `github.com/go-playground/validator/v10`.

## Appendix B: Assessment Notes

Assessment covers single-value rules, tag composition, recursive structures, field selection, collection traversal, maps, registrations, callbacks, error classes, metadata, namespaces, and cross-view consistency. Tests call only the documented import surface and assert observable results. Each top-level Go test function is evaluated independently, with separate atomic and integration groups.
