// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"strings"
	"testing"

	"github.com/antchfx/xpath"
)

func TestMalformedExpressionError(t *testing.T) {
	for _, expr := range []string{"///", "book[", "@", "child::", "1 +", "1 = ", ")"} {
		wantCompileErr(t, expr, "expression must evaluate to a node-set")
	}
}

func TestUnknownFunctionError(t *testing.T) {
	wantCompileErr(t, "unknownfunc()", "not yet support this function unknownfunc()")
}

func TestUnsupportedStandardFunctions(t *testing.T) {
	wantCompileErr(t, "id('b1')", "not yet support this function id()")
	wantCompileErr(t, "lang('en')", "not yet support this function lang()")
	wantCompileErr(t, "current()", "not yet support this function current()")
	wantCompileErr(t, "key('k','v')", "not yet support this function key()")
	wantCompileErr(t, "document('')", "not yet support this function document()")
}

func TestUnknownAxisError(t *testing.T) {
	wantCompileErr(t, "nosuchaxis::node()", "unknown axe type: nosuchaxis")
}

func TestVariableReferenceError(t *testing.T) {
	wantCompileErr(t, "$undeclared",
		"undeclared variable in XPath expression: $undeclared")
}

func TestNamespaceAxisUnsupported(t *testing.T) {
	wantCompileErr(t, "namespace::*",
		"undeclared variable in XPath expression: namespace::*")
	wantCompileErr(t, "//book/namespace::*",
		"undeclared variable in XPath expression: //book/namespace::*")
}

func TestUnclosedStringLiteralError(t *testing.T) {
	wantCompileErr(t, "'unclosed", "xpath: scanString got unclosed string")
}

func TestNodeSetFunctionArityErrors(t *testing.T) {
	wantCompileErr(t, "count()",
		"xpath: count(node-sets) function must with have parameters node-sets")
	wantCompileErr(t, "sum()",
		"xpath: sum(node-sets) function must with have parameters node-sets")
	wantCompileErr(t, "reverse()",
		"xpath: reverse(node-sets) function must with have parameters node-sets")
}

func TestNumericFunctionArityErrors(t *testing.T) {
	// floor, ceiling, and round all report the ceiling message.
	for _, expr := range []string{"floor()", "ceiling()", "round()"} {
		wantCompileErr(t, expr,
			"xpath: ceiling(node-sets) function must with have parameters node-sets")
	}
	wantCompileErr(t, "number('a','b')",
		"xpath: number function must have at most one parameter")
}

func TestStringFunctionArityErrors(t *testing.T) {
	wantCompileErr(t, "substring('a')",
		"xpath: substring function must have at least two parameter")
	// substring-before and substring-after share the substring-before message.
	wantCompileErr(t, "substring-before('a')",
		"xpath: substring-before function must have two parameters")
	wantCompileErr(t, "substring-after('a')",
		"xpath: substring-before function must have two parameters")
	wantCompileErr(t, "translate('a','b')",
		"xpath: translate function must have three parameters")
	wantCompileErr(t, "translate('a','b','c','d')",
		"xpath: translate function must have three parameters")
	wantCompileErr(t, "concat('a')",
		"xpath: concat() must have at least two arguments")
	wantCompileErr(t, "string-length()",
		"xpath: string-length function must have at least one parameter")
	wantCompileErr(t, "string('a','b')",
		"xpath: string function must have at most one parameter")
	wantCompileErr(t, "name('a','b')",
		"xpath: name function must have at most one parameter")
	wantCompileErr(t, "not()",
		"xpath: not function must have at least one parameter")
	wantCompileErr(t, "matches('a')",
		"xpath: matches function must have two parameters")
	wantCompileErr(t, "replace('a','b')",
		"xpath: replace function must have three parameters")
	wantCompileErr(t, "string-join(//book)",
		"xpath: string-join(node-sets, separator) function requires node-set and argument")
}

func TestAffixArityErrorsAreNonNil(t *testing.T) {
	for _, expr := range []string{"starts-with('a')", "ends-with('a')", "contains('a')"} {
		if _, err := xpath.Compile(expr); err == nil {
			t.Fatalf("Compile(%q) succeeded, want an error", expr)
		}
	}
	// Guard: correct arity compiles.
	compileOK(t, "starts-with('a', 'b')")
}

func TestMatchesInvalidPatternCompileError(t *testing.T) {
	if _, err := xpath.Compile("matches('a', '[')"); err == nil {
		t.Fatal("matches with an invalid literal pattern compiled")
	}
	// Guard: a valid pattern compiles.
	compileOK(t, "matches('a', '[a-z]')")
}

func TestReplaceInvalidPatternPanicsOnEvaluate(t *testing.T) {
	doc := bookstore()
	e := compileOK(t, "replace('a', '[', 'x')")
	defer func() {
		if recover() == nil {
			t.Fatal("evaluating replace with an invalid pattern did not panic")
		}
	}()
	e.Evaluate(newNav(doc))
}

func TestSumOverNonNumericStringPanics(t *testing.T) {
	doc := bookstore()
	e := compileOK(t, "sum('abc')")
	defer func() {
		r := recover()
		if r == nil {
			t.Fatal("sum over a non-numeric string did not panic")
		}
		err, ok := r.(error)
		if !ok {
			t.Fatalf("panic value %#v is not an error", r)
		}
		if !strings.Contains(err.Error(),
			"sum() function argument type must be a node-set or number") {
			t.Fatalf("panic message = %q", err.Error())
		}
	}()
	e.Evaluate(newNav(doc))
}
