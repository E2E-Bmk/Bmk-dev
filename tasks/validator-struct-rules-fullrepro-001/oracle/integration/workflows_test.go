package integration_test

import (
	"context"
	"reflect"
	"strings"
	"testing"

	validator "github.com/go-playground/validator/v10"
)

func errorsOf(t *testing.T, err error) validator.ValidationErrors {
	t.Helper()
	ves, ok := err.(validator.ValidationErrors)
	if !ok || len(ves) == 0 {
		t.Fatalf("want ValidationErrors, got %T %v", err, err)
	}
	return ves
}

type address struct {
	City string `validate:"required" json:"city"`
}

type profile struct {
	Name    string   `validate:"required,min=3" json:"name"`
	Email   string   `validate:"required,email" json:"email"`
	Address address  `json:"address"`
	Scores  []int    `validate:"dive,gte=0" json:"scores"`
	Ignored string   `validate:"-" json:"ignored"`
	Alias   *address `validate:"omitempty" json:"alias"`
}

// Verifies: VAL-STRUCT-001, VAL-ERR-008
// Depends-On: TestVAL002Required, TestVAL033ValidationErrorsCollection
func TestVAL041NestedStructTraversal(t *testing.T) {
	err := validator.New().Struct(profile{Name: "valid", Email: "a@example.com", Address: address{}})
	ves := errorsOf(t, err)
	if len(ves) != 1 || ves[0].StructNamespace() != "profile.Address.City" {
		t.Fatalf("errors=%v ns=%q", len(ves), ves[0].StructNamespace())
	}
}

// Verifies: VAL-STRUCT-002
// Depends-On: TestVAL002Required
func TestVAL042DashSkipsField(t *testing.T) {
	type input struct {
		Ignored  string `validate:"-"`
		Required string `validate:"required"`
	}
	ves := errorsOf(t, validator.New().Struct(input{}))
	if len(ves) != 1 || ves[0].StructField() != "Required" {
		t.Fatalf("ignored field must not add an error: %v", ves)
	}
}

// Verifies: VAL-STRUCT-003
// Depends-On: TestVAL002Required
func TestVAL043RequiredStructOption(t *testing.T) {
	type marker struct{ X int }
	type request struct {
		Marker marker `validate:"required"`
	}
	if err := validator.New().Struct(request{}); err != nil {
		t.Fatalf("legacy zero struct should traverse without required failure: %v", err)
	}
	fe := errorsOf(t, validator.New(validator.WithRequiredStructEnabled()).Struct(request{}))[0]
	if fe.StructField() != "Marker" || fe.Tag() != "required" {
		t.Fatalf("field=%q tag=%q", fe.StructField(), fe.Tag())
	}
}

// Verifies: VAL-STRUCT-004, VAL-CVI-003
// Depends-On: TestVAL002Required, TestVAL018Email
func TestVAL044StructPartialSelectsOnlyNamedFields(t *testing.T) {
	type input struct {
		Name  string `validate:"required"`
		Email string `validate:"required,email"`
	}
	v := validator.New()
	x := input{}
	ves := errorsOf(t, v.StructPartial(x, "Email"))
	if len(ves) != 1 || ves[0].StructField() != "Email" {
		t.Fatalf("%v", ves)
	}
}

// Verifies: VAL-STRUCT-004, VAL-ERR-008
// Depends-On: TestVAL002Required
func TestVAL045StructPartialNestedPath(t *testing.T) {
	type input struct {
		Home address
		Work address
	}
	ves := errorsOf(t, validator.New().StructPartial(input{}, "Home.City"))
	if len(ves) != 1 || ves[0].StructNamespace() != "input.Home.City" {
		t.Fatalf("%v", ves)
	}
}

// Verifies: VAL-STRUCT-005, VAL-CVI-003
// Depends-On: TestVAL002Required
func TestVAL046StructExceptSkipsNamedFields(t *testing.T) {
	type input struct {
		A string `validate:"required"`
		B string `validate:"required"`
	}
	ves := errorsOf(t, validator.New().StructExcept(input{}, "A"))
	if len(ves) != 1 || ves[0].StructField() != "B" {
		t.Fatalf("%v", ves)
	}
}

