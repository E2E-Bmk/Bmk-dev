package integration

import (
	"context"
	"errors"
	"reflect"
	"sort"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/expr-lang/expr"
	"github.com/expr-lang/expr/ast"
	"github.com/expr-lang/expr/file"
)

func compileRun(t *testing.T, source string, env any, options ...expr.Option) any {
	t.Helper()
	p, err := expr.Compile(source, options...)
	if err != nil {
		t.Fatalf("Compile(%q): %v", source, err)
	}
	out, err := expr.Run(p, env)
	if err != nil {
		t.Fatalf("Run(%q): %v", source, err)
	}
	return out
}

func same(t *testing.T, got, want any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %#v (%T), want %#v (%T)", got, got, want, want)
	}
}

func sequence(t *testing.T, got any) []any {
	t.Helper()
	v := reflect.ValueOf(got)
	if v.Kind() != reflect.Array && v.Kind() != reflect.Slice {
		t.Fatalf("got %T, want sequence", got)
	}
	out := make([]any, v.Len())
	for i := range out {
		out[i] = v.Index(i).Interface()
	}
	return out
}

// Verifies: EXPR-070
// Depends-On: atomic::TestMapEnvironment
func TestCompileOnceRunMany(t *testing.T) {
	p, err := expr.Compile(`x*10+y`, expr.Env(map[string]any{"x": 0, "y": 0}))
	if err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		env  map[string]any
		want int
	}{{map[string]any{"x": 2, "y": 1}, 21}, {map[string]any{"x": 7, "y": 3}, 73}} {
		out, err := expr.Run(p, tc.env)
		if err != nil {
			t.Fatal(err)
		}
		same(t, out, tc.want)
	}
}

// Verifies: EXPR-069
// Depends-On: atomic::TestArithmeticPrecedence, atomic::TestMapEnvironment
func TestEvalCompileRunAgreement(t *testing.T) {
	env := map[string]any{"a": 6, "b": 7}
	direct, err := expr.Eval(`a*b+1`, env)
	if err != nil {
		t.Fatal(err)
	}
	compiled := compileRun(t, `a*b+1`, env, expr.Env(env))
	same(t, direct, compiled)
}

// Verifies: EXPR-049
// Depends-On: atomic::TestArithmeticPrecedence
func TestOptimizationParity(t *testing.T) {
	source := `map([1,2,3,4], {#*2})[2] + (3*4)`
	a := compileRun(t, source, nil)
	b := compileRun(t, source, nil, expr.Optimize(false))
	same(t, a, b)
}

