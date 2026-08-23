package atomic_test

import (
	"context"
	"errors"
	"reflect"
	"testing"
	"time"

	"github.com/itchyny/gojq"
)

func run(t *testing.T, src string, input any) []any {
	t.Helper()
	q, err := gojq.Parse(src)
	if err != nil {
		t.Fatalf("parse %q: %v", src, err)
	}
	return drain(q.Run(input), 100)
}

func drain(iter gojq.Iter, limit int) []any {
	vs := make([]any, 0)
	for len(vs) < limit {
		v, ok := iter.Next()
		if !ok {
			break
		}
		vs = append(vs, v)
	}
	return vs
}

func assertValues(t *testing.T, got, want []any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %#v, want %#v", got, want)
	}
}

// Verifies: GJQ001, GJQ005
func TestGJQ001ParseIdentity(t *testing.T) {
	input := map[string]any{"a": 1}
	assertValues(t, run(t, ".", input), []any{input})
}

// Verifies: GJQ002
func TestGJQ002ParseErrorOffsetAndToken(t *testing.T) {
	_, err := gojq.Parse(`"é" | ]`)
	var pe *gojq.ParseError
	if !errors.As(err, &pe) || pe.Offset < len(`"é" | `) || pe.Token != "]" || pe.Error() == "" {
		t.Fatalf("parse error = %#v", err)
	}
}

// Verifies: GJQ003
func TestGJQ003QueryStringRoundTrip(t *testing.T) {
	q, err := gojq.Parse(`def twice(f): f|f; (.a + 1) | twice(.)`)
	if err != nil {
		t.Fatal(err)
	}
	q2, err := gojq.Parse(q.String())
	if err != nil {
		t.Fatalf("reparse %q: %v", q.String(), err)
	}
	assertValues(t, drain(q.Run(map[string]any{"a": 2}), 10), drain(q2.Run(map[string]any{"a": 2}), 10))
}

// Verifies: GJQ004
func TestGJQ004NewIterAndExhaustion(t *testing.T) {
	it := gojq.NewIter("a", "b", "c")
	assertValues(t, drain(it, 10), []any{"a", "b", "c"})
	if v, ok := it.Next(); ok || v != nil {
		t.Fatalf("exhausted iterator returned %#v, %v", v, ok)
	}
	if _, ok := gojq.NewIter[int]().Next(); ok {
		t.Fatal("empty iterator emitted a value")
	}
}

// Verifies: GJQ005
func TestGJQ005CommaPipeAndEmpty(t *testing.T) {
	assertValues(t, run(t, `(1,2,empty,3) | . * 10`, nil), []any{10, 20, 30})
}

// Verifies: GJQ006
func TestGJQ006LiteralAndArrayConstruction(t *testing.T) {
	want := []any{[]any{nil, true, "x", 3}}
	assertValues(t, run(t, `[null,true,"x",3]`, nil), want)
}

// Verifies: GJQ006
func TestGJQ007ObjectConstructionAlternatives(t *testing.T) {
	want := []any{map[string]any{"x": 1}, map[string]any{"x": 2}}
	assertValues(t, run(t, `{x:(1,2)}`, nil), want)
}

// Verifies: GJQ007
func TestGJQ008ObjectLookupMissingAndOptional(t *testing.T) {
	assertValues(t, run(t, `.a,.missing`, map[string]any{"a": 7}), []any{7, nil})
	assertValues(t, run(t, `.a?`, 1), []any{})
}

// Verifies: GJQ007
func TestGJQ009ObjectIterationSortedKeys(t *testing.T) {
	in := map[string]any{"z": 3, "a": 1, "m": 2}
	assertValues(t, run(t, `.[]`, in), []any{1, 2, 3})
}

// Verifies: GJQ008
func TestGJQ010ArrayIndices(t *testing.T) {
	in := []any{"a", "b", "c"}
	assertValues(t, run(t, `.[0],.[-1],.[99]`, in), []any{"a", "c", nil})
}

// Verifies: GJQ008
func TestGJQ011ArrayAndUnicodeStringSlices(t *testing.T) {
	assertValues(t, run(t, `.[1:3]`, []any{0, 1, 2, 3}), []any{[]any{1, 2}})
	assertValues(t, run(t, `.[1:3]`, "a世界z"), []any{"世界"})
}

