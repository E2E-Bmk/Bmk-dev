package atomic

import (
	"reflect"
	"sort"
	"testing"

	"github.com/expr-lang/expr"
)

func eval(t *testing.T, source string, env any) any {
	t.Helper()
	out, err := expr.Eval(source, env)
	if err != nil {
		t.Fatalf("Eval(%q): %v", source, err)
	}
	return out
}

func equal(t *testing.T, got, want any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %#v (%T), want %#v (%T)", got, got, want, want)
	}
}

func sequence(t *testing.T, got any) []any {
	t.Helper()
	v := reflect.ValueOf(got)
	if v.Kind() != reflect.Array && v.Kind() != reflect.Slice {
		t.Fatalf("got %T, want an ordered sequence", got)
	}
	out := make([]any, v.Len())
	for i := range out {
		out[i] = v.Index(i).Interface()
	}
	return out
}

func numeric(t *testing.T, got any, want float64) {
	t.Helper()
	v := reflect.ValueOf(got)
	var n float64
	switch v.Kind() {
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		n = float64(v.Int())
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		n = float64(v.Uint())
	case reflect.Float32, reflect.Float64:
		n = v.Float()
	default:
		t.Fatalf("got %T, want numeric %v", got, want)
	}
	if n != want {
		t.Fatalf("got %v (%T), want numeric %v", got, got, want)
	}
}

// Verifies: EXPR-001
func TestLiterals(t *testing.T) {
	equal(t, eval(t, `42`, nil), 42)
	equal(t, eval(t, `2.5`, nil), 2.5)
	equal(t, eval(t, `"go"`, nil), "go")
	equal(t, eval(t, `true`, nil), true)
	if eval(t, `nil`, nil) != nil {
		t.Fatal("nil literal")
	}
}

// Verifies: EXPR-002
func TestArithmeticPrecedence(t *testing.T) {
	equal(t, eval(t, `2 + 3 * 4`, nil), 14)
	equal(t, eval(t, `(2 + 3) * 4`, nil), 20)
	numeric(t, eval(t, `2 ** 3`, nil), 8)
}

// Verifies: EXPR-003
func TestStringConcatenation(t *testing.T) { equal(t, eval(t, `"go" + "pher"`, nil), "gopher") }

// Verifies: EXPR-004, EXPR-005
func TestUnaryAndComparisons(t *testing.T) {
	equal(t, eval(t, `-5`, nil), -5)
	equal(t, eval(t, `not false and 3 < 4 and 4 >= 4`, nil), true)
}

// Verifies: EXPR-007, EXPR-008
func TestMembershipAndCoalescing(t *testing.T) {
	equal(t, eval(t, `2 in [1,2,3] and 4 not in [1,2,3]`, nil), true)
	equal(t, eval(t, `nil ?? "fallback"`, nil), "fallback")
}

// Verifies: EXPR-009
func TestOptionalMember(t *testing.T) {
	if eval(t, `item?.name`, map[string]any{"item": nil}) != nil {
		t.Fatal("want nil")
	}
}

// Verifies: EXPR-010
func TestIndexSliceAndRange(t *testing.T) {
	equal(t, sequence(t, eval(t, `[10,20,30,40][1:3]`, nil)), []any{20, 30})
	equal(t, eval(t, `2..5`, nil), []int{2, 3, 4, 5})
}

// Verifies: EXPR-018
func TestLetAndSequence(t *testing.T) { equal(t, eval(t, `let x = 3; let y = 4; x*y`, nil), 12) }

// Verifies: EXPR-011
func TestMapEnvironment(t *testing.T) {
	equal(t, eval(t, `price * qty`, map[string]any{"price": 7, "qty": 6}), 42)
}

type taggedEnv struct {
	Value int `expr:"renamed"`
}

// Verifies: EXPR-012, EXPR-013
func TestStructAndTaggedEnvironment(t *testing.T) {
	p, err := expr.Compile(`renamed + 1`, expr.Env(taggedEnv{}))
	if err != nil {
		t.Fatal(err)
	}
	out, err := expr.Run(p, taggedEnv{Value: 8})
	if err != nil {
		t.Fatal(err)
	}
	equal(t, out, 9)
}

type methodEnv struct{ Base int }

func (e methodEnv) Add(v int) int { return e.Base + v }