// Verifies: EXPR-072
// Depends-On: atomic::TestMapEnvironment
func TestConcurrentProgramRuns(t *testing.T) {
	p, err := expr.Compile(`x*x`, expr.Env(map[string]any{"x": 0}))
	if err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	errs := make(chan error, 20)
	for i := 0; i < 20; i++ {
		i := i
		wg.Add(1)
		go func() {
			defer wg.Done()
			out, err := expr.Run(p, map[string]any{"x": i})
			if err != nil {
				errs <- err
				return
			}
			if out != i*i {
				errs <- errors.New("cross-run state")
			}
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Fatal(err)
	}
}

// Verifies: EXPR-006
// Depends-On: atomic::TestUnaryAndComparisons
func TestDefaultShortCircuit(t *testing.T) {
	var calls int
	env := map[string]any{"foo": func() bool { calls++; return true }, "bar": func() bool { calls++; return true }}
	same(t, compileRun(t, `foo() or bar()`, env, expr.Env(env)), true)
	if calls != 1 {
		t.Fatalf("calls=%d", calls)
	}
}

// Verifies: EXPR-050
// Depends-On: atomic::TestUnaryAndComparisons
func TestDisabledShortCircuit(t *testing.T) {
	var calls int
	env := map[string]any{"foo": func() bool { calls++; return true }, "bar": func() bool { calls++; return true }}
	same(t, compileRun(t, `foo() or bar()`, env, expr.Env(env), expr.DisableShortCircuit()), true)
	if calls != 2 {
		t.Fatalf("calls=%d", calls)
	}
}

// Verifies: EXPR-052
// Depends-On: atomic::TestConversions
func TestRegisteredFunction(t *testing.T) {
	upperLen := expr.Function("upperLen", func(params ...any) (any, error) { return len(params[0].(string)), nil }, new(func(string) int))
	same(t, compileRun(t, `upperLen("gopher") + 1`, nil, upperLen), 7)
}

// Verifies: EXPR-052
func TestRegisteredFunctionTypeCheck(t *testing.T) {
	fn := expr.Function("twice", func(params ...any) (any, error) { return params[0].(int) * 2, nil }, new(func(int) int))
	if p, err := expr.Compile(`twice("bad")`, fn); err == nil || p != nil {
		t.Fatal("typed function call must fail")
	}
}

// Verifies: EXPR-053, EXPR-067
func TestFunctionErrorThenSuccessfulRun(t *testing.T) {
	fn := expr.Function("checked", func(params ...any) (any, error) {
		n := params[0].(int)
		if n < 0 {
			return nil, errors.New("negative")
		}
		return n * 2, nil
	}, new(func(int) int))
	p, err := expr.Compile(`checked(x)`, expr.Env(map[string]any{"x": 0}), fn)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = expr.Run(p, map[string]any{"x": -1}); err == nil {
		t.Fatal("want runtime error")
	}
	out, err := expr.Run(p, map[string]any{"x": 4})
	if err != nil {
		t.Fatal(err)
	}
	same(t, out, 8)
}

type decimal struct{ N int }

// Verifies: EXPR-054
// Depends-On: atomic::TestArithmeticPrecedence
func TestOperatorOverloadComposes(t *testing.T) {
	env := map[string]any{"a": decimal{2}, "b": decimal{3}, "add": func(x, y decimal) decimal { return decimal{x.N + y.N} }}
	out := compileRun(t, `a + b`, env, expr.Env(env), expr.Operator("+", "add"))
	same(t, out, decimal{5})
}

// Verifies: EXPR-055
func TestConstExpressionRunsAtCompileTime(t *testing.T) {
	var calls int
	env := map[string]any{"twice": func(x int) int { calls++; return x * 2 }}
	p, err := expr.Compile(`twice(21)`, expr.Env(env), expr.ConstExpr("twice"))
	if err != nil {
		t.Fatal(err)
	}
	if calls != 1 {
		t.Fatalf("compile calls=%d", calls)
	}
	for i := 0; i < 2; i++ {
		out, err := expr.Run(p, env)
		if err != nil {
			t.Fatal(err)
		}
		same(t, out, 42)
	}
	if calls != 1 {
		t.Fatalf("runtime calls=%d", calls)
	}
}

// Verifies: EXPR-055
// Depends-On: atomic::TestMapEnvironment
func TestConstExpressionLeavesVariableCallsRuntime(t *testing.T) {
	var calls int
	shape := map[string]any{"x": 0, "twice": func(x int) int { calls++; return x * 2 }}
	p, err := expr.Compile(`twice(x)`, expr.Env(shape), expr.ConstExpr("twice"))
	if err != nil {
		t.Fatal(err)
	}
	if calls != 0 {
		t.Fatal("variable call folded")
	}
	out, err := expr.Run(p, map[string]any{"x": 5, "twice": shape["twice"]})
	if err != nil {
		t.Fatal(err)
	}
	same(t, out, 10)
	if calls != 1 {
		t.Fatalf("calls=%d", calls)
	}
}

type ctxKey struct{}

// Verifies: EXPR-057
func TestContextInjection(t *testing.T) {
	ctx := context.WithValue(context.Background(), ctxKey{}, "ok")
	env := map[string]any{"ctx": ctx, "read": func(c context.Context, n int) string { return c.Value(ctxKey{}).(string) + string(rune('0'+n)) }}
	same(t, compileRun(t, `read(7)`, env, expr.Env(env), expr.WithContext("ctx")), "ok7")
}

// Verifies: EXPR-058
func TestTimezoneAffectsDate(t *testing.T) {
	out := compileRun(t, `date("2024-01-02 03:04:05")`, nil, expr.Timezone("UTC")).(time.Time)
	same(t, out.Location().String(), "UTC")
}

// Verifies: EXPR-064
func TestProgramSourceProjection(t *testing.T) {
	source := `let x = 4; x + 2`
	p, err := expr.Compile(source, expr.Optimize(false))
	if err != nil {
		t.Fatal(err)
	}
	if p.Source().String() != source {
		t.Fatalf("source=%q", p.Source().String())
	}
}

type recorder struct{ kinds []string }

func (v *recorder) Visit(node *ast.Node) { v.kinds = append(v.kinds, reflect.TypeOf(*node).String()) }

// Verifies: EXPR-059
func TestASTWalkPostOrder(t *testing.T) {
	root := ast.Node(&ast.BinaryNode{Operator: "+", Left: &ast.IntegerNode{Value: 1}, Right: &ast.IntegerNode{Value: 2}})
	v := &recorder{}
	ast.Walk(&root, v)
	same(t, v.kinds, []string{"*ast.IntegerNode", "*ast.IntegerNode", "*ast.BinaryNode"})
}

// Verifies: EXPR-059
func TestASTWalkNil(t *testing.T) {
	var root ast.Node
	v := &recorder{}
	ast.Walk(&root, v)
	if len(v.kinds) != 0 {
		t.Fatal(v.kinds)
	}
}

// Verifies: EXPR-060
func TestASTFind(t *testing.T) {
	root := ast.Node(&ast.BinaryNode{Operator: "+", Left: &ast.IdentifierNode{Value: "x"}, Right: &ast.IntegerNode{Value: 2}})
	found := ast.Find(root, func(n ast.Node) bool { id, ok := n.(*ast.IdentifierNode); return ok && id.Value == "x" })
	if found == nil {
		t.Fatal("not found")
	}
	if ast.Find(root, func(n ast.Node) bool { return false }) != nil {
		t.Fatal("unexpected match")
	}
}

// Verifies: EXPR-061
func TestASTPatchReplacesNode(t *testing.T) {
	root := ast.Node(&ast.IntegerNode{Value: 1})
	root.SetLocation(file.Location{From: 3, To: 4})
	ast.Patch(&root, &ast.IntegerNode{Value: 9})
	if root.(*ast.IntegerNode).Value != 9 {
		t.Fatalf("%#v", root)
	}
}

type replaceFoo struct{}

func (replaceFoo) Visit(node *ast.Node) {
	if n, ok := (*node).(*ast.IdentifierNode); ok && n.Value == "foo" {
		ast.Patch(node, &ast.IntegerNode{Value: 41})
	}
}

// Verifies: EXPR-062
// Depends-On: atomic::TestMapEnvironment
func TestCompilePatchChangesResult(t *testing.T) {
	same(t, compileRun(t, `foo + 1`, nil, expr.Patch(replaceFoo{})), 42)
}

// Verifies: EXPR-062, EXPR-074
func TestCompilePatchChangesNodeNotSource(t *testing.T) {
	p, err := expr.Compile(`foo + 1`, expr.Patch(replaceFoo{}), expr.Optimize(false))
	if err != nil {
		t.Fatal(err)
	}
	if p.Source().String() != `foo + 1` {
		t.Fatal(p.Source().String())
	}
	if ast.Find(p.Node(), func(n ast.Node) bool { id, ok := n.(*ast.IdentifierNode); return ok && id.Value == "foo" }) != nil {
		t.Fatal("unpatched node")
	}
}

// Verifies: EXPR-063
func TestNodeTypeRoundTrip(t *testing.T) {
	n := ast.Node(&ast.IntegerNode{Value: 1})
	typ := reflect.TypeOf(int64(0))
	n.SetType(typ)
	if n.Type() != typ {
		t.Fatalf("type=%v", n.Type())
	}
}

// Verifies: EXPR-067
// Depends-On: atomic::TestMapEnvironment
func TestRuntimeFailureDoesNotPoisonProgram(t *testing.T) {
	shape := map[string]any{"items": []int{}}
	p, err := expr.Compile(`items[0]`, expr.Env(shape))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = expr.Run(p, map[string]any{"items": []int{}}); err == nil {
		t.Fatal("want bounds error")
	}
	out, err := expr.Run(p, map[string]any{"items": []int{9}})
	if err != nil {
		t.Fatal(err)
	}
	same(t, out, 9)
}

// Verifies: EXPR-045, EXPR-071
// Depends-On: atomic::TestReturnKindOptions
func TestAllNumericReturnKinds(t *testing.T) {
	cases := []struct {
		option expr.Option
		typ    reflect.Type
	}{{expr.AsInt(), reflect.TypeOf(int(0))}, {expr.AsInt64(), reflect.TypeOf(int64(0))}, {expr.AsFloat64(), reflect.TypeOf(float64(0))}}
	for _, tc := range cases {
		out := compileRun(t, `7`, nil, tc.option)
		if reflect.TypeOf(out) != tc.typ {
			t.Fatalf("got %T want %v", out, tc.typ)
		}
	}
}

// Verifies: EXPR-047
func TestWarnOnAnyRejectsAny(t *testing.T) {
	env := map[string]any{"items": []any{1}}
	if p, err := expr.Compile(`items[0]`, expr.Env(env), expr.AsInt(), expr.WarnOnAny()); err == nil || p != nil {
		t.Fatal("any result accepted")
	}
}

// Verifies: EXPR-048
func TestWarnOnAnyMisusePanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("want panic")
		}
	}()
	_, _ = expr.Compile(`1`, expr.WarnOnAny())
}

