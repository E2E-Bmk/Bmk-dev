package integration_test

import (
	"context"
	"errors"
	"reflect"
	"sync"
	"testing"
	"time"

	tengo "github.com/d5/tengo/v2"
)

func run(t *testing.T, src string, vars map[string]interface{}) *tengo.Compiled {
	t.Helper()
	s := tengo.NewScript([]byte(src))
	for k, v := range vars {
		if err := s.Add(k, v); err != nil {
			t.Fatal(err)
		}
	}
	c, err := s.Run()
	if err != nil {
		t.Fatalf("run: %v", err)
	}
	return c
}

// Depends-On: TestTGO001IntegerArithmetic, TestTGO022VariableAccessors
func TestTGO031EvalScriptParity(t *testing.T) {
	v, err := tengo.Eval(context.Background(), "x * 2 + 1", map[string]interface{}{"x": 9})
	if err != nil {
		t.Fatal(err)
	}
	c := run(t, "out := x * 2 + 1", map[string]interface{}{"x": 9})
	if !reflect.DeepEqual(v, c.Get("out").Value()) {
		t.Fatalf("%#v != %#v", v, c.Get("out").Value())
	}
}

// Depends-On: TestTGO023ScriptAddRemove
func TestTGO032CompileSetRerun(t *testing.T) {
	s := tengo.NewScript([]byte("out := input * 3"))
	_ = s.Add("input", 2)
	c, err := s.Compile()
	if err != nil {
		t.Fatal(err)
	}
	if err = c.Run(); err != nil {
		t.Fatal(err)
	}
	if c.Get("out").Int() != 6 {
		t.Fatal(c.Get("out").Value())
	}
	if err = c.Set("input", 7); err != nil {
		t.Fatal(err)
	}
	if err = c.Run(); err != nil || c.Get("out").Int() != 21 {
		t.Fatalf("%v %#v", err, c.Get("out").Value())
	}
}

// Depends-On: TestTGO022VariableAccessors
func TestTGO033GetViewsAgree(t *testing.T) {
	c := run(t, "a := 1; b := a + 1", nil)
	if !c.IsDefined("a") || c.IsDefined("missing") || !c.Get("missing").IsUndefined() {
		t.Fatal("definition mismatch")
	}
	seen := map[string]interface{}{}
	for _, v := range c.GetAll() {
		seen[v.Name()] = v.Value()
	}
	if !reflect.DeepEqual(seen["a"], c.Get("a").Value()) || !reflect.DeepEqual(seen["b"], c.Get("b").Value()) {
		t.Fatal(seen)
	}
}

// Depends-On: TestTGO023ScriptAddRemove
func TestTGO034CloneScalarIsolation(t *testing.T) {
	s := tengo.NewScript([]byte("out := input + 1"))
	_ = s.Add("input", 1)
	orig, err := s.Compile()
	if err != nil {
		t.Fatal(err)
	}
	clone := orig.Clone()
	_ = clone.Set("input", 10)
	_ = orig.Run()
	_ = clone.Run()
	if orig.Get("out").Int() != 2 || clone.Get("out").Int() != 11 {
		t.Fatal("clone not isolated")
	}
}

// Depends-On: TestTGO016FromInterfaceNested
func TestTGO035CloneCollectionIsolation(t *testing.T) {
	s := tengo.NewScript([]byte("input[0].x += 1; out := input[0].x"))
	_ = s.Add("input", []interface{}{map[string]interface{}{"x": int64(1)}})
	orig, err := s.Compile()
	if err != nil {
		t.Fatal(err)
	}
	clone := orig.Clone()
	if err = clone.Run(); err != nil {
		t.Fatal(err)
	}
	if orig.Get("input").Array()[0].(map[string]interface{})["x"] != int64(1) {
		t.Fatalf("original changed: %#v", orig.Get("input").Value())
	}
}

// Depends-On: TestTGO015FunctionCall
func TestTGO036ClosureState(t *testing.T) {
	c := run(t, `make := func() { n := 0; return func() { n++; return n } }; f := make(); a := f(); b := f()`, nil)
	if c.Get("a").Int() != 1 || c.Get("b").Int() != 2 {
		t.Fatal("closure state")
	}
}