// Verifies: VAL-STRUCT-006, VAL-CVI-003
// Depends-On: TestVAL002Required
func TestVAL047StructFilteredUsesNamespace(t *testing.T) {
	type input struct {
		A string `validate:"required"`
		B string `validate:"required"`
	}
	seen := []string{}
	err := validator.New().StructFiltered(input{}, func(ns []byte) bool {
		seen = append(seen, string(ns))
		return strings.HasSuffix(string(ns), ".A")
	})
	ves := errorsOf(t, err)
	if len(ves) != 1 || ves[0].StructField() != "B" || len(seen) != 2 {
		t.Fatalf("errors=%v seen=%v", ves, seen)
	}
}

// Verifies: VAL-STRUCT-007
// Depends-On: TestVAL008EqualityAndInequality
func TestVAL048EqualField(t *testing.T) {
	type password struct {
		Value   string `validate:"required"`
		Confirm string `validate:"eqfield=Value"`
	}
	v := validator.New()
	if v.Struct(password{Value: "secret", Confirm: "secret"}) != nil {
		t.Fatal("matching fields")
	}
	if fe := errorsOf(t, v.Struct(password{Value: "secret", Confirm: "other"}))[0]; fe.Tag() != "eqfield" || fe.Param() != "Value" {
		t.Fatalf("tag=%q param=%q", fe.Tag(), fe.Param())
	}
}

// Verifies: VAL-STRUCT-007
// Depends-On: TestVAL007NumericOrdering
func TestVAL049GreaterThanField(t *testing.T) {
	type window struct {
		Start int
		End   int `validate:"gtfield=Start"`
	}
	v := validator.New()
	if v.Struct(window{Start: 2, End: 3}) != nil || v.Struct(window{Start: 3, End: 2}) == nil {
		t.Fatal("gtfield")
	}
}

// Verifies: VAL-STRUCT-008
// Depends-On: TestVAL002Required
func TestVAL050RequiredIf(t *testing.T) {
	type item struct {
		Mode string
		Code string `validate:"required_if=Mode strict"`
	}
	v := validator.New()
	if v.Struct(item{Mode: "loose"}) != nil || v.Struct(item{Mode: "strict"}) == nil || v.Struct(item{Mode: "strict", Code: "x"}) != nil {
		t.Fatal("required_if")
	}
}

// Verifies: VAL-STRUCT-008
// Depends-On: TestVAL002Required
func TestVAL051RequiredWithout(t *testing.T) {
	type contact struct {
		Email string
		Phone string `validate:"required_without=Email"`
	}
	v := validator.New()
	if v.Struct(contact{Email: "a@b.test"}) != nil || v.Struct(contact{}) == nil {
		t.Fatal("required_without")
	}
}

// Verifies: VAL-STRUCT-009
// Depends-On: TestVAL002Required
func TestVAL052ExcludedIf(t *testing.T) {
	type item struct {
		Mode   string
		Secret string `validate:"excluded_if=Mode public"`
	}
	v := validator.New()
	if v.Struct(item{Mode: "private", Secret: "x"}) != nil || v.Struct(item{Mode: "public", Secret: "x"}) == nil {
		t.Fatal("excluded_if")
	}
}

// Verifies: VAL-STRUCT-010, VAL-STRUCT-012, VAL-CVI-005
// Depends-On: TestVAL038DiveSlice, TestVAL002Required
func TestVAL053DiveNestedStructs(t *testing.T) {
	type batch struct {
		Items []address `validate:"dive"`
	}
	ves := errorsOf(t, validator.New().Struct(batch{Items: []address{{City: "ok"}, {}}}))
	if len(ves) != 1 || ves[0].Value() != "" || ves[0].StructNamespace() != "batch.Items[1].City" {
		t.Fatalf("%v", ves)
	}
}

