<!-- clauses.cleaned.md -->
# WTForms Contract Clauses

The clauses below restate the required public behavior in a stable identifier form.

| clause_id | section | clause |
|---|---|---|
| WTFORMS-PSM-001 | Product State Model | The input projection must return the same current value through `field.data` and `form.data[field_name]`. |
| WTFORMS-PSM-002 | Product State Model | A validation failure must return through both the field error projection and `form.errors[field_name]`. |
| WTFORMS-PSM-003 | Product State Model | A selected presentation choice must return the current input-projection value. |
| WTFORMS-FADP-001 | Forms and data processing | `Form(formdata=None, obj=None, prefix="", data=None, meta=None, **kwargs)` must bind declared public fields in declaration order and expose each one via both `form.field_name` and `form["field_name"]`. |
| WTFORMS-FADP-002 | Forms and data processing | Underscore-prefixed declarations must not bind. |
| WTFORMS-FADP-003 | Forms and data processing | A missing mapping key must raise `KeyError`. |
| WTFORMS-FADP-004 | Forms and data processing | `Form.process(formdata=None, obj=None, data=None, extra_filters=None, **kwargs)` must resolve each field using this complete precedence order: `formdata[field_name] > obj.field_name > kwargs[field_name] > data[field_name] > field default`. |
| WTFORMS-FADP-005 | Forms and data processing | A missing source must advance to the next source; a missing default must produce the empty/default field state rather than raise. |
| WTFORMS-FADP-006 | Forms and data processing | `Form.process` must run declared filters, then `extra_filters`, then an inline `filter_<fieldname>` method. |
| WTFORMS-FADP-007 | Forms and data processing | A filter that raises `ValueError` must add a processing error and make later validation fail without raising from form construction. |
| WTFORMS-FADP-008 | Forms and data processing | `Form.validate(extra_validators=None)` must validate every bound field, append an inline `validate_<fieldname>` after declared and supplied validators, populate errors, and return `True` only when all fields validate. |
| WTFORMS-FADP-009 | Forms and data processing | A non-callable validator, or a validator class supplied instead of an instance, must raise `TypeError` before validation. |
| WTFORMS-FADP-010 | Forms and data processing | `Form.populate_obj(obj)` must assign each current field value to the matching object attribute and overwrite an existing value. |
| WTFORMS-FADP-011 | Forms and data processing | A field that cannot populate its object must raise its documented `TypeError`. |
| WTFORMS-FADP-012 | Forms and data processing | `BaseForm(fields, prefix="", meta=...)` must expose the same processing, validation, data, errors, iteration, and mapping behavior for an explicit field mapping. |
| WTFORMS-FADP-013 | Forms and data processing | `Form` item assignment must raise `TypeError`; `BaseForm` must bind an assigned public field before processing and must raise the underlying lookup error for a missing item. |
| WTFORMS-FVAR-001 | Fields, validation, and rendering | `Field(label=None, validators=None, filters=(), description="", id=None, default=None, invalid_value_message=None, widget=None, render_kw=None, name=None, datalist=None, ...)` must be an unbound declaration outside a form and a bound field after binding. |
| WTFORMS-FVAR-002 | Fields, validation, and rendering | A bound field must expose `data`, `object_data`, `raw_data`, `process_errors`, `errors`, `name`, `short_name`, `id`, `label`, `description`, `flags`, `filters`, `widget`, and `meta`. |
| WTFORMS-FVAR-003 | Fields, validation, and rendering | A bound field must process object/default input before submitted input; submitted input must replace current data. |
| WTFORMS-FVAR-004 | Fields, validation, and rendering | A conversion or filter failure must accumulate in `process_errors`; `Field.validate` must copy it to `errors` and return `False`. |
| WTFORMS-FVAR-005 | Fields, validation, and rendering | `Field.validate(form, extra_validators=())` must run `pre_validate`, declared and extra validators, then `post_validate`. |
| WTFORMS-FVAR-006 | Fields, validation, and rendering | `ValidationError(message)` must add its message and continue. |
| WTFORMS-FVAR-007 | Fields, validation, and rendering | `StopValidation(message)` must add a non-empty message, stop remaining validators, and still run `post_validate`. |
| WTFORMS-FVAR-008 | Fields, validation, and rendering | A clean run must return `True` with empty errors. |
| WTFORMS-FVAR-009 | Fields, validation, and rendering | Calling a field, converting it with `str`, or calling `__html__` must return HTML-safe widget rendering. |
| WTFORMS-FVAR-010 | Fields, validation, and rendering | Rendering keyword arguments must reach the widget; a widget failure must propagate. |
| WTFORMS-FVAR-011 | Fields, validation, and rendering | `Label` must render an escaped label associated with its field id, and `Flags` must return `None` for an unset public flag. |
| WTFORMS-SATF-001 | Scalar and temporal fields | `StringField` must retain the first submitted value as text. |
| WTFORMS-SATF-002 | Scalar and temporal fields | `TextAreaField`, `HiddenField`, `SearchField`, `TelField`, `URLField`, `EmailField`, and `ColorField` must keep that data behavior while selecting their HTML control kinds. |
| WTFORMS-SATF-003 | Scalar and temporal fields | Missing submitted input must retain processed default or empty data. |
| WTFORMS-SATF-004 | Scalar and temporal fields | `BooleanField(false_values=(False, "false", ""))` must store `False` for a missing value or a first submitted value in `false_values`, and `True` otherwise. |
| WTFORMS-SATF-005 | Scalar and temporal fields | `SubmitField` must use that behavior. |
| WTFORMS-SATF-006 | Scalar and temporal fields | `ButtonField` must store its submitted text when clicked and `None` when absent, and must use its label as visible button content. |
| WTFORMS-SATF-007 | Scalar and temporal fields | `IntegerField`, `FloatField`, and `DecimalField` must coerce submitted text to `int`, `float`, and `decimal.Decimal`. |
| WTFORMS-SATF-008 | Scalar and temporal fields | Invalid text must set `data` to `None`, record a processing error, and make validation return `False` without raising from construction. |
| WTFORMS-SATF-009 | Scalar and temporal fields | `DecimalField` must use two display places when `places` is omitted and must not quantize display when `places=None`. |
| WTFORMS-SATF-010 | Scalar and temporal fields | Locale-aware numeric processing must raise `ImportError` when enabled without Babel. |
| WTFORMS-SATF-011 | Scalar and temporal fields | `DateTimeField(format="%Y-%m-%d %H:%M:%S")`, `DateField(format="%Y-%m-%d")`, `TimeField(format="%H:%M")`, `MonthField(format="%Y-%m")`, and `WeekField(format="%Y-W%W")` must parse input to documented `datetime`, `date`, or `time` values. |
| WTFORMS-SATF-012 | Scalar and temporal fields | Invalid input must set `data` to `None`, record a processing error, and make validation return `False`. |
| WTFORMS-SATF-013 | Scalar and temporal fields | `MonthField` must store day one; `WeekField` must store Monday when its format lacks a weekday. |
| WTFORMS-SATF-014 | Scalar and temporal fields | `DateTimeLocalField(tz=None)` must return naive values when `tz` resolves to `None` and attach the resolved timezone otherwise. |
| WTFORMS-SATF-015 | Scalar and temporal fields | `PasswordField` must accept submitted text but must not render stored text. |
| WTFORMS-SATF-016 | Scalar and temporal fields | `FileField` must preserve the framework-supplied filename or value without upload storage; `MultipleFileField` must retain the submitted list. |
| WTFORMS-CFDAN-001 | Choice fields, datalists, and nesting | `SelectChoice(value, label=None, render_kw={}, optgroup=None)` must default a missing label to value. |
| WTFORMS-CFDAN-002 | Choice fields, datalists, and nesting | `Choice(value, label, selected, render_kw)` must be the choice-iteration value. |
| WTFORMS-CFDAN-003 | Choice fields, datalists, and nesting | An unsupported choice tuple length must raise `ValueError` when normalized. |
| WTFORMS-CFDAN-004 | Choice fields, datalists, and nesting | `SelectField(label=None, validators=None, coerce=str, choices=None, validate_choice=True, invalid_value_message=None, invalid_choice_message=None, ...)` must coerce input, expose selected `Choice` values, and reject a value outside `choices` when choice validation is enabled. |
| WTFORMS-CFDAN-005 | Choice fields, datalists, and nesting | Coercion failure must be a processing error; invalid membership must be a validation error; missing choices with enabled validation must raise `TypeError`. |
| WTFORMS-CFDAN-006 | Choice fields, datalists, and nesting | Disabled choice validation must accept a coercible non-member. |
| WTFORMS-CFDAN-007 | Choice fields, datalists, and nesting | `SelectMultipleField` must coerce all submitted values to a list and reject every invalid selection when membership validation is enabled. |
| WTFORMS-CFDAN-008 | Choice fields, datalists, and nesting | `RadioField` must retain `SelectField` data and validation while iterating individual option fields. |
| WTFORMS-CFDAN-009 | Choice fields, datalists, and nesting | Choice callbacks must run once per processing cycle. |
| WTFORMS-CFDAN-010 | Choice fields, datalists, and nesting | A `(form, field)` callback must receive the bound form and field after processing; a no-argument callback must receive no arguments. |
| WTFORMS-CFDAN-011 | Choice fields, datalists, and nesting | A callback exception must propagate. |
| WTFORMS-CFDAN-012 | Choice fields, datalists, and nesting | `enum_choices(enum_cls, by="value", label=None)` must create `SelectChoice` values; `enum_coerce(enum_cls, by="value")` must round-trip the same member representation. |
| WTFORMS-CFDAN-013 | Choice fields, datalists, and nesting | A `by` value other than `"value"` or `"name"` must raise `ValueError`. |
| WTFORMS-CFDAN-014 | Choice fields, datalists, and nesting | `DataList(choices=None, *, render_kw=None, widget=None)` must provide suggestions for a text-like field without restricting submitted text. |
| WTFORMS-CFDAN-015 | Choice fields, datalists, and nesting | `DataListChoice(value, label=None, render_kw={})` must default label to value; `enum_datalist` must create analogous enum suggestions. |
| WTFORMS-CFDAN-016 | Choice fields, datalists, and nesting | An inline `DataList` must render its field-specific list reference and list; a string list reference must make `field.datalist()` return empty markup because the application owns it. |
| WTFORMS-CFDAN-017 | Choice fields, datalists, and nesting | `FormField(form_class, ..., separator="-")` must prefix, expose data and errors from, validate through, and populate a nested form. |
| WTFORMS-CFDAN-018 | Choice fields, datalists, and nesting | Filters, validators, and extra validators must raise `TypeError` because the enclosed form owns them. |
| WTFORMS-CFDAN-019 | Choice fields, datalists, and nesting | `FieldList(unbound_field, ..., min_entries=0, max_entries=None, separator="-", default=())` must expose ordered entries and list data, create enough blank entries for `min_entries`, cap submitted entries at `max_entries`, and compact indices, names, and ids after sparse input, insertion, or removal. |
| WTFORMS-CFDAN-020 | Choice fields, datalists, and nesting | Filters and extra filters must raise `TypeError`; `append_entry`, `insert_entry`, and `pop_entry` must return or remove the affected entry while preserving indices. |
| WTFORMS-VP-001 | Validator predicates | Every validator failure below must add a validation error and make field and form validation return `False`; `message` customizes that error without fixing its exact text. |
| WTFORMS-VP-002 | Validator predicates | `field_flags` from the documented validators must remain observable through `field.flags`. |
| WTFORMS-VP-003 | Validator predicates | `DataRequired(message=None)` must accept only truthy post-coercion `data`, with whitespace-only strings treated as false. |
| WTFORMS-VP-004 | Validator predicates | On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the remaining chain. |
| WTFORMS-VP-005 | Validator predicates | `InputRequired(message=None)` must instead accept only a non-empty first `raw_data` item; object/default data must not count as submitted input. |
| WTFORMS-VP-006 | Validator predicates | On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the chain. |
| WTFORMS-VP-007 | Validator predicates | `Optional(strip_whitespace=True)` must detect missing input, empty input, and, when whitespace stripping is enabled, whitespace-only first input; it must clear prior errors and stop remaining validators. |
| WTFORMS-VP-008 | Validator predicates | Thus `Optional()` before `DataRequired()` must validate empty submitted input successfully with no errors. |
| WTFORMS-VP-009 | Validator predicates | `EqualTo(fieldname, message=None)` must require equal `data` from the named field. |
| WTFORMS-VP-010 | Validator predicates | A missing named field must produce a validation failure. |
| WTFORMS-VP-011 | Validator predicates | `Length(min=-1, max=-1, message=None)` uses `-1` for an unset bound; construction must require at least one of `min` or `max` to differ from `-1` and must raise `AssertionError` when both remain `-1`. |
| WTFORMS-VP-012 | Validator predicates | A constructed `Length` must accept inclusive configured bounds and reject values outside them. |
| WTFORMS-VP-013 | Validator predicates | `NumberRange(min=None, max=None, message=None)` and `DateRange(min=None, max=None, message=None)` must accept inclusive comparable bounds, resolve callable bounds at validation time, and reject missing or out-of-range values; `NumberRange` must reject `NaN`. |
| WTFORMS-VP-014 | Validator predicates | `Regexp(regex, flags=0, message=None, matcher=re.match, html_pattern=False)` must accept a supplied matcher result and reject no match. |
| WTFORMS-VP-015 | Validator predicates | String patterns must compile with `flags`; `matcher` must default to prefix matching. |
| WTFORMS-VP-016 | Validator predicates | `html_pattern` must leave the presentation pattern unset when false, use the regex source when true, use a supplied string as the pattern, and resolve a callable against the compiled regex. |
| WTFORMS-VP-017 | Validator predicates | `Email(...)` must validate through the optional `email_validator` dependency; missing that dependency must raise its installation exception. |
| WTFORMS-VP-018 | Validator predicates | Its default deliverability check must be disabled. |
| WTFORMS-VP-019 | Validator predicates | `IPAddress(ipv4=True, ipv6=False, message=None)` must accept only enabled address families; enabling neither family must raise `ValueError`. |
| WTFORMS-VP-020 | Validator predicates | `MacAddress(message=None)` must accept only six colon-separated hexadecimal octets. |
| WTFORMS-VP-021 | Validator predicates | `URL(require_tld=True, allow_ip=True, allow_userinfo=False, schemes=("http", "https"), message=None)` must require a scheme and valid hostname, enforce configured TLD, IP, user-info, and scheme rules, and reject an invalid port. |
| WTFORMS-VP-022 | Validator predicates | `UUID(message=None)` must accept a `uuid.UUID` object or a parseable UUID string and reject other data. |
| WTFORMS-VP-023 | Validator predicates | `AnyOf(values, message=None, values_formatter=None)` must accept scalar data when it is a member of `values`, and list data when at least one element of `data` is a member of `values`. |
| WTFORMS-VP-024 | Validator predicates | `NoneOf(values, message=None, values_formatter=None)` must accept scalar data when it is absent from `values`, and list data when no element of `data` is a member of `values`. |
| WTFORMS-VP-025 | Validator predicates | `ReadOnly()` must set the readonly flag and reject a value different from `object_data`, including default-derived object data. |
| WTFORMS-VP-026 | Validator predicates | `Disabled()` must set the disabled flag and reject any submitted raw value, even when it equals object data. |
| WTFORMS-MCAT-001 | Meta, CSRF, and translations | Forms use `class Meta` to customize `DefaultMeta` behavior, and a form constructor `meta={...}` override must apply to that instance. |
| WTFORMS-MCAT-002 | Meta, CSRF, and translations | `csrf=True` must enable CSRF; `csrf_field_name` must name the automatically added token field; `csrf_class` must choose the implementation. |
| WTFORMS-MCAT-003 | Meta, CSRF, and translations | `DefaultMeta.build_csrf` must construct `csrf_class` without arguments when set, and otherwise construct `SessionCSRF`, once for each form instance. |
| WTFORMS-MCAT-004 | Meta, CSRF, and translations | `bind_field`, `wrap_formdata`, and `render_field` are override hooks: their returned bound field, wrapped formdata, or rendering result must become the form's public behavior. |
| WTFORMS-MCAT-005 | Meta, CSRF, and translations | The default wrapper must accept a `getlist` input object, adapt an iterable `getall` input object, and raise `TypeError` for another non-null submitted-data object. |
| WTFORMS-MCAT-006 | Meta, CSRF, and translations | A `getall` object that is not iterable must raise `TypeError` when form processing needs membership. |
| WTFORMS-MCAT-007 | Meta, CSRF, and translations | `CSRF.setup_form(form)` must add one `CSRFTokenField` named by `form.meta.csrf_field_name`. |
| WTFORMS-MCAT-008 | Meta, CSRF, and translations | A token field must retain submitted token data for validation, render its newly generated current token regardless of that submission, and never populate an application object. |
| WTFORMS-MCAT-009 | Meta, CSRF, and translations | Default CSRF validation must reject submitted data unequal to the current token. |
| WTFORMS-MCAT-010 | Meta, CSRF, and translations | A `CSRF` subclass must provide token generation; using its unimplemented generator must raise `NotImplementedError`. |
| WTFORMS-MCAT-011 | Meta, CSRF, and translations | `SessionCSRF` must require a byte `csrf_secret` and a session-like `csrf_context`; a missing secret must raise an exception and a missing context must raise `TypeError`. |
| WTFORMS-MCAT-012 | Meta, CSRF, and translations | It must keep a per-session CSRF value, generate a token authenticated with that value and the configured secret, and accept a later submission only when its authentication matches the same session and secret. |
| WTFORMS-MCAT-013 | Meta, CSRF, and translations | `csrf_time_limit` must default to 30 minutes; `None` must make tokens non-expiring, while a `timedelta` must make expired tokens fail validation. |
| WTFORMS-MCAT-014 | Meta, CSRF, and translations | `Meta.locales` must accept an ordered locale sequence for built-in-message translation, or `False` to disable translation. |
| WTFORMS-MCAT-015 | Meta, CSRF, and translations | `DefaultMeta.get_translations` must return `None` when locales are false; otherwise it must return an object with `gettext` and `ngettext`. |
| WTFORMS-MCAT-016 | Meta, CSRF, and translations | With `cache_translations=True`, equal locale choices must reuse the cached translation object. |
| WTFORMS-MCAT-017 | Meta, CSRF, and translations | An overriding `get_translations(form)` must supply the object used for built-in strings. |
| WTFORMS-ES-001 | Error Semantics | Conversion and filter `ValueError` instances must be reported by validation rather than escape construction. |
| WTFORMS-ES-002 | Error Semantics | Invalid choice coercion must be a processing error, invalid membership a validation error, and missing choices with required membership a `TypeError`. |
| WTFORMS-ES-003 | Error Semantics | Unsupported enum modes must raise `ValueError`; invalid declared validators must raise `TypeError`. |
| WTFORMS-ES-004 | Error Semantics | `Length` construction must raise `AssertionError` when both bounds are left at `-1`. |
| WTFORMS-CVI-001 | Cross-View Invariants | `form.data` must return each bound field's current `data` under its form attribute name. 2. |
| WTFORMS-CVI-002 | Cross-View Invariants | `form.errors` must return a field only when its `errors` is non-empty after validation. 3. |
| WTFORMS-CVI-003 | Cross-View Invariants | `form.validate()` must return `False` when any bound field reports errors, and `True` only when the error projection is empty. 4. |
| WTFORMS-CVI-004 | Cross-View Invariants | Submitted scalar input must appear in `field.raw_data` and, after successful coercion, return through `field.data` and `form.data`. 5. |
| WTFORMS-CVI-005 | Cross-View Invariants | A processing failure must return through `field.process_errors`, occur in `field.errors` after validation, and make `form.validate()` return `False`. 6. |
| WTFORMS-CVI-006 | Cross-View Invariants | A selected `iter_choices()` value must reflect the field's `data` value. 7. |
| WTFORMS-CVI-007 | Cross-View Invariants | `FormField.data` must equal its enclosed form's `data`, and `FormField.errors` must equal its enclosed form's error mapping. 8. |
| WTFORMS-CVI-008 | Cross-View Invariants | Each `FieldList` entry index, name, and id must return its contiguous sequence position. |
| WTFORMS-RW-001 | Representative Workflow | The form must convert submitted values before validation and expose failures through `errors`. |
| WTFORMS-RW-002 | Representative Workflow | Without submitted data, an application must construct the form without expecting automatic validation. |
| WTFORMS-UN-001 | Usage Notes | Applications must rely on public imports, public state projections, declared conversion and validation behavior, and template-safe rendering. |
| WTFORMS-UN-002 | Usage Notes | They must not rely on private attributes, internal module layout, exact error wording, or exact HTML serialization. |

