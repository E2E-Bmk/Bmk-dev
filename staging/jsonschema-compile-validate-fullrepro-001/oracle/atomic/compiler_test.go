package atomic

import (
	"encoding/json"
	"strings"
	"testing"

	jsonschema "github.com/santhosh-tekuri/jsonschema/v6"
	"github.com/santhosh-tekuri/jsonschema/v6/kind"
)

// ── document decoding ──────────────────────────────────────────────────

func TestUnmarshalJSONPreservesNumberPrecision(t *testing.T) {
	v, err := jsonschema.UnmarshalJSON(strings.NewReader(`{"amount": 10.30}`))
	if err != nil {
		t.Fatal(err)
	}
	num, ok := v.(map[string]any)["amount"].(json.Number)
	if !ok {
		t.Fatalf("amount decoded as %T, want json.Number", v.(map[string]any)["amount"])
	}
	if num.String() != "10.30" {
		t.Fatalf("number text = %q, want 10.30", num.String())
	}
}

func TestUnmarshalJSONDecodesContainers(t *testing.T) {
	v, err := jsonschema.UnmarshalJSON(strings.NewReader(`{"list": [true, null, "s"]}`))
	if err != nil {
		t.Fatal(err)
	}
	obj, ok := v.(map[string]any)
	if !ok {
		t.Fatalf("top-level decoded as %T, want map[string]any", v)
	}
	arr, ok := obj["list"].([]any)
	if !ok {
		t.Fatalf("list decoded as %T, want []any", obj["list"])
	}
	if len(arr) != 3 || arr[0] != true || arr[1] != nil || arr[2] != "s" {
		t.Fatalf("array content = %v", arr)
	}
}

func TestUnmarshalJSONRejectsTrailingContent(t *testing.T) {
	if _, err := jsonschema.UnmarshalJSON(strings.NewReader(`{"a": 1} {"b": 2}`)); err == nil {
		t.Fatal("trailing document must be rejected")
	}
	if _, err := jsonschema.UnmarshalJSON(strings.NewReader(`{"a": `)); err == nil {
		t.Fatal("malformed document must be rejected")
	}
}

// ── compiler operations ────────────────────────────────────────────────

func TestAddResourceDuplicateURLFails(t *testing.T) {
	c := jsonschema.NewCompiler()
	if err := c.AddResource("https://spec.test/dup.json", map[string]any{}); err != nil {
		t.Fatal(err)
	}
	err := c.AddResource("https://spec.test/dup.json", map[string]any{"type": "string"})
	if _, ok := err.(*jsonschema.ResourceExistsError); !ok {
		t.Fatalf("second AddResource returned %T (%v), want *ResourceExistsError", err, err)
	}
}

func TestCompiledSchemaExposesLocationAndDraft(t *testing.T) {
	c := jsonschema.NewCompiler()
	if err := c.AddResource("https://spec.test/s.json", mustJSON(t, `{"$defs": {"word": {"type": "string"}}}`)); err != nil {
		t.Fatal(err)
	}
	sch, err := c.Compile("https://spec.test/s.json")
	if err != nil {
		t.Fatal(err)
	}
	if sch.Location != "https://spec.test/s.json#" {
		t.Fatalf("Location = %q", sch.Location)
	}
	if sch.DraftVersion != 2020 {
		t.Fatalf("DraftVersion = %d, want 2020", sch.DraftVersion)
	}
	if sch.Bool != nil {
		t.Fatalf("Bool field = %v for a non-boolean schema, want nil", sch.Bool)
	}
	sub, err := c.Compile("https://spec.test/s.json#/$defs/word")
	if err != nil {
		t.Fatal(err)
	}
	if sub.Location != "https://spec.test/s.json#/$defs/word" {
		t.Fatalf("subschema Location = %q", sub.Location)
	}
}

func TestCompileMetaSchemaViolationFails(t *testing.T) {
	c := jsonschema.NewCompiler()
	if err := c.AddResource("https://spec.test/bad.json", mustJSON(t, `{"type": 1}`)); err != nil {
		t.Fatalf("AddResource must defer meta validation, got %v", err)
	}
	_, err := c.Compile("https://spec.test/bad.json")
	if _, ok := err.(*jsonschema.SchemaValidationError); !ok {
		t.Fatalf("Compile returned %T (%v), want *SchemaValidationError", err, err)
	}
}

func TestCompileUnloadableURLFails(t *testing.T) {
	c := jsonschema.NewCompiler()
	_, err := c.Compile("https://spec.test/never-added.json")
	if _, ok := err.(*jsonschema.LoadURLError); !ok {
		t.Fatalf("Compile returned %T (%v), want *LoadURLError", err, err)
	}
}

