# WTForms Specification

## Product Overview

WTForms provides declarative, framework-independent Python forms for accepting,
converting, validating, and rendering user input. A form declaration contains
field declarations; every form instance owns bound field instances with its own
data and errors. Submitted data must provide `getlist(name)`; a plain mapping
supplied as submitted data must raise the form-data wrapping error.

## Scope

This specification covers the form lifecycle, public field state and rendering,
scalar and temporal fields, choices and datalists, nested and repeated fields,
validators, documented widget utilities, and the documented Meta, CSRF, and
translation extension points. It does not prescribe a web framework, template
engine, or byte-for-byte HTML serialization.

## Installable Surface

Install with `pip install WTForms`. The root package exports `Form`,
`ValidationError`, `Field`, `Flags`, `Label`, `DataList`, `DataListChoice`,
`enum_datalist`, `Choice`, `SelectChoice`, `SelectField`,
`SelectMultipleField`, `SelectFieldBase`, `RadioField`, `FormField`,
`FieldList`, `BooleanField`, `ButtonField`, `StringField`, `TextAreaField`,
`PasswordField`, `FileField`, `MultipleFileField`, `HiddenField`,
`SearchField`, `SubmitField`, `TelField`, `URLField`, `EmailField`,
`ColorField`, `IntegerField`, `DecimalField`, `FloatField`,
`IntegerRangeField`, `DecimalRangeField`, `DateTimeField`, `DateField`,
`TimeField`, `MonthField`, `WeekField`, and `DateTimeLocalField`, plus the
`validators` and `widgets` namespaces.

`BaseForm` is available from `wtforms.form`; it is not an alternate export of
`wtforms.fields`. `wtforms.fields` exports the field types above, `Choice`,
`SelectChoice`, `enum_choices`, and `enum_coerce`.

`wtforms.validators` exports `ValidationError`, `StopValidation`,
`DataRequired`/`data_required`, `InputRequired`/`input_required`,
`Optional`/`optional`, `Length`/`length`, `NumberRange`/`number_range`,
`DateRange`/`date_range`, `EqualTo`/`equal_to`, `Regexp`/`regexp`,
`Email`/`email`, `IPAddress`/`ip_address`, `MacAddress`/`mac_address`,
`URL`/`url`, `UUID`, `AnyOf`/`any_of`, `NoneOf`/`none_of`,
`ReadOnly`/`readonly`, and `Disabled`/`disabled`. Each lowercase name is an
alias for its corresponding public class.

`wtforms.widgets` exports `html_params`, `Input`, `TextInput`,
`PasswordInput`, `HiddenInput`, `CheckboxInput`, `RadioInput`, `FileInput`,
`SubmitInput`, `SearchInput`, `TelInput`, `URLInput`, `EmailInput`,
`ColorInput`, `NumberInput`, `RangeInput`, `DateTimeInput`, `DateInput`,
`MonthInput`, `WeekInput`, `TimeInput`, `DateTimeLocalInput`, `TextArea`,
`Button`, `Option`, `Select`, `ListWidget`, `TableWidget`, and
`DataListWidget`. `CSRF` and `CSRFTokenField` are available from
`wtforms.csrf.core`, `SessionCSRF` from `wtforms.csrf.session`, and
`DefaultMeta` from `wtforms.meta`.

## Product State Model

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

## Public API

### Forms and data processing

`Form(formdata=None, obj=None, prefix="", data=None, meta=None, **kwargs)`
must bind declared public fields in declaration order and expose each one via
both `form.field_name` and `form["field_name"]`. Underscore-prefixed
declarations must not bind. A missing mapping key must raise `KeyError`.

`Form.process(formdata=None, obj=None, data=None, extra_filters=None, **kwargs)`
must resolve each field using this complete precedence order:
`formdata[field_name] > obj.field_name > kwargs[field_name] > data[field_name]
> field default`. A missing source must advance to the next source; a missing
default must produce the empty/default field state rather than raise.

`Form.process` must run declared filters, then `extra_filters`, then an inline
`filter_<fieldname>` method. A filter that raises `ValueError` must add a
processing error and make later validation fail without raising from form
construction.

