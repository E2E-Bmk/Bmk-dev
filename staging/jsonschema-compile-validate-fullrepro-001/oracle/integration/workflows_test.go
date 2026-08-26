package integration

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	jsonschema "github.com/santhosh-tekuri/jsonschema/v6"
	"github.com/santhosh-tekuri/jsonschema/v6/kind"
)

func mustJSON(t *testing.T, s string) any {
	t.Helper()
	v, err := jsonschema.UnmarshalJSON(strings.NewReader(s))
	if err != nil {
		t.Fatalf("unmarshal %q: %v", s, err)
	}
	return v
}

func addResource(t *testing.T, c *jsonschema.Compiler, url, doc string) {
	t.Helper()
	if err := c.AddResource(url, mustJSON(t, doc)); err != nil {
		t.Fatalf("AddResource(%s): %v", url, err)
	}
}

type loaderFunc func(url string) (any, error)

func (f loaderFunc) Load(url string) (any, error) { return f(url) }

func leafErrors(e *jsonschema.ValidationError) []*jsonschema.ValidationError {
	if len(e.Causes) == 0 {
		return []*jsonschema.ValidationError{e}
	}
	var out []*jsonschema.ValidationError
	for _, c := range e.Causes {
		out = append(out, leafErrors(c)...)
	}
	return out
}

func pointer(path []string) string {
	var b strings.Builder
	for _, seg := range path {
		b.WriteString("/")
		b.WriteString(strings.ReplaceAll(strings.ReplaceAll(seg, "~", "~0"), "/", "~1"))
	}
	return b.String()
}

// ── reference graphs ───────────────────────────────────────────────────

// Seam: protocol handoff — a schema compiled in one resource constrains
// instances validated through a reference held by another resource.
// Depends-On: TestPropertiesApplyToMatchingMembers, TestStringLengthCountsCodePoints
func TestCrossResourceRefEnforcesTargetRules(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/name.json", `{"type": "string", "minLength": 2}`)
	addResource(t, c, "https://graph.test/person.json", `{
		"type": "object",
		"properties": {"name": {"$ref": "name.json"}},
		"required": ["name"]
	}`)
	sch, err := c.Compile("https://graph.test/person.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"name": "bo"}`)); err != nil {
		t.Fatalf("conforming instance rejected: %v", err)
	}
	if sch.Validate(mustJSON(t, `{"name": "b"}`)) == nil {
		t.Fatal("referenced minLength must reject one-character name")
	}
}

// CVI-4: an instance rejected by a directly compiled subschema is rejected
// through $ref from another resource.
// Depends-On: TestStringLengthCountsCodePoints
func TestRefTransparencyAgreesWithDirectCompile(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/limit.json", `{"maximum": 6}`)
	addResource(t, c, "https://graph.test/holder.json", `{"$ref": "limit.json"}`)
	direct, err := c.Compile("https://graph.test/limit.json")
	if err != nil {
		t.Fatal(err)
	}
	viaRef, err := c.Compile("https://graph.test/holder.json")
	if err != nil {
		t.Fatal(err)
	}
	if direct.Validate(mustJSON(t, `6`)) != nil {
		t.Fatal("6 must satisfy maximum 6 directly")
	}
	if direct.Validate(mustJSON(t, `6.5`)) == nil {
		t.Fatal("6.5 must violate maximum 6 directly")
	}
	for _, inst := range []string{`6`, `6.5`, `"text"`, `-2`} {
		d := direct.Validate(mustJSON(t, inst))
		r := viaRef.Validate(mustJSON(t, inst))
		if (d == nil) != (r == nil) {
			t.Fatalf("instance %s: direct=%v viaRef=%v", inst, d, r)
		}
	}
}

