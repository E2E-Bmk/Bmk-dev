package integration_test

import (
	"context"
	"encoding/json"
	"errors"
	"math"
	"math/big"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/itchyny/gojq"
)

func parse(t *testing.T, src string) *gojq.Query {
	t.Helper()
	q, err := gojq.Parse(src)
	if err != nil {
		t.Fatalf("parse %q: %v", src, err)
	}
	return q
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

func compile(t *testing.T, src string, opts ...gojq.CompilerOption) *gojq.Code {
	t.Helper()
	c, err := gojq.Compile(parse(t, src), opts...)
	if err != nil {
		t.Fatalf("compile %q: %v", src, err)
	}
	return c
}

// Verifies: GJQ025
// Depends-On: TestGJQ001ParseIdentity, TestGJQ005CommaPipeAndEmpty
func TestGJQ036CompiledAndDirectExecutionAgree(t *testing.T) {
	q := parse(t, `.items[] | select(.active) | .name`)
	in := map[string]any{"items": []any{
		map[string]any{"name": "a", "active": true},
		map[string]any{"name": "b", "active": false},
		map[string]any{"name": "c", "active": true},
	}}
	c, err := gojq.Compile(q)
	if err != nil {
		t.Fatal(err)
	}
	assertValues(t, drain(q.Run(in), 10), drain(c.Run(in), 10))
}

// Verifies: GJQ028
// Depends-On: TestGJQ012NumericArithmetic
func TestGJQ037VariablesBindPositionally(t *testing.T) {
	c := compile(t, `$x * 100 + $y, $z`, gojq.WithVariables([]string{"$x", "$y", "$z"}))
	assertValues(t, drain(c.Run(nil, 12, 42, 128), 10), []any{1242, 128})
}

// Verifies: GJQ028
// Depends-On: TestGJQ002ParseErrorOffsetAndToken
func TestGJQ038InvalidVariableNameFailsCompile(t *testing.T) {
	q := parse(t, `.`)
	for _, name := range []string{"x", "$", "$x-y"} {
		if _, err := gojq.Compile(q, gojq.WithVariables([]string{name})); err == nil {
			t.Fatalf("invalid variable %q accepted", name)
		}
	}
}

// Verifies: GJQ028
// Depends-On: TestGJQ014InvalidArithmeticEmitsError
func TestGJQ039VariableValueCountErrors(t *testing.T) {
	c := compile(t, `$x + $y`, gojq.WithVariables([]string{"$x", "$y"}))
	for _, values := range [][]any{{1}, {1, 2, 3}} {
		vs := drain(c.Run(nil, values...), 5)
		if len(vs) != 1 {
			t.Fatalf("values = %#v", vs)
		}
		if _, ok := vs[0].(error); !ok {
			t.Fatalf("expected error, got %#v", vs[0])
		}
	}
}

// Verifies: GJQ029
// Depends-On: TestGJQ012NumericArithmetic
func TestGJQ040CustomFunctionReceivesInputAndArgs(t *testing.T) {
	c := compile(t, `combine(4;5)`, gojq.WithFunction("combine", 2, 2, func(v any, args []any) any {
		return v.(int) + args[0].(int)*10 + args[1].(int)
	}))
	assertValues(t, drain(c.Run(3), 5), []any{48})
}

// Verifies: GJQ029
// Depends-On: TestGJQ033FunctionsArgumentsAndRecursion
func TestGJQ041CustomFunctionMultipleArities(t *testing.T) {
	q := parse(t, `[f, f(4)]`)
	c, err := gojq.Compile(q,
		gojq.WithFunction("f", 0, 0, func(v any, _ []any) any { return v }),
		gojq.WithFunction("f", 1, 1, func(v any, a []any) any { return v.(int) + a[0].(int) }),
	)
	if err != nil {
		t.Fatal(err)
	}
	assertValues(t, drain(c.Run(3), 5), []any{[]any{3, 7}})
}

// Verifies: GJQ029
// Depends-On: TestGJQ004NewIterAndExhaustion
func TestGJQ042CustomFunctionArityPanicsImmediately(t *testing.T) {
	for _, bounds := range [][2]int{{-1, 0}, {2, 1}, {0, 31}} {
		func() {
			defer func() {
				if recover() == nil {
					t.Errorf("bounds %v did not panic", bounds)
				}
			}()
			_ = gojq.WithFunction("f", bounds[0], bounds[1], func(any, []any) any { return nil })
		}()
	}
}

type valuedError struct{ value any }

func (e valuedError) Error() string { return "custom failure" }
func (e valuedError) Value() any    { return e.value }

// Verifies: GJQ023, GJQ029
// Depends-On: TestGJQ035TryOptionalAndHalt
func TestGJQ043CustomValueErrorIsCatchable(t *testing.T) {
	c := compile(t, `try fail catch .`, gojq.WithFunction("fail", 0, 0, func(any, []any) any {
		return valuedError{map[string]any{"code": 9}}
	}))
	assertValues(t, drain(c.Run(nil), 5), []any{map[string]any{"code": 9}})
}

// Verifies: GJQ030
// Depends-On: TestGJQ004NewIterAndExhaustion, TestGJQ005CommaPipeAndEmpty
func TestGJQ044CustomIterFunctionStreamsValues(t *testing.T) {
	c := compile(t, `fan(3)`, gojq.WithIterFunction("fan", 1, 1, func(v any, args []any) gojq.Iter {
		n := args[0].(int)
		return gojq.NewIter[any](v, n, v.(int)+n)
	}))
	assertValues(t, drain(c.Run(5), 10), []any{5, 3, 8})
}

// Verifies: GJQ030
// Depends-On: TestGJQ004NewIterAndExhaustion
func TestGJQ045IterAndNonIterNameConflictPanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("mixed function definitions did not panic")
		}
	}()
	q := parse(t, `f`)
	_, _ = gojq.Compile(q,
		gojq.WithFunction("f", 0, 0, func(any, []any) any { return 1 }),
		gojq.WithIterFunction("f", 0, 0, func(any, []any) gojq.Iter { return gojq.NewIter(1) }),
	)
}