// Verifies: GJQ009
func TestGJQ012NumericArithmetic(t *testing.T) {
	assertValues(t, run(t, `1+2, 7-3, 6*4, 7/2, 7%4, -5`, nil), []any{3, 4, 24, 3.5, 3, -5})
}

// Verifies: GJQ010
func TestGJQ013PolymorphicAddition(t *testing.T) {
	assertValues(t, run(t, `"ab"+"cd", [1]+[2,3], {a:1}+{b:2,a:9}`, nil), []any{
		"abcd", []any{1, 2, 3}, map[string]any{"a": 9, "b": 2},
	})
}

// Verifies: GJQ009
func TestGJQ014InvalidArithmeticEmitsError(t *testing.T) {
	vs := run(t, `"x" - 1`, nil)
	if len(vs) != 1 {
		t.Fatalf("values = %#v", vs)
	}
	if _, ok := vs[0].(error); !ok {
		t.Fatalf("expected error, got %#v", vs[0])
	}
}

// Verifies: GJQ011
func TestGJQ015EqualityAndTotalOrder(t *testing.T) {
	assertValues(t, run(t, `null < false, false < true, true < 0, 0 < "", "" < [], [] < {}, [1,2] < [1,3]`, nil),
		[]any{true, true, true, true, true, true, true})
}

// Verifies: GJQ011
func TestGJQ016RecursiveEquality(t *testing.T) {
	assertValues(t, run(t, `{b:[1,{x:true}],a:2} == {a:2,b:[1,{x:true}]}`, nil), []any{true})
}

// Verifies: GJQ012
func TestGJQ017TruthinessAndShortCircuit(t *testing.T) {
	assertValues(t, run(t, `null or 0, false and error("bad"), true or error("bad")`, nil), []any{true, false, true})
}

// Verifies: GJQ013
func TestGJQ018ConditionalAndSelect(t *testing.T) {
	assertValues(t, run(t, `if . > 2 then "big" else "small" end`, 3), []any{"big"})
	assertValues(t, run(t, `.[] | select(. % 2 == 0)`, []any{1, 2, 3, 4}), []any{2, 4})
}

// Verifies: GJQ014
func TestGJQ019MapLengthKeysHas(t *testing.T) {
	assertValues(t, run(t, `map(. * 2)`, []any{1, 2, 3}), []any{[]any{2, 4, 6}})
	assertValues(t, run(t, `[("世界"|length), ({z:1,a:2}|keys), ([4,5]|keys), ({a:1}|has("a")), ([1]|has(1))]`, nil),
		[]any{[]any{2, []any{"a", "z"}, []any{0, 1}, true, false}})
}

// Verifies: GJQ015
func TestGJQ020AggregatesAndEmptyConventions(t *testing.T) {
	assertValues(t, run(t, `[ ([1,2,3]|add), ([]|add), ([false,true]|any), ([]|any), ([true,true]|all), ([]|all) ]`, nil),
		[]any{[]any{6, nil, true, false, true, true}})
}

// Verifies: GJQ015
func TestGJQ021MinMaxSortUnique(t *testing.T) {
	assertValues(t, run(t, `[3,1,2,1] | [min,max,sort,unique]`, nil),
		[]any{[]any{1, 3, []any{1, 1, 2, 3}, []any{1, 2, 3}}})
}

// Verifies: GJQ016
func TestGJQ022RangeFirstLastLimit(t *testing.T) {
	assertValues(t, run(t, `range(1;6;2), first(4,5), last(6,7), limit(2; 8,9,10)`, nil),
		[]any{1, 3, 5, 4, 7, 8, 9})
}

// Verifies: GJQ016
func TestGJQ023UntilAndWhile(t *testing.T) {
	assertValues(t, run(t, `1 | until(. >= 8; . * 2)`, nil), []any{8})
	assertValues(t, run(t, `1 | while(. < 5; . + 1)`, nil), []any{1, 2, 3, 4})
}

// Verifies: GJQ017
func TestGJQ024StringCaseAffixAndTrim(t *testing.T) {
	assertValues(t, run(t, `[("AbC"|ascii_downcase), ("AbC"|ascii_upcase), ("foobar"|startswith("foo")), ("foobar"|endswith("bar")), ("xxab"|ltrimstr("xx")), ("abyy"|rtrimstr("yy"))]`, nil),
		[]any{[]any{"abc", "ABC", true, true, "ab", "ab"}})
}