// CVI-3: repeated compiles and both fragment addressings return the
// identical *Schema pointer.
// Depends-On: TestCompiledSchemaExposesLocationAndDraft
func TestCompileCachingReturnsIdenticalPointer(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/root.json", `{
		"$defs": {"word": {"$anchor": "word", "type": "string"}}
	}`)
	first, err := c.Compile("https://graph.test/root.json")
	if err != nil {
		t.Fatal(err)
	}
	second, err := c.Compile("https://graph.test/root.json")
	if err != nil {
		t.Fatal(err)
	}
	if first != second {
		t.Fatal("repeated Compile must return the identical *Schema")
	}
	byAnchor, err := c.Compile("https://graph.test/root.json#word")
	if err != nil {
		t.Fatal(err)
	}
	byPointer, err := c.Compile("https://graph.test/root.json#/$defs/word")
	if err != nil {
		t.Fatal(err)
	}
	if byAnchor != byPointer {
		t.Fatal("anchor and JSON-Pointer fragments must compile to the identical *Schema")
	}
	if byAnchor.Validate(mustJSON(t, `5`)) == nil {
		t.Fatal("anchored subschema must reject a number")
	}
}

// CVI-5: MustCompile agrees with Compile on both success identity and
// failure situations.
// Depends-On: TestMustCompilePanicsWhereCompileErrors
func TestMustCompileAgreesWithCompile(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/ok.json", `{"type": "array"}`)
	compiled, err := c.Compile("https://graph.test/ok.json")
	if err != nil {
		t.Fatal(err)
	}
	if must := c.MustCompile("https://graph.test/ok.json"); must != compiled {
		t.Fatal("MustCompile must return the identical *Schema for a compilable location")
	}
	panicked := false
	func() {
		defer func() {
			if recover() != nil {
				panicked = true
			}
		}()
		c.MustCompile("https://graph.test/gone.json")
	}()
	if _, err := c.Compile("https://graph.test/gone.json"); err == nil || !panicked {
		t.Fatalf("Compile err=%v panicked=%v; both must fail", err, panicked)
	}
}

// Seam: error propagation — a dangling anchor in a referenced resource
// fails compilation of the referencing resource with a typed error.
func TestAnchorNotFoundAcrossResources(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/target.json", `{"type": "string"}`)
	addResource(t, c, "https://graph.test/user.json", `{"$ref": "target.json#nowhere"}`)
	_, err := c.Compile("https://graph.test/user.json")
	if _, ok := err.(*jsonschema.AnchorNotFoundError); !ok {
		t.Fatalf("Compile returned %T (%v), want *AnchorNotFoundError", err, err)
	}
}

// Seam: state consistency — an embedded resource declared by $id is
// referenceable without its own AddResource call.
func TestEmbeddedResourceWithIDIsReferenceable(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/outer.json", `{
		"$id": "https://graph.test/outer.json",
		"$defs": {"inner": {"$id": "https://graph.test/inner.json", "type": "boolean"}},
		"$ref": "inner.json"
	}`)
	sch, err := c.Compile("https://graph.test/outer.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(true); err != nil {
		t.Fatalf("boolean must conform: %v", err)
	}
	if sch.Validate(mustJSON(t, `7`)) == nil {
		t.Fatal("number must be rejected through the embedded resource")
	}
	if err := sch.Validate(false); err != nil {
		t.Fatalf("boolean false must also conform: %v", err)
	}
}

// Seam: lifecycle crossing — a self-referential schema compiles and
// terminates on finite instances.
// Depends-On: TestPropertiesApplyToMatchingMembers
func TestRecursiveSchemaValidatesNestedTree(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/node.json", `{
		"type": "object",
		"properties": {
			"label": {"type": "string"},
			"kids": {"type": "array", "items": {"$ref": "#"}}
		},
		"required": ["label"]
	}`)
	sch, err := c.Compile("https://graph.test/node.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"label": "root", "kids": [{"label": "leaf", "kids": []}]}`)); err != nil {
		t.Fatalf("nested tree must conform: %v", err)
	}
	err = sch.Validate(mustJSON(t, `{"label": "root", "kids": [{"kids": []}]}`))
	if err == nil {
		t.Fatal("nested node missing label must be rejected")
	}
	leaves := leafErrors(err.(*jsonschema.ValidationError))
	found := false
	for _, l := range leaves {
		if pointer(l.InstanceLocation) == "/kids/0" {
			if _, ok := l.ErrorKind.(*kind.Required); ok {
				found = true
			}
		}
	}
	if !found {
		t.Fatalf("expected required violation at /kids/0, leaves: %v", err)
	}
}