// Verifies: EXPR-014
func TestStructMethod(t *testing.T) {
	p, err := expr.Compile(`Add(5)`, expr.Env(methodEnv{}))
	if err != nil {
		t.Fatal(err)
	}
	out, err := expr.Run(p, methodEnv{Base: 7})
	if err != nil {
		t.Fatal(err)
	}
	equal(t, out, 12)
}

// Verifies: EXPR-015
func TestUnknownVariableRejected(t *testing.T) {
	p, err := expr.Compile(`known + missing`, expr.Env(map[string]any{"known": 1}))
	if err == nil || p != nil {
		t.Fatal("unknown variable must fail compilation")
	}
}

// Verifies: EXPR-016
func TestAllowUndefinedVariable(t *testing.T) {
	p, err := expr.Compile(`missing ?? 9`, expr.Env(map[string]any{}), expr.AllowUndefinedVariables())
	if err != nil {
		t.Fatal(err)
	}
	out, err := expr.Run(p, map[string]any{})
	if err != nil {
		t.Fatal(err)
	}
	equal(t, out, 9)
}

// Verifies: EXPR-017
func TestDynamicMapMissingMember(t *testing.T) {
	env := map[string]any{"object": map[string]any{"present": 1}}
	if eval(t, `object.missing`, env) != nil {
		t.Fatal("want nil")
	}
}

// Verifies: EXPR-021
func TestQuantifiers(t *testing.T) {
	equal(t, eval(t, `all([2,4,6], {# % 2 == 0})`, nil), true)
	equal(t, eval(t, `any([1,3,4], {# % 2 == 0})`, nil), true)
	equal(t, eval(t, `none([1,3], {# % 2 == 0})`, nil), true)
	equal(t, eval(t, `one([1,2,3], {# % 2 == 0})`, nil), true)
}

// Verifies: EXPR-022
func TestPredicateIndex(t *testing.T) {
	equal(t, sequence(t, eval(t, `map([10,20,30], {# + #index})`, nil)), []any{10, 21, 32})
}

// Verifies: EXPR-023, EXPR-024
func TestFilterAndMap(t *testing.T) {
	equal(t, sequence(t, eval(t, `filter([1,2,3,4], {# % 2 == 0})`, nil)), []any{2, 4})
	equal(t, sequence(t, eval(t, `map([1,2,3], {# * 3})`, nil)), []any{3, 6, 9})
}

// Verifies: EXPR-025, EXPR-026
func TestCountAndFind(t *testing.T) {
	equal(t, eval(t, `count([1,2,3,4], {# > 2})`, nil), 2)
	equal(t, eval(t, `find([1,4,6], {# % 2 == 0})`, nil), 4)
	equal(t, eval(t, `findIndex([1,4,6], {# % 2 == 0})`, nil), 1)
}

// Verifies: EXPR-027
func TestGroupBy(t *testing.T) {
	got := eval(t, `groupBy([1,2,3,4], {string(# % 2)})`, nil).(map[any][]any)
	equal(t, got["0"], []any{2, 4})
	equal(t, got["1"], []any{1, 3})
}

// Verifies: EXPR-028
func TestConcatFlattenUniq(t *testing.T) {
	equal(t, sequence(t, eval(t, `concat([1,2], [3,4])`, nil)), []any{1, 2, 3, 4})
	equal(t, sequence(t, eval(t, `flatten([[1,2],[3]])`, nil)), []any{1, 2, 3})
	equal(t, sequence(t, eval(t, `uniq([2,1,2,3,1])`, nil)), []any{2, 1, 3})
}

// Verifies: EXPR-029, EXPR-030
func TestJoinAndReduce(t *testing.T) {
	equal(t, eval(t, `join(["a","b","c"], "-")`, nil), "a-b-c")
	equal(t, eval(t, `reduce([1,2,3], {#acc + #}, 10)`, nil), 16)
}

// Verifies: EXPR-031
func TestAggregates(t *testing.T) {
	equal(t, eval(t, `sum([1,2,3,4])`, nil), 10)
	equal(t, eval(t, `mean([2,4,6])`, nil), 4.0)
	equal(t, eval(t, `median([9,1,5])`, nil), 5.0)
}

// Verifies: EXPR-032, EXPR-033
func TestOrderingBuiltins(t *testing.T) {
	equal(t, sequence(t, eval(t, `take(reverse(sort([3,1,2])), 2)`, nil)), []any{3, 2})
	if eval(t, `first([])`, nil) != nil || eval(t, `last([])`, nil) != nil {
		t.Fatal("empty first/last")
	}
}