<!-- solver-specification.complete.md -->
# WTForms Complete Public Specification

This document combines the base contract, the stable clause catalog, and the
lifecycle clarification addendum. When the addendum is more specific, its
observable public behavior takes precedence.

---


# WTForms Specification

> **Contract Authority**: This document defines the required public behavior.
> Compatibility with similarly named software does not supersede the
> interfaces, parameter names, behavioral boundaries, and error semantics
> stated here.

## Product Overview

WTForms provides declarative, framework-independent Python forms for accepting,
converting, validating, and rendering user input. A form declaration contains
field declarations; every form instance owns bound field instances with its own
data and errors. Submitted data must provide `getlist(name)`; a plain mapping
supplied as submitted data must raise the form-data wrapping error.

Applications must rely on public imports, public state projections, declared conversion and validation behavior, and template-safe rendering. They must not rely on private attributes, internal module layout, exact error wording, or exact HTML serialization.

## Non-Goals

- This API does not load requests, save models, or store uploaded file bytes.
- This API does not provide a web-framework integration or template language.
- This API does not require exact rendered-HTML ordering or whitespace beyond
  public field, label, choice, datalist, and widget contracts.
- This API does not promise exact default error wording.

## Representative Workflows

```python
from wtforms import Form, IntegerField, SelectField, StringField, validators

class Registration(Form):
    name = StringField("Name", [validators.InputRequired(), validators.Length(min=2)])
    age = IntegerField("Age", [validators.NumberRange(min=13)])
    role = SelectField("Role", choices=[("user", "User"), ("admin", "Admin")])

form = Registration(request.form)
if form.validate():
    account.name = form.name.data
    account.age = form.age.data
    account.role = form.role.data
else:
    errors = form.errors
```

The form must convert submitted values before validation and expose failures
through `errors`. Without submitted data, an application must construct the
form without expecting automatic validation.

## Form Processing and Binding

This section defines how forms bind fields, process input sources, run filters, validate fields, and populate objects.

**Field binding and access.** `Form` must bind declared public fields in declaration order and expose each one via both `form.field_name` and `form["field_name"]`. Underscore-prefixed declarations must not bind. A missing mapping key must raise `KeyError`. `Form` item assignment must raise `TypeError`.

**Processing precedence.** `Form.process` must resolve each field using this complete precedence order: `formdata[field_name]` takes highest priority, then `obj.field_name`, then `kwargs[field_name]`, then `data[field_name]`, and finally the field default. A missing source must advance to the next source; a missing default must produce the empty/default field state rather than raise.

**Filter chain.** `Form.process` must run declared filters first, then `extra_filters`, then an inline `filter_<fieldname>` method defined on the form class. A filter that raises `ValueError` must add a processing error and make later validation fail without raising from form construction.

**Validation.** `Form.validate` must validate every bound field, append an inline `validate_<fieldname>` after declared and supplied validators, populate errors, and return `True` only when all fields validate. A non-callable validator, or a validator class supplied instead of an instance, must raise `TypeError` before validation.

**Object population.** `Form.populate_obj(obj)` must assign each current field value to the matching object attribute and overwrite an existing value. A field that cannot populate its object must raise its documented `TypeError`.

**Data and error projections.** `Form.data` must return a mapping from each bound field's attribute name to its current `data`. `Form.errors` must return a mapping containing only fields whose `errors` is non-empty after validation.

**BaseForm.** `BaseForm` must expose the same processing, validation, data, errors, iteration, and mapping behavior for an explicit field mapping. `BaseForm` must bind an assigned public field before processing and must raise the underlying lookup error for a missing item.

## Field Lifecycle and Rendering

This section defines the lifecycle of a field from unbound declaration through bound processing, validation, and rendering.

**Binding and state.** A `Field` must be an unbound declaration outside a form and a bound field after binding. A bound field must expose `data`, `object_data`, `raw_data`, `process_errors`, `errors`, `name`, `short_name`, `id`, `label`, `description`, `flags`, `filters`, `widget`, and `meta`.

**Processing.** A bound field must process object/default input before submitted input; submitted input must replace current data. A conversion or filter failure must accumulate in `process_errors`. `Field.validate` must copy process errors to `errors` and return `False`.

**Validation chain.** `Field.validate` must run `pre_validate`, declared and extra validators, then `post_validate`. `ValidationError(message)` must add its message and continue. `StopValidation(message)` must add a non-empty message, stop remaining validators, and still run `post_validate`. A clean run must return `True` with empty errors.