// Seam: protocol handoff — $dynamicRef re-resolves against the dynamic
// scope during validation.
func TestDynamicRefResolvesRecursively(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://graph.test/tree.json", `{
		"$id": "https://graph.test/tree.json",
		"$dynamicAnchor": "node",
		"type": "object",
		"properties": {"children": {"type": "array", "items": {"$dynamicRef": "#node"}}}
	}`)
	sch, err := c.Compile("https://graph.test/tree.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"children": [{"children": []}]}`)); err != nil {
		t.Fatalf("nested object tree must conform: %v", err)
	}
	if sch.Validate(mustJSON(t, `{"children": [{"children": [12]}]}`)) == nil {
		t.Fatal("a number two levels down must violate the dynamic node schema")
	}
}

// ── output projections ─────────────────────────────────────────────────

// CVI-2: every leaf cause appears in BasicOutput with the JSON-Pointer
// encoding of its instance location.
// Depends-On: TestValidationErrorSchemaURLPointsAtFailingSubschema
func TestErrorTreeAgreesWithBasicOutput(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://out.test/s.json", `{
		"type": "object",
		"properties": {
			"rows": {"items": {"type": "object", "required": ["id"]}},
			"tag": {"type": "string"}
		}
	}`)
	sch, err := c.Compile("https://out.test/s.json")
	if err != nil {
		t.Fatal(err)
	}
	verr := sch.Validate(mustJSON(t, `{"rows": [{"id": 1}, {}], "tag": 9}`)).(*jsonschema.ValidationError)
	leaves := leafErrors(verr)
	if len(leaves) != 2 {
		t.Fatalf("leaves = %d, want 2", len(leaves))
	}
	basic := verr.BasicOutput()
	if basic.Valid {
		t.Fatal("basic root must be invalid")
	}
	locations := map[string]bool{}
	for _, unit := range basic.Errors {
		if !unit.Valid {
			locations[unit.InstanceLocation] = true
		}
	}
	for _, leaf := range leaves {
		enc := pointer(leaf.InstanceLocation)
		if !locations[enc] {
			t.Fatalf("leaf at %q missing from basic output units %v", enc, locations)
		}
	}
}

// Seam: state consistency — basic output flattens what detailed output
// nests, over the same failure state.
// Depends-On: TestAnyOfRequiresAtLeastOneBranch
func TestBasicOutputFlattensWhatDetailedNests(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://out.test/any.json", `{"anyOf": [{"type": "string"}, {"minimum": 20}]}`)
	sch, err := c.Compile("https://out.test/any.json")
	if err != nil {
		t.Fatal(err)
	}
	verr := sch.Validate(mustJSON(t, `7`)).(*jsonschema.ValidationError)

	basic := verr.BasicOutput()
	basicLocs := map[string]bool{}
	for _, u := range basic.Errors {
		basicLocs[u.KeywordLocation] = true
		if len(u.Errors) != 0 {
			t.Fatalf("basic units must not nest, got children under %q", u.KeywordLocation)
		}
	}
	for _, want := range []string{"/anyOf", "/anyOf/0/type", "/anyOf/1/minimum"} {
		if !basicLocs[want] {
			t.Fatalf("basic output missing keywordLocation %q (have %v)", want, basicLocs)
		}
	}

	detailed := verr.DetailedOutput()
	if len(detailed.Errors) != 1 || detailed.Errors[0].KeywordLocation != "/anyOf" {
		t.Fatalf("detailed root children = %+v, want single /anyOf unit", detailed.Errors)
	}
	nested := detailed.Errors[0].Errors
	nestedLocs := map[string]bool{}
	for _, u := range nested {
		nestedLocs[u.KeywordLocation] = true
	}
	if !nestedLocs["/anyOf/0/type"] || !nestedLocs["/anyOf/1/minimum"] {
		t.Fatalf("detailed /anyOf children = %v", nestedLocs)
	}
}

// CVI-1: flag, basic, and detailed projections agree with Validate on
// validity.
// Depends-On: TestValidateReturnsNilOnConformingInstance
func TestOutputProjectionsAgreeOnValidity(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://out.test/v.json", `{"required": ["k"], "properties": {"k": {"type": "integer"}}}`)
	sch, err := c.Compile("https://out.test/v.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"k": 3}`)); err != nil {
		t.Fatalf("conforming instance rejected: %v", err)
	}
	for _, inst := range []string{`{}`, `{"k": "s"}`} {
		err := sch.Validate(mustJSON(t, inst))
		if err == nil {
			t.Fatalf("instance %s must be rejected", inst)
		}
		verr := err.(*jsonschema.ValidationError)
		if verr.FlagOutput().Valid || verr.BasicOutput().Valid || verr.DetailedOutput().Valid {
			t.Fatalf("all projections must report invalid for %s", inst)
		}
	}
}

