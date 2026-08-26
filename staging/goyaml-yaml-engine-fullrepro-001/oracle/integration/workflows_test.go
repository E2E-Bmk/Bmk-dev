package integration

import (
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/parser"
)

type serverConfig struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

type rangeError struct{ field string }

func (e rangeError) Error() string       { return "port out of range" }
func (e rangeError) StructField() string { return e.field }

type rangeErrors []rangeError

func (s rangeErrors) Error() string { return s[0].Error() }

type portValidator struct{}

func (portValidator) Struct(v interface{}) error {
	cfg, ok := v.(serverConfig)
	if !ok {
		return nil
	}
	if cfg.Port < 1 || cfg.Port > 65535 {
		return rangeErrors{{"Port"}}
	}
	return nil
}

// Verifies: Representative Workflows (workflow 1: strict fields plus
// validation with annotated failure output).
func TestConfigLoadingWorkflow(t *testing.T) {
	good := "host: web1\nport: 8080\n"
	var cfg serverConfig
	if err := yaml.UnmarshalWithOptions([]byte(good), &cfg,
		yaml.DisallowUnknownField(), yaml.Validator(portValidator{})); err != nil {
		t.Fatalf("valid config rejected: %v", err)
	}
	if cfg.Host != "web1" || cfg.Port != 8080 {
		t.Fatalf("decoded %+v", cfg)
	}

	bad := "host: web1\nport: 99999\n"
	var cfg2 serverConfig
	err := yaml.UnmarshalWithOptions([]byte(bad), &cfg2,
		yaml.DisallowUnknownField(), yaml.Validator(portValidator{}))
	if err == nil {
		t.Fatal("out-of-range port accepted")
	}
	if !strings.HasPrefix(err.Error(), "[2:7] port out of range") {
		t.Fatalf("validation failure %q is not annotated at the port field", err.Error())
	}
	formatted := yaml.FormatError(err, false, true)
	if !strings.Contains(formatted, ">  2 | port: 99999") || !strings.Contains(formatted, "^") {
		t.Fatalf("formatted failure %q lacks the annotated excerpt", formatted)
	}
}

// Verifies: Representative Workflows (workflow 1: unknown keys rejected with
// a matchable error).
func TestConfigLoadingRejectsUnknownKey(t *testing.T) {
	src := "host: web1\nport: 8080\ntypo_field: x\n"
	var cfg serverConfig
	err := yaml.UnmarshalWithOptions([]byte(src), &cfg,
		yaml.DisallowUnknownField(), yaml.Validator(portValidator{}))
	if err == nil {
		t.Fatal("unknown key accepted")
	}
	if !strings.Contains(err.Error(), `unknown field "typo_field"`) {
		t.Fatalf("error %q does not name the unknown key", err.Error())
	}
	formatted := yaml.FormatError(err, false, true)
	if !strings.Contains(formatted, ">  3 | typo_field: x") {
		t.Fatalf("formatted error %q does not point at line 3", formatted)
	}
}

// Verifies: Representative Workflows (workflow 2: surgical rewrite that
// preserves comments and unrelated bytes).
func TestSurgicalRewriteWorkflow(t *testing.T) {
	src := "# storefront\nstore:\n  bicycle:\n    color: red\n    price: 19.95 # retail\n  book: fine\n"
	f, err := parser.ParseBytes([]byte(src), parser.ParseComments)
	if err != nil {
		t.Fatal(err)
	}

	p, err := yaml.PathString("$.store.bicycle.color")
	if err != nil {
		t.Fatal(err)
	}
	if err := p.ReplaceWithReader(f, strings.NewReader("blue")); err != nil {
		t.Fatal(err)
	}

	m, err := yaml.PathString("$.store.bicycle")
	if err != nil {
		t.Fatal(err)
	}
	if err := m.MergeFromReader(f, strings.NewReader("brand: acme")); err != nil {
		t.Fatal(err)
	}

	out := f.String()
	if !strings.Contains(out, "# storefront") {
		t.Fatalf("head comment lost: %q", out)
	}
	if !strings.Contains(out, "color: blue") {
		t.Fatalf("replacement missing: %q", out)
	}
	if !strings.Contains(out, "price: 19.95 # retail") || !strings.Contains(out, "book: fine") {
		t.Fatalf("unrelated content or its comment disturbed: %q", out)
	}
	if !strings.Contains(out, "brand: acme") {
		t.Fatalf("merge missing: %q", out)
	}

	var color string
	pc, _ := yaml.PathString("$.store.bicycle.color")
	if err := pc.Read(strings.NewReader(out), &color); err != nil {
		t.Fatal(err)
	}
	if color != "blue" {
		t.Fatalf("re-read color = %q, want blue", color)
	}
}

// Verifies: Representative Workflows (comment-carrying transformation chain
// described in the workflows section).
func TestCommentPreservingTransformWorkflow(t *testing.T) {
	src := "# deployment\nreplicas: 2 # low\nimage: app:v1\n"
	cm := yaml.CommentMap{}
	var v yaml.MapSlice
	if err := yaml.UnmarshalWithOptions([]byte(src), &v, yaml.CommentToMap(cm)); err != nil {
		t.Fatal(err)
	}
	for i, item := range v {
		if item.Key == "replicas" {
			v[i].Value = uint64(5)
		}
	}
	out := mustMarshal(t, v, yaml.WithComment(cm))
	want := "# deployment\nreplicas: 5 # low\nimage: app:v1\n"
	if out != want {
		t.Fatalf("transformed document = %q, want %q", out, want)
	}
}
