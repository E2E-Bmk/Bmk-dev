package atomic

import (
	"strings"
	"testing"

	jsonschema "github.com/santhosh-tekuri/jsonschema/v6"
	"github.com/santhosh-tekuri/jsonschema/v6/kind"
)

func mustJSON(t *testing.T, s string) any {
	t.Helper()
	v, err := jsonschema.UnmarshalJSON(strings.NewReader(s))
	if err != nil {
		t.Fatalf("unmarshal %q: %v", s, err)
	}
	return v
}

func compile(t *testing.T, doc string) *jsonschema.Schema {
	t.Helper()
	c := jsonschema.NewCompiler()
	if err := c.AddResource("https://spec.test/s.json", mustJSON(t, doc)); err != nil {
		t.Fatalf("AddResource: %v", err)
	}
	sch, err := c.Compile("https://spec.test/s.json")
	if err != nil {
		t.Fatalf("Compile: %v", err)
	}
	return sch
}

func allKinds(e *jsonschema.ValidationError) []jsonschema.ErrorKind {
	kinds := []jsonschema.ErrorKind{e.ErrorKind}
	for _, c := range e.Causes {
		kinds = append(kinds, allKinds(c)...)
	}
	return kinds
}

func assertFailsWith(t *testing.T, sch *jsonschema.Schema, inst any, match func(jsonschema.ErrorKind) bool, label string) {
	t.Helper()
	err := sch.Validate(inst)
	if err == nil {
		t.Fatalf("expected %s violation, got valid", label)
	}
	verr, ok := err.(*jsonschema.ValidationError)
	if !ok {
		t.Fatalf("expected *ValidationError, got %T", err)
	}
	for _, k := range allKinds(verr) {
		if match(k) {
			return
		}
	}
	t.Fatalf("no %s kind in error tree: %v", label, err)
}

func assertValid(t *testing.T, sch *jsonschema.Schema, inst any) {
	t.Helper()
	if err := sch.Validate(inst); err != nil {
		t.Fatalf("expected valid, got %v", err)
	}
}

// ── type / enum / const ────────────────────────────────────────────────

func TestTypeIntegerAcceptsZeroFractionNumbers(t *testing.T) {
	sch := compile(t, `{"type": "integer"}`)
	assertValid(t, sch, mustJSON(t, `7`))
	assertValid(t, sch, mustJSON(t, `7.0`))
	assertFailsWith(t, sch, mustJSON(t, `7.5`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Type)
		return ok
	}, "type")
}

func TestTypeKindReportsGotAndWant(t *testing.T) {
	sch := compile(t, `{"type": "integer"}`)
	err := sch.Validate("seven").(*jsonschema.ValidationError)
	var tk *kind.Type
	for _, k := range allKinds(err) {
		if v, ok := k.(*kind.Type); ok {
			tk = v
		}
	}
	if tk == nil {
		t.Fatal("no kind.Type in tree")
	}
	if tk.Got != "string" {
		t.Fatalf("Got = %q, want \"string\"", tk.Got)
	}
	if len(tk.Want) != 1 || tk.Want[0] != "integer" {
		t.Fatalf("Want = %v, want [integer]", tk.Want)
	}
}

func TestTypeListMatchesAnyListedType(t *testing.T) {
	sch := compile(t, `{"type": ["string", "null"]}`)
	assertValid(t, sch, "text")
	assertValid(t, sch, nil)
	assertFailsWith(t, sch, mustJSON(t, `12`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Type)
		return ok
	}, "type")
}

func TestEnumUsesRationalNumberEquality(t *testing.T) {
	sch := compile(t, `{"enum": [4, "blue"]}`)
	assertValid(t, sch, mustJSON(t, `4.0`))
	assertValid(t, sch, "blue")
	assertFailsWith(t, sch, mustJSON(t, `4.5`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Enum)
		return ok
	}, "enum")
}

func TestConstBehavesAsSingleValueEnum(t *testing.T) {
	sch := compile(t, `{"const": 12}`)
	assertValid(t, sch, mustJSON(t, `12.0`))
	assertFailsWith(t, sch, mustJSON(t, `13`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Const)
		return ok
	}, "const")
}

func TestConstObjectEqualityIgnoresKeyOrder(t *testing.T) {
	sch := compile(t, `{"const": {"a": 1, "b": [true, null]}}`)
	assertValid(t, sch, mustJSON(t, `{"b": [true, null], "a": 1.0}`))
	assertFailsWith(t, sch, mustJSON(t, `{"a": 1, "b": [null, true]}`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Const)
		return ok
	}, "const")
}