// Seam: state consistency — the error JSON uses the documented member names.
// Depends-On: TestFlagOutputCarriesValidityOnly
func TestBasicOutputJSONMemberNames(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://out.test/j.json", `{"properties": {"n": {"minimum": 15}}}`)
	sch, err := c.Compile("https://out.test/j.json")
	if err != nil {
		t.Fatal(err)
	}
	verr := sch.Validate(mustJSON(t, `{"n": 4}`)).(*jsonschema.ValidationError)
	raw, err := json.Marshal(verr.BasicOutput())
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]any
	if err := json.Unmarshal(raw, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded["valid"] != false {
		t.Fatalf("top-level valid = %v", decoded["valid"])
	}
	units, ok := decoded["errors"].([]any)
	if !ok || len(units) == 0 {
		t.Fatalf("errors member = %v", decoded["errors"])
	}
	unit := units[0].(map[string]any)
	if unit["keywordLocation"] != "/properties/n/minimum" {
		t.Fatalf("keywordLocation = %v", unit["keywordLocation"])
	}
	if unit["instanceLocation"] != "/n" {
		t.Fatalf("instanceLocation = %v", unit["instanceLocation"])
	}
	if _, present := unit["error"]; !present {
		t.Fatal("leaf unit must carry an error member")
	}
}