// Verifies: GJQ031
// Depends-On: TestGJQ014InvalidArithmeticEmitsError
func TestGJQ046InputDisabledByDefault(t *testing.T) {
	if _, err := gojq.Compile(parse(t, `input`)); err == nil {
		t.Fatal("input compiled without WithInputIter")
	}
}

// Verifies: GJQ031
// Depends-On: TestGJQ004NewIterAndExhaustion, TestGJQ006LiteralAndArrayConstruction
func TestGJQ047InputIteratorConsumption(t *testing.T) {
	c := compile(t, `[input, inputs]`, gojq.WithInputIter(gojq.NewIter(1, 2, 3)))
	assertValues(t, drain(c.Run(nil), 10), []any{[]any{1, 2, 3}})
}

// Verifies: GJQ032
// Depends-On: TestGJQ007ObjectConstructionAlternatives
func TestGJQ048EnvironmentLoaderIsolationAndDuplicates(t *testing.T) {
	assertValues(t, drain(compile(t, `[env, $ENV]`).Run(nil), 5), []any{[]any{map[string]any{}, map[string]any{}}})
	c := compile(t, `env`, gojq.WithEnvironLoader(func() []string {
		return []string{"A=1", "bad", "A=2", "=ignored", "EMPTY="}
	}))
	assertValues(t, drain(c.Run(nil), 5), []any{map[string]any{"A": "2", "EMPTY": ""}})
}

type memoryLoader struct {
	module *gojq.Query
	json   any
	err    error
}

func (l memoryLoader) LoadInitModules() ([]*gojq.Query, error) {
	if l.err != nil {
		return nil, l.err
	}
	return []*gojq.Query{l.module}, nil
}
func (l memoryLoader) LoadModuleWithMeta(string, map[string]any) (*gojq.Query, error) {
	return l.module, l.err
}
func (l memoryLoader) LoadJSONWithMeta(string, map[string]any) (any, error) {
	return l.json, l.err
}

// Verifies: GJQ033
func TestGJQ049CustomModuleAndJSONLoader(t *testing.T) {
	module := parse(t, `def inc: . + 1; def twice: . * 2;`)
	loader := memoryLoader{module: module, json: map[string]any{"n": 4}}
	c := compile(t, `import "m" as m; import "data" as $data; [inc, m::twice, $data.n]`, gojq.WithModuleLoader(loader))
	assertValues(t, drain(c.Run(3), 5), []any{[]any{4, 6, 4}})
}

// Verifies: GJQ033
func TestGJQ050ModuleLoaderErrorPropagates(t *testing.T) {
	sentinel := errors.New("loader failed")
	q := parse(t, `import "m" as m; m::f`)
	_, err := gojq.Compile(q, gojq.WithModuleLoader(memoryLoader{err: sentinel}))
	if !errors.Is(err, sentinel) {
		t.Fatalf("compile error = %v", err)
	}
}

// Verifies: GJQ034
func TestGJQ051FilesystemModuleSearchForms(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "math.jq"), []byte(`def triple: . * 3;`), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(filepath.Join(dir, "nested"), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "nested", "nested.jq"), []byte(`def plusone: . + 1;`), 0o600); err != nil {
		t.Fatal(err)
	}
	loader := gojq.NewModuleLoader([]string{"", dir})
	c := compile(t, `import "math" as m; import "nested" as n; [m::triple,n::plusone]`, gojq.WithModuleLoader(loader))
	assertValues(t, drain(c.Run(4), 5), []any{[]any{12, 5}})
}

// Verifies: GJQ034, GJQ035
func TestGJQ052FilesystemJSONImportPreservesNumbers(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "data.json"), []byte("12345678901234567890\n2.5\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	c := compile(t, `import "data" as $d; $d`, gojq.WithModuleLoader(gojq.NewModuleLoader([]string{dir})))
	vs := drain(c.Run(nil), 5)
	want := []any{[]any{json.Number("12345678901234567890"), json.Number("2.5")}}
	assertValues(t, vs, want)
}

