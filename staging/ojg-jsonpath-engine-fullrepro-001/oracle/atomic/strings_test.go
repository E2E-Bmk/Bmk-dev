package atomic

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Canonical String Forms — dot-preferred String rendering.
func TestStringDotPreferred(t *testing.T) {
	eq(t, "plain chain", "$.a.b", mustParse(t, "$.a.b").String())
	eq(t, "index", "$.a[0].b", mustParse(t, "$.a[0].b").String())
	eq(t, "bracket input to dot", "$['a']['b']", mustParse(t, "$['a']['b']").BracketString())
	eq(t, "dot output for simple keys", "a.b", mustParse(t, "['a']['b']").String())
}

// Verifies: Canonical String Forms — BracketString rendering.
func TestBracketStringRendering(t *testing.T) {
	eq(t, "children", "$['a']['b']", mustParse(t, "$.a.b").BracketString())
	eq(t, "wildcard", "$[*]", mustParse(t, "$.*").BracketString())
	eq(t, "descent", "$[..]['b']", mustParse(t, "$..b").BracketString())
	eq(t, "index kept", "$['a'][0]", mustParse(t, "$.a[0]").BracketString())
	eq(t, "relative", "['a'][*][1:3]", jp.C("a").W().S(1, 3).BracketString())
}

// Verifies: Canonical String Forms — bracket-form descent is output-only.
func TestBracketDescentDoesNotReparse(t *testing.T) {
	x := mustParse(t, "$..b")
	bs := x.BracketString()
	eq(t, "bracket text", "$[..]['b']", bs)
	_, err := jp.ParseString(bs)
	wantErr(t, "reparse bracket descent", err, "parse error at 3 in $[..]['b']")
}

// Verifies: Canonical String Forms — descent collapse before brackets.
func TestDescentCollapseBeforeBracket(t *testing.T) {
	x := mustParse(t, "$..[1]")
	eq(t, "fragments", 3, len(x))
	eq(t, "collapsed String", "$.[1]", x.String())
	eq(t, "bracket form", "$[..][1]", x.BracketString())
	_, err := jp.ParseString("$.[1]")
	wantErr(t, "collapsed form reparse", err,
		"an expression fragment can not start with a '[' at 4 in $.[1]")
}

// Verifies: Canonical String Forms — Append with and without brackets.
func TestAppendBuffer(t *testing.T) {
	x := jp.R().C("a").N(0)
	eq(t, "plain append", "$.a[0]", string(x.Append(nil)))
	eq(t, "bracket append", "$['a'][0]", string(x.Append(nil, true)))
	eq(t, "prefix preserved", "path: $.a[0]", string(x.Append([]byte("path: "))))
}

// Verifies: Canonical String Forms — AppendString quoting and escapes.
func TestAppendStringEscapes(t *testing.T) {
	eq(t, "plain", "'abc'", string(jp.AppendString(nil, "abc", '\'')))
	eq(t, "embedded quotes", `'a\'b\"c'`, string(jp.AppendString(nil, `a'b"c`, '\'')))
	eq(t, "controls", `"a\tb\nc\u0002"`, string(jp.AppendString(nil, "a\tb\nc\x02", '"')))
	eq(t, "unicode passthrough", `"日本"`, string(jp.AppendString(nil, "日本", '"')))
}

// Verifies: Canonical String Forms — Normal classification.
func TestNormalClassification(t *testing.T) {
	for src, want := range map[string]bool{
		"$.a.b":     true,
		"$[1]":      true,
		"@.a":       true,
		"$[-1]":     true,
		"a.*":       false,
		"$..b":      false,
		"$[1:3]":    false,
		"$[1,2]":    false,
		"$[?(@.x)]": false,
	} {
		eq(t, "Normal "+src, want, mustParse(t, src).Normal())
	}
	// empty expression is normal, and built normal paths agree
	eq(t, "empty", true, mustParse(t, "").Normal())
	eq(t, "built", true, jp.R().C("a").N(1).Normal())
}

// Verifies: Canonical String Forms — canonical form is a parse fixpoint.
func TestStringParseFixpoint(t *testing.T) {
	for _, src := range []string{
		"$.a.b", "a[*].b", "$..b", "$[1:3:2]", "$['a',2]", "$[?(@.x == 1)].b",
		"$['a-b'][0]", "@.x.*",
	} {
		once := mustParse(t, src).String()
		twice := mustParse(t, once).String()
		eq(t, "fixpoint "+src, once, twice)
	}
	// a normalizing case anchors the canonicalization
	eq(t, "normalized", "$[?(@.x == 1)]", mustParse(t, "$[?(@.x==1)]").String())
}

// Verifies: Canonical String Forms — number rendering in fragments.
func TestNumberRendering(t *testing.T) {
	eq(t, "big index", "[1234567]", jp.N(1234567).String())
	eq(t, "negative index", "[-1]", jp.N(-1).String())
	eq(t, "filter float drops zero", "[?(@.x == 1)]", mustParse(t, "[?(@.x == 1.0)]").String())
	eq(t, "filter float kept", "[?(@.x == -1.5)]", mustParse(t, "[?(@.x == -1.5)]").String())
}