// Depends-On: TestTGO015FunctionCall
func TestTGO037Recursion(t *testing.T) {
	c := run(t, `fib := func(x) { if x < 2 { return x }; return fib(x-1) + fib(x-2) }; out := fib(10)`, nil)
	if c.Get("out").Int() != 55 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO001IntegerArithmetic
func TestTGO038LoopBreakContinue(t *testing.T) {
	c := run(t, `sum := 0; for i := 0; i < 10; i++ { if i == 3 { continue }; if i == 7 { break }; sum += i }`, nil)
	if c.Get("sum").Int() != 18 {
		t.Fatal(c.Get("sum").Value())
	}
}

// Depends-On: TestTGO008ArrayIndex, TestTGO009MapSelector
func TestTGO039CollectionMutation(t *testing.T) {
	c := run(t, `a := [1,2,3]; for i, v in a { a[i] = v * 2 }; m := {x: 1, y: 2}; delete(m, "x"); out := a[2] + m.y`, nil)
	if c.Get("out").Int() != 8 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO013Append, TestTGO015FunctionCall
func TestTGO040VariadicSpread(t *testing.T) {
	c := run(t, `f := func(a, ...rest) { return a + len(rest) }; xs := [10,20,30]; out := f(xs...)`, nil)
	if c.Get("out").Int() != 12 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO027ModuleMapLifecycle
func TestTGO041BuiltinModule(t *testing.T) {
	m := tengo.NewModuleMap()
	m.AddBuiltinModule("mathx", map[string]tengo.Object{"answer": &tengo.Int{Value: 42}})
	s := tengo.NewScript([]byte(`mod := import("mathx"); out := mod.answer`))
	s.SetImports(m)
	c, err := s.Run()
	if err != nil {
		t.Fatal(err)
	}
	if c.Get("out").Int() != 42 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO027ModuleMapLifecycle
func TestTGO042SourceModule(t *testing.T) {
	m := tengo.NewModuleMap()
	m.AddSourceModule("double", []byte(`export func(x) { return x * 2 }`))
	s := tengo.NewScript([]byte(`double := import("double"); out := double(21)`))
	s.SetImports(m)
	c, err := s.Run()
	if err != nil {
		t.Fatal(err)
	}
	if c.Get("out").Int() != 42 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO027ModuleMapLifecycle
func TestTGO043NestedModules(t *testing.T) {
	m := tengo.NewModuleMap()
	m.AddSourceModule("base", []byte(`export {n: 20}`))
	m.AddSourceModule("calc", []byte(`b := import("base"); export b.n + 2`))
	s := tengo.NewScript([]byte(`out := import("calc")`))
	s.SetImports(m)
	c, err := s.Run()
	if err != nil {
		t.Fatal(err)
	}
	if c.Get("out").Int() != 22 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO026CallableError
func TestTGO044GoFunctionComposition(t *testing.T) {
	add := &tengo.UserFunction{Name: "add", Value: func(args ...tengo.Object) (tengo.Object, error) {
		a, _ := tengo.ToInt64(args[0])
		b, _ := tengo.ToInt64(args[1])
		return &tengo.Int{Value: a + b}, nil
	}}
	c := run(t, "out := add(20, 22)", map[string]interface{}{"add": add})
	if c.Get("out").Int() != 42 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO023ScriptAddRemove
func TestTGO045UnknownSetFails(t *testing.T) {
	c := run(t, "x := 1", nil)
	if err := c.Set("missing", 2); err == nil {
		t.Fatal("expected error")
	}
}

// Depends-On: TestTGO029PreCanceledContext
func TestTGO046RunningCancellation(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	start := time.Now()
	_, err := tengo.NewScript([]byte("for {}")).RunContext(ctx)
	if err == nil || time.Since(start) > time.Second {
		t.Fatalf("err=%v elapsed=%v", err, time.Since(start))
	}
}

// Depends-On: TestTGO029PreCanceledContext
func TestTGO047CanceledCompiledRemainsUsable(t *testing.T) {
	s := tengo.NewScript([]byte("for x < 0 {}; out := x + 1"))
	_ = s.Add("x", -1)
	c, err := s.Compile()
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if err = c.RunContext(ctx); err == nil {
		t.Fatal("expected cancellation")
	}
	if err = c.Set("x", 2); err != nil {
		t.Fatal(err)
	}
	if err = c.Run(); err != nil || c.Get("out").Int() != 3 {
		t.Fatalf("%v %#v", err, c.Get("out").Value())
	}
}

// Depends-On: TestTGO023ScriptAddRemove
func TestTGO048ConcurrentClones(t *testing.T) {
	s := tengo.NewScript([]byte("out := input * input"))
	_ = s.Add("input", 0)
	base, err := s.Compile()
	if err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	for i := 1; i <= 8; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			c := base.Clone()
			if e := c.Set("input", i); e != nil {
				errs <- e
				return
			}
			if e := c.Run(); e != nil {
				errs <- e
				return
			}
			if c.Get("out").Int() != i*i {
				errs <- errors.New("wrong result")
			}
		}(i)
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Error(err)
	}
}

// Depends-On: TestTGO008ArrayIndex
func TestTGO049ImmutableMutationFails(t *testing.T) {
	if _, err := tengo.NewScript([]byte(`a := immutable([1,2]); a[0] = 9`)).Run(); err == nil {
		t.Fatal("expected mutation error")
	}
}

// Depends-On: TestTGO009MapSelector
func TestTGO050ErrorObjectWorkflow(t *testing.T) {
	c := run(t, `e := error("bad"); ok := is_error(e); value := e.value`, nil)
	if !c.Get("ok").Bool() || c.Get("value").String() != "bad" {
		t.Fatalf("%#v %#v", c.Get("ok").Value(), c.Get("value").Value())
	}
}

// Depends-On: TestTGO001IntegerArithmetic
func TestTGO056WhileLoopWorkflow(t *testing.T) {
	c := run(t, `i := 0; sum := 0; for i < 5 { sum += i; i++ }`, nil)
	if c.Get("sum").Int() != 10 {
		t.Fatal(c.Get("sum").Value())
	}
}

// Depends-On: TestTGO015FunctionCall
func TestTGO057IndependentReturnedClosures(t *testing.T) {
	c := run(t, `make := func(n) { return func(x) { return n + x } }; a := make(10); b := make(20); x := a(1); y := b(2)`, nil)
	if c.Get("x").Int() != 11 || c.Get("y").Int() != 22 {
		t.Fatal("returned closures share state")
	}
}

// Depends-On: TestTGO027ModuleMapLifecycle
func TestTGO058SourceModuleObjectExport(t *testing.T) {
	m := tengo.NewModuleMap()
	m.AddSourceModule("cfg", []byte(`export {x: 7, name: "go"}`))
	s := tengo.NewScript([]byte(`cfg := import("cfg"); out := cfg.x + len(cfg.name)`))
	s.SetImports(m)
	c, err := s.Run()
	if err != nil {
		t.Fatal(err)
	}
	if c.Get("out").Int() != 9 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO028MaxConstants
func TestTGO059AllocationLimitDoesNotPoisonNewScript(t *testing.T) {
	limited := tengo.NewScript([]byte(`a := [1, 2, 3]`))
	limited.SetMaxAllocs(0)
	if _, err := limited.Run(); err == nil {
		t.Fatal("expected allocation limit error")
	}
	c := run(t, `a := [1, 2, 3]; out := len(a)`, nil)
	if c.Get("out").Int() != 3 {
		t.Fatal(c.Get("out").Value())
	}
}

// Depends-On: TestTGO055ModuleMapMerge
func TestTGO060MergedModulesCompileTogether(t *testing.T) {
	a := tengo.NewModuleMap()
	b := tengo.NewModuleMap()
	a.AddSourceModule("left", []byte(`export 20`))
	b.AddSourceModule("right", []byte(`export 22`))
	a.AddMap(b)
	s := tengo.NewScript([]byte(`out := import("left") + import("right")`))
	s.SetImports(a)
	c, err := s.Run()
	if err != nil {
		t.Fatal(err)
	}
	if c.Get("out").Int() != 42 {
		t.Fatal(c.Get("out").Value())
	}
}