**Rendering.** Calling a field, converting it with `str`, or calling `__html__` must return HTML-safe widget rendering. Rendering keyword arguments must reach the widget; a widget failure must propagate. `Label` must render an escaped label associated with its field id. `Flags` must return `None` for an unset public flag.

## Scalar and Temporal Fields

This section defines data coercion, storage, and temporal parsing for scalar value fields.

**String-like fields.** `StringField` must retain the first submitted value as text. When multiple values are submitted, `raw_data` must contain all submitted values but `data` must reflect the first value only. `TextAreaField`, `HiddenField`, `SearchField`, `TelField`, `URLField`, `EmailField`, and `ColorField` must keep that data behavior while selecting their HTML control kinds. Missing submitted input must retain the processed default or empty data.

**Boolean fields.** `BooleanField` must store `False` for a missing value or a first submitted value in `false_values` (defaulting to `(False, "false", "")`), and `True` otherwise. `SubmitField` must use that behavior; a submit field with no submitted value must store `False`. `ButtonField` must store its submitted text when clicked and `None` when absent, and must use its label as visible button content.

**Numeric fields.** `IntegerField`, `FloatField`, and `DecimalField` must coerce submitted text to `int`, `float`, and `decimal.Decimal`. Invalid text must set `data` to `None`, record a processing error, and make validation return `False` without raising from construction. `DecimalField` must use two display places when `places` is omitted and must not quantize display when `places=None`. Locale-aware numeric processing must raise `ImportError` when enabled without the locale processing dependency.

**Temporal fields.** `DateTimeField` (format `%Y-%m-%d %H:%M:%S`), `DateField` (format `%Y-%m-%d`), `TimeField` (format `%H:%M`), `MonthField` (format `%Y-%m`), and `WeekField` (format `%Y-W%W`) must parse input to documented `datetime`, `date`, `time`, or `date` values. Invalid input must set `data` to `None`, record a processing error, and make validation return `False`. `MonthField` must store day one of the parsed month. `WeekField` must store Monday when its format lacks a weekday. `DateTimeLocalField` must return naive values when `tz` resolves to `None` and attach the resolved timezone otherwise.

**Password and file fields.** `PasswordField` must accept submitted text but must not render stored text. `FileField` must preserve the framework-supplied filename or value without upload storage; `MultipleFileField` must retain the submitted list.

## Choice Fields, Datalists, and Nesting

This section defines selection fields, suggestion lists, and composite field structures for nested and repeated data.

**Choice types.** `SelectChoice` must default a missing label to value. `Choice` must be the choice-iteration value. An unsupported choice tuple length must raise `ValueError` when normalized.

**SelectField.** `SelectField` must coerce input, expose selected `Choice` values through `SelectField.iter_choices()`, and reject a value outside `choices` when choice validation is enabled. Coercion failure must be a processing error; invalid membership must be a validation error; missing choices with enabled validation must raise `TypeError`. When `validate_choice=False` is set, the field must accept a coercible non-member without raising a membership error. `SelectMultipleField` must coerce all submitted values to a list and reject every invalid selection when membership validation is enabled. `RadioField` must retain `SelectField` data and validation while iterating individual option fields.

**Choice callbacks.** Choice callbacks must run once per processing cycle. A `(form, field)` callback must receive the bound form and field after processing; a no-argument callback must receive no arguments. A callback exception must propagate.

**Enum helpers.** `enum_choices` must create `SelectChoice` values from an enum class; `enum_coerce` must round-trip the same member representation. A `by` value other than `"value"` or `"name"` must raise `ValueError`.

**DataList.** `DataList` must provide suggestions for a text-like field without restricting submitted text. `DataListChoice` must default label to value; `enum_datalist` must create analogous enum suggestions. An inline `DataList` must render its field-specific list reference and list; a string list reference must make `field.datalist()` return empty markup because the application owns it.

**FormField.** `FormField` must prefix its enclosed form's field names, delegate validation to the enclosed form, and expose nested data and errors. Filters, validators, and extra validators must raise `TypeError` because the enclosed form owns them.

**FieldList.** `FieldList` must expose ordered entries and list data, create enough blank entries for `min_entries`, cap submitted entries at `max_entries`, and compact indices, names, and ids after sparse input, insertion, or removal. Filters and extra filters must raise `TypeError`. `append_entry`, `insert_entry`, and `pop_entry` must return or remove the affected entry while preserving contiguous indices.

## Validator Predicates

This section defines the behavioral contract for each built-in validator.

**General contract.** Every validator failure must add a validation error and make field and form validation return `False`. The `message` parameter customizes that error without fixing its exact text. `field_flags` from the documented validators must remain observable through `field.flags`.

**DataRequired and InputRequired.** `DataRequired` must accept only truthy post-coercion `data`, with whitespace-only strings treated as false. On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the remaining chain. `InputRequired` must instead accept only a non-empty first `raw_data` item; object/default data must not count as submitted input. On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the chain.

**Optional.** `Optional` must detect missing input, empty input, and, when whitespace stripping is enabled, whitespace-only first input. It must clear prior errors and stop remaining validators. Thus `Optional()` before `DataRequired()` must validate empty submitted input successfully with no errors.

**EqualTo.** `EqualTo` must require equal `data` from the named field. A missing named field must produce a validation failure.

**Length.** `Length` uses `-1` for an unset bound. Construction must require at least one of `min` or `max` to differ from `-1` and must raise `AssertionError` when both remain `-1`. A constructed `Length` must accept values within inclusive configured bounds and reject values outside them.

**NumberRange and DateRange.** `NumberRange` must accept inclusive comparable bounds, resolve callable bounds at validation time, and reject missing or out-of-range values. `NumberRange` must reject `NaN`. `DateRange` must accept inclusive comparable date/time bounds and reject out-of-range values.

**Regexp.** `Regexp` must accept a supplied matcher result and reject no match. String patterns must compile with `flags`. The `matcher` parameter must default to prefix matching. `html_pattern` must leave the presentation pattern unset when false, use the regex source when true, use a supplied string as the pattern, and resolve a callable against the compiled regex.

**Network and identifier validators.** `Email` must validate through the optional `email_validator` dependency; missing that dependency must raise its installation exception. Its default deliverability check must be disabled. `IPAddress` must accept only enabled address families; enabling neither family must raise `ValueError`. `MacAddress` must accept only six colon-separated hexadecimal octets. `URL` must require a scheme and valid hostname, enforce configured TLD, IP, user-info, and scheme rules, and reject an invalid port. `UUID` must accept a `uuid.UUID` object or a parseable UUID string and reject other data.

**Set membership validators.** `AnyOf` must accept scalar data when it is a member of `values`, and list data when at least one element of `data` is a member of `values`. `NoneOf` must accept scalar data when it is absent from `values`, and list data when no element of `data` is a member of `values`.

**ReadOnly and Disabled.** `ReadOnly` must set the `readonly` flag and reject a value different from `object_data`, including default-derived object data. `Disabled` must set the `disabled` flag and reject any submitted raw value, even when it equals object data.

## Meta, CSRF, and Translations

This section defines form metaclass behavior, CSRF token protection, and built-in message translation.

**Meta customization.** Forms use `class Meta` to customize `DefaultMeta` behavior, and a form constructor `meta={...}` override must apply to that instance. `bind_field`, `wrap_formdata`, and `render_field` are override hooks: their returned bound field, wrapped formdata, or rendering result must become the form's public behavior.

**Formdata wrapping.** The default wrapper must accept a `getlist` input object, adapt an iterable `getall` input object, and raise `TypeError` for another non-null submitted-data object. A `getall` object that is not iterable must raise `TypeError` when form processing needs membership.

**CSRF.** `csrf=True` must enable CSRF; `csrf_field_name` must name the automatically added token field; `csrf_class` must choose the implementation. `DefaultMeta.build_csrf` must construct `csrf_class` without arguments when set, and otherwise construct `SessionCSRF`, once for each form instance. `CSRF.setup_form` must add one `CSRFTokenField` named by `form.meta.csrf_field_name`. A token field must retain submitted token data for validation, render its newly generated current token regardless of that submission, and never populate an application object. Default CSRF validation must reject submitted data unequal to the current token. A `CSRF` subclass must provide token generation; using its unimplemented generator must raise `NotImplementedError`.

**SessionCSRF.** `SessionCSRF` must require a byte `csrf_secret` and a session-like `csrf_context`; a missing secret must raise an exception and a missing context must raise `TypeError`. It must keep a per-session CSRF value, generate a token authenticated with that value and the configured secret, and accept a later submission only when its authentication matches the same session and secret. `csrf_time_limit` must default to 30 minutes; `None` must make tokens non-expiring, while a `timedelta` must make expired tokens fail validation.

**Translations.** `Meta.locales` must accept an ordered locale sequence for built-in-message translation, or `False` to disable translation. `DefaultMeta.get_translations` must return `None` when locales are false; otherwise it must return an object with `gettext` and `ngettext`. With `cache_translations=True`, equal locale choices must reuse the cached translation object. An overriding `get_translations(form)` must supply the object used for built-in strings. Caller-provided labels and messages remain caller data.

## State Model

A form has three public projections of one lifecycle state:

1. **Input projection:** each bound field exposes `raw_data`, `object_data`,
   and `data`; `form.data` maps field names to current `data`.
2. **Validation projection:** each field exposes `process_errors` and
   `errors`; `form.errors` contains non-empty field errors and form-level
   errors.
3. **Presentation projection:** each field exposes `name`, `id`, `label`,
   `flags`, and a callable renderer; choice fields expose selection through
   `Choice` values.

The input projection must return the same current value through `field.data`
and `form.data[field_name]`. A validation failure must return through both the
field error projection and `form.errors[field_name]`. A selected presentation
choice must return the current input-projection value.

## Error Semantics

`ValidationError` represents a validator failure; `StopValidation` stops the
remaining validator chain. Conversion and filter `ValueError` instances must be
reported by validation rather than escape construction. Invalid choice coercion
must be a processing error, invalid membership a validation error, and missing
choices with required membership a `TypeError`. Unsupported enum modes must
raise `ValueError`; invalid declared validators must raise `TypeError`.
`Length` construction must raise `AssertionError` when both bounds are left at
`-1`.

## Cross-View Invariants

1. `form.data` must return each bound field's current `data` under its form
   attribute name.
2. `form.errors` must return a field only when its `errors` is non-empty after
   validation.
3. `form.validate()` must return `False` when any bound field reports errors,
   and `True` only when the error projection is empty.
4. Submitted scalar input must appear in `field.raw_data` and, after successful
   coercion, return through `field.data` and `form.data`.
5. A processing failure must return through `field.process_errors`, occur in
   `field.errors` after validation, and make `form.validate()` return `False`.
6. A selected `iter_choices()` value must reflect the field's `data` value.
7. `FormField.data` must equal its enclosed form's `data`, and `FormField.errors`
   must equal its enclosed form's error mapping.
8. Each `FieldList` entry index, name, and id must return its contiguous
   sequence position.
9. `Form.populate_obj(obj)` must write each field's current `data` to the
   matching object attribute, so the resulting attribute value agrees with
   `field.data` at the time of population.

## Public Interface

### Import Surface

Install with `pip install WTForms`.

```python
from wtforms import (
    Form, ValidationError, Field, Flags, Label, DataList, DataListChoice,
    enum_datalist, Choice, SelectChoice, SelectField, SelectMultipleField,
    SelectFieldBase, RadioField, FormField, FieldList, BooleanField,
    ButtonField, StringField, TextAreaField, PasswordField, FileField,
    MultipleFileField, HiddenField, SearchField, SubmitField, TelField,
    URLField, EmailField, ColorField, IntegerField, DecimalField, FloatField,
    IntegerRangeField, DecimalRangeField, DateTimeField, DateField, TimeField,
    MonthField, WeekField, DateTimeLocalField, validators, widgets,
)
from wtforms.form import BaseForm
from wtforms.fields import (
    Choice, SelectChoice, SelectField, SelectMultipleField, SelectFieldBase,
    RadioField, FormField, FieldList, BooleanField, ButtonField, StringField,
    TextAreaField, PasswordField, FileField, MultipleFileField, HiddenField,
    SearchField, SubmitField, TelField, URLField, EmailField, ColorField,
    IntegerField, DecimalField, FloatField, IntegerRangeField, DecimalRangeField,
    DateTimeField, DateField, TimeField, MonthField, WeekField,
    DateTimeLocalField, enum_choices, enum_coerce,
)
from wtforms.validators import (
    ValidationError, StopValidation,
    DataRequired, data_required, InputRequired, input_required,
    Optional, optional, Length, length, NumberRange, number_range,
    DateRange, date_range, EqualTo, equal_to, Regexp, regexp,
    Email, email, IPAddress, ip_address, MacAddress, mac_address,
    URL, url, UUID, AnyOf, any_of, NoneOf, none_of,
    ReadOnly, readonly, Disabled, disabled,
)
from wtforms.widgets import (
    html_params, Input, TextInput, PasswordInput, HiddenInput, CheckboxInput,
    RadioInput, FileInput, SubmitInput, SearchInput, TelInput, URLInput,
    EmailInput, ColorInput, NumberInput, RangeInput, DateTimeInput, DateInput,
    MonthInput, WeekInput, TimeInput, DateTimeLocalInput, TextArea, Button,
    Option, Select, ListWidget, TableWidget, DataListWidget,
)
from wtforms.csrf.core import CSRF, CSRFTokenField
from wtforms.csrf.session import SessionCSRF
from wtforms.meta import DefaultMeta
```

