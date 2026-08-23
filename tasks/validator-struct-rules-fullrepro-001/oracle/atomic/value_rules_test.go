package atomic_test

import (
	"context"
	"reflect"
	"strings"
	"testing"
	"time"

	validator "github.com/go-playground/validator/v10"
)

func first(t *testing.T, err error) validator.FieldError {
	t.Helper()
	ves, ok := err.(validator.ValidationErrors)
	if !ok || len(ves) == 0 {
		t.Fatalf("want ValidationErrors, got %T %v", err, err)
	}
	return ves[0]
}

func expectPanic(t *testing.T, fn func()) {
	t.Helper()
	defer func() {
		if recover() == nil {
			t.Fatal("want panic")
		}
	}()
	fn()
}

// Verifies: VAL-ERR-001, VAL-REG-010
func TestVAL001NewIndependentValidators(t *testing.T) {
	a, b := validator.New(), validator.New()
	if a == nil || b == nil || a == b {
		t.Fatal("New must return independent non-nil instances")
	}
}

// Verifies: VAL-VALUE-003, VAL-ERR-006
func TestVAL002Required(t *testing.T) {
	v := validator.New()
	if v.Var("ok", "required") != nil {
		t.Fatal("non-empty should pass")
	}
	if fe := first(t, v.Var("", "required")); fe.Tag() != "required" || fe.Value() != "" {
		t.Fatalf("metadata: %#v", fe)
	}
}

// Verifies: VAL-VALUE-004
func TestVAL003OmitEmptySkipsRemainder(t *testing.T) {
	v := validator.New()
	if err := v.Var("", "omitempty,min=4"); err != nil {
		t.Fatalf("empty must skip min: %v", err)
	}
	if err := v.Var("abc", "omitempty,min=4"); first(t, err).Tag() != "min" {
		t.Fatal("non-empty must continue")
	}
}

// Verifies: VAL-VALUE-005
func TestVAL004OmitNilDistinguishesZeroPointer(t *testing.T) {
	v := validator.New()
	var p *int
	if err := v.Var(p, "omitnil,gt=0"); err != nil {
		t.Fatalf("nil skipped: %v", err)
	}
	z := 0
	if first(t, v.Var(&z, "omitnil,gt=0")).Tag() != "gt" {
		t.Fatal("non-nil pointer must continue")
	}
}

// Verifies: VAL-VALUE-006
func TestVAL005LenUsesRuneCount(t *testing.T) {
	v := validator.New()
	if v.Var("世界", "len=2") != nil || v.Var("世界", "len=6") == nil {
		t.Fatal("string length must count runes")
	}
}

// Verifies: VAL-VALUE-006
func TestVAL006CollectionLengthRules(t *testing.T) {
	v := validator.New()
	if v.Var([]int{1, 2}, "min=2,max=2") != nil || v.Var([]int{1}, "min=2") == nil {
		t.Fatal("collection length")
	}
}

// Verifies: VAL-VALUE-006
func TestVAL007NumericOrdering(t *testing.T) {
	v := validator.New()
	if v.Var(7, "gt=6,lte=7") != nil || v.Var(7, "lt=7") == nil {
		t.Fatal("numeric ordering")
	}
}