// Verifies: EXPR-034
func TestMapKeysAndValues(t *testing.T) {
	keys := sequence(t, eval(t, `keys({b:2,a:1})`, nil))
	ss := []string{keys[0].(string), keys[1].(string)}
	sort.Strings(ss)
	equal(t, ss, []string{"a", "b"})
}

// Verifies: EXPR-035
func TestTrimAndCase(t *testing.T) {
	equal(t, eval(t, `upper(trim("  Go  ")) + lower("LANG")`, nil), "GOlang")
}

// Verifies: EXPR-036
func TestOtherStringBuiltins(t *testing.T) {
	equal(t, eval(t, `join(split(replace("a-b-a", "a", "x"), "-"), ":")`, nil), "x:b:x")
	equal(t, eval(t, `hasPrefix("gopher", "go") and hasSuffix("gopher", "her")`, nil), true)
}

// Verifies: EXPR-037, EXPR-038
func TestLenAndGet(t *testing.T) {
	equal(t, eval(t, `len("abc") + len([1,2]) + len({a:1})`, nil), 6)
	if eval(t, `get([1,2], 9)`, nil) != nil {
		t.Fatal("get unavailable must be nil")
	}
}

// Verifies: EXPR-039
func TestNumericBuiltins(t *testing.T) {
	equal(t, eval(t, `max(abs(-3), min(8, 4)) + ceil(1.2) + floor(1.8) + round(1.5)`, nil), 9.0)
}

// Verifies: EXPR-040
func TestConversions(t *testing.T) {
	equal(t, eval(t, `int(2.9)`, nil), 2)
	equal(t, eval(t, `float(2)`, nil), 2.0)
	equal(t, eval(t, `type([1])`, nil), "array")
}

// Verifies: EXPR-041
func TestBase64RoundTrip(t *testing.T) {
	equal(t, eval(t, `fromBase64(toBase64("你好, Go"))`, nil), "你好, Go")
}

// Verifies: EXPR-042
func TestPairsRoundTrip(t *testing.T) {
	equal(t, eval(t, `fromPairs(toPairs({a:1,b:2})).a + fromPairs(toPairs({a:1,b:2})).b`, nil), 3)
}

// Verifies: EXPR-043
func TestBitwiseBuiltins(t *testing.T) {
	equal(t, eval(t, `bitand(14, 11)`, nil), 10)
	equal(t, eval(t, `bitor(8, 3)`, nil), 11)
	equal(t, eval(t, `bitxor(15, 10)`, nil), 5)
	equal(t, eval(t, `bitshl(3, 2)`, nil), 12)
}

// Verifies: EXPR-044, EXPR-045, EXPR-071
func TestReturnKindOptions(t *testing.T) {
	p, err := expr.Compile(`2 + 3`, expr.AsInt64())
	if err != nil {
		t.Fatal(err)
	}
	out, err := expr.Run(p, nil)
	if err != nil {
		t.Fatal(err)
	}
	if _, ok := out.(int64); !ok || out.(int64) != 5 {
		t.Fatalf("%#v %T", out, out)
	}
	if p, err = expr.Compile(`"x"`, expr.AsBool()); err == nil || p != nil {
		t.Fatal("incompatible return kind")
	}
}

// Verifies: EXPR-051
func TestNodeBudget(t *testing.T) {
	if p, err := expr.Compile(`1+2+3+4`, expr.MaxNodes(2)); err == nil || p != nil {
		t.Fatal("node budget")
	}
	if _, err := expr.Compile(`1+2+3+4`, expr.MaxNodes(0)); err != nil {
		t.Fatal(err)
	}
}

// Verifies: EXPR-056
func TestBuiltinControls(t *testing.T) {
	if p, err := expr.Compile(`len([1])`, expr.Env(map[string]any{}), expr.DisableBuiltin("len")); err == nil || p != nil {
		t.Fatal("disabled builtin")
	}
	p, err := expr.Compile(`len([1])`, expr.DisableAllBuiltins(), expr.EnableBuiltin("len"))
	if err != nil || p == nil {
		t.Fatalf("re-enabled: %v", err)
	}
}

// Verifies: EXPR-066, EXPR-075
func TestCompileErrorsReturnNilProgram(t *testing.T) {
	for _, source := range []string{`1 +`, `1 + true`} {
		p, err := expr.Compile(source)
		if err == nil || p != nil {
			t.Fatalf("%q: program=%v err=%v", source, p, err)
		}
	}
}
