package integration

import (
	"strings"
	"testing"

	"github.com/alecthomas/kong"
)

// app bundles a parser with captured output streams and exit codes.
type app struct {
	k     *kong.Kong
	out   *strings.Builder
	errw  *strings.Builder
	exits []int
}

// build constructs a parser named "app" whose exit function records codes
// instead of terminating, and whose output streams are captured.
func build(t *testing.T, grammar interface{}, opts ...kong.Option) *app {
	t.Helper()
	a := &app{out: &strings.Builder{}, errw: &strings.Builder{}}
	all := append([]kong.Option{
		kong.Name("app"),
		kong.Writers(a.out, a.errw),
		kong.Exit(func(code int) { a.exits = append(a.exits, code) }),
	}, opts...)
	k, err := kong.New(grammar, all...)
	if err != nil {
		t.Fatalf("kong.New failed: %v", err)
	}
	a.k = k
	return a
}

func mustParse(t *testing.T, a *app, args []string) *kong.Context {
	t.Helper()
	ctx, err := a.k.Parse(args)
	if err != nil {
		t.Fatalf("Parse(%v) failed: %v", args, err)
	}
	return ctx
}

func parseErr(t *testing.T, a *app, args []string) error {
	t.Helper()
	_, err := a.k.Parse(args)
	if err == nil {
		t.Fatalf("Parse(%v) unexpectedly succeeded", args)
	}
	return err
}

func wantContains(t *testing.T, got, want, label string) {
	t.Helper()
	if !strings.Contains(got, want) {
		t.Fatalf("%s: %q does not contain %q", label, got, want)
	}
}

func wantEq(t *testing.T, got, want interface{}, label string) {
	t.Helper()
	if got != want {
		t.Fatalf("%s: got %#v, want %#v", label, got, want)
	}
}

// collectFlags walks the model from the root along the given command names
// and returns every flag reachable at the destination node.
func collectFlags(t *testing.T, k *kong.Kong, path ...string) []*kong.Flag {
	t.Helper()
	node := k.Model.Node
	for _, name := range path {
		var next *kong.Node
		for _, c := range node.Children {
			if c.Name == name {
				next = c
				break
			}
		}
		if next == nil {
			t.Fatalf("command %q not found under %q", name, node.Name)
		}
		node = next
	}
	var flags []*kong.Flag
	for n := node; n != nil; n = n.Parent {
		flags = append(flags, n.Flags...)
	}
	return flags
}