// Seam: state consistency — one Validate call reports every violated
// keyword together.
// Depends-On: TestRequiredReportsExactlyMissingMembers, TestTypeKindReportsGotAndWant
func TestMultipleViolationsReportedTogether(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://out.test/multi.json", `{
		"required": ["p", "q"],
		"properties": {"r": {"type": "string"}}
	}`)
	sch, err := c.Compile("https://out.test/multi.json")
	if err != nil {
		t.Fatal(err)
	}
	verr := sch.Validate(mustJSON(t, `{"r": 5}`)).(*jsonschema.ValidationError)
	if len(verr.Causes) != 2 {
		t.Fatalf("causes = %d, want 2", len(verr.Causes))
	}
	var hasRequired, hasType bool
	for _, leaf := range leafErrors(verr) {
		switch leaf.ErrorKind.(type) {
		case *kind.Required:
			hasRequired = true
		case *kind.Type:
			hasType = true
		}
	}
	if !hasRequired || !hasType {
		t.Fatalf("required=%v type=%v; both kinds must be reported", hasRequired, hasType)
	}
}

// Seam: state consistency — instance locations address nested values as
// member names and decimal array indices.
// Depends-On: TestItemsAloneCoversEveryElement
func TestNestedInstanceLocationPath(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://out.test/deep.json", `{
		"properties": {"rows": {"items": {"properties": {"id": {"type": "integer"}}}}}
	}`)
	sch, err := c.Compile("https://out.test/deep.json")
	if err != nil {
		t.Fatal(err)
	}
	verr := sch.Validate(mustJSON(t, `{"rows": [{"id": 1}, {"id": "bad"}]}`)).(*jsonschema.ValidationError)
	leaves := leafErrors(verr)
	if len(leaves) != 1 {
		t.Fatalf("leaves = %d, want 1", len(leaves))
	}
	loc := leaves[0].InstanceLocation
	if len(loc) != 3 || loc[0] != "rows" || loc[1] != "1" || loc[2] != "id" {
		t.Fatalf("InstanceLocation = %v, want [rows 1 id]", loc)
	}
	if leaves[0].SchemaURL != "https://out.test/deep.json#/properties/rows/items/properties/id" {
		t.Fatalf("SchemaURL = %q", leaves[0].SchemaURL)
	}
}

// ── loaders ────────────────────────────────────────────────────────────

// CVI-7: a document served by a caller-registered loader validates
// identically to the same document registered via AddResource.
// Depends-On: TestCompileUnloadableURLFails
func TestCustomLoaderEquivalentToAddResource(t *testing.T) {
	doc := `{"type": "integer", "minimum": 4}`
	registered := jsonschema.NewCompiler()
	addResource(t, registered, "https://load.test/n.json", doc)
	direct, err := registered.Compile("https://load.test/n.json")
	if err != nil {
		t.Fatal(err)
	}

	loaded := jsonschema.NewCompiler()
	loaded.UseLoader(loaderFunc(func(url string) (any, error) {
		if url == "https://load.test/n.json" {
			return mustJSON(t, doc), nil
		}
		return nil, fmt.Errorf("unknown url %q", url)
	}))
	viaLoader, err := loaded.Compile("https://load.test/n.json")
	if err != nil {
		t.Fatal(err)
	}
	if viaLoader.Validate(mustJSON(t, `9`)) != nil {
		t.Fatal("9 must satisfy the loader-served schema")
	}
	if viaLoader.Validate(mustJSON(t, `3`)) == nil {
		t.Fatal("3 must violate the loader-served minimum")
	}
	for _, inst := range []string{`4`, `3`, `4.5`, `"x"`} {
		a := direct.Validate(mustJSON(t, inst))
		b := viaLoader.Validate(mustJSON(t, inst))
		if (a == nil) != (b == nil) {
			t.Fatalf("instance %s: registered=%v loader=%v", inst, a, b)
		}
	}
}

// Seam: lifecycle crossing — a schema written to disk compiles through the
// default FileLoader and enforces its rules.
func TestFileLoaderCompilesFromDisk(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "disk.json")
	if err := os.WriteFile(path, []byte(`{"type": "string", "maxLength": 4}`), 0o644); err != nil {
		t.Fatal(err)
	}
	c := jsonschema.NewCompiler()
	sch, err := c.Compile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate("abcd"); err != nil {
		t.Fatalf("conforming string rejected: %v", err)
	}
	if sch.Validate("abcde") == nil {
		t.Fatal("maxLength from on-disk schema must apply")
	}
}

// Seam: config interaction — SchemeURLLoader dispatches by scheme and
// Compile surfaces unloadable URLs as LoadURLError.
// Depends-On: TestSchemeURLLoaderRejectsUnknownScheme
func TestSchemeURLLoaderDispatchAndFailure(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "s.json")
	if err := os.WriteFile(path, []byte(`{"const": 3}`), 0o644); err != nil {
		t.Fatal(err)
	}
	c := jsonschema.NewCompiler()
	c.UseLoader(jsonschema.SchemeURLLoader{"file": jsonschema.FileLoader{}})
	sch, err := c.Compile("file://" + path)
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `3.0`)); err != nil {
		t.Fatalf("const with rational equality must accept 3.0: %v", err)
	}
	_, err = c.Compile("https://load.test/unreachable.json")
	if _, ok := err.(*jsonschema.LoadURLError); !ok {
		t.Fatalf("Compile returned %T (%v), want *LoadURLError", err, err)
	}
}

// ── dialects ───────────────────────────────────────────────────────────

// Seam: config interaction — DefaultDraft changes how documents without
// $schema are interpreted.
// Depends-On: TestPrefixItemsThenItemsSplit
func TestDefaultDraftSevenArrayItemsSemantics(t *testing.T) {
	c := jsonschema.NewCompiler()
	c.DefaultDraft(jsonschema.Draft7)
	addResource(t, c, "https://dialect.test/d7.json", `{
		"items": [{"type": "integer"}, {"type": "string"}]
	}`)
	sch, err := c.Compile("https://dialect.test/d7.json")
	if err != nil {
		t.Fatal(err)
	}
	if sch.DraftVersion != 7 {
		t.Fatalf("DraftVersion = %d, want 7", sch.DraftVersion)
	}
	if err := sch.Validate(mustJSON(t, `[3, "a", true]`)); err != nil {
		t.Fatalf("positional items must accept matching prefix: %v", err)
	}
	if sch.Validate(mustJSON(t, `["a"]`)) == nil {
		t.Fatal("first position must require an integer")
	}
}

// Seam: config interaction — a $schema declaration overrides the compiler
// default per resource, switching keyword vocabularies.
// Depends-On: TestCompiledSchemaExposesLocationAndDraft
func TestSchemaDeclarationOverridesDefaultDraft(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://dialect.test/legacy.json", `{
		"$schema": "http://json-schema.org/draft-07/schema#",
		"definitions": {"pos": {"minimum": 0}},
		"properties": {"n": {"$ref": "#/definitions/pos"}}
	}`)
	sch, err := c.Compile("https://dialect.test/legacy.json")
	if err != nil {
		t.Fatal(err)
	}
	if sch.DraftVersion != 7 {
		t.Fatalf("DraftVersion = %d, want 7", sch.DraftVersion)
	}
	if err := sch.Validate(mustJSON(t, `{"n": 2}`)); err != nil {
		t.Fatalf("conforming instance rejected: %v", err)
	}
	if sch.Validate(mustJSON(t, `{"n": -1}`)) == nil {
		t.Fatal("definitions-referenced minimum must apply under draft-07")
	}
}

// ── evaluation-state interplay ─────────────────────────────────────────

// Seam: state consistency — members evaluated inside allOf branches count
// for the parent's unevaluatedProperties.
// Depends-On: TestAllOfRequiresEveryBranch, TestPropertiesApplyToMatchingMembers
func TestUnevaluatedPropertiesSeesAllOfEvaluation(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://uneval.test/p.json", `{
		"allOf": [{"properties": {"a": {"type": "integer"}}}],
		"properties": {"b": {"type": "integer"}},
		"unevaluatedProperties": false
	}`)
	sch, err := c.Compile("https://uneval.test/p.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"a": 1, "b": 2}`)); err != nil {
		t.Fatalf("members evaluated by allOf and parent must be accepted: %v", err)
	}
	if sch.Validate(mustJSON(t, `{"c": 1}`)) == nil {
		t.Fatal("unevaluated member must be rejected")
	}
}