// ── numeric keywords ───────────────────────────────────────────────────

func TestMinimumAndMaximumAreInclusive(t *testing.T) {
	sch := compile(t, `{"minimum": 4, "maximum": 9}`)
	assertValid(t, sch, mustJSON(t, `4`))
	assertValid(t, sch, mustJSON(t, `9`))
	assertFailsWith(t, sch, mustJSON(t, `3.99`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Minimum)
		return ok
	}, "minimum")
	assertFailsWith(t, sch, mustJSON(t, `9.01`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Maximum)
		return ok
	}, "maximum")
}

func TestExclusiveBoundsRejectBoundaryValues(t *testing.T) {
	sch := compile(t, `{"exclusiveMinimum": 2, "exclusiveMaximum": 6}`)
	assertValid(t, sch, mustJSON(t, `2.5`))
	assertFailsWith(t, sch, mustJSON(t, `2`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.ExclusiveMinimum)
		return ok
	}, "exclusiveMinimum")
	assertFailsWith(t, sch, mustJSON(t, `6`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.ExclusiveMaximum)
		return ok
	}, "exclusiveMaximum")
}

func TestMultipleOfUsesRationalArithmetic(t *testing.T) {
	sch := compile(t, `{"multipleOf": 0.1}`)
	assertValid(t, sch, mustJSON(t, `0.3`))
	assertValid(t, sch, mustJSON(t, `1.7`))
	assertFailsWith(t, sch, mustJSON(t, `0.25`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MultipleOf)
		return ok
	}, "multipleOf")
}

func TestNumericKeywordsIgnoreNonNumbers(t *testing.T) {
	sch := compile(t, `{"minimum": 100}`)
	assertValid(t, sch, "tiny")
	assertValid(t, sch, true)
	assertValid(t, sch, mustJSON(t, `[]`))
	if sch.Validate(mustJSON(t, `99`)) == nil {
		t.Fatal("the keyword must still bind numbers")
	}
}

func TestValidateAcceptsNativeGoNumbers(t *testing.T) {
	sch := compile(t, `{"minimum": 4}`)
	assertValid(t, sch, 5)
	assertValid(t, sch, int32(6))
	assertValid(t, sch, 4.25)
	if sch.Validate(3.5) == nil {
		t.Fatal("3.5 must violate minimum 4")
	}
}

// ── string keywords ────────────────────────────────────────────────────

func TestStringLengthCountsCodePoints(t *testing.T) {
	sch := compile(t, `{"minLength": 3, "maxLength": 4}`)
	assertValid(t, sch, "héé")
	assertValid(t, sch, "日本語文")
	assertFailsWith(t, sch, "hé", func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MinLength)
		return ok
	}, "minLength")
	assertFailsWith(t, sch, "héééé", func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MaxLength)
		return ok
	}, "maxLength")
}

func TestPatternMatchesAnywhereInString(t *testing.T) {
	sch := compile(t, `{"pattern": "ab+c"}`)
	assertValid(t, sch, "xxabbbcyy")
	assertFailsWith(t, sch, "acb", func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Pattern)
		return ok
	}, "pattern")
}

// ── object keywords ────────────────────────────────────────────────────

func TestPropertiesApplyToMatchingMembers(t *testing.T) {
	sch := compile(t, `{"properties": {"size": {"type": "integer"}}}`)
	assertValid(t, sch, mustJSON(t, `{"size": 3, "other": "free"}`))
	assertValid(t, sch, mustJSON(t, `{}`))
	if sch.Validate(mustJSON(t, `{"size": "big"}`)) == nil {
		t.Fatal("size string must fail")
	}
}

func TestRequiredReportsExactlyMissingMembers(t *testing.T) {
	sch := compile(t, `{"required": ["alpha", "beta", "gamma"]}`)
	err := sch.Validate(mustJSON(t, `{"beta": 1}`)).(*jsonschema.ValidationError)
	var rk *kind.Required
	for _, k := range allKinds(err) {
		if v, ok := k.(*kind.Required); ok {
			rk = v
		}
	}
	if rk == nil {
		t.Fatal("no kind.Required in tree")
	}
	if len(rk.Missing) != 2 || rk.Missing[0] != "alpha" || rk.Missing[1] != "gamma" {
		t.Fatalf("Missing = %v, want [alpha gamma]", rk.Missing)
	}
}

func TestPatternPropertiesApplyByNameMatch(t *testing.T) {
	sch := compile(t, `{"patternProperties": {"^n_": {"type": "number"}}}`)
	assertValid(t, sch, mustJSON(t, `{"n_a": 1, "s_a": "x"}`))
	if sch.Validate(mustJSON(t, `{"n_a": "x"}`)) == nil {
		t.Fatal("n_a string must fail")
	}
}