`BaseForm` is available from `wtforms.form`; it is not an alternate export of `wtforms.fields`. Each lowercase validator name is an alias for its corresponding public class.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Form` | class | Declarative form with field binding, processing, validation, and rendering |
| `BaseForm` | class | Explicit-field form with the same processing and validation contract |
| `Field` | class | Base field with data processing, validation, and widget rendering |
| `Flags` | class | Boolean flag container observable through field attributes |
| `Label` | class | HTML label element associated with a field id |
| `StringField` | class | Single-value text field |
| `TextAreaField` | class | Multi-line text field |
| `PasswordField` | class | Text field that does not render stored text |
| `HiddenField` | class | Hidden-input text field |
| `SearchField` | class | Search-input text field |
| `TelField` | class | Telephone-input text field |
| `URLField` | class | URL-input text field |
| `EmailField` | class | Email-input text field |
| `ColorField` | class | Color-input text field |
| `IntegerField` | class | Field coercing input to `int` |
| `FloatField` | class | Field coercing input to `float` |
| `DecimalField` | class | Field coercing input to `decimal.Decimal` |
| `IntegerRangeField` | class | Range-input integer field |
| `DecimalRangeField` | class | Range-input decimal field |
| `BooleanField` | class | Checkbox field storing `True` or `False` |
| `SubmitField` | class | Submit-button boolean field |
| `ButtonField` | class | Button field storing clicked text or `None` |
| `FileField` | class | File-upload field preserving framework-supplied value |
| `MultipleFileField` | class | Multi-file-upload field retaining a list |
| `DateTimeField` | class | Field parsing datetime from formatted text |
| `DateField` | class | Field parsing date from formatted text |
| `TimeField` | class | Field parsing time from formatted text |
| `MonthField` | class | Field parsing year-month to day-one date |
| `WeekField` | class | Field parsing year-week to Monday date |
| `DateTimeLocalField` | class | Datetime field with optional timezone attachment |
| `SelectField` | class | Single-selection choice field with coercion and validation |
| `SelectMultipleField` | class | Multi-selection choice field coercing to a list |
| `RadioField` | class | Radio-button choice field iterating individual options |
| `SelectFieldBase` | class | Base class for choice-based fields |
| `Choice` | namedtuple | Choice-iteration value with value, label, selected, and render_kw |
| `SelectChoice` | class | Choice declaration with value, label, render_kw, and optgroup |
| `DataList` | class | Suggestion list for text-like fields without restricting input |
| `DataListChoice` | class | Suggestion entry with value, label, and render_kw |
| `enum_datalist` | function | Create `DataList` suggestions from an enum class |
| `enum_choices` | function | Create `SelectChoice` values from an enum class |
| `enum_coerce` | function | Create a coerce function round-tripping enum members |
| `FormField` | class | Field wrapping a nested form with prefixed names |
| `FieldList` | class | Field wrapping an ordered list of sub-field entries |
| `ValidationError` | exception | Validator failure carrying an error message |
| `StopValidation` | exception | Stop remaining validators with an optional message |
| `DataRequired` | class | Validator requiring truthy post-coercion data |
| `InputRequired` | class | Validator requiring non-empty submitted raw data |
| `Optional` | class | Validator that clears errors and stops chain on missing input |
| `Length` | class | Validator enforcing inclusive string-length bounds |
| `NumberRange` | class | Validator enforcing inclusive numeric bounds |
| `DateRange` | class | Validator enforcing inclusive date/time bounds |
| `EqualTo` | class | Validator requiring equal data from a named sibling field |
| `Regexp` | class | Validator matching data against a regular expression |
| `Email` | class | Validator checking email via `email_validator` dependency |
| `IPAddress` | class | Validator accepting enabled IPv4/IPv6 address families |
| `MacAddress` | class | Validator accepting six colon-separated hex octets |
| `URL` | class | Validator enforcing scheme, hostname, and port rules |
| `UUID` | class | Validator accepting UUID objects or parseable UUID strings |
| `AnyOf` | class | Validator accepting data present in a value set |
| `NoneOf` | class | Validator accepting data absent from a value set |
| `ReadOnly` | class | Validator rejecting changes from original object data |
| `Disabled` | class | Validator rejecting any submitted raw value |
| `DefaultMeta` | class | Default form meta with CSRF, translation, and hook support |
| `CSRF` | class | Base CSRF implementation adding a token field to forms |
| `CSRFTokenField` | class | Auto-generated CSRF token field |
| `SessionCSRF` | class | Session-and-secret-based CSRF token implementation |

### CLI Entry Points

There is no console script for this package. `python -m WTForms`.` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` in the implementation's top-level directory. All declared dependencies must be installable before the package is used.

## Appendix B: Lifecycle Notes

Applications that evolve form declarations must treat each form instance as
owning its bound fields, current data, and error state. A declaration remains
an unbound field until form binding; changes made while processing one form
must not alter another form instance's bound field state.

Applications that introduce new input paths must preserve the documented
processing order: submitted values take precedence over object attributes,
keyword values, mapping data, and field defaults. Conversion and filter
failures must remain visible through processing and validation errors rather
than escaping form construction.

Applications that customize rendering, validation, or form metadata must rely
on the declared public hooks and projections. Bound-field rendering must remain
HTML-safe, validation failures must remain available through field and form
errors, and configured Meta, CSRF, and translation behavior must apply to the
form instance that receives it.



---

# WTForms Contract Clauses

The clauses below restate the required public behavior in a stable identifier form.

| clause_id | section | clause |
|---|---|---|
| WTFORMS-PSM-001 | Product State Model | The input projection must return the same current value through `field.data` and `form.data[field_name]`. |
| WTFORMS-PSM-002 | Product State Model | A validation failure must return through both the field error projection and `form.errors[field_name]`. |
| WTFORMS-PSM-003 | Product State Model | A selected presentation choice must return the current input-projection value. |
| WTFORMS-FADP-001 | Forms and data processing | `Form(formdata=None, obj=None, prefix="", data=None, meta=None, **kwargs)` must bind declared public fields in declaration order and expose each one via both `form.field_name` and `form["field_name"]`. |
| WTFORMS-FADP-002 | Forms and data processing | Underscore-prefixed declarations must not bind. |
| WTFORMS-FADP-003 | Forms and data processing | A missing mapping key must raise `KeyError`. |
| WTFORMS-FADP-004 | Forms and data processing | `Form.process(formdata=None, obj=None, data=None, extra_filters=None, **kwargs)` must resolve each field using this complete precedence order: `formdata[field_name] > obj.field_name > kwargs[field_name] > data[field_name] > field default`. |
| WTFORMS-FADP-005 | Forms and data processing | A missing source must advance to the next source; a missing default must produce the empty/default field state rather than raise. |
| WTFORMS-FADP-006 | Forms and data processing | `Form.process` must run declared filters, then `extra_filters`, then an inline `filter_<fieldname>` method. |
| WTFORMS-FADP-007 | Forms and data processing | A filter that raises `ValueError` must add a processing error and make later validation fail without raising from form construction. |
| WTFORMS-FADP-008 | Forms and data processing | `Form.validate(extra_validators=None)` must validate every bound field, append an inline `validate_<fieldname>` after declared and supplied validators, populate errors, and return `True` only when all fields validate. |
| WTFORMS-FADP-009 | Forms and data processing | A non-callable validator, or a validator class supplied instead of an instance, must raise `TypeError` before validation. |
| WTFORMS-FADP-010 | Forms and data processing | `Form.populate_obj(obj)` must assign each current field value to the matching object attribute and overwrite an existing value. |
| WTFORMS-FADP-011 | Forms and data processing | A field that cannot populate its object must raise its documented `TypeError`. |
| WTFORMS-FADP-012 | Forms and data processing | `BaseForm(fields, prefix="", meta=...)` must expose the same processing, validation, data, errors, iteration, and mapping behavior for an explicit field mapping. |
| WTFORMS-FADP-013 | Forms and data processing | `Form` item assignment must raise `TypeError`; `BaseForm` must bind an assigned public field before processing and must raise the underlying lookup error for a missing item. |
| WTFORMS-FVAR-001 | Fields, validation, and rendering | `Field(label=None, validators=None, filters=(), description="", id=None, default=None, invalid_value_message=None, widget=None, render_kw=None, name=None, datalist=None, ...)` must be an unbound declaration outside a form and a bound field after binding. |
| WTFORMS-FVAR-002 | Fields, validation, and rendering | A bound field must expose `data`, `object_data`, `raw_data`, `process_errors`, `errors`, `name`, `short_name`, `id`, `label`, `description`, `flags`, `filters`, `widget`, and `meta`. |
| WTFORMS-FVAR-003 | Fields, validation, and rendering | A bound field must process object/default input before submitted input; submitted input must replace current data. |
| WTFORMS-FVAR-004 | Fields, validation, and rendering | A conversion or filter failure must accumulate in `process_errors`; `Field.validate` must copy it to `errors` and return `False`. |
| WTFORMS-FVAR-005 | Fields, validation, and rendering | `Field.validate(form, extra_validators=())` must run `pre_validate`, declared and extra validators, then `post_validate`. |
| WTFORMS-FVAR-006 | Fields, validation, and rendering | `ValidationError(message)` must add its message and continue. |
| WTFORMS-FVAR-007 | Fields, validation, and rendering | `StopValidation(message)` must add a non-empty message, stop remaining validators, and still run `post_validate`. |
| WTFORMS-FVAR-008 | Fields, validation, and rendering | A clean run must return `True` with empty errors. |
| WTFORMS-FVAR-009 | Fields, validation, and rendering | Calling a field, converting it with `str`, or calling `__html__` must return HTML-safe widget rendering. |
| WTFORMS-FVAR-010 | Fields, validation, and rendering | Rendering keyword arguments must reach the widget; a widget failure must propagate. |
| WTFORMS-FVAR-011 | Fields, validation, and rendering | `Label` must render an escaped label associated with its field id, and `Flags` must return `None` for an unset public flag. |
| WTFORMS-SATF-001 | Scalar and temporal fields | `StringField` must retain the first submitted value as text. |
| WTFORMS-SATF-002 | Scalar and temporal fields | `TextAreaField`, `HiddenField`, `SearchField`, `TelField`, `URLField`, `EmailField`, and `ColorField` must keep that data behavior while selecting their HTML control kinds. |
| WTFORMS-SATF-003 | Scalar and temporal fields | Missing submitted input must retain processed default or empty data. |
| WTFORMS-SATF-004 | Scalar and temporal fields | `BooleanField(false_values=(False, "false", ""))` must store `False` for a missing value or a first submitted value in `false_values`, and `True` otherwise. |
| WTFORMS-SATF-005 | Scalar and temporal fields | `SubmitField` must use that behavior. |
| WTFORMS-SATF-006 | Scalar and temporal fields | `ButtonField` must store its submitted text when clicked and `None` when absent, and must use its label as visible button content. |
| WTFORMS-SATF-007 | Scalar and temporal fields | `IntegerField`, `FloatField`, and `DecimalField` must coerce submitted text to `int`, `float`, and `decimal.Decimal`. |
| WTFORMS-SATF-008 | Scalar and temporal fields | Invalid text must set `data` to `None`, record a processing error, and make validation return `False` without raising from construction. |
| WTFORMS-SATF-009 | Scalar and temporal fields | `DecimalField` must use two display places when `places` is omitted and must not quantize display when `places=None`. |
| WTFORMS-SATF-010 | Scalar and temporal fields | Locale-aware numeric processing must raise `ImportError` when enabled without Babel. |
| WTFORMS-SATF-011 | Scalar and temporal fields | `DateTimeField(format="%Y-%m-%d %H:%M:%S")`, `DateField(format="%Y-%m-%d")`, `TimeField(format="%H:%M")`, `MonthField(format="%Y-%m")`, and `WeekField(format="%Y-W%W")` must parse input to documented `datetime`, `date`, or `time` values. |
| WTFORMS-SATF-012 | Scalar and temporal fields | Invalid input must set `data` to `None`, record a processing error, and make validation return `False`. |
| WTFORMS-SATF-013 | Scalar and temporal fields | `MonthField` must store day one; `WeekField` must store Monday when its format lacks a weekday. |
| WTFORMS-SATF-014 | Scalar and temporal fields | `DateTimeLocalField(tz=None)` must return naive values when `tz` resolves to `None` and attach the resolved timezone otherwise. |
| WTFORMS-SATF-015 | Scalar and temporal fields | `PasswordField` must accept submitted text but must not render stored text. |
| WTFORMS-SATF-016 | Scalar and temporal fields | `FileField` must preserve the framework-supplied filename or value without upload storage; `MultipleFileField` must retain the submitted list. |
| WTFORMS-CFDAN-001 | Choice fields, datalists, and nesting | `SelectChoice(value, label=None, render_kw={}, optgroup=None)` must default a missing label to value. |
| WTFORMS-CFDAN-002 | Choice fields, datalists, and nesting | `Choice(value, label, selected, render_kw)` must be the choice-iteration value. |
| WTFORMS-CFDAN-003 | Choice fields, datalists, and nesting | An unsupported choice tuple length must raise `ValueError` when normalized. |
| WTFORMS-CFDAN-004 | Choice fields, datalists, and nesting | `SelectField(label=None, validators=None, coerce=str, choices=None, validate_choice=True, invalid_value_message=None, invalid_choice_message=None, ...)` must coerce input, expose selected `Choice` values, and reject a value outside `choices` when choice validation is enabled. |
| WTFORMS-CFDAN-005 | Choice fields, datalists, and nesting | Coercion failure must be a processing error; invalid membership must be a validation error; missing choices with enabled validation must raise `TypeError`. |
| WTFORMS-CFDAN-006 | Choice fields, datalists, and nesting | Disabled choice validation must accept a coercible non-member. |
| WTFORMS-CFDAN-007 | Choice fields, datalists, and nesting | `SelectMultipleField` must coerce all submitted values to a list and reject every invalid selection when membership validation is enabled. |
| WTFORMS-CFDAN-008 | Choice fields, datalists, and nesting | `RadioField` must retain `SelectField` data and validation while iterating individual option fields. |
| WTFORMS-CFDAN-009 | Choice fields, datalists, and nesting | Choice callbacks must run once per processing cycle. |
| WTFORMS-CFDAN-010 | Choice fields, datalists, and nesting | A `(form, field)` callback must receive the bound form and field after processing; a no-argument callback must receive no arguments. |
| WTFORMS-CFDAN-011 | Choice fields, datalists, and nesting | A callback exception must propagate. |
| WTFORMS-CFDAN-012 | Choice fields, datalists, and nesting | `enum_choices(enum_cls, by="value", label=None)` must create `SelectChoice` values; `enum_coerce(enum_cls, by="value")` must round-trip the same member representation. |
| WTFORMS-CFDAN-013 | Choice fields, datalists, and nesting | A `by` value other than `"value"` or `"name"` must raise `ValueError`. |
| WTFORMS-CFDAN-014 | Choice fields, datalists, and nesting | `DataList(choices=None, *, render_kw=None, widget=None)` must provide suggestions for a text-like field without restricting submitted text. |
| WTFORMS-CFDAN-015 | Choice fields, datalists, and nesting | `DataListChoice(value, label=None, render_kw={})` must default label to value; `enum_datalist` must create analogous enum suggestions. |
| WTFORMS-CFDAN-016 | Choice fields, datalists, and nesting | An inline `DataList` must render its field-specific list reference and list; a string list reference must make `field.datalist()` return empty markup because the application owns it. |
| WTFORMS-CFDAN-017 | Choice fields, datalists, and nesting | `FormField(form_class, ..., separator="-")` must prefix, expose data and errors from, validate through, and populate a nested form. |
| WTFORMS-CFDAN-018 | Choice fields, datalists, and nesting | Filters, validators, and extra validators must raise `TypeError` because the enclosed form owns them. |
| WTFORMS-CFDAN-019 | Choice fields, datalists, and nesting | `FieldList(unbound_field, ..., min_entries=0, max_entries=None, separator="-", default=())` must expose ordered entries and list data, create enough blank entries for `min_entries`, cap submitted entries at `max_entries`, and compact indices, names, and ids after sparse input, insertion, or removal. |
| WTFORMS-CFDAN-020 | Choice fields, datalists, and nesting | Filters and extra filters must raise `TypeError`; `append_entry`, `insert_entry`, and `pop_entry` must return or remove the affected entry while preserving indices. |
| WTFORMS-VP-001 | Validator predicates | Every validator failure below must add a validation error and make field and form validation return `False`; `message` customizes that error without fixing its exact text. |
| WTFORMS-VP-002 | Validator predicates | `field_flags` from the documented validators must remain observable through `field.flags`. |
| WTFORMS-VP-003 | Validator predicates | `DataRequired(message=None)` must accept only truthy post-coercion `data`, with whitespace-only strings treated as false. |
| WTFORMS-VP-004 | Validator predicates | On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the remaining chain. |
| WTFORMS-VP-005 | Validator predicates | `InputRequired(message=None)` must instead accept only a non-empty first `raw_data` item; object/default data must not count as submitted input. |
| WTFORMS-VP-006 | Validator predicates | On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the chain. |
| WTFORMS-VP-007 | Validator predicates | `Optional(strip_whitespace=True)` must detect missing input, empty input, and, when whitespace stripping is enabled, whitespace-only first input; it must clear prior errors and stop remaining validators. |
| WTFORMS-VP-008 | Validator predicates | Thus `Optional()` before `DataRequired()` must validate empty submitted input successfully with no errors. |
| WTFORMS-VP-009 | Validator predicates | `EqualTo(fieldname, message=None)` must require equal `data` from the named field. |
| WTFORMS-VP-010 | Validator predicates | A missing named field must produce a validation failure. |
| WTFORMS-VP-011 | Validator predicates | `Length(min=-1, max=-1, message=None)` uses `-1` for an unset bound; construction must require at least one of `min` or `max` to differ from `-1` and must raise `AssertionError` when both remain `-1`. |
| WTFORMS-VP-012 | Validator predicates | A constructed `Length` must accept inclusive configured bounds and reject values outside them. |
| WTFORMS-VP-013 | Validator predicates | `NumberRange(min=None, max=None, message=None)` and `DateRange(min=None, max=None, message=None)` must accept inclusive comparable bounds, resolve callable bounds at validation time, and reject missing or out-of-range values; `NumberRange` must reject `NaN`. |
| WTFORMS-VP-014 | Validator predicates | `Regexp(regex, flags=0, message=None, matcher=re.match, html_pattern=False)` must accept a supplied matcher result and reject no match. |
| WTFORMS-VP-015 | Validator predicates | String patterns must compile with `flags`; `matcher` must default to prefix matching. |
| WTFORMS-VP-016 | Validator predicates | `html_pattern` must leave the presentation pattern unset when false, use the regex source when true, use a supplied string as the pattern, and resolve a callable against the compiled regex. |
| WTFORMS-VP-017 | Validator predicates | `Email(...)` must validate through the optional `email_validator` dependency; missing that dependency must raise its installation exception. |
| WTFORMS-VP-018 | Validator predicates | Its default deliverability check must be disabled. |
| WTFORMS-VP-019 | Validator predicates | `IPAddress(ipv4=True, ipv6=False, message=None)` must accept only enabled address families; enabling neither family must raise `ValueError`. |
| WTFORMS-VP-020 | Validator predicates | `MacAddress(message=None)` must accept only six colon-separated hexadecimal octets. |
| WTFORMS-VP-021 | Validator predicates | `URL(require_tld=True, allow_ip=True, allow_userinfo=False, schemes=("http", "https"), message=None)` must require a scheme and valid hostname, enforce configured TLD, IP, user-info, and scheme rules, and reject an invalid port. |
| WTFORMS-VP-022 | Validator predicates | `UUID(message=None)` must accept a `uuid.UUID` object or a parseable UUID string and reject other data. |
| WTFORMS-VP-023 | Validator predicates | `AnyOf(values, message=None, values_formatter=None)` must accept scalar data when it is a member of `values`, and list data when at least one element of `data` is a member of `values`. |
| WTFORMS-VP-024 | Validator predicates | `NoneOf(values, message=None, values_formatter=None)` must accept scalar data when it is absent from `values`, and list data when no element of `data` is a member of `values`. |
| WTFORMS-VP-025 | Validator predicates | `ReadOnly()` must set the readonly flag and reject a value different from `object_data`, including default-derived object data. |
| WTFORMS-VP-026 | Validator predicates | `Disabled()` must set the disabled flag and reject any submitted raw value, even when it equals object data. |
| WTFORMS-MCAT-001 | Meta, CSRF, and translations | Forms use `class Meta` to customize `DefaultMeta` behavior, and a form constructor `meta={...}` override must apply to that instance. |
| WTFORMS-MCAT-002 | Meta, CSRF, and translations | `csrf=True` must enable CSRF; `csrf_field_name` must name the automatically added token field; `csrf_class` must choose the implementation. |
| WTFORMS-MCAT-003 | Meta, CSRF, and translations | `DefaultMeta.build_csrf` must construct `csrf_class` without arguments when set, and otherwise construct `SessionCSRF`, once for each form instance. |
| WTFORMS-MCAT-004 | Meta, CSRF, and translations | `bind_field`, `wrap_formdata`, and `render_field` are override hooks: their returned bound field, wrapped formdata, or rendering result must become the form's public behavior. |
| WTFORMS-MCAT-005 | Meta, CSRF, and translations | The default wrapper must accept a `getlist` input object, adapt an iterable `getall` input object, and raise `TypeError` for another non-null submitted-data object. |
| WTFORMS-MCAT-006 | Meta, CSRF, and translations | A `getall` object that is not iterable must raise `TypeError` when form processing needs membership. |
| WTFORMS-MCAT-007 | Meta, CSRF, and translations | `CSRF.setup_form(form)` must add one `CSRFTokenField` named by `form.meta.csrf_field_name`. |
| WTFORMS-MCAT-008 | Meta, CSRF, and translations | A token field must retain submitted token data for validation, render its newly generated current token regardless of that submission, and never populate an application object. |
| WTFORMS-MCAT-009 | Meta, CSRF, and translations | Default CSRF validation must reject submitted data unequal to the current token. |
| WTFORMS-MCAT-010 | Meta, CSRF, and translations | A `CSRF` subclass must provide token generation; using its unimplemented generator must raise `NotImplementedError`. |
| WTFORMS-MCAT-011 | Meta, CSRF, and translations | `SessionCSRF` must require a byte `csrf_secret` and a session-like `csrf_context`; a missing secret must raise an exception and a missing context must raise `TypeError`. |
| WTFORMS-MCAT-012 | Meta, CSRF, and translations | It must keep a per-session CSRF value, generate a token authenticated with that value and the configured secret, and accept a later submission only when its authentication matches the same session and secret. |
| WTFORMS-MCAT-013 | Meta, CSRF, and translations | `csrf_time_limit` must default to 30 minutes; `None` must make tokens non-expiring, while a `timedelta` must make expired tokens fail validation. |
| WTFORMS-MCAT-014 | Meta, CSRF, and translations | `Meta.locales` must accept an ordered locale sequence for built-in-message translation, or `False` to disable translation. |
| WTFORMS-MCAT-015 | Meta, CSRF, and translations | `DefaultMeta.get_translations` must return `None` when locales are false; otherwise it must return an object with `gettext` and `ngettext`. |
| WTFORMS-MCAT-016 | Meta, CSRF, and translations | With `cache_translations=True`, equal locale choices must reuse the cached translation object. |
| WTFORMS-MCAT-017 | Meta, CSRF, and translations | An overriding `get_translations(form)` must supply the object used for built-in strings. |
| WTFORMS-ES-001 | Error Semantics | Conversion and filter `ValueError` instances must be reported by validation rather than escape construction. |
| WTFORMS-ES-002 | Error Semantics | Invalid choice coercion must be a processing error, invalid membership a validation error, and missing choices with required membership a `TypeError`. |
| WTFORMS-ES-003 | Error Semantics | Unsupported enum modes must raise `ValueError`; invalid declared validators must raise `TypeError`. |
| WTFORMS-ES-004 | Error Semantics | `Length` construction must raise `AssertionError` when both bounds are left at `-1`. |
| WTFORMS-CVI-001 | Cross-View Invariants | `form.data` must return each bound field's current `data` under its form attribute name. 2. |
| WTFORMS-CVI-002 | Cross-View Invariants | `form.errors` must return a field only when its `errors` is non-empty after validation. 3. |
| WTFORMS-CVI-003 | Cross-View Invariants | `form.validate()` must return `False` when any bound field reports errors, and `True` only when the error projection is empty. 4. |
| WTFORMS-CVI-004 | Cross-View Invariants | Submitted scalar input must appear in `field.raw_data` and, after successful coercion, return through `field.data` and `form.data`. 5. |
| WTFORMS-CVI-005 | Cross-View Invariants | A processing failure must return through `field.process_errors`, occur in `field.errors` after validation, and make `form.validate()` return `False`. 6. |
| WTFORMS-CVI-006 | Cross-View Invariants | A selected `iter_choices()` value must reflect the field's `data` value. 7. |
| WTFORMS-CVI-007 | Cross-View Invariants | `FormField.data` must equal its enclosed form's `data`, and `FormField.errors` must equal its enclosed form's error mapping. 8. |
| WTFORMS-CVI-008 | Cross-View Invariants | Each `FieldList` entry index, name, and id must return its contiguous sequence position. |
| WTFORMS-RW-001 | Representative Workflow | The form must convert submitted values before validation and expose failures through `errors`. |
| WTFORMS-RW-002 | Representative Workflow | Without submitted data, an application must construct the form without expecting automatic validation. |
| WTFORMS-UN-001 | Usage Notes | Applications must rely on public imports, public state projections, declared conversion and validation behavior, and template-safe rendering. |
| WTFORMS-UN-002 | Usage Notes | They must not rely on private attributes, internal module layout, exact error wording, or exact HTML serialization. |



---


# WTForms Lifecycle Clarification Addendum

This addendum extends the WTForms specification for the locked public behavior.
It is authoritative where it is more specific than the base specification. It
describes observable behavior only; it does not prescribe an internal module
layout, cache, metaclass algorithm, or token representation.

## Declaration evolution and binding

A declarative form class may inherit fields, replace an inherited field, and
add or delete public field declarations after the class has already been used.
The next form instance must reflect the current declarations. An instance that
was already constructed keeps its own bound fields and is not retroactively
changed by later class edits.

Inherited declarations retain their declaration positions. A replacement is a
new declaration and participates in ordering at its new declaration position.
Every instance owns distinct bound field state, including `data`, `raw_data`,
errors, filters, flags, labels, and nested entries.

`BaseForm` remains the dynamic counterpart to declarative `Form`. Assigning an
unbound field declaration through `base_form[name]` must bind it using that
form's current prefix and Meta object. Replacing a name replaces the bound
field; deleting a name removes it. A newly assigned or replaced field receives
data when `process(...)` is next called.

## Prefix and presentation identity

A non-empty form prefix that does not already end in one of `-_;:/.` is joined
to field names with `-`. A prefix already ending in one of those separators is
used as supplied. The bound field's `short_name` remains the declaration name;
its public `name` and default `id` contain the effective prefix. Submitted data
is looked up by that public `name`.

At initial binding, a default label is associated with the bound field's
public id. An inline datalist at initial binding likewise uses the fully
prefixed field id, so multiple form instances or repeated entries do not share
a list reference accidentally.

## Whole-form post-processing

`Form.post_process(formdata=None)` and `Field.post_process(formdata=None)` are
public lifecycle hooks. A top-level processing cycle first processes every bound
field, including conversion and filters, and then invokes whole-form
post-processing exactly once. The default form hook forwards the resolved
formdata to every field in declaration order.

An overriding form hook may perform cross-field finalization. Code run before
`super().post_process(...)` is visible to downstream field and nested-form
hooks; code run after `super()` observes their completed state.

Nested forms do not start an independent automatic cycle while their parent is
being processed. `FormField` and `FieldList` propagate the top-level cycle so every
nested field receives one post-processing call, not zero calls and not two.
Calling `process(...)` again starts a new cycle and repeats the same contract
once for the new state.

## Dynamic choices and datalists

A callable supplied as `SelectField.choices` is resolved during
post-processing, after all fields in its owning form have current converted and
filtered data. A `(form, field)` callable receives that owning form and the
bound select field; a no-argument callable receives no arguments. The callable
runs once per processing cycle, replaces the choices for that cycle, and may
base them on public sibling-field state. Its exception propagates.

The submitted select value is converted before the choices callback runs.
Membership validation and `iter_choices()` then use the choices resolved for
that same cycle. Re-processing the form refreshes the callable choices instead
of retaining a stale result from the earlier cycle.

An inline callable `DataList` is likewise resolved for each bound field after
that field's data is current. Repeated fields receive independent values and
initial list associations. Rendering must preserve the public association made
at initial binding without requiring an exact HTML serialization.

## Repeated and nested fields

`FieldList` validates every entry before running validators attached to the
list itself. When any entry fails, the public error list remains positionally
aligned with the compacted entries, including empty error projections for
valid siblings.

Sparse submitted indices select object data at the same original indices.
After processing, public entries are compacted. For a
`FieldList(FormField(...))`, `populate_obj` updates the selected existing nested
objects, preserves their identity, emits them in compacted order, and does not
silently substitute an object from a skipped index.

`append_entry` and `insert_entry` bind the new entry through
`form.meta.bind_field`, process its object/default data, and post-process that
entry once. This includes resolving callable choices or datalists in nested
fields. `insert_entry` and `pop_entry` compact remaining entry indices; public
entry and descendant `name` and `id` values follow the compacted positions.

## Validation and re-processing

The field validation order remains `pre_validate`, the declared and supplied
validator chain, then `post_validate`. If a validator raises
`StopValidation`, later validators do not run, but `post_validate` still runs
and receives `validation_stopped=True`. A non-empty stop message is retained
alongside errors already accumulated by validators that ran earlier.

Calling `process(...)` again recomputes `object_data`, `raw_data`, converted
`data`, processing errors, filters, and post-processing for the new cycle. A
later `validate()` projects only the current cycle's processing and validation
outcome; an earlier conversion failure must not force a successfully
reprocessed value to remain invalid.

## Meta hooks, inheritance, and translations

Nested Meta classes follow the form class inheritance order. Attributes from
applicable parent Meta classes remain available unless a more specific form
Meta overrides them. A constructor `meta={...}` override applies only to that
form instance.

`Meta.bind_field` applies not only to top-level declarations but also to entries
created by `FieldList` during construction or later mutation. A custom bound
field returned by the hook is the field used by subsequent processing,
validation, and rendering.

`Meta.render_field` receives the bound field and the merged rendering keyword
arguments; its returned HTML-safe value is the field's public rendering.
`Meta.get_translations` supplies the object used by built-in validator
messages. Objects with `gettext` and `ngettext` are sufficient. Equal locale
selections may share a cached translation object when caching is enabled, but
instance-level Meta overrides must not leak into unrelated forms.

## CSRF lifecycle

When CSRF is enabled, `csrf_field_name` controls the public field name. The
token field validates submitted token data while rendering the current token,
and `populate_obj` must not overwrite an application attribute for that token
field.

`SessionCSRF` ties validation to the same session-like context, secret, and
configured time limit. A token accepted before its expiry must fail after its
expiry. A public `SessionCSRF` subclass may override `now()` to supply a
deterministic clock; no wall-clock sleeping or exact token byte format is part
of this contract.

## Explicit non-contracts

- No private attribute, internal cache, generated Meta base tuple, or module
  arrangement is observable behavior.
- Exact default error wording and exact complete HTML strings remain outside
  the contract unless caller-supplied text is being preserved.
- CSRF token algorithms, delimiters, digests, and random session values are not
  fixed by this addendum.
- Initial label-to-id and datalist-to-field association is public. This
  addendum does not require an already-created `Label` or cloned `DataList`
  association id to be rewritten after sparse compaction or a later
  `FieldList` insertion/removal. Mutation guarantees compacted field and
  descendant `name` and `id` values only.

<!-- spec.cleaned.md -->

# WTForms Specification

> **Contract Authority**: This document defines the required public behavior.
> Compatibility with similarly named software does not supersede the
> interfaces, parameter names, behavioral boundaries, and error semantics
> stated here.

## Product Overview

WTForms provides declarative, framework-independent Python forms for accepting,
converting, validating, and rendering user input. A form declaration contains
field declarations; every form instance owns bound field instances with its own
data and errors. Submitted data must provide `getlist(name)`; a plain mapping
supplied as submitted data must raise the form-data wrapping error.

Applications must rely on public imports, public state projections, declared conversion and validation behavior, and template-safe rendering. They must not rely on private attributes, internal module layout, exact error wording, or exact HTML serialization.

## Non-Goals

- This API does not load requests, save models, or store uploaded file bytes.
- This API does not provide a web-framework integration or template language.
- This API does not require exact rendered-HTML ordering or whitespace beyond
  public field, label, choice, datalist, and widget contracts.
- This API does not promise exact default error wording.

## Representative Workflows

```python
from wtforms import Form, IntegerField, SelectField, StringField, validators