// Seam: state consistency — a $ref'd base schema's properties count as
// evaluated in the referencing schema.
// Depends-On: TestPropertiesApplyToMatchingMembers
func TestUnevaluatedPropertiesAcrossRef(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://uneval.test/base.json", `{"properties": {"a": {"type": "integer"}}}`)
	addResource(t, c, "https://uneval.test/ext.json", `{
		"$ref": "base.json",
		"properties": {"b": {"type": "integer"}},
		"unevaluatedProperties": false
	}`)
	sch, err := c.Compile("https://uneval.test/ext.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"a": 1, "b": 2}`)); err != nil {
		t.Fatalf("members evaluated through $ref must count: %v", err)
	}
	if sch.Validate(mustJSON(t, `{"z": 1}`)) == nil {
		t.Fatal("member unknown to both resources must be rejected")
	}
}

// Seam: state consistency — items evaluated by prefixItems count for
// unevaluatedItems.
// Depends-On: TestPrefixItemsThenItemsSplit
func TestUnevaluatedItemsAfterPrefix(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://uneval.test/i.json", `{
		"prefixItems": [{"type": "integer"}],
		"unevaluatedItems": false
	}`)
	sch, err := c.Compile("https://uneval.test/i.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `[5]`)); err != nil {
		t.Fatalf("prefix-evaluated element must be accepted: %v", err)
	}
	if sch.Validate(mustJSON(t, `[5, 6]`)) == nil {
		t.Fatal("element past the prefix must be rejected")
	}
}

// ── composition and equality agreement ─────────────────────────────────

// CVI-6: const equality and uniqueItems duplicate detection agree.
// Depends-On: TestConstObjectEqualityIgnoresKeyOrder, TestUniqueItemsUsesRationalEquality
func TestConstAndUniqueItemsEqualityAgree(t *testing.T) {
	pairs := []struct {
		a, b  string
		equal bool
	}{
		{`{"x": 1, "y": [2, 3]}`, `{"y": [2.0, 3], "x": 1.0}`, true},
		{`[1, 2]`, `[2, 1]`, false},
		{`"5"`, `5`, false},
		{`0.5`, `0.50`, true},
	}
	for _, p := range pairs {
		c := jsonschema.NewCompiler()
		addResource(t, c, "https://eq.test/const.json",
			`{"const": `+p.a+`}`)
		constSch, err := c.Compile("https://eq.test/const.json")
		if err != nil {
			t.Fatal(err)
		}
		constEqual := constSch.Validate(mustJSON(t, p.b)) == nil

		addResource(t, c, "https://eq.test/unique.json", `{"uniqueItems": true}`)
		uniqueSch, err := c.Compile("https://eq.test/unique.json")
		if err != nil {
			t.Fatal(err)
		}
		duplicate := uniqueSch.Validate(mustJSON(t, `[`+p.a+`,`+p.b+`]`)) != nil

		if constEqual != p.equal || duplicate != p.equal {
			t.Fatalf("pair (%s, %s): const-equal=%v unique-duplicate=%v want %v",
				p.a, p.b, constEqual, duplicate, p.equal)
		}
	}
}

// Seam: state consistency — a compiled schema is immune to later compiler
// mutations.
// Depends-On: TestCompiledSchemaExposesLocationAndDraft
func TestCompiledSchemaImmuneToLaterCompilerMutations(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://state.test/first.json", `{"type": "integer"}`)
	sch, err := c.Compile("https://state.test/first.json")
	if err != nil {
		t.Fatal(err)
	}
	c.DefaultDraft(jsonschema.Draft7)
	addResource(t, c, "https://state.test/second.json", `{"type": "string"}`)
	if _, err := c.Compile("https://state.test/second.json"); err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `41`)); err != nil {
		t.Fatalf("previously compiled schema must keep accepting integers: %v", err)
	}
	if sch.Validate("nope") == nil {
		t.Fatal("previously compiled schema must keep rejecting strings")
	}
	if sch.DraftVersion != 2020 {
		t.Fatalf("DraftVersion changed to %d after compiler mutation", sch.DraftVersion)
	}
}

// Seam: state consistency — validation is pure: results do not depend on
// earlier validations against the same schema.
// Depends-On: TestValidateReturnsNilOnConformingInstance
func TestValidationIsPureAcrossInstances(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://state.test/pure.json", `{"minItems": 2}`)
	sch, err := c.Compile("https://state.test/pure.json")
	if err != nil {
		t.Fatal(err)
	}
	bad := mustJSON(t, `[1]`)
	good := mustJSON(t, `[1, 2]`)
	for round := 0; round < 3; round++ {
		if sch.Validate(bad) == nil {
			t.Fatalf("round %d: short array must fail", round)
		}
		if err := sch.Validate(good); err != nil {
			t.Fatalf("round %d: conforming array rejected: %v", round, err)
		}
	}
}

// Seam: config interaction — conditionals compose in conjunction with
// sibling keywords.
// Depends-On: TestIfThenElseSelectsBranch, TestRequiredReportsExactlyMissingMembers
func TestConditionalComposesWithSiblingKeywords(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://comp.test/cond.json", `{
		"type": "object",
		"required": ["mode"],
		"if": {"properties": {"mode": {"const": "strict"}}, "required": ["mode"]},
		"then": {"required": ["limit"]}
	}`)
	sch, err := c.Compile("https://comp.test/cond.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"mode": "loose"}`)); err != nil {
		t.Fatalf("else-less non-matching instance must conform: %v", err)
	}
	if err := sch.Validate(mustJSON(t, `{"mode": "strict", "limit": 3}`)); err != nil {
		t.Fatalf("then-obligation satisfied must conform: %v", err)
	}
	if sch.Validate(mustJSON(t, `{"mode": "strict"}`)) == nil {
		t.Fatal("then-obligation must apply in conjunction")
	}
	if sch.Validate(mustJSON(t, `{"limit": 3}`)) == nil {
		t.Fatal("sibling required must still apply")
	}
}