// Verifies: VAL-STRUCT-011, VAL-STRUCT-012
// Depends-On: TestVAL038DiveSlice, TestVAL014LowerAndUppercase
func TestVAL054MapKeyAndValueDive(t *testing.T) {
	type labels struct {
		Values map[string]string `validate:"dive,keys,lowercase,endkeys,required"`
	}
	ves := errorsOf(t, validator.New().Struct(labels{Values: map[string]string{"Bad": "", "good": "ok"}}))
	if len(ves) != 2 {
		t.Fatalf("want key and value failures, got %d: %v", len(ves), ves)
	}
	for _, fe := range ves {
		if !strings.Contains(fe.Namespace(), "[Bad]") {
			t.Fatalf("namespace=%q", fe.Namespace())
		}
	}
}

// Verifies: VAL-STRUCT-013, VAL-STRUCT-014
// Depends-On: TestVAL002Required, TestVAL018Email
func TestVAL055ValidateMapProjectsOnlyFailures(t *testing.T) {
	v := validator.New()
	result := v.ValidateMap(map[string]interface{}{"name": "ok", "email": "bad"}, map[string]interface{}{"name": "required", "email": "email"})
	if _, ok := result["name"]; ok {
		t.Fatal("successful key must be absent")
	}
	if _, ok := result["email"].(validator.ValidationErrors); !ok {
		t.Fatalf("email result=%T", result["email"])
	}
}

// Verifies: VAL-STRUCT-013, VAL-STRUCT-014
// Depends-On: TestVAL002Required, TestVAL018Email
func TestVAL056ValidateMapNestedRules(t *testing.T) {
	v := validator.New()
	result := v.ValidateMap(
		map[string]interface{}{"user": map[string]interface{}{"email": "bad"}},
		map[string]interface{}{"user": map[string]interface{}{"email": "email"}},
	)
	nested, ok := result["user"].(map[string]interface{})
	if !ok {
		t.Fatalf("nested=%T %#v", result["user"], result["user"])
	}
	if _, ok := nested["email"].(validator.ValidationErrors); !ok {
		t.Fatalf("email=%T", nested["email"])
	}
}

// Verifies: VAL-ERR-007, VAL-ERR-009, VAL-ERR-012, VAL-CVI-002
// Depends-On: TestVAL033ValidationErrorsCollection
func TestVAL057AlternateFieldNamesAndNamespaces(t *testing.T) {
	v := validator.New()
	v.RegisterTagNameFunc(func(sf reflect.StructField) string { return strings.SplitN(sf.Tag.Get("json"), ",", 2)[0] })
	ves := errorsOf(t, v.Struct(profile{Name: "ok", Email: "bad", Address: address{City: "ok"}}))
	if len(ves) != 2 {
		t.Fatalf("errors=%d %v", len(ves), ves)
	}
	fe := ves[0]
	if fe.Field() != "name" || fe.StructField() != "Name" || fe.Namespace() != "profile.name" || fe.StructNamespace() != "profile.Name" {
		t.Fatalf("field=%q struct=%q ns=%q sns=%q", fe.Field(), fe.StructField(), fe.Namespace(), fe.StructNamespace())
	}
}

// Verifies: VAL-ERR-011
// Depends-On: TestVAL002Required
func TestVAL058SetTagNameSelectsRuleTag(t *testing.T) {
	type input struct {
		Name string `check:"required" validate:"-"`
	}
	v := validator.New()
	v.SetTagName("check")
	fe := errorsOf(t, v.Struct(input{}))[0]
	if fe.StructField() != "Name" || fe.Tag() != "required" {
		t.Fatalf("field=%q tag=%q", fe.StructField(), fe.Tag())
	}
}

// Verifies: VAL-REG-006, VAL-REG-007, VAL-REG-008, VAL-CVI-004
// Depends-On: TestVAL033ValidationErrorsCollection
func TestVAL059StructLevelReportedErrors(t *testing.T) {
	type interval struct{ Start, End int }
	v := validator.New()
	v.RegisterStructValidation(func(sl validator.StructLevel) {
		x := sl.Current().Interface().(interval)
		if x.End <= x.Start {
			sl.ReportError(x.End, "End", "End", "afterstart", "Start")
		}
	}, interval{})
	fe := errorsOf(t, v.Struct(interval{Start: 5, End: 4}))[0]
	if fe.StructField() != "End" || fe.Tag() != "afterstart" || fe.Param() != "Start" || fe.Value() != 4 {
		t.Fatalf("bad report: field=%q tag=%q param=%q value=%v", fe.StructField(), fe.Tag(), fe.Param(), fe.Value())
	}
}