class Registration(Form):
    name = StringField("Name", [validators.InputRequired(), validators.Length(min=2)])
    age = IntegerField("Age", [validators.NumberRange(min=13)])
    role = SelectField("Role", choices=[("user", "User"), ("admin", "Admin")])

form = Registration(request.form)
if form.validate():
    account.name = form.name.data
    account.age = form.age.data
    account.role = form.role.data
else:
    errors = form.errors
```

The form must convert submitted values before validation and expose failures
through `errors`. Without submitted data, an application must construct the
form without expecting automatic validation.

## Form Processing and Binding

This section defines how forms bind fields, process input sources, run filters, validate fields, and populate objects.

**Field binding and access.** `Form` must bind declared public fields in declaration order and expose each one via both `form.field_name` and `form["field_name"]`. Underscore-prefixed declarations must not bind. A missing mapping key must raise `KeyError`. `Form` item assignment must raise `TypeError`.

**Processing precedence.** `Form.process` must resolve each field using this complete precedence order: `formdata[field_name]` takes highest priority, then `obj.field_name`, then `kwargs[field_name]`, then `data[field_name]`, and finally the field default. A missing source must advance to the next source; a missing default must produce the empty/default field state rather than raise.

**Filter chain.** `Form.process` must run declared filters first, then `extra_filters`, then an inline `filter_<fieldname>` method defined on the form class. A filter that raises `ValueError` must add a processing error and make later validation fail without raising from form construction.

**Validation.** `Form.validate` must validate every bound field, append an inline `validate_<fieldname>` after declared and supplied validators, populate errors, and return `True` only when all fields validate. A non-callable validator, or a validator class supplied instead of an instance, must raise `TypeError` before validation.

**Object population.** `Form.populate_obj(obj)` must assign each current field value to the matching object attribute and overwrite an existing value. A field that cannot populate its object must raise its documented `TypeError`.

**Data and error projections.** `Form.data` must return a mapping from each bound field's attribute name to its current `data`. `Form.errors` must return a mapping containing only fields whose `errors` is non-empty after validation.

**BaseForm.** `BaseForm` must expose the same processing, validation, data, errors, iteration, and mapping behavior for an explicit field mapping. `BaseForm` must bind an assigned public field before processing and must raise the underlying lookup error for a missing item.

## Field Lifecycle and Rendering

This section defines the lifecycle of a field from unbound declaration through bound processing, validation, and rendering.

**Binding and state.** A `Field` must be an unbound declaration outside a form and a bound field after binding. A bound field must expose `data`, `object_data`, `raw_data`, `process_errors`, `errors`, `name`, `short_name`, `id`, `label`, `description`, `flags`, `filters`, `widget`, and `meta`.

**Processing.** A bound field must process object/default input before submitted input; submitted input must replace current data. A conversion or filter failure must accumulate in `process_errors`. `Field.validate` must copy process errors to `errors` and return `False`.

**Validation chain.** `Field.validate` must run `pre_validate`, declared and extra validators, then `post_validate`. `ValidationError(message)` must add its message and continue. `StopValidation(message)` must add a non-empty message, stop remaining validators, and still run `post_validate`. A clean run must return `True` with empty errors.

**Rendering.** Calling a field, converting it with `str`, or calling `__html__` must return HTML-safe widget rendering. Rendering keyword arguments must reach the widget; a widget failure must propagate. `Label` must render an escaped label associated with its field id. `Flags` must return `None` for an unset public flag.

## Scalar and Temporal Fields

This section defines data coercion, storage, and temporal parsing for scalar value fields.

**String-like fields.** `StringField` must retain the first submitted value as text. When multiple values are submitted, `raw_data` must contain all submitted values but `data` must reflect the first value only. `TextAreaField`, `HiddenField`, `SearchField`, `TelField`, `URLField`, `EmailField`, and `ColorField` must keep that data behavior while selecting their HTML control kinds. Missing submitted input must retain the processed default or empty data.

**Boolean fields.** `BooleanField` must store `False` for a missing value or a first submitted value in `false_values` (defaulting to `(False, "false", "")`), and `True` otherwise. `SubmitField` must use that behavior; a submit field with no submitted value must store `False`. `ButtonField` must store its submitted text when clicked and `None` when absent, and must use its label as visible button content.

**Numeric fields.** `IntegerField`, `FloatField`, and `DecimalField` must coerce submitted text to `int`, `float`, and `decimal.Decimal`. Invalid text must set `data` to `None`, record a processing error, and make validation return `False` without raising from construction. `DecimalField` must use two display places when `places` is omitted and must not quantize display when `places=None`. Locale-aware numeric processing must raise `ImportError` when enabled without the locale processing dependency.

**Temporal fields.** `DateTimeField` (format `%Y-%m-%d %H:%M:%S`), `DateField` (format `%Y-%m-%d`), `TimeField` (format `%H:%M`), `MonthField` (format `%Y-%m`), and `WeekField` (format `%Y-W%W`) must parse input to documented `datetime`, `date`, `time`, or `date` values. Invalid input must set `data` to `None`, record a processing error, and make validation return `False`. `MonthField` must store day one of the parsed month. `WeekField` must store Monday when its format lacks a weekday. `DateTimeLocalField` must return naive values when `tz` resolves to `None` and attach the resolved timezone otherwise.

**Password and file fields.** `PasswordField` must accept submitted text but must not render stored text. `FileField` must preserve the framework-supplied filename or value without upload storage; `MultipleFileField` must retain the submitted list.

## Choice Fields, Datalists, and Nesting

This section defines selection fields, suggestion lists, and composite field structures for nested and repeated data.

**Choice types.** `SelectChoice` must default a missing label to value. `Choice` must be the choice-iteration value. An unsupported choice tuple length must raise `ValueError` when normalized.

**SelectField.** `SelectField` must coerce input, expose selected `Choice` values through `SelectField.iter_choices()`, and reject a value outside `choices` when choice validation is enabled. Coercion failure must be a processing error; invalid membership must be a validation error; missing choices with enabled validation must raise `TypeError`. When `validate_choice=False` is set, the field must accept a coercible non-member without raising a membership error. `SelectMultipleField` must coerce all submitted values to a list and reject every invalid selection when membership validation is enabled. `RadioField` must retain `SelectField` data and validation while iterating individual option fields.

**Choice callbacks.** Choice callbacks must run once per processing cycle. A `(form, field)` callback must receive the bound form and field after processing; a no-argument callback must receive no arguments. A callback exception must propagate.

**Enum helpers.** `enum_choices` must create `SelectChoice` values from an enum class; `enum_coerce` must round-trip the same member representation. A `by` value other than `"value"` or `"name"` must raise `ValueError`.

**DataList.** `DataList` must provide suggestions for a text-like field without restricting submitted text. `DataListChoice` must default label to value; `enum_datalist` must create analogous enum suggestions. An inline `DataList` must render its field-specific list reference and list; a string list reference must make `field.datalist()` return empty markup because the application owns it.

**FormField.** `FormField` must prefix its enclosed form's field names, delegate validation to the enclosed form, and expose nested data and errors. Filters, validators, and extra validators must raise `TypeError` because the enclosed form owns them.

**FieldList.** `FieldList` must expose ordered entries and list data, create enough blank entries for `min_entries`, cap submitted entries at `max_entries`, and compact indices, names, and ids after sparse input, insertion, or removal. Filters and extra filters must raise `TypeError`. `append_entry`, `insert_entry`, and `pop_entry` must return or remove the affected entry while preserving contiguous indices.

## Validator Predicates

This section defines the behavioral contract for each built-in validator.

**General contract.** Every validator failure must add a validation error and make field and form validation return `False`. The `message` parameter customizes that error without fixing its exact text. `field_flags` from the documented validators must remain observable through `field.flags`.

**DataRequired and InputRequired.** `DataRequired` must accept only truthy post-coercion `data`, with whitespace-only strings treated as false. On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the remaining chain. `InputRequired` must instead accept only a non-empty first `raw_data` item; object/default data must not count as submitted input. On failure it must clear validation errors accumulated by the current chain, leave `process_errors` intact, and stop the chain.

**Optional.** `Optional` must detect missing input, empty input, and, when whitespace stripping is enabled, whitespace-only first input. It must clear prior errors and stop remaining validators. Thus `Optional()` before `DataRequired()` must validate empty submitted input successfully with no errors.

**EqualTo.** `EqualTo` must require equal `data` from the named field. A missing named field must produce a validation failure.

**Length.** `Length` uses `-1` for an unset bound. Construction must require at least one of `min` or `max` to differ from `-1` and must raise `AssertionError` when both remain `-1`. A constructed `Length` must accept values within inclusive configured bounds and reject values outside them.

**NumberRange and DateRange.** `NumberRange` must accept inclusive comparable bounds, resolve callable bounds at validation time, and reject missing or out-of-range values. `NumberRange` must reject `NaN`. `DateRange` must accept inclusive comparable date/time bounds and reject out-of-range values.

**Regexp.** `Regexp` must accept a supplied matcher result and reject no match. String patterns must compile with `flags`. The `matcher` parameter must default to prefix matching. `html_pattern` must leave the presentation pattern unset when false, use the regex source when true, use a supplied string as the pattern, and resolve a callable against the compiled regex.

**Network and identifier validators.** `Email` must validate through the optional `email_validator` dependency; missing that dependency must raise its installation exception. Its default deliverability check must be disabled. `IPAddress` must accept only enabled address families; enabling neither family must raise `ValueError`. `MacAddress` must accept only six colon-separated hexadecimal octets. `URL` must require a scheme and valid hostname, enforce configured TLD, IP, user-info, and scheme rules, and reject an invalid port. `UUID` must accept a `uuid.UUID` object or a parseable UUID string and reject other data.

**Set membership validators.** `AnyOf` must accept scalar data when it is a member of `values`, and list data when at least one element of `data` is a member of `values`. `NoneOf` must accept scalar data when it is absent from `values`, and list data when no element of `data` is a member of `values`.

**ReadOnly and Disabled.** `ReadOnly` must set the `readonly` flag and reject a value different from `object_data`, including default-derived object data. `Disabled` must set the `disabled` flag and reject any submitted raw value, even when it equals object data.

## Meta, CSRF, and Translations

This section defines form metaclass behavior, CSRF token protection, and built-in message translation.

**Meta customization.** Forms use `class Meta` to customize `DefaultMeta` behavior, and a form constructor `meta={...}` override must apply to that instance. `bind_field`, `wrap_formdata`, and `render_field` are override hooks: their returned bound field, wrapped formdata, or rendering result must become the form's public behavior.

**Formdata wrapping.** The default wrapper must accept a `getlist` input object, adapt an iterable `getall` input object, and raise `TypeError` for another non-null submitted-data object. A `getall` object that is not iterable must raise `TypeError` when form processing needs membership.

**CSRF.** `csrf=True` must enable CSRF; `csrf_field_name` must name the automatically added token field; `csrf_class` must choose the implementation. `DefaultMeta.build_csrf` must construct `csrf_class` without arguments when set, and otherwise construct `SessionCSRF`, once for each form instance. `CSRF.setup_form` must add one `CSRFTokenField` named by `form.meta.csrf_field_name`. A token field must retain submitted token data for validation, render its newly generated current token regardless of that submission, and never populate an application object. Default CSRF validation must reject submitted data unequal to the current token. A `CSRF` subclass must provide token generation; using its unimplemented generator must raise `NotImplementedError`.

**SessionCSRF.** `SessionCSRF` must require a byte `csrf_secret` and a session-like `csrf_context`; a missing secret must raise an exception and a missing context must raise `TypeError`. It must keep a per-session CSRF value, generate a token authenticated with that value and the configured secret, and accept a later submission only when its authentication matches the same session and secret. `csrf_time_limit` must default to 30 minutes; `None` must make tokens non-expiring, while a `timedelta` must make expired tokens fail validation.

**Translations.** `Meta.locales` must accept an ordered locale sequence for built-in-message translation, or `False` to disable translation. `DefaultMeta.get_translations` must return `None` when locales are false; otherwise it must return an object with `gettext` and `ngettext`. With `cache_translations=True`, equal locale choices must reuse the cached translation object. An overriding `get_translations(form)` must supply the object used for built-in strings. Caller-provided labels and messages remain caller data.

## State Model

A form has three public projections of one lifecycle state:

1. **Input projection:** each bound field exposes `raw_data`, `object_data`,
   and `data`; `form.data` maps field names to current `data`.
2. **Validation projection:** each field exposes `process_errors` and
   `errors`; `form.errors` contains non-empty field errors and form-level
   errors.
3. **Presentation projection:** each field exposes `name`, `id`, `label`,
   `flags`, and a callable renderer; choice fields expose selection through
   `Choice` values.

The input projection must return the same current value through `field.data`
and `form.data[field_name]`. A validation failure must return through both the
field error projection and `form.errors[field_name]`. A selected presentation
choice must return the current input-projection value.

## Error Semantics

`ValidationError` represents a validator failure; `StopValidation` stops the
remaining validator chain. Conversion and filter `ValueError` instances must be
reported by validation rather than escape construction. Invalid choice coercion
must be a processing error, invalid membership a validation error, and missing
choices with required membership a `TypeError`. Unsupported enum modes must
raise `ValueError`; invalid declared validators must raise `TypeError`.
`Length` construction must raise `AssertionError` when both bounds are left at
`-1`.

## Cross-View Invariants

1. `form.data` must return each bound field's current `data` under its form
   attribute name.
2. `form.errors` must return a field only when its `errors` is non-empty after
   validation.
3. `form.validate()` must return `False` when any bound field reports errors,
   and `True` only when the error projection is empty.
4. Submitted scalar input must appear in `field.raw_data` and, after successful
   coercion, return through `field.data` and `form.data`.
5. A processing failure must return through `field.process_errors`, occur in
   `field.errors` after validation, and make `form.validate()` return `False`.
6. A selected `iter_choices()` value must reflect the field's `data` value.
7. `FormField.data` must equal its enclosed form's `data`, and `FormField.errors`
   must equal its enclosed form's error mapping.
8. Each `FieldList` entry index, name, and id must return its contiguous
   sequence position.
9. `Form.populate_obj(obj)` must write each field's current `data` to the
   matching object attribute, so the resulting attribute value agrees with
   `field.data` at the time of population.

## Public Interface

### Import Surface

Install with `pip install WTForms`.

```python
from wtforms import (
    Form, ValidationError, Field, Flags, Label, DataList, DataListChoice,
    enum_datalist, Choice, SelectChoice, SelectField, SelectMultipleField,
    SelectFieldBase, RadioField, FormField, FieldList, BooleanField,
    ButtonField, StringField, TextAreaField, PasswordField, FileField,
    MultipleFileField, HiddenField, SearchField, SubmitField, TelField,
    URLField, EmailField, ColorField, IntegerField, DecimalField, FloatField,
    IntegerRangeField, DecimalRangeField, DateTimeField, DateField, TimeField,
    MonthField, WeekField, DateTimeLocalField, validators, widgets,
)
from wtforms.form import BaseForm
from wtforms.fields import (
    Choice, SelectChoice, SelectField, SelectMultipleField, SelectFieldBase,
    RadioField, FormField, FieldList, BooleanField, ButtonField, StringField,
    TextAreaField, PasswordField, FileField, MultipleFileField, HiddenField,
    SearchField, SubmitField, TelField, URLField, EmailField, ColorField,
    IntegerField, DecimalField, FloatField, IntegerRangeField, DecimalRangeField,
    DateTimeField, DateField, TimeField, MonthField, WeekField,
    DateTimeLocalField, enum_choices, enum_coerce,
)
from wtforms.validators import (
    ValidationError, StopValidation,
    DataRequired, data_required, InputRequired, input_required,
    Optional, optional, Length, length, NumberRange, number_range,
    DateRange, date_range, EqualTo, equal_to, Regexp, regexp,
    Email, email, IPAddress, ip_address, MacAddress, mac_address,
    URL, url, UUID, AnyOf, any_of, NoneOf, none_of,
    ReadOnly, readonly, Disabled, disabled,
)
from wtforms.widgets import (
    html_params, Input, TextInput, PasswordInput, HiddenInput, CheckboxInput,
    RadioInput, FileInput, SubmitInput, SearchInput, TelInput, URLInput,
    EmailInput, ColorInput, NumberInput, RangeInput, DateTimeInput, DateInput,
    MonthInput, WeekInput, TimeInput, DateTimeLocalInput, TextArea, Button,
    Option, Select, ListWidget, TableWidget, DataListWidget,
)
from wtforms.csrf.core import CSRF, CSRFTokenField
from wtforms.csrf.session import SessionCSRF
from wtforms.meta import DefaultMeta
```

`BaseForm` is available from `wtforms.form`; it is not an alternate export of `wtforms.fields`. Each lowercase validator name is an alias for its corresponding public class.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Form` | class | Declarative form with field binding, processing, validation, and rendering |
| `BaseForm` | class | Explicit-field form with the same processing and validation contract |
| `Field` | class | Base field with data processing, validation, and widget rendering |
| `Flags` | class | Boolean flag container observable through field attributes |
| `Label` | class | HTML label element associated with a field id |
| `StringField` | class | Single-value text field |
| `TextAreaField` | class | Multi-line text field |
| `PasswordField` | class | Text field that does not render stored text |
| `HiddenField` | class | Hidden-input text field |
| `SearchField` | class | Search-input text field |
| `TelField` | class | Telephone-input text field |
| `URLField` | class | URL-input text field |
| `EmailField` | class | Email-input text field |
| `ColorField` | class | Color-input text field |
| `IntegerField` | class | Field coercing input to `int` |
| `FloatField` | class | Field coercing input to `float` |
| `DecimalField` | class | Field coercing input to `decimal.Decimal` |
| `IntegerRangeField` | class | Range-input integer field |
| `DecimalRangeField` | class | Range-input decimal field |
| `BooleanField` | class | Checkbox field storing `True` or `False` |
| `SubmitField` | class | Submit-button boolean field |
| `ButtonField` | class | Button field storing clicked text or `None` |
| `FileField` | class | File-upload field preserving framework-supplied value |
| `MultipleFileField` | class | Multi-file-upload field retaining a list |
| `DateTimeField` | class | Field parsing datetime from formatted text |
| `DateField` | class | Field parsing date from formatted text |
| `TimeField` | class | Field parsing time from formatted text |
| `MonthField` | class | Field parsing year-month to day-one date |
| `WeekField` | class | Field parsing year-week to Monday date |
| `DateTimeLocalField` | class | Datetime field with optional timezone attachment |
| `SelectField` | class | Single-selection choice field with coercion and validation |
| `SelectMultipleField` | class | Multi-selection choice field coercing to a list |
| `RadioField` | class | Radio-button choice field iterating individual options |
| `SelectFieldBase` | class | Base class for choice-based fields |
| `Choice` | namedtuple | Choice-iteration value with value, label, selected, and render_kw |
| `SelectChoice` | class | Choice declaration with value, label, render_kw, and optgroup |
| `DataList` | class | Suggestion list for text-like fields without restricting input |
| `DataListChoice` | class | Suggestion entry with value, label, and render_kw |
| `enum_datalist` | function | Create `DataList` suggestions from an enum class |
| `enum_choices` | function | Create `SelectChoice` values from an enum class |
| `enum_coerce` | function | Create a coerce function round-tripping enum members |
| `FormField` | class | Field wrapping a nested form with prefixed names |
| `FieldList` | class | Field wrapping an ordered list of sub-field entries |
| `ValidationError` | exception | Validator failure carrying an error message |
| `StopValidation` | exception | Stop remaining validators with an optional message |
| `DataRequired` | class | Validator requiring truthy post-coercion data |
| `InputRequired` | class | Validator requiring non-empty submitted raw data |
| `Optional` | class | Validator that clears errors and stops chain on missing input |
| `Length` | class | Validator enforcing inclusive string-length bounds |
| `NumberRange` | class | Validator enforcing inclusive numeric bounds |
| `DateRange` | class | Validator enforcing inclusive date/time bounds |
| `EqualTo` | class | Validator requiring equal data from a named sibling field |
| `Regexp` | class | Validator matching data against a regular expression |
| `Email` | class | Validator checking email via `email_validator` dependency |
| `IPAddress` | class | Validator accepting enabled IPv4/IPv6 address families |
| `MacAddress` | class | Validator accepting six colon-separated hex octets |
| `URL` | class | Validator enforcing scheme, hostname, and port rules |
| `UUID` | class | Validator accepting UUID objects or parseable UUID strings |
| `AnyOf` | class | Validator accepting data present in a value set |
| `NoneOf` | class | Validator accepting data absent from a value set |
| `ReadOnly` | class | Validator rejecting changes from original object data |
| `Disabled` | class | Validator rejecting any submitted raw value |
| `DefaultMeta` | class | Default form meta with CSRF, translation, and hook support |
| `CSRF` | class | Base CSRF implementation adding a token field to forms |
| `CSRFTokenField` | class | Auto-generated CSRF token field |
| `SessionCSRF` | class | Session-and-secret-based CSRF token implementation |