func TestAdditionalPropertiesFalseRejectsUnmatched(t *testing.T) {
	sch := compile(t, `{"properties": {"id": true}, "additionalProperties": false}`)
	assertValid(t, sch, mustJSON(t, `{"id": 9}`))
	assertFailsWith(t, sch, mustJSON(t, `{"id": 9, "extra": 1}`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.AdditionalProperties)
		return ok
	}, "additionalProperties")
}

func TestAdditionalPropertiesSchemaValidatesUnmatched(t *testing.T) {
	sch := compile(t, `{"properties": {"id": true}, "additionalProperties": {"type": "string"}}`)
	assertValid(t, sch, mustJSON(t, `{"id": 9, "note": "ok"}`))
	if sch.Validate(mustJSON(t, `{"id": 9, "note": 5}`)) == nil {
		t.Fatal("non-string extra member must fail")
	}
}

func TestPropertyNamesValidatesMemberNames(t *testing.T) {
	sch := compile(t, `{"propertyNames": {"maxLength": 3}}`)
	assertValid(t, sch, mustJSON(t, `{"abc": 1, "d": 2}`))
	assertFailsWith(t, sch, mustJSON(t, `{"abcd": 1}`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MaxLength)
		return ok
	}, "propertyNames/maxLength")
}

func TestMinAndMaxPropertiesBoundMemberCount(t *testing.T) {
	sch := compile(t, `{"minProperties": 1, "maxProperties": 2}`)
	assertValid(t, sch, mustJSON(t, `{"a": 1, "b": 2}`))
	assertFailsWith(t, sch, mustJSON(t, `{}`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MinProperties)
		return ok
	}, "minProperties")
	assertFailsWith(t, sch, mustJSON(t, `{"a":1,"b":2,"c":3}`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MaxProperties)
		return ok
	}, "maxProperties")
}

func TestDependentRequiredAddsObligations(t *testing.T) {
	sch := compile(t, `{"dependentRequired": {"card": ["expiry"]}}`)
	assertValid(t, sch, mustJSON(t, `{"cash": 1}`))
	assertValid(t, sch, mustJSON(t, `{"card": "4", "expiry": "12/28"}`))
	assertFailsWith(t, sch, mustJSON(t, `{"card": "4"}`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.DependentRequired)
		return ok
	}, "dependentRequired")
}

func TestDependentSchemasApplyWhenMemberPresent(t *testing.T) {
	sch := compile(t, `{"dependentSchemas": {"loan": {"required": ["term"]}}}`)
	assertValid(t, sch, mustJSON(t, `{"other": true}`))
	assertValid(t, sch, mustJSON(t, `{"loan": 100, "term": 12}`))
	assertFailsWith(t, sch, mustJSON(t, `{"loan": 100}`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Required)
		return ok
	}, "dependentSchemas/required")
}

// ── array keywords ─────────────────────────────────────────────────────

func TestPrefixItemsThenItemsSplit(t *testing.T) {
	sch := compile(t, `{"prefixItems": [{"type": "integer"}], "items": {"type": "string"}}`)
	assertValid(t, sch, mustJSON(t, `[4, "a", "b"]`))
	if sch.Validate(mustJSON(t, `[4, "a", 5]`)) == nil {
		t.Fatal("post-prefix number must fail")
	}
	if sch.Validate(mustJSON(t, `["a"]`)) == nil {
		t.Fatal("prefix violation must fail")
	}
}

func TestItemsAloneCoversEveryElement(t *testing.T) {
	sch := compile(t, `{"items": {"minimum": 0}}`)
	assertValid(t, sch, mustJSON(t, `[0, 5, 2.5]`))
	if sch.Validate(mustJSON(t, `[1, -2]`)) == nil {
		t.Fatal("negative element must fail")
	}
}

func TestMinAndMaxItemsBoundLength(t *testing.T) {
	sch := compile(t, `{"minItems": 2, "maxItems": 3}`)
	assertValid(t, sch, mustJSON(t, `[1, 2]`))
	assertFailsWith(t, sch, mustJSON(t, `[1]`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MinItems)
		return ok
	}, "minItems")
	assertFailsWith(t, sch, mustJSON(t, `[1,2,3,4]`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MaxItems)
		return ok
	}, "maxItems")
}