// Verifies: VAL-REG-003, VAL-REG-006, VAL-REG-008
// Depends-On: TestVAL031ContextValidationReceivesContext
func TestVAL060StructLevelContext(t *testing.T) {
	type key struct{}
	type item struct{ N int }
	ctx := context.WithValue(context.Background(), key{}, 7)
	v := validator.New()
	seen := 0
	v.RegisterStructValidationCtx(func(c context.Context, sl validator.StructLevel) { seen = c.Value(key{}).(int) }, item{})
	if err := v.StructCtx(ctx, item{N: 1}); err != nil || seen != 7 {
		t.Fatalf("err=%v seen=%d", err, seen)
	}
}

// Verifies: VAL-REG-009
// Depends-On: TestVAL005LenUsesRuneCount
func TestVAL061StructMapRulesOverrideTags(t *testing.T) {
	type item struct {
		Name string `validate:"min=2"`
	}
	v := validator.New()
	v.RegisterStructValidationMapRules(map[string]string{"Name": "min=5"}, item{})
	fe := errorsOf(t, v.Struct(item{Name: "abc"}))[0]
	if fe.Tag() != "min" || fe.Param() != "5" {
		t.Fatalf("tag=%q param=%q", fe.Tag(), fe.Param())
	}
}

// Verifies: VAL-REG-010, VAL-CVI-008
// Depends-On: TestVAL029CustomValidationFieldLevel
func TestVAL062RegistrationsAreInstanceLocal(t *testing.T) {
	a, b := validator.New(), validator.New()
	if err := a.RegisterValidation("even", func(fl validator.FieldLevel) bool { return fl.Field().Int()%2 == 0 }); err != nil {
		t.Fatal(err)
	}
	if a.Var(3, "even") == nil {
		t.Fatal("registered validator should run")
	}
	defer func() {
		if recover() == nil {
			t.Fatal("unregistered instance must not inherit custom tag")
		}
	}()
	_ = b.Var(2, "even")
}

// Verifies: VAL-CVI-004, VAL-ERR-003
// Depends-On: TestVAL002Required, TestVAL029CustomValidationFieldLevel
func TestVAL063BuiltInAndCustomErrorsCompose(t *testing.T) {
	type input struct {
		Name string `validate:"required"`
		N    int    `validate:"even"`
	}
	v := validator.New()
	_ = v.RegisterValidation("even", func(fl validator.FieldLevel) bool { return fl.Field().Int()%2 == 0 })
	ves := errorsOf(t, v.Struct(input{N: 3}))
	if len(ves) != 2 || ves[0].StructField() != "Name" || ves[1].StructField() != "N" {
		t.Fatalf("%v", ves)
	}
}

// Verifies: VAL-STRUCT-007, VAL-CVI-007
// Depends-On: TestVAL008EqualityAndInequality
func TestVAL064VarWithValueContextParity(t *testing.T) {
	v := validator.New()
	if v.VarWithValue("same", "same", "eqfield") != nil || v.VarWithValueCtx(context.Background(), "same", "other", "eqfield") == nil {
		t.Fatal("VarWithValue parity")
	}
}

// Verifies: VAL-CVI-007, VAL-STRUCT-014
// Depends-On: TestVAL018Email, TestVAL031ContextValidationReceivesContext
func TestVAL065ContextAndPlainMapValidationAgree(t *testing.T) {
	v := validator.New()
	data := map[string]interface{}{"name": "", "age": 3}
	rules := map[string]interface{}{"name": "required", "age": "gte=5"}
	a := v.ValidateMap(data, rules)
	b := v.ValidateMapCtx(context.Background(), data, rules)
	if !reflect.DeepEqual(mapKeys(a), mapKeys(b)) || len(a) != 2 {
		t.Fatalf("plain=%v ctx=%v", mapKeys(a), mapKeys(b))
	}
}

func mapKeys(m map[string]interface{}) map[string]bool {
	out := map[string]bool{}
	for k := range m {
		out[k] = true
	}
	return out
}