### CLI Entry Points

There is no console script for this package. `python -m WTForms`.` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` in the implementation's top-level directory. All declared dependencies must be installable before the package is used.

## Appendix B: Lifecycle Notes

Applications that evolve form declarations must treat each form instance as
owning its bound fields, current data, and error state. A declaration remains
an unbound field until form binding; changes made while processing one form
must not alter another form instance's bound field state.

Applications that introduce new input paths must preserve the documented
processing order: submitted values take precedence over object attributes,
keyword values, mapping data, and field defaults. Conversion and filter
failures must remain visible through processing and validation errors rather
than escaping form construction.

Applications that customize rendering, validation, or form metadata must rely
on the declared public hooks and projections. Bound-field rendering must remain
HTML-safe, validation failures must remain available through field and form
errors, and configured Meta, CSRF, and translation behavior must apply to the
form instance that receives it.

<!-- spec-addendum.cleaned.md -->

# WTForms Lifecycle Clarification Addendum

This addendum extends the WTForms specification for the locked public behavior.
It is authoritative where it is more specific than the base specification. It
describes observable behavior only; it does not prescribe an internal module
layout, cache, metaclass algorithm, or token representation.

## Declaration evolution and binding

A declarative form class may inherit fields, replace an inherited field, and
add or delete public field declarations after the class has already been used.
The next form instance must reflect the current declarations. An instance that
was already constructed keeps its own bound fields and is not retroactively
changed by later class edits.