// Verifies: EXPR-073
func TestInvalidFunctionDescriptorPanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("want panic")
		}
	}()
	_, _ = expr.Compile(`bad()`, expr.Function("bad", func(params ...any) (any, error) { return nil, nil }, 123))
}

// Verifies: EXPR-058
func TestUnknownTimezonePanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("want panic")
		}
	}()
	_ = expr.Timezone("No/Such_Zone_Expr_Task")
}

// Verifies: EXPR-019
// Depends-On: atomic::TestMapEnvironment
func TestWholeEnvironmentProjection(t *testing.T) {
	env := map[string]any{"a": 2, "b": 5}
	same(t, compileRun(t, `$env.a + $env.b`, env, expr.Env(env)), 7)
}

type embeddedHelper struct{}

func (embeddedHelper) Triple(v int) int { return v * 3 }

type embeddedEnv struct {
	embeddedHelper
	X int
}

// Verifies: EXPR-014
// Depends-On: atomic::TestStructMethod
func TestEmbeddedMethodWorkflow(t *testing.T) {
	p, err := expr.Compile(`Triple(X)`, expr.Env(embeddedEnv{}))
	if err != nil {
		t.Fatal(err)
	}
	out, err := expr.Run(p, embeddedEnv{X: 4})
	if err != nil {
		t.Fatal(err)
	}
	same(t, out, 12)
}