`Form.validate(extra_validators=None)` must validate every bound field, append
an inline `validate_<fieldname>` after declared and supplied validators,
populate errors, and return `True` only when all fields validate. A non-callable
validator, or a validator class supplied instead of an instance, must raise
`TypeError` before validation.

`Form.populate_obj(obj)` must assign each current field value to the matching
object attribute and overwrite an existing value. A field that cannot populate
its object must raise its documented `TypeError`.

`BaseForm(fields, prefix="", meta=...)` must expose the same processing,
validation, data, errors, iteration, and mapping behavior for an explicit field
mapping. `Form` item assignment must raise `TypeError`; `BaseForm` must bind an
assigned public field before processing and must raise the underlying lookup
error for a missing item.

### Fields, validation, and rendering

`Field(label=None, validators=None, filters=(), description="", id=None,
default=None, invalid_value_message=None, widget=None, render_kw=None,
name=None, datalist=None, ...)` must be an unbound declaration outside a form
and a bound field after binding. A bound field must expose `data`,
`object_data`, `raw_data`, `process_errors`, `errors`, `name`, `short_name`,
`id`, `label`, `description`, `flags`, `filters`, `widget`, and `meta`.

A bound field must process object/default input before submitted input;
submitted input must replace current data. A conversion or filter failure must
accumulate in `process_errors`; `Field.validate` must copy it to `errors` and
return `False`.

`Field.validate(form, extra_validators=())` must run `pre_validate`, declared
and extra validators, then `post_validate`. `ValidationError(message)` must add
its message and continue. `StopValidation(message)` must add a non-empty
message, stop remaining validators, and still run `post_validate`. A clean run
must return `True` with empty errors.

Calling a field, converting it with `str`, or calling `__html__` must return
HTML-safe widget rendering. Rendering keyword arguments must reach the widget;
a widget failure must propagate. `Label` must render an escaped label associated
with its field id, and `Flags` must return `None` for an unset public flag.

### Scalar and temporal fields

`StringField` must retain the first submitted value as text. `TextAreaField`,
`HiddenField`, `SearchField`, `TelField`, `URLField`, `EmailField`, and
`ColorField` must keep that data behavior while selecting their HTML control
kinds. Missing submitted input must retain processed default or empty data.

`BooleanField(false_values=(False, "false", ""))` must store `False` for a
missing value or a first submitted value in `false_values`, and `True`
otherwise. `SubmitField` must use that behavior. `ButtonField` must store its
submitted text when clicked and `None` when absent, and must use its label as
visible button content.

`IntegerField`, `FloatField`, and `DecimalField` must coerce submitted text to
`int`, `float`, and `decimal.Decimal`. Invalid text must set `data` to `None`,
record a processing error, and make validation return `False` without raising
from construction. `DecimalField` must use two display places when `places` is
omitted and must not quantize display when `places=None`. Locale-aware numeric
processing must raise `ImportError` when enabled without Babel.

`DateTimeField(format="%Y-%m-%d %H:%M:%S")`, `DateField(format="%Y-%m-%d")`,
`TimeField(format="%H:%M")`, `MonthField(format="%Y-%m")`, and
`WeekField(format="%Y-W%W")` must parse input to documented `datetime`,
`date`, or `time` values. Invalid input must set `data` to `None`, record a
processing error, and make validation return `False`. `MonthField` must store
day one; `WeekField` must store Monday when its format lacks a weekday.
`DateTimeLocalField(tz=None)` must return naive values when `tz` resolves to
`None` and attach the resolved timezone otherwise.

`PasswordField` must accept submitted text but must not render stored text.
`FileField` must preserve the framework-supplied filename or value without
upload storage; `MultipleFileField` must retain the submitted list.

### Choice fields, datalists, and nesting

`SelectChoice(value, label=None, render_kw={}, optgroup=None)` must default a
missing label to value. `Choice(value, label, selected, render_kw)` must be the
choice-iteration value. An unsupported choice tuple length must raise
`ValueError` when normalized.