Inherited declarations retain their declaration positions. A replacement is a
new declaration and participates in ordering at its new declaration position.
Every instance owns distinct bound field state, including `data`, `raw_data`,
errors, filters, flags, labels, and nested entries.

`BaseForm` remains the dynamic counterpart to declarative `Form`. Assigning an
unbound field declaration through `base_form[name]` must bind it using that
form's current prefix and Meta object. Replacing a name replaces the bound
field; deleting a name removes it. A newly assigned or replaced field receives
data when `process(...)` is next called.

## Prefix and presentation identity

A non-empty form prefix that does not already end in one of `-_;:/.` is joined
to field names with `-`. A prefix already ending in one of those separators is
used as supplied. The bound field's `short_name` remains the declaration name;
its public `name` and default `id` contain the effective prefix. Submitted data
is looked up by that public `name`.

At initial binding, a default label is associated with the bound field's
public id. An inline datalist at initial binding likewise uses the fully
prefixed field id, so multiple form instances or repeated entries do not share
a list reference accidentally.

## Whole-form post-processing

`Form.post_process(formdata=None)` and `Field.post_process(formdata=None)` are
public lifecycle hooks. A top-level processing cycle first processes every bound
field, including conversion and filters, and then invokes whole-form
post-processing exactly once. The default form hook forwards the resolved
formdata to every field in declaration order.