// Verifies: EXPR-017
// Depends-On: atomic::TestDynamicMapMissingMember
func TestStaticUnknownFieldRejected(t *testing.T) {
	if p, err := expr.Compile(`missing`, expr.Env(struct{ Present int }{})); err == nil || p != nil {
		t.Fatal("unknown static field")
	}
}

// Verifies: EXPR-023, EXPR-024, EXPR-029
// Depends-On: atomic::TestFilterAndMap, atomic::TestJoinAndReduce
func TestCollectionPipeline(t *testing.T) {
	source := `join(sort(map(filter(users, {.Active}), {upper(.Name)})), ",")`
	env := map[string]any{"users": []map[string]any{{"Name": "zoe", "Active": true}, {"Name": "amy", "Active": false}, {"Name": "bob", "Active": true}}}
	same(t, compileRun(t, source, env, expr.Env(env)), "BOB,ZOE")
}

// Verifies: EXPR-065
// Depends-On: atomic::TestArithmeticPrecedence
func TestProgramNodeMatchesExecution(t *testing.T) {
	p, err := expr.Compile(`1 + 2`, expr.Optimize(false))
	if err != nil {
		t.Fatal(err)
	}
	bin, ok := p.Node().(*ast.BinaryNode)
	if !ok || bin.Operator != "+" {
		t.Fatalf("node=%T %#v", p.Node(), p.Node())
	}
	out, err := expr.Run(p, nil)
	if err != nil {
		t.Fatal(err)
	}
	same(t, out, 3)
}

