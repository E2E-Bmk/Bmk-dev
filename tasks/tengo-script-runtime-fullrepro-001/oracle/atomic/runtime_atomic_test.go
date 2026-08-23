package atomic_test

import (
	"context"
	"errors"
	"reflect"
	"testing"
	"time"

	tengo "github.com/d5/tengo/v2"
)

func eval(t *testing.T, expr string, params map[string]interface{}) interface{} {
	t.Helper()
	v, err := tengo.Eval(context.Background(), expr, params)
	if err != nil {
		t.Fatalf("Eval: %v", err)
	}
	return v
}

func want(t *testing.T, got, expected interface{}) {
	t.Helper()
	if !reflect.DeepEqual(got, expected) {
		t.Fatalf("got %#v (%T), want %#v (%T)", got, got, expected, expected)
	}
}

func TestTGO001IntegerArithmetic(t *testing.T) { want(t, eval(t, "1 + 2 * 3", nil), int64(7)) }
func TestTGO002DivisionRemainder(t *testing.T) { want(t, eval(t, "17 / 5 + 17 % 5", nil), int64(5)) }
func TestTGO003FloatArithmetic(t *testing.T)   { want(t, eval(t, "1.5 * 2 + 0.5", nil), 3.5) }
func TestTGO004StringConcat(t *testing.T)      { want(t, eval(t, `"go" + "pher"`, nil), "gopher") }
func TestTGO005Comparison(t *testing.T)        { want(t, eval(t, "3 < 4 && 4 >= 4 && 3 != 4", nil), true) }
func TestTGO006ShortCircuit(t *testing.T)      { want(t, eval(t, "false && (1 / 0 == 0)", nil), false) }
func TestTGO007Conditional(t *testing.T)       { want(t, eval(t, "true ? 11 : 22", nil), int64(11)) }
func TestTGO008ArrayIndex(t *testing.T)        { want(t, eval(t, "[3, 5, 8][1]", nil), int64(5)) }
func TestTGO009MapSelector(t *testing.T)       { want(t, eval(t, `{a: 4, b: 9}.b`, nil), int64(9)) }
func TestTGO010StringByteLength(t *testing.T)  { want(t, eval(t, `len("你好a")`, nil), int64(7)) }
func TestTGO011MissingMapValue(t *testing.T)   { want(t, eval(t, `{a: 1}.missing`, nil), nil) }
func TestTGO012Range(t *testing.T) {
	want(t, eval(t, "range(2, 8, 2)", nil), []interface{}{int64(2), int64(4), int64(6)})
}
func TestTGO013Append(t *testing.T) {
	want(t, eval(t, "append([1, 2], 3, 4)", nil), []interface{}{int64(1), int64(2), int64(3), int64(4)})
}
func TestTGO014Splice(t *testing.T) {
	want(t, eval(t, `splice([1, 2, 3], 1, 1, 8, 9)`, nil), []interface{}{int64(2)})
}
func TestTGO015FunctionCall(t *testing.T) {
	want(t, eval(t, `(func(a, b) { return a * b })(6, 7)`, nil), int64(42))
}
func TestTGO016FromInterfaceNested(t *testing.T) {
	o, err := tengo.FromInterface(map[string]interface{}{"a": []interface{}{int64(1), "x"}})
	if err != nil {
		t.Fatal(err)
	}
	want(t, tengo.ToInterface(o), map[string]interface{}{"a": []interface{}{int64(1), "x"}})
}
func TestTGO017FromInterfaceOverflow(t *testing.T) {
	if _, err := tengo.FromInterface(^uint64(0)); err == nil {
		t.Fatal("expected overflow error")
	}
}
func TestTGO018ScalarConversions(t *testing.T) {
	i := &tengo.Int{Value: 12}
	if v, ok := tengo.ToInt64(i); !ok || v != 12 {
		t.Fatalf("int64: %v %v", v, ok)
	}
	if v, ok := tengo.ToFloat64(i); !ok || v != 12 {
		t.Fatalf("float: %v %v", v, ok)
	}
}
func TestTGO019BytesRetainInputView(t *testing.T) {
	src := []byte("abc")
	o, err := tengo.FromInterface(src)
	if err != nil {
		t.Fatal(err)
	}
	src[0] = 'z'
	want(t, tengo.ToInterface(o), []byte("zbc"))
}
func TestTGO020TimeRoundTrip(t *testing.T) {
	tm := time.Unix(123, 456).UTC()
	o, err := tengo.FromInterface(tm)
	if err != nil {
		t.Fatal(err)
	}
	got, ok := tengo.ToTime(o)
	if !ok || !got.Equal(tm) {
		t.Fatalf("got %v %v", got, ok)
	}
}
func TestTGO021CountObjects(t *testing.T) {
	o, _ := tengo.FromInterface([]interface{}{int64(1), map[string]interface{}{"x": true}})
	if got := tengo.CountObjects(o); got != 4 {
		t.Fatalf("got %d", got)
	}
}
func TestTGO022VariableAccessors(t *testing.T) {
	v, err := tengo.NewVariable("n", int64(42))
	if err != nil {
		t.Fatal(err)
	}
	if v.Name() != "n" || v.Int64() != 42 || v.ValueType() != "int" || v.IsUndefined() {
		t.Fatalf("bad variable: %#v", v)
	}
}
func TestTGO023ScriptAddRemove(t *testing.T) {
	s := tengo.NewScript([]byte("out := x + 1"))
	if err := s.Add("x", 4); err != nil {
		t.Fatal(err)
	}
	if !s.Remove("x") || s.Remove("x") {
		t.Fatal("remove semantics")
	}
}
func TestTGO024CompileSyntaxError(t *testing.T) {
	if _, err := tengo.NewScript([]byte("x := ")).Compile(); err == nil {
		t.Fatal("expected syntax error")
	}
}
func TestTGO025EvalEmptyError(t *testing.T) {
	if _, err := tengo.Eval(context.Background(), "", nil); err == nil {
		t.Fatal("expected error")
	}
}
func TestTGO026CallableError(t *testing.T) {
	boom := errors.New("boom")
	s := tengo.NewScript([]byte("out := fail()"))
	err := s.Add("fail", &tengo.UserFunction{Name: "fail", Value: func(...tengo.Object) (tengo.Object, error) { return nil, boom }})
	if err != nil {
		t.Fatal(err)
	}
	if _, err = s.Run(); !errors.Is(err, boom) {
		t.Fatalf("got %v", err)
	}
}
func TestTGO027ModuleMapLifecycle(t *testing.T) {
	m := tengo.NewModuleMap()
	m.AddSourceModule("a", []byte("export 1"))
	if m.Len() != 1 || m.Get("a") == nil || m.GetSourceModule("a") == nil {
		t.Fatal("missing module")
	}
	c := m.Copy()
	m.Remove("a")
	if m.Len() != 0 || c.Len() != 1 {
		t.Fatal("copy membership aliased")
	}
}
func TestTGO028MaxConstants(t *testing.T) {
	s := tengo.NewScript([]byte("x := [1, 2, 3, 4]"))
	s.SetMaxConstObjects(1)
	if _, err := s.Compile(); err == nil {
		t.Fatal("expected constant limit error")
	}
}
func TestTGO029PreCanceledContext(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := tengo.NewScript([]byte("for {}")).RunContext(ctx); err == nil {
		t.Fatal("expected cancellation")
	}
}
func TestTGO030ObjectTruthAndType(t *testing.T) {
	if !(&tengo.Int{Value: 0}).IsFalsy() || (&tengo.String{Value: "x"}).TypeName() != "string" {
		t.Fatal("object semantics")
	}
}

func TestTGO051BitwiseOperators(t *testing.T) {
	want(t, eval(t, "((5 & 3) | 8) ^ 1", nil), int64(8))
}

func TestTGO052ArraySlice(t *testing.T) {
	want(t, eval(t, "[1, 2, 3, 4][1:3]", nil), []interface{}{int64(2), int64(3)})
}

func TestTGO053CharConversion(t *testing.T) {
	v, ok := tengo.ToRune(&tengo.Char{Value: '界'})
	if !ok || v != '界' {
		t.Fatalf("got %q %v", v, ok)
	}
}

func TestTGO054UnsupportedGoValue(t *testing.T) {
	if _, err := tengo.FromInterface(make(chan int)); err == nil {
		t.Fatal("expected unsupported-value error")
	}
}

func TestTGO055ModuleMapMerge(t *testing.T) {
	a := tengo.NewModuleMap()
	b := tengo.NewModuleMap()
	a.AddSourceModule("a", []byte("export 1"))
	b.AddSourceModule("b", []byte("export 2"))
	a.AddMap(b)
	if a.Len() != 2 || a.Get("a") == nil || a.Get("b") == nil {
		t.Fatal("module map merge failed")
	}
}