// Verifies: GJQ036
func TestGJQ053CompareTotalOrderAndCompositeValues(t *testing.T) {
	values := []any{nil, false, true, 0, "", []any{}, map[string]any{}}
	for i := 0; i < len(values)-1; i++ {
		if gojq.Compare(values[i], values[i+1]) != -1 || gojq.Compare(values[i+1], values[i]) != 1 {
			t.Fatalf("bad order at %d", i)
		}
	}
	if gojq.Compare(map[string]any{"b": 2, "a": 1}, map[string]any{"a": 1, "b": 2}) != 0 {
		t.Fatal("equal maps differ")
	}
}

// Verifies: GJQ036, GJQ037
func TestGJQ054CompareNumericRepresentationsNaNAndZero(t *testing.T) {
	bi := new(big.Int)
	bi.SetString("42", 10)
	for _, v := range []any{42, 42.0, bi, json.Number("42")} {
		if gojq.Compare(42, v) != 0 {
			t.Fatalf("42 != %#v", v)
		}
	}
	if gojq.Compare(math.NaN(), math.NaN()) != -1 || gojq.Compare(math.NaN(), -100.0) != -1 {
		t.Fatal("NaN ordering mismatch")
	}
	if gojq.Compare(math.Copysign(0, -1), 0.0) != 0 {
		t.Fatal("signed zero differs")
	}
}

// Verifies: GJQ038
func TestGJQ055MarshalSpecialFloatsAndEscaping(t *testing.T) {
	got, err := gojq.Marshal([]any{math.NaN(), math.Inf(1), math.Inf(-1), "\b\f<>&\u2028\u2029"})
	if err != nil {
		t.Fatal(err)
	}
	s := string(got)
	if !strings.HasPrefix(s, `[null,1.7976931348623157e+308,-1.7976931348623157e+308,`) ||
		!strings.Contains(s, `\b\f<>&`) || strings.Contains(s, `\u003c`) || strings.Contains(s, `\u2028`) {
		t.Fatalf("marshal = %s", s)
	}
}

// Verifies: GJQ038, GJQ039
func TestGJQ056MarshalSortsKeysAndPreservesNumbers(t *testing.T) {
	bi := new(big.Int)
	bi.SetString("123456789012345678901234567890", 10)
	got, err := gojq.Marshal(map[string]any{"z": json.Number("1.2300"), "a": bi})
	if err != nil || string(got) != `{"a":123456789012345678901234567890,"z":1.2300}` {
		t.Fatalf("marshal = %s, %v", got, err)
	}
}

// Verifies: GJQ040
func TestGJQ057TypeOfSupportedAndUnsupported(t *testing.T) {
	cases := []struct {
		v    any
		want string
	}{
		{nil, "null"}, {true, "boolean"}, {1, "number"}, {1.5, "number"},
		{json.Number("2"), "number"}, {big.NewInt(3), "number"}, {"x", "string"},
		{[]any{}, "array"}, {map[string]any{}, "object"},
	}
	for _, tc := range cases {
		if got := gojq.TypeOf(tc.v); got != tc.want {
			t.Fatalf("TypeOf(%#v) = %q", tc.v, got)
		}
	}
	defer func() {
		if recover() == nil {
			t.Fatal("unsupported value did not panic")
		}
	}()
	_ = gojq.TypeOf([]int{1})
}

// Verifies: GJQ041
func TestGJQ058PreviewPrimitiveAndUTF8Truncation(t *testing.T) {
	if got := gojq.Preview(map[string]any{"a": 1}); got != `{"a":1}` {
		t.Fatalf("preview = %q", got)
	}
	got := gojq.Preview("世界世界世界世界世界世界世界世界")
	if !strings.Contains(got, "...") || !strings.HasSuffix(got, ` ..."`) || strings.ToValidUTF8(got, "?") != got {
		t.Fatalf("truncated preview = %q", got)
	}
}

// Verifies: GJQ026
func TestGJQ059RunWithContextCancellation(t *testing.T) {
	c := compile(t, `repeat(0)`)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	done := make(chan any, 1)
	go func() {
		v, _ := c.RunWithContext(ctx, nil).Next()
		done <- v
	}()
	select {
	case v := <-done:
		if err, ok := v.(error); !ok || !errors.Is(err, context.Canceled) {
			t.Fatalf("cancellation value = %#v", v)
		}
	case <-time.After(time.Second):
		t.Fatal("cancellation did not stop execution")
	}
	if vs := drain(c.Run(nil), 3); !reflect.DeepEqual(vs, []any{0, 0, 0}) {
		t.Fatalf("reuse after cancel = %#v", vs)
	}
}

// Verifies: GJQ027, GJQ042
func TestGJQ060ConcurrentReuseAndIsolation(t *testing.T) {
	c := compile(t, `.value | [., . * 2]`)
	const n = 24
	var wg sync.WaitGroup
	errs := make(chan any, n)
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			got := drain(c.Run(map[string]any{"value": i}), 5)
			want := []any{[]any{i, i * 2}}
			if !reflect.DeepEqual(got, want) {
				errs <- got
			}
		}(i)
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Fatalf("concurrent result = %#v", err)
	}
}