func TestMustCompilePanicsWhereCompileErrors(t *testing.T) {
	c := jsonschema.NewCompiler()
	panicked := false
	func() {
		defer func() {
			if recover() != nil {
				panicked = true
			}
		}()
		c.MustCompile("https://spec.test/absent.json")
	}()
	if !panicked {
		t.Fatal("MustCompile must panic for an unloadable location")
	}
}

func TestSchemeURLLoaderRejectsUnknownScheme(t *testing.T) {
	loader := jsonschema.SchemeURLLoader{"file": jsonschema.FileLoader{}}
	_, err := loader.Load("https://spec.test/x.json")
	if _, ok := err.(*jsonschema.UnsupportedURLSchemeError); !ok {
		t.Fatalf("Load returned %T (%v), want *UnsupportedURLSchemeError", err, err)
	}
}

func TestFileLoaderToFileConvertsURL(t *testing.T) {
	path, err := jsonschema.FileLoader{}.ToFile("file:///tmp/schemas/root.json")
	if err != nil {
		t.Fatal(err)
	}
	if path != "/tmp/schemas/root.json" {
		t.Fatalf("ToFile = %q", path)
	}
}

// ── boolean schemas ────────────────────────────────────────────────────

func TestTrueSchemaAcceptsEverything(t *testing.T) {
	sch := compile(t, `true`)
	assertValid(t, sch, nil)
	assertValid(t, sch, mustJSON(t, `{"any": ["thing", 1]}`))
	if sch.Bool == nil || *sch.Bool != true {
		t.Fatalf("Bool field = %v, want pointer to true", sch.Bool)
	}
}

func TestFalseSchemaRejectsEverything(t *testing.T) {
	sch := compile(t, `false`)
	if sch.Bool == nil || *sch.Bool != false {
		t.Fatalf("Bool field = %v, want pointer to false", sch.Bool)
	}
	assertFailsWith(t, sch, mustJSON(t, `0`), func(k jsonschema.ErrorKind) bool {
		_, ok := k.(*kind.FalseSchema)
		return ok
	}, "falseSchema")
}

func TestBooleanSubschemaInsideKeyword(t *testing.T) {
	sch := compile(t, `{"items": false}`)
	assertValid(t, sch, mustJSON(t, `[]`))
	if sch.Validate(mustJSON(t, `[1]`)) == nil {
		t.Fatal("items:false must reject any element")
	}
}

// ── validation error surface ───────────────────────────────────────────

func TestValidateReturnsNilOnConformingInstance(t *testing.T) {
	sch := compile(t, `{"type": "object", "required": ["k"]}`)
	if err := sch.Validate(mustJSON(t, `{"k": 1}`)); err != nil {
		t.Fatalf("expected nil, got %v", err)
	}
	if sch.Validate(mustJSON(t, `{}`)) == nil {
		t.Fatal("missing required member must be rejected")
	}
}

func TestValidationErrorRootKindIsSchema(t *testing.T) {
	sch := compile(t, `{"type": "string"}`)
	verr := sch.Validate(mustJSON(t, `5`)).(*jsonschema.ValidationError)
	if _, ok := verr.ErrorKind.(*kind.Schema); !ok {
		t.Fatalf("root ErrorKind = %T, want *kind.Schema", verr.ErrorKind)
	}
	if len(verr.InstanceLocation) != 0 {
		t.Fatalf("root InstanceLocation = %v, want empty", verr.InstanceLocation)
	}
}

func TestValidationErrorSchemaURLPointsAtFailingSubschema(t *testing.T) {
	sch := compile(t, `{"properties": {"n": {"minimum": 5}}}`)
	verr := sch.Validate(mustJSON(t, `{"n": 1}`)).(*jsonschema.ValidationError)
	if len(verr.Causes) != 1 {
		t.Fatalf("causes = %d, want 1", len(verr.Causes))
	}
	cause := verr.Causes[0]
	if cause.SchemaURL != "https://spec.test/s.json#/properties/n" {
		t.Fatalf("cause SchemaURL = %q", cause.SchemaURL)
	}
	if len(cause.InstanceLocation) != 1 || cause.InstanceLocation[0] != "n" {
		t.Fatalf("cause InstanceLocation = %v, want [n]", cause.InstanceLocation)
	}
}

func TestFlagOutputCarriesValidityOnly(t *testing.T) {
	sch := compile(t, `{"maximum": 2}`)
	verr := sch.Validate(mustJSON(t, `3`)).(*jsonschema.ValidationError)
	flag := verr.FlagOutput()
	if flag.Valid {
		t.Fatal("FlagOutput().Valid must be false")
	}
	raw, err := json.Marshal(flag)
	if err != nil {
		t.Fatal(err)
	}
	if string(raw) != `{"valid":false}` {
		t.Fatalf("flag JSON = %s", raw)
	}
}