// Verifies: GJQ017
func TestGJQ025SplitJoinExplodeImplodeConversions(t *testing.T) {
	assertValues(t, run(t, `[("a,b,c"|split(",")), (["a",2,true]|join("-")), ("A世"|explode|implode), (12|tostring), ("12.5"|tonumber)]`, nil),
		[]any{[]any{[]any{"a", "b", "c"}, "a-2-true", "A世", "12", 12.5}})
}

// Verifies: GJQ018
func TestGJQ026RegexTestAndMatch(t *testing.T) {
	assertValues(t, run(t, `[("Abc123"|test("^[a-z]+[0-9]+$";"i")), ("abc123"|match("[0-9]+")|.string)]`, nil),
		[]any{[]any{true, "123"}})
}

// Verifies: GJQ018
func TestGJQ027RegexCaptureAndScan(t *testing.T) {
	assertValues(t, run(t, `"abc-42" | capture("(?<word>[a-z]+)-(?<num>[0-9]+)")`, nil),
		[]any{map[string]any{"word": "abc", "num": "42"}})
	assertValues(t, run(t, `"a1b22" | scan("[0-9]+")`, nil), []any{"1", "22"})
}

// Verifies: GJQ018
func TestGJQ028RegexSubAndGsub(t *testing.T) {
	assertValues(t, run(t, `[("a1b2"|sub("[0-9]";"X")), ("a1b2"|gsub("[0-9]";"X"))]`, nil),
		[]any{[]any{"aXb2", "aXbX"}})
}

// Verifies: GJQ019
func TestGJQ029PathAndGetPath(t *testing.T) {
	in := map[string]any{"a": []any{4, 5}}
	assertValues(t, run(t, `[path(.a[1]), getpath(["a",0])]`, in), []any{[]any{[]any{"a", 1}, 4}})
}

// Verifies: GJQ019
func TestGJQ030SetPathAndDelPaths(t *testing.T) {
	in := map[string]any{"a": []any{1, 2, 3}, "b": 4}
	assertValues(t, run(t, `setpath(["a",1];9) | delpaths([["b"],["a",0]])`, in),
		[]any{map[string]any{"a": []any{9, 3}}})
}

// Verifies: GJQ020, GJQ042
func TestGJQ031AssignmentsDoNotMutateInput(t *testing.T) {
	in := map[string]any{"a": 2, "b": 3}
	assertValues(t, run(t, `.a = 9 | .b |= . * 10 | .a += 1`, in), []any{map[string]any{"a": 10, "b": 30}})
	if !reflect.DeepEqual(in, map[string]any{"a": 2, "b": 3}) {
		t.Fatalf("input mutated: %#v", in)
	}
}

// Verifies: GJQ020
func TestGJQ032Delete(t *testing.T) {
	assertValues(t, run(t, `del(.a, .xs[1])`, map[string]any{"a": 1, "xs": []any{4, 5, 6}}),
		[]any{map[string]any{"xs": []any{4, 6}}})
}

// Verifies: GJQ021
func TestGJQ033FunctionsArgumentsAndRecursion(t *testing.T) {
	assertValues(t, run(t, `def twice(f): f,f; def fact: if . <= 1 then 1 else . * ((.-1)|fact) end; [(3|twice(.+1)), (5|fact)]`, nil),
		[]any{[]any{4, 4, 120}})
}

// Verifies: GJQ022
func TestGJQ034ReduceAndForeach(t *testing.T) {
	assertValues(t, run(t, `reduce .[] as $x (0; . + $x)`, []any{1, 2, 3}), []any{6})
	assertValues(t, run(t, `foreach .[] as $x (0; . + $x; .)`, []any{1, 2, 3}), []any{1, 3, 6})
}

// Verifies: GJQ023, GJQ024
func TestGJQ035TryOptionalAndHalt(t *testing.T) {
	assertValues(t, run(t, `try error("bad") catch .`, nil), []any{"bad"})
	assertValues(t, run(t, `[1,0] | .[] | (10 / .)?`, nil), []any{10})
	vs := run(t, `"stop" | halt_error(7)`, nil)
	if len(vs) != 1 {
		t.Fatalf("halt values = %#v", vs)
	}
	var h *gojq.HaltError
	if !errors.As(vs[0].(error), &h) || h.Value() != "stop" || h.ExitCode() != 7 {
		t.Fatalf("halt = %#v", vs[0])
	}
}

// Keep context imported in this package so the public signature is compile-checked here.
var _ = context.Background
var _ = time.Second