func TestUniqueItemsUsesRationalEquality(t *testing.T) {
	sch := compile(t, `{"uniqueItems": true}`)
	assertValid(t, sch, mustJSON(t, `[1, 2, "1"]`))
	assertFailsWith(t, sch, mustJSON(t, `[3, 3.0]`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.UniqueItems)
		return ok
	}, "uniqueItems")
}

func TestContainsRequiresAtLeastOneMatch(t *testing.T) {
	sch := compile(t, `{"contains": {"type": "string"}}`)
	assertValid(t, sch, mustJSON(t, `[1, "found", 2]`))
	assertFailsWith(t, sch, mustJSON(t, `[1, 2]`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Contains)
		return ok
	}, "contains")
}

func TestMinAndMaxContainsBoundMatchCount(t *testing.T) {
	sch := compile(t, `{"contains": {"type": "string"}, "minContains": 2, "maxContains": 3}`)
	assertValid(t, sch, mustJSON(t, `["a", 1, "b"]`))
	assertFailsWith(t, sch, mustJSON(t, `["a", 1]`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MinContains)
		return ok
	}, "minContains")
	assertFailsWith(t, sch, mustJSON(t, `["a","b","c","d"]`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.MaxContains)
		return ok
	}, "maxContains")
}

func TestMinContainsZeroAcceptsNoMatches(t *testing.T) {
	sch := compile(t, `{"contains": {"type": "string"}, "minContains": 0}`)
	assertValid(t, sch, mustJSON(t, `[1, 2]`))
	assertValid(t, sch, mustJSON(t, `[]`))
	strict := compile(t, `{"contains": {"type": "string"}, "minContains": 1}`)
	if strict.Validate(mustJSON(t, `[1, 2]`)) == nil {
		t.Fatal("minContains 1 must reject a match-free array")
	}
}

// ── combinators and conditionals ───────────────────────────────────────

func TestAllOfRequiresEveryBranch(t *testing.T) {
	sch := compile(t, `{"allOf": [{"minimum": 2}, {"maximum": 8}]}`)
	assertValid(t, sch, mustJSON(t, `5`))
	assertFailsWith(t, sch, mustJSON(t, `9`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.AllOf)
		return ok
	}, "allOf")
}

func TestAnyOfRequiresAtLeastOneBranch(t *testing.T) {
	sch := compile(t, `{"anyOf": [{"type": "string"}, {"minimum": 10}]}`)
	assertValid(t, sch, "word")
	assertValid(t, sch, mustJSON(t, `11`))
	assertFailsWith(t, sch, mustJSON(t, `5`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.AnyOf)
		return ok
	}, "anyOf")
}

func TestOneOfRequiresExactlyOneMatch(t *testing.T) {
	sch := compile(t, `{"oneOf": [{"type": "number"}, {"type": "boolean"}]}`)
	assertValid(t, sch, mustJSON(t, `8`))
	assertFailsWith(t, sch, "neither", func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.OneOf)
		return ok
	}, "oneOf zero matches")
	sch2 := compile(t, `{"oneOf": [{"type": "number"}, {"maximum": 100}]}`)
	assertFailsWith(t, sch2, mustJSON(t, `5`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.OneOf)
		return ok
	}, "oneOf two matches")
}

func TestNotInvertsItsSubschema(t *testing.T) {
	sch := compile(t, `{"not": {"type": "string"}}`)
	assertValid(t, sch, mustJSON(t, `31`))
	assertFailsWith(t, sch, "nope", func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.Not)
		return ok
	}, "not")
}

func TestIfThenElseSelectsBranch(t *testing.T) {
	sch := compile(t, `{
		"if": {"required": ["card"]},
		"then": {"required": ["expiry"]},
		"else": {"required": ["iban"]}
	}`)
	assertValid(t, sch, mustJSON(t, `{"card": "4", "expiry": "01/30"}`))
	assertValid(t, sch, mustJSON(t, `{"iban": "DE00"}`))
	if sch.Validate(mustJSON(t, `{"card": "4"}`)) == nil {
		t.Fatal("then branch obligation must apply")
	}
	if sch.Validate(mustJSON(t, `{"cash": 1}`)) == nil {
		t.Fatal("else branch obligation must apply")
	}
}

func TestIfWithoutBranchesConstrainsNothing(t *testing.T) {
	sch := compile(t, `{"if": {"type": "string"}}`)
	assertValid(t, sch, "s")
	assertValid(t, sch, mustJSON(t, `5`))
	withThen := compile(t, `{"if": {"type": "string"}, "then": {"minLength": 4}}`)
	if withThen.Validate("abc") == nil {
		t.Fatal("adding then must activate the conditional")
	}
}