// Seam: config interaction — oneOf branch selection composes with outer
// object constraints.
// Depends-On: TestOneOfRequiresExactlyOneMatch
func TestOneOfBranchesComposeWithOuterType(t *testing.T) {
	c := jsonschema.NewCompiler()
	addResource(t, c, "https://comp.test/one.json", `{
		"type": "object",
		"required": ["kind"],
		"oneOf": [
			{"properties": {"kind": {"const": "disk"}}, "required": ["path"]},
			{"properties": {"kind": {"const": "mem"}}, "required": ["size"]}
		]
	}`)
	sch, err := c.Compile("https://comp.test/one.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := sch.Validate(mustJSON(t, `{"kind": "disk", "path": "/tmp/x"}`)); err != nil {
		t.Fatalf("disk branch must conform: %v", err)
	}
	if err := sch.Validate(mustJSON(t, `{"kind": "mem", "size": 64}`)); err != nil {
		t.Fatalf("mem branch must conform: %v", err)
	}
	if sch.Validate(mustJSON(t, `{"kind": "disk"}`)) == nil {
		t.Fatal("disk branch obligation must apply")
	}
	if sch.Validate(mustJSON(t, `"top-level-string"`)) == nil {
		t.Fatal("outer type must reject non-objects")
	}
}