// Verifies: VAL-VALUE-006
func TestVAL008EqualityAndInequality(t *testing.T) {
	v := validator.New()
	if v.Var("x", "eq=x") != nil || v.Var("x", "ne=x") == nil {
		t.Fatal("eq/ne")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL009OneOf(t *testing.T) {
	v := validator.New()
	if v.Var("blue", "oneof=red blue") != nil || v.Var("green", "oneof=red blue") == nil {
		t.Fatal("oneof")
	}
}

// Verifies: VAL-VALUE-008, VAL-VALUE-009
func TestVAL010OneOfCaseInsensitive(t *testing.T) {
	v := validator.New()
	if v.Var("BLUE", "oneofci=red blue") != nil || v.Var("BLUE", "noneofci=blue red") == nil {
		t.Fatal("case-insensitive membership")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL011ContainsAndExcludes(t *testing.T) {
	v := validator.New()
	if v.Var("gopher", "contains=ophe,excludes=z") != nil || v.Var("gopher", "excludes=ph") == nil {
		t.Fatal("contains/excludes")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL012ContainsAny(t *testing.T) {
	v := validator.New()
	if v.Var("gopher", "containsany=xyzp") != nil || v.Var("gopher", "containsany=xyz") == nil {
		t.Fatal("containsany")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL013StartsAndEndsWith(t *testing.T) {
	v := validator.New()
	if v.Var("gopher", "startswith=go,endswith=her") != nil || v.Var("gopher", "startswith=x") == nil {
		t.Fatal("prefix/suffix")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL014LowerAndUppercase(t *testing.T) {
	v := validator.New()
	if v.Var("lower", "lowercase") != nil || v.Var("UPPER", "uppercase") != nil || v.Var("Mixed", "lowercase") == nil {
		t.Fatal("case rules")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL015AlphaAndAlphanum(t *testing.T) {
	v := validator.New()
	if v.Var("GoLang", "alpha") != nil || v.Var("Go42", "alphanum") != nil || v.Var("Go-42", "alphanum") == nil {
		t.Fatal("alpha rules")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL016NumericString(t *testing.T) {
	v := validator.New()
	if v.Var("123.5", "numeric") != nil || v.Var("12x", "numeric") == nil {
		t.Fatal("numeric")
	}
}

// Verifies: VAL-VALUE-008
func TestVAL017BooleanString(t *testing.T) {
	v := validator.New()
	if v.Var("true", "boolean") != nil || v.Var("not-bool", "boolean") == nil {
		t.Fatal("boolean")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL018Email(t *testing.T) {
	v := validator.New()
	if v.Var("a@example.com", "email") != nil || v.Var("bad@", "email") == nil {
		t.Fatal("email")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL019URL(t *testing.T) {
	v := validator.New()
	if v.Var("https://example.com/a?q=1", "url") != nil || v.Var(":bad", "url") == nil {
		t.Fatal("url")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL020IPFamilies(t *testing.T) {
	v := validator.New()
	if v.Var("127.0.0.1", "ip,ipv4") != nil || v.Var("::1", "ipv6") != nil || v.Var("300.1.1.1", "ip") == nil {
		t.Fatal("ip")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL021CIDR(t *testing.T) {
	v := validator.New()
	if v.Var("10.0.0.0/8", "cidr") != nil || v.Var("10.0.0.0/99", "cidr") == nil {
		t.Fatal("cidr")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL022UUID(t *testing.T) {
	v := validator.New()
	id := "550e8400-e29b-41d4-a716-446655440000"
	if v.Var(id, "uuid,uuid4") != nil || v.Var("550e8400", "uuid") == nil {
		t.Fatal("uuid")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL023JSON(t *testing.T) {
	v := validator.New()
	if v.Var(`{"a":[1,true]}`, "json") != nil || v.Var(`{"a":`, "json") == nil {
		t.Fatal("json")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL024Base64(t *testing.T) {
	v := validator.New()
	if v.Var("aGVsbG8=", "base64") != nil || v.Var("%%%", "base64") == nil {
		t.Fatal("base64")
	}
}

// Verifies: VAL-VALUE-010, VAL-VALUE-011
func TestVAL025DatetimeLayout(t *testing.T) {
	v := validator.New()
	if v.Var("2026-08-21", "datetime=2006-01-02") != nil || v.Var("21/08/2026", "datetime=2006-01-02") == nil {
		t.Fatal("datetime")
	}
}

// Verifies: VAL-VALUE-010
func TestVAL026Timezone(t *testing.T) {
	v := validator.New()
	if v.Var("Asia/Shanghai", "timezone") != nil || v.Var("Mars/Olympus", "timezone") == nil {
		t.Fatal("timezone")
	}
}

// Verifies: VAL-VALUE-012, VAL-VALUE-013
func TestVAL027AlternativeExpression(t *testing.T) {
	v := validator.New()
	if v.Var("abc", "email|alpha") != nil {
		t.Fatal("one alternative should pass")
	}
	if tag := first(t, v.Var("123", "email|alpha")).Tag(); tag != "email|alpha" {
		t.Fatalf("tag=%q", tag)
	}
}

// Verifies: VAL-VALUE-014, VAL-CVI-006
func TestVAL028AliasMetadata(t *testing.T) {
	v := validator.New()
	v.RegisterAlias("shortname", "required,min=3")
	fe := first(t, v.Var("ab", "shortname"))
	if fe.Tag() != "shortname" || fe.ActualTag() != "min" {
		t.Fatalf("tag=%q actual=%q", fe.Tag(), fe.ActualTag())
	}
}

// Verifies: VAL-REG-001, VAL-REG-002
func TestVAL029CustomValidationFieldLevel(t *testing.T) {
	v := validator.New()
	seen := ""
	if err := v.RegisterValidation("prefix", func(fl validator.FieldLevel) bool {
		seen = fl.Param() + ":" + fl.Field().String()
		return strings.HasPrefix(fl.Field().String(), fl.Param())
	}); err != nil {
		t.Fatal(err)
	}
	if v.Var("gopher", "prefix=go") != nil || seen != "go:gopher" || v.Var("rust", "prefix=go") == nil {
		t.Fatalf("seen=%q", seen)
	}
}

// Verifies: VAL-REG-001, VAL-REG-011
func TestVAL030InvalidRegistrationName(t *testing.T) {
	v := validator.New()
	if err := v.RegisterValidation("", func(validator.FieldLevel) bool { return true }); err == nil {
		t.Fatal("empty name must return error")
	}
	expectPanic(t, func() { _ = v.RegisterValidation("bad,name", func(validator.FieldLevel) bool { return true }) })
}

// Verifies: VAL-REG-003
func TestVAL031ContextValidationReceivesContext(t *testing.T) {
	type key struct{}
	ctx := context.WithValue(context.Background(), key{}, "token")
	v := validator.New()
	var got any
	if err := v.RegisterValidationCtx("ctxvalue", func(c context.Context, fl validator.FieldLevel) bool {
		got = c.Value(key{})
		return got == fl.Param()
	}); err != nil {
		t.Fatal(err)
	}
	if err := v.VarCtx(ctx, "x", "ctxvalue=token"); err != nil || got != "token" {
		t.Fatalf("err=%v got=%v", err, got)
	}
}

type wrappedNumber struct{ N int }

// Verifies: VAL-REG-004
func TestVAL032CustomTypeProjection(t *testing.T) {
	v := validator.New()
	v.RegisterCustomTypeFunc(func(rv reflect.Value) interface{} { return rv.Interface().(wrappedNumber).N }, wrappedNumber{})
	if v.Var(wrappedNumber{N: 4}, "gte=4") != nil || v.Var(wrappedNumber{N: 3}, "gte=4") == nil {
		t.Fatal("custom projection")
	}
}

// Verifies: VAL-ERR-002, VAL-ERR-003
func TestVAL033ValidationErrorsCollection(t *testing.T) {
	err := validator.New().Var("", "required")
	ves, ok := err.(validator.ValidationErrors)
	if !ok || len(ves) != 1 || ves[0] == nil {
		t.Fatalf("%T %#v", err, err)
	}
}

// Verifies: VAL-ERR-004
func TestVAL034InvalidValidationError(t *testing.T) {
	err := validator.New().Struct(42)
	if _, ok := err.(*validator.InvalidValidationError); !ok {
		t.Fatalf("want InvalidValidationError, got %T", err)
	}
}

// Verifies: VAL-ERR-005
func TestVAL035UndefinedTagPanics(t *testing.T) {
	expectPanic(t, func() { _ = validator.New().Var("x", "definitely_unknown") })
}

// Verifies: VAL-ERR-005, VAL-VALUE-007
func TestVAL036MalformedParameterPanics(t *testing.T) {
	expectPanic(t, func() { _ = validator.New().Var("x", "min") })
}

// Verifies: VAL-ERR-006, VAL-CVI-001
func TestVAL037FieldErrorValueKindType(t *testing.T) {
	fe := first(t, validator.New().Var(3, "gt=5"))
	if fe.Tag() != "gt" || fe.ActualTag() != "gt" || fe.Param() != "5" || fe.Value() != 3 || fe.Kind() != reflect.Int || fe.Type() != reflect.TypeOf(3) {
		t.Fatalf("bad metadata: tag=%s actual=%s param=%s value=%v kind=%v type=%v", fe.Tag(), fe.ActualTag(), fe.Param(), fe.Value(), fe.Kind(), fe.Type())
	}
}

// Verifies: VAL-STRUCT-010, VAL-ERR-010
func TestVAL038DiveSlice(t *testing.T) {
	fe := first(t, validator.New().Var([]int{2, -1, 4}, "dive,gt=0"))
	if fe.Value() != -1 || !strings.Contains(fe.Namespace(), "[1]") {
		t.Fatalf("value=%v ns=%q", fe.Value(), fe.Namespace())
	}
}

// Verifies: VAL-STRUCT-010, VAL-VALUE-008
func TestVAL039UniqueSlice(t *testing.T) {
	v := validator.New()
	if v.Var([]string{"a", "b"}, "unique") != nil || v.Var([]string{"a", "a"}, "unique") == nil {
		t.Fatal("unique")
	}
}

// Verifies: VAL-VALUE-006
func TestVAL040DurationOrdering(t *testing.T) {
	v := validator.New()
	if v.Var(5*time.Second, "gte=5000000000") != nil || v.Var(3*time.Second, "gt=5000000000") == nil {
		t.Fatal("duration numeric ordering")
	}
}
