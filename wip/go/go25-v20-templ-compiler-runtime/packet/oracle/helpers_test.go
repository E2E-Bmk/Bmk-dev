package templgate_test

import (
	"bytes"
	"context"
	"errors"
	templ "github.com/a-h/templ"
	"github.com/a-h/templ/receipt"
	"io"
	"testing"
)

func runSynthetic(t *testing.T, root, family string) {
	t.Helper()
	name := "component-" + root
	sourceBytes := []byte("templ " + name + "() { <a href=\"/safe\">hello</a> }")
	empty := receipt.NewRenderPlan()
	if _, err := empty.SelectSource("", sourceBytes); err == nil {
		t.Fatal("empty source accepted")
	}
	plan, err := empty.SelectSource(name, sourceBytes)
	if err != nil {
		t.Fatal(err)
	}
	plan = plan.IncludeGenerated().IncludeDirectRender().IncludeHTTPRender()
	source := receipt.SourceFact{Name: name, Valid: true, Components: []string{name}, Ranges: []receipt.RangeFact{{Start: 0, End: len(sourceBytes)}}, Contexts: []string{"url", "text"}, Formatted: []byte("templ " + name + "() { <a> hello </a> }")}
	generated := &receipt.GeneratedFact{Path: name + "_templ.go", Imports: []string{"context", "io"}, Declarations: []string{name, "Render"}, SourceMap: map[string]receipt.RangeFact{name: {Start: 0, End: len(sourceBytes)}}, Compiles: true}
	body := []byte("<a href=\"/safe\">hello</a>")
	direct := &receipt.RenderFact{Context: "url", Bytes: body, Attributes: []receipt.AttributeFact{{Name: "aria-current", Boolean: true, Present: true}, {Name: "href", Value: "/safe", Present: true}}, Escaped: true}
	httpFact := &receipt.HTTPFact{Status: 200, Headers: map[string]string{"Content-Type": "text/html"}, Body: body}
	journal := receipt.NewWriterJournal()
	owned := append([]byte(nil), body...)
	entry := journal.Record(owned, nil)
	owned[0] = 'X'
	if entry.Seq != 1 || string(journal.Entries()[0].Bytes) != string(body) {
		t.Fatal("writer journal ownership failure")
	}
	got, err := receipt.Capture(plan, source, generated, direct, httpFact, journal)
	if err != nil {
		t.Fatal(err)
	}
	if got.Digest() == "" || got.Validate() != nil {
		t.Fatal("invalid render receipt")
	}
	source.Formatted[0] = 'X'
	if got.Source.Formatted[0] == 'X' {
		t.Fatal("capture retained source storage")
	}
	switch family {
	case "M-TEMPLATE-PARSE":
		bad := got
		bad.Source.Valid = false
		if bad.Validate() == nil {
			t.Fatal("malformed source validated")
		}
	case "M-COMPONENT-CODEGEN":
		bad := got
		copyGenerated := *got.Generated
		copyGenerated.Compiles = false
		bad.Generated = &copyGenerated
		if bad.Validate() == nil {
			t.Fatal("uncompilable artifact validated")
		}
	case "M-CONTEXT-ESCAPE":
		bad := got
		copyRender := *got.Direct
		copyRender.Escaped = false
		bad.Direct = &copyRender
		if bad.Validate() == nil {
			t.Fatal("unsafe contextual render validated")
		}
	case "M-ATTRIBUTE-SEMANTICS":
		bad := got
		copyRender := *got.Direct
		copyRender.Attributes = append(copyRender.Attributes, copyRender.Attributes[0])
		bad.Direct = &copyRender
		if bad.Validate() == nil {
			t.Fatal("duplicate attribute ownership validated")
		}
	case "M-RUNTIME-RENDER":
		bad := got
		copyRender := *got.Direct
		copyRender.Error = "writer failed"
		bad.Direct = &copyRender
		bad.Writes = []receipt.WriterFact{{Seq: 1, Error: "writer failed"}, {Seq: 2, Bytes: []byte("late")}}
		if bad.Validate() == nil {
			t.Fatal("write after first failure validated")
		}
	case "M-FORMAT-IDEMPOTENCE":
		equivalentSource := source
		equivalentSource.Formatted = []byte("templ   " + name + "() {   <a> hello </a>   }")
		equal, err := receipt.Capture(plan, equivalentSource, generated, direct, httpFact, journal)
		if err != nil || !got.Equivalent(equal) {
			t.Fatal("harmless formatting changed receipt")
		}
	case "M-CLI-DIAGNOSTICS":
		changedSource := source
		changedSource.Diagnostics = []receipt.DiagnosticFact{{Code: "E100", Message: "bad expression", Start: 6, End: 9}}
		changed, err := receipt.Capture(plan, changedSource, generated, direct, httpFact, journal)
		if err != nil || len(receipt.Diff(got, changed).Changes) != 1 {
			t.Fatal("diagnostic change hidden")
		}
	default:
		t.Fatalf("unknown family %q", family)
	}
}

func runNative(t *testing.T, root, _ string) {
	t.Helper()
	var output bytes.Buffer
	component := templ.ComponentFunc(func(ctx context.Context, w io.Writer) error {
		_, err := w.Write([]byte("<p>" + templ.EscapeString(root) + "</p>"))
		return err
	})
	if err := component.Render(context.Background(), &output); err != nil || output.String() != "<p>"+root+"</p>" {
		t.Fatal("native component render drift")
	}
	if got := templ.URL("javascript:alert(1)"); got == "javascript:alert(1)" {
		t.Fatal("unsafe URL passed unchanged")
	}
	failing := templ.ComponentFunc(func(context.Context, io.Writer) error { return errors.New("stop") })
	if failing.Render(context.Background(), &output) == nil {
		t.Fatal("component error lost")
	}
}