`SelectField(label=None, validators=None, coerce=str, choices=None,
validate_choice=True, invalid_value_message=None, invalid_choice_message=None,
...)` must coerce input, expose selected `Choice` values, and reject a value
outside `choices` when choice validation is enabled. Coercion failure must be a
processing error; invalid membership must be a validation error; missing
choices with enabled validation must raise `TypeError`. Disabled choice
validation must accept a coercible non-member. `SelectMultipleField` must
coerce all submitted values to a list and reject every invalid selection when
membership validation is enabled. `RadioField` must retain `SelectField` data
and validation while iterating individual option fields.

Choice callbacks must run once per processing cycle. A `(form, field)` callback
must receive the bound form and field after processing; a no-argument callback
must receive no arguments. A callback exception must propagate.

`enum_choices(enum_cls, by="value", label=None)` must create `SelectChoice`
values; `enum_coerce(enum_cls, by="value")` must round-trip the same member
representation. A `by` value other than `"value"` or `"name"` must raise
`ValueError`.

`DataList(choices=None, *, render_kw=None, widget=None)` must provide
suggestions for a text-like field without restricting submitted text.
`DataListChoice(value, label=None, render_kw={})` must default label to value;
`enum_datalist` must create analogous enum suggestions. An inline `DataList`
must render its field-specific list reference and list; a string list reference
must make `field.datalist()` return empty markup because the application owns it.

`FormField(form_class, ..., separator="-")` must prefix, expose data and
errors from, validate through, and populate a nested form. Filters, validators,
and extra validators must raise `TypeError` because the enclosed form owns them.
`FieldList(unbound_field, ..., min_entries=0, max_entries=None, separator="-",
default=())` must expose ordered entries and list data, create enough blank
entries for `min_entries`, cap submitted entries at `max_entries`, and compact
indices, names, and ids after sparse input, insertion, or removal. Filters and
extra filters must raise `TypeError`; `append_entry`, `insert_entry`, and
`pop_entry` must return or remove the affected entry while preserving indices.

### Validator predicates

Every validator failure below must add a validation error and make field and
form validation return `False`; `message` customizes that error without fixing
its exact text. `field_flags` from the documented validators must remain
observable through `field.flags`.

`DataRequired(message=None)` must accept only truthy post-coercion `data`, with
whitespace-only strings treated as false. On failure it must clear validation
errors accumulated by the current chain, leave `process_errors` intact, and stop
the remaining chain. `InputRequired(message=None)` must instead accept only a
non-empty first `raw_data` item; object/default data must not count as submitted
input. On failure it must clear validation errors accumulated by the current
chain, leave `process_errors` intact, and stop the chain.
`Optional(strip_whitespace=True)` must detect missing input, empty input, and,
when whitespace stripping is enabled, whitespace-only first input; it must
clear prior errors and stop remaining validators. Thus `Optional()` before
`DataRequired()` must validate empty submitted input successfully with no
errors.

`EqualTo(fieldname, message=None)` must require equal `data` from the named
field. A missing named field must produce a validation failure. `Length(min=-1,
max=-1, message=None)` uses `-1` for an unset bound; construction must require
at least one of `min` or `max` to differ from `-1` and must raise
`AssertionError` when both remain `-1`. A constructed `Length` must accept
inclusive configured bounds and reject values outside them. `NumberRange(min=None,
max=None, message=None)` and
`DateRange(min=None, max=None, message=None)` must accept inclusive comparable
bounds, resolve callable bounds at validation time, and reject missing or
out-of-range values; `NumberRange` must reject `NaN`.

`Regexp(regex, flags=0, message=None, matcher=re.match, html_pattern=False)`
must accept a supplied matcher result and reject no match. String patterns must
compile with `flags`; `matcher` must default to prefix matching. `html_pattern`
must leave the presentation pattern unset when false, use the regex source when
true, use a supplied string as the pattern, and resolve a callable against the
compiled regex.