// Verifies: EXPR-046
func TestAsAnyAllowsDifferentResults(t *testing.T) {
	for _, source := range []string{`42`, `"x"`, `[1,2]`} {
		if _, err := expr.Compile(source, expr.AsAny()); err != nil {
			t.Fatalf("%s: %v", source, err)
		}
	}
}

// Verifies: EXPR-020
// Depends-On: atomic::TestMapEnvironment
func TestTypedEnvironmentFunctionWorkflow(t *testing.T) {
	env := map[string]any{"format": func(prefix string, n int) string { return prefix + string(rune('0'+n)) }, "n": 6}
	same(t, compileRun(t, `format("v", n)`, env, expr.Env(env)), "v6")
}

// Verifies: EXPR-072
// Depends-On: atomic::TestReturnKindOptions
func TestConcurrentRunsKeepConcreteType(t *testing.T) {
	p, err := expr.Compile(`x+1`, expr.Env(map[string]any{"x": 0}), expr.AsInt64())
	if err != nil {
		t.Fatal(err)
	}
	var bad atomic.Int32
	var wg sync.WaitGroup
	for i := 0; i < 12; i++ {
		i := i
		wg.Add(1)
		go func() {
			defer wg.Done()
			out, err := expr.Run(p, map[string]any{"x": i})
			if err != nil || reflect.TypeOf(out).Kind() != reflect.Int64 || out.(int64) != int64(i+1) {
				bad.Add(1)
			}
		}()
	}
	wg.Wait()
	if bad.Load() != 0 {
		t.Fatalf("bad runs=%d", bad.Load())
	}
}

// Verifies: EXPR-034
// Depends-On: atomic::TestMapKeysAndValues
func TestMapProjectionInvariant(t *testing.T) {
	out := sequence(t, compileRun(t, `[sort(keys(data)), sort(values(data))]`, map[string]any{"data": map[string]int{"b": 2, "a": 1}}, expr.Env(map[string]any{"data": map[string]int{}})))
	keysAny := sequence(t, out[0])
	valsAny := sequence(t, out[1])
	keys := []string{keysAny[0].(string), keysAny[1].(string)}
	vals := []int{valsAny[0].(int), valsAny[1].(int)}
	sort.Strings(keys)
	sort.Ints(vals)
	same(t, keys, []string{"a", "b"})
	same(t, vals, []int{1, 2})
}

// Verifies: EXPR-058
func TestTimezoneProducesExpectedInstant(t *testing.T) {
	out := compileRun(t, `date("2024-01-02 03:04:05")`, nil, expr.Timezone("UTC")).(time.Time)
	want := time.Date(2024, 1, 2, 3, 4, 5, 0, time.UTC)
	if !out.Equal(want) {
		t.Fatalf("got %v want %v", out, want)
	}
}