An overriding form hook may perform cross-field finalization. Code run before
`super().post_process(...)` is visible to downstream field and nested-form
hooks; code run after `super()` observes their completed state.

Nested forms do not start an independent automatic cycle while their parent is
being processed. `FormField` and `FieldList` propagate the top-level cycle so every
nested field receives one post-processing call, not zero calls and not two.
Calling `process(...)` again starts a new cycle and repeats the same contract
once for the new state.

## Dynamic choices and datalists

A callable supplied as `SelectField.choices` is resolved during
post-processing, after all fields in its owning form have current converted and
filtered data. A `(form, field)` callable receives that owning form and the
bound select field; a no-argument callable receives no arguments. The callable
runs once per processing cycle, replaces the choices for that cycle, and may
base them on public sibling-field state. Its exception propagates.

The submitted select value is converted before the choices callback runs.
Membership validation and `iter_choices()` then use the choices resolved for
that same cycle. Re-processing the form refreshes the callable choices instead
of retaining a stale result from the earlier cycle.

An inline callable `DataList` is likewise resolved for each bound field after
that field's data is current. Repeated fields receive independent values and
initial list associations. Rendering must preserve the public association made
at initial binding without requiring an exact HTML serialization.

## Repeated and nested fields

`FieldList` validates every entry before running validators attached to the
list itself. When any entry fails, the public error list remains positionally
aligned with the compacted entries, including empty error projections for
valid siblings.

Sparse submitted indices select object data at the same original indices.
After processing, public entries are compacted. For a
`FieldList(FormField(...))`, `populate_obj` updates the selected existing nested
objects, preserves their identity, emits them in compacted order, and does not
silently substitute an object from a skipped index.

`append_entry` and `insert_entry` bind the new entry through
`form.meta.bind_field`, process its object/default data, and post-process that
entry once. This includes resolving callable choices or datalists in nested
fields. `insert_entry` and `pop_entry` compact remaining entry indices; public
entry and descendant `name` and `id` values follow the compacted positions.

## Validation and re-processing

The field validation order remains `pre_validate`, the declared and supplied
validator chain, then `post_validate`. If a validator raises
`StopValidation`, later validators do not run, but `post_validate` still runs
and receives `validation_stopped=True`. A non-empty stop message is retained
alongside errors already accumulated by validators that ran earlier.

Calling `process(...)` again recomputes `object_data`, `raw_data`, converted
`data`, processing errors, filters, and post-processing for the new cycle. A
later `validate()` projects only the current cycle's processing and validation
outcome; an earlier conversion failure must not force a successfully
reprocessed value to remain invalid.

## Meta hooks, inheritance, and translations

Nested Meta classes follow the form class inheritance order. Attributes from
applicable parent Meta classes remain available unless a more specific form
Meta overrides them. A constructor `meta={...}` override applies only to that
form instance.

`Meta.bind_field` applies not only to top-level declarations but also to entries
created by `FieldList` during construction or later mutation. A custom bound
field returned by the hook is the field used by subsequent processing,
validation, and rendering.

`Meta.render_field` receives the bound field and the merged rendering keyword
arguments; its returned HTML-safe value is the field's public rendering.
`Meta.get_translations` supplies the object used by built-in validator
messages. Objects with `gettext` and `ngettext` are sufficient. Equal locale
selections may share a cached translation object when caching is enabled, but
instance-level Meta overrides must not leak into unrelated forms.

## CSRF lifecycle

When CSRF is enabled, `csrf_field_name` controls the public field name. The
token field validates submitted token data while rendering the current token,
and `populate_obj` must not overwrite an application attribute for that token
field.

`SessionCSRF` ties validation to the same session-like context, secret, and
configured time limit. A token accepted before its expiry must fail after its
expiry. A public `SessionCSRF` subclass may override `now()` to supply a
deterministic clock; no wall-clock sleeping or exact token byte format is part
of this contract.

## Explicit non-contracts

- No private attribute, internal cache, generated Meta base tuple, or module
  arrangement is observable behavior.
- Exact default error wording and exact complete HTML strings remain outside
  the contract unless caller-supplied text is being preserved.
- CSRF token algorithms, delimiters, digests, and random session values are not
  fixed by this addendum.
- Initial label-to-id and datalist-to-field association is public. This
  addendum does not require an already-created `Label` or cloned `DataList`
  association id to be rewritten after sparse compaction or a later
  `FieldList` insertion/removal. Mutation guarantees compacted field and
  descendant `name` and `id` values only.