`Email(...)` must validate through the optional `email_validator` dependency;
missing that dependency must raise its installation exception. Its default
deliverability check must be disabled. `IPAddress(ipv4=True, ipv6=False,
message=None)` must accept only enabled address families; enabling neither
family must raise `ValueError`. `MacAddress(message=None)` must accept only six
colon-separated hexadecimal octets. `URL(require_tld=True, allow_ip=True,
allow_userinfo=False, schemes=("http", "https"), message=None)` must require a
scheme and valid hostname, enforce configured TLD, IP, user-info, and scheme
rules, and reject an invalid port. `UUID(message=None)` must accept a
`uuid.UUID` object or a parseable UUID string and reject other data.

`AnyOf(values, message=None, values_formatter=None)` must accept scalar data
when it is a member of `values`, and list data when at least one element of
`data` is a member of `values`. `NoneOf(values, message=None,
values_formatter=None)` must accept scalar data when it is absent from `values`,
and list data when no element of `data` is a member of `values`. `ReadOnly()` must
set the readonly flag and reject a value different from `object_data`, including
default-derived object data. `Disabled()` must set the disabled flag and reject
any submitted raw value, even when it equals object data.

### Meta, CSRF, and translations

Forms use `class Meta` to customize `DefaultMeta` behavior, and a form
constructor `meta={...}` override must apply to that instance. `csrf=True`
must enable CSRF; `csrf_field_name` must name the automatically added token
field; `csrf_class` must choose the implementation. `DefaultMeta.build_csrf`
must construct `csrf_class` without arguments when set, and otherwise construct
`SessionCSRF`, once for each form instance. `bind_field`, `wrap_formdata`, and
`render_field` are override hooks: their returned bound field, wrapped formdata,
or rendering result must become the form's public behavior. The default wrapper
must accept a `getlist` input object, adapt an iterable `getall` input object,
and raise `TypeError` for another non-null submitted-data object. A `getall`
object that is not iterable must raise `TypeError` when form processing needs
membership.

`CSRF.setup_form(form)` must add one `CSRFTokenField` named by
`form.meta.csrf_field_name`. A token field must retain submitted token data for
validation, render its newly generated current token regardless of that
submission, and never populate an application object. Default CSRF validation
must reject submitted data unequal to the current token. A `CSRF` subclass must
provide token generation; using its unimplemented generator must raise
`NotImplementedError`.

`SessionCSRF` must require a byte `csrf_secret` and a session-like
`csrf_context`; a missing secret must raise an exception and a missing context
must raise `TypeError`. It must keep a per-session CSRF value, generate a token
authenticated with that value and the configured secret, and accept a later
submission only when its authentication matches the same session and secret.
`csrf_time_limit` must default to 30 minutes; `None` must make tokens
non-expiring, while a `timedelta` must make expired tokens fail validation.

`Meta.locales` must accept an ordered locale sequence for built-in-message
translation, or `False` to disable translation. `DefaultMeta.get_translations`
must return `None` when locales are false; otherwise it must return an object
with `gettext` and `ngettext`. With `cache_translations=True`, equal locale
choices must reuse the cached translation object. An overriding
`get_translations(form)` must supply the object used for built-in strings.
Caller-provided labels and messages remain caller data.

## Error Semantics

`ValidationError` represents a validator failure; `StopValidation` stops the
remaining validator chain. Conversion and filter `ValueError` instances must be
reported by validation rather than escape construction. Invalid choice coercion
must be a processing error, invalid membership a validation error, and missing
choices with required membership a `TypeError`. Unsupported enum modes must
raise `ValueError`; invalid declared validators must raise `TypeError`.
`Length` construction must raise `AssertionError` when both bounds are left at
`-1`.

## Consistency Invariants

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

## Representative Workflow

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

## Non-Goals

- This API does not load requests, save models, or store uploaded file bytes.
- This API does not provide a web-framework integration or template language.
- This API does not require exact rendered-HTML ordering or whitespace beyond
  public field, label, choice, datalist, and widget contracts.
- This API does not promise exact default error wording.

## Evolution Notes

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

## Usage Notes

Applications must rely on public imports, public state projections, declared
conversion and validation behavior, and template-safe rendering. They must not
rely on private attributes, internal module layout, exact error wording, or
exact HTML serialization.
