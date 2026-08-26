// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// Parsing Shell Programs
package atomic

import (
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

func TestParseBasicPositions(t *testing.T) {
	f := parse(t, "foo bar baz\n")
	wantPos(t, f.Pos(), 0, 1, 1, "File.Pos")
	wantPos(t, f.End(), 11, 1, 12, "File.End")
	ce := call(t, f, 0)
	wantEq(t, len(ce.Args), 3, "arg count")
	wantPos(t, ce.Args[0].Pos(), 0, 1, 1, "arg0.Pos")
	wantPos(t, ce.Args[0].End(), 3, 1, 4, "arg0.End")
	wantPos(t, ce.Args[1].Pos(), 4, 1, 5, "arg1.Pos")
	wantPos(t, ce.Args[2].Pos(), 8, 1, 9, "arg2.Pos")
	wantPos(t, ce.Args[2].End(), 11, 1, 12, "arg2.End")
}

func TestMultiLinePositions(t *testing.T) {
	f := parse(t, "foo\nbar baz\n")
	wantEq(t, len(f.Stmts), 2, "stmt count")
	wantPos(t, f.Stmts[1].Pos(), 4, 2, 1, "second stmt pos")
	ce, ok := f.Stmts[1].Cmd.(*syntax.CallExpr)
	if !ok {
		t.Fatalf("cmd %T", f.Stmts[1].Cmd)
	}
	wantPos(t, ce.Args[1].Pos(), 8, 2, 5, "second word on line 2")
}

func TestColumnsCountBytes(t *testing.T) {
	// "névé" is six bytes long in UTF-8.
	f := parse(t, "echo névé x\n")
	ce := call(t, f, 0)
	wantPos(t, ce.Args[1].Pos(), 5, 1, 6, "multibyte word pos")
	wantPos(t, ce.Args[2].Pos(), 12, 1, 13, "word after multibyte")
}

func TestFileNameRecorded(t *testing.T) {
	f := parseNamed(t, "foo\n", "my-script.sh")
	wantEq(t, f.Name, "my-script.sh", "File.Name")
}

func TestEmptyInput(t *testing.T) {
	f := parse(t, "")
	wantEq(t, len(f.Stmts), 0, "stmt count")
	wantEq(t, f.Name, "src.sh", "File.Name records the given name")
	wantEq(t, f.Pos().IsValid(), false, "empty File.Pos validity")
	wantEq(t, f.End().IsValid(), false, "empty File.End validity")
}

func TestParserReuse(t *testing.T) {
	p := syntax.NewParser()
	f1, err := p.Parse(strings.NewReader("foo\n"), "a.sh")
	if err != nil {
		t.Fatal(err)
	}
	f2, err := p.Parse(strings.NewReader("bar\n"), "b.sh")
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, f1.Name, "a.sh", "first name")
	wantEq(t, f2.Name, "b.sh", "second name")
	wantEq(t, f1.Stmts[0].Cmd.(*syntax.CallExpr).Args[0].Lit(), "foo", "first parse content")
	wantEq(t, f2.Stmts[0].Cmd.(*syntax.CallExpr).Args[0].Lit(), "bar", "second parse content")
}

func TestSemicolonPosition(t *testing.T) {
	f := parse(t, "foo; bar\n")
	wantEq(t, f.Stmts[0].Semicolon.IsValid(), true, "first stmt Semicolon validity")
	wantPos(t, f.Stmts[0].Semicolon, 3, 1, 4, "Semicolon pos")
	wantEq(t, f.Stmts[1].Semicolon.IsValid(), false, "second stmt Semicolon validity")
}

func TestBackgroundAndNegated(t *testing.T) {
	f := parse(t, "! foo &\nbar\n")
	st := f.Stmts[0]
	wantEq(t, st.Negated, true, "Negated")
	wantEq(t, st.Background, true, "Background")
	wantEq(t, st.Semicolon.IsValid(), true, "ampersand recorded in Semicolon")
	wantEq(t, f.Stmts[1].Background, false, "second stmt Background")
}

func TestCoprocessMksh(t *testing.T) {
	f := parse(t, "foo |& bar\n", syntax.Variant(syntax.LangMirBSDKorn))
	st := f.Stmts[0]
	wantEq(t, st.Coprocess, true, "Coprocess under mksh")
	if _, ok := st.Cmd.(*syntax.CallExpr); !ok {
		t.Fatalf("command is %T, want *syntax.CallExpr", st.Cmd)
	}
}

func TestPipeAllBash(t *testing.T) {
	f := parse(t, "foo |& bar\n")
	bc, ok := f.Stmts[0].Cmd.(*syntax.BinaryCmd)
	if !ok {
		t.Fatalf("command is %T, want *syntax.BinaryCmd", f.Stmts[0].Cmd)
	}
	wantEq(t, bc.Op, syntax.PipeAll, "operator")
}

func TestRedirsAttach(t *testing.T) {
	f := parse(t, "foo 2>err {fd}>named >&2 <in\n")
	st := f.Stmts[0]
	wantEq(t, len(st.Redirs), 4, "redir count")
	wantEq(t, st.Redirs[0].N.Value, "2", "fd literal")
	wantEq(t, st.Redirs[0].Op, syntax.RdrOut, "first op")
	wantEq(t, st.Redirs[0].Word.Lit(), "err", "first target")
	wantEq(t, st.Redirs[1].N.Value, "{fd}", "named fd")
	if st.Redirs[2].N != nil {
		t.Fatalf("dup redirect N = %v, want nil", st.Redirs[2].N)
	}
	wantEq(t, st.Redirs[2].Op, syntax.DplOut, "dup operator")
	wantEq(t, st.Redirs[2].Word.Lit(), "2", "dup target")
	wantEq(t, st.Redirs[3].Op, syntax.RdrIn, "input operator")
}

func TestCommentsDiscardedByDefault(t *testing.T) {
	f := parse(t, "foo # trailing\n")
	wantEq(t, len(f.Stmts[0].Comments), 0, "comments without KeepComments")
}

func TestKeepCommentsAttach(t *testing.T) {
	f := parse(t, "# leading\nfoo # trailing\n# only\n", syntax.KeepComments(true))
	st := f.Stmts[0]
	wantEq(t, len(st.Comments), 2, "stmt comment count")
	wantEq(t, st.Comments[0].Text, " leading", "leading comment text")
	wantPos(t, st.Comments[0].Hash, 0, 1, 1, "leading comment hash pos")
	wantEq(t, st.Comments[1].Text, " trailing", "trailing comment text")
	wantEq(t, len(f.Last), 1, "file Last count")
	wantEq(t, f.Last[0].Text, " only", "file Last text")
}

func TestKeepCommentsDirectApplication(t *testing.T) {
	p := syntax.NewParser()
	syntax.KeepComments(true)(p)
	f, err := p.Parse(strings.NewReader("foo # hi\n"), "")
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, len(f.Stmts[0].Comments), 1, "comment kept after direct option application")
	wantEq(t, f.Stmts[0].Comments[0].Text, " hi", "comment text")
}

func TestHeredocBody(t *testing.T) {
	f := parse(t, "cat <<EOF\nhello $x\nEOF\n")
	r := f.Stmts[0].Redirs[0]
	wantEq(t, r.Op, syntax.Hdoc, "operator")
	wantEq(t, r.Word.Lit(), "EOF", "delimiter word")
	wantEq(t, len(r.Hdoc.Parts), 3, "body part count")
	if _, ok := r.Hdoc.Parts[1].(*syntax.ParamExp); !ok {
		t.Fatalf("body part 1 is %T, want *syntax.ParamExp", r.Hdoc.Parts[1])
	}
	wantPos(t, r.Hdoc.Pos(), 10, 2, 1, "body pos")
}

func TestHeredocQuotedDelim(t *testing.T) {
	f := parse(t, "cat <<'EOF'\nhello $x\nEOF\n")
	r := f.Stmts[0].Redirs[0]
	wantEq(t, len(r.Hdoc.Parts), 1, "quoted-delimiter body parts")
	wantEq(t, r.Hdoc.Lit(), "hello $x\n", "body literal")
}

func TestDashHeredocKeepsTabs(t *testing.T) {
	f := parse(t, "cat <<-EOF\n\thello\n\tEOF\n")
	r := f.Stmts[0].Redirs[0]
	wantEq(t, r.Op, syntax.DashHdoc, "operator")
	wantEq(t, r.Hdoc.Lit(), "\thello\n\t", "tabs preserved in body")
}

func TestHereString(t *testing.T) {
	f := parse(t, "cat <<<word\n")
	r := f.Stmts[0].Redirs[0]
	wantEq(t, r.Op, syntax.WordHdoc, "operator")
	wantEq(t, r.Word.Lit(), "word", "word")
	if r.Hdoc != nil {
		t.Fatalf("Hdoc = %v, want nil", r.Hdoc)
	}
}

func TestUnclosedHeredocError(t *testing.T) {
	err := parseErr(t, "cat <<EOF\nhello\n")
	pe, ok := err.(syntax.ParseError)
	if !ok {
		t.Fatalf("error type %T, want syntax.ParseError", err)
	}
	wantEq(t, pe.Text, "unclosed here-document `EOF`", "error text")
	wantEq(t, pe.Incomplete, true, "Incomplete")
	wantEq(t, syntax.IsIncomplete(err), true, "IsIncomplete")
}

func TestStmtEndCoversHeredoc(t *testing.T) {
	src := "cat <<EOF\nhello $x\nEOF\n"
	f := parse(t, src)
	end := f.Stmts[0].End()
	wantEq(t, end.Line(), uint(3), "stmt end line reaches delimiter line")
	if end.Offset() <= 10 {
		t.Fatalf("stmt end offset %d does not extend past heredoc start", end.Offset())
	}
}

func TestParseErrorFormatWithName(t *testing.T) {
	_, err := syntax.NewParser().Parse(strings.NewReader("if true; then\n"), "src.sh")
	if err == nil {
		t.Fatal("expected error")
	}
	pe, ok := err.(syntax.ParseError)
	if !ok {
		t.Fatalf("error type %T, want syntax.ParseError", err)
	}
	wantEq(t, pe.Filename, "src.sh", "Filename")
	wantEq(t, pe.Text, "`then` must be followed by a statement list", "Text")
	wantPos(t, pe.Pos, 9, 1, 10, "error position")
	wantEq(t, err.Error(), "src.sh:1:10: `then` must be followed by a statement list", "rendered message")
}

func TestParseErrorFormatNoName(t *testing.T) {
	_, err := syntax.NewParser().Parse(strings.NewReader("foo ("), "")
	if err == nil {
		t.Fatal("expected error")
	}
	wantEq(t, err.Error(), "1:1: `foo(` must be followed by `)`", "message without name prefix")
}

func TestStopAtWord(t *testing.T) {
	f := parse(t, "foo bar $$ baz", syntax.StopAt("$$"))
	ce := call(t, f, 0)
	wantEq(t, len(ce.Args), 2, "args before stop word")
	wantEq(t, ce.Args[1].Lit(), "bar", "last arg")
}

func TestStopAtQuotedNotStopped(t *testing.T) {
	f := parse(t, "foo '$$' bar", syntax.StopAt("$$"))
	ce := call(t, f, 0)
	wantEq(t, len(ce.Args), 3, "quoted stop word does not stop")
}

func TestRecoverErrorsSubshell(t *testing.T) {
	p := syntax.NewParser(syntax.RecoverErrors(3))
	f, err := p.Parse(strings.NewReader("(foo |"), "")
	if err != nil {
		t.Fatalf("recovery failed: %v", err)
	}
	sub, ok := f.Stmts[0].Cmd.(*syntax.Subshell)
	if !ok {
		t.Fatalf("command is %T, want *syntax.Subshell", f.Stmts[0].Cmd)
	}
	wantEq(t, sub.Rparen.IsRecovered(), true, "Rparen recovered")
	wantEq(t, sub.Rparen.IsValid(), false, "recovered position not valid")
	bc, ok := sub.Stmts[0].Cmd.(*syntax.BinaryCmd)
	if !ok {
		t.Fatalf("inner command is %T, want *syntax.BinaryCmd", sub.Stmts[0].Cmd)
	}
	wantEq(t, bc.Y.Pos().IsRecovered(), true, "pipe right operand recovered")
}

func TestRecoverZeroFails(t *testing.T) {
	p := syntax.NewParser(syntax.RecoverErrors(0))
	_, err := p.Parse(strings.NewReader("(foo |"), "")
	if err == nil {
		t.Fatal("expected error with RecoverErrors(0)")
	}
	wantContains(t, err.Error(), "`|` must be followed by a statement", "error text")
}

func TestKeywordOutOfPlaceErrors(t *testing.T) {
	cases := []struct{ src, text string }{
		{"then", "`then` can only be used in an `if`"},
		{"fi", "`fi` can only be used to end an `if`"},
		{"done", "`done` can only be used to end a loop"},
		{"esac", "`esac` can only be used to end a `case`"},
		{"do", "`do` can only be used in a loop"},
		{"foo ;; bar", "`;;` can only be used in a case clause"},
		{"foo & ; bar", "`;` can only immediately follow a statement"},
	}
	for _, tc := range cases {
		err := parseErr(t, tc.src)
		pe, ok := err.(syntax.ParseError)
		if !ok {
			t.Fatalf("%q: error type %T, want syntax.ParseError", tc.src, err)
		}
		wantEq(t, pe.Text, tc.text, "error text for "+tc.src)
	}
}

func TestUnclosedConstructsIncomplete(t *testing.T) {
	cases := []struct{ src, text string }{
		{"echo 'foo", "reached EOF without closing quote `'`"},
		{`echo "foo`, "reached EOF without closing quote `\"`"},
		{"echo ${a", "reached EOF without matching `${` with `}`"},
		{"echo $((a", "reached EOF without matching `$((` with `))`"},
		{"echo $(foo", "reached EOF without matching `$(` with `)`"},
	}
	for _, tc := range cases {
		err := parseErr(t, tc.src)
		pe, ok := err.(syntax.ParseError)
		if !ok {
			t.Fatalf("%q: error type %T, want syntax.ParseError", tc.src, err)
		}
		wantEq(t, pe.Text, tc.text, "error text for "+tc.src)
		wantEq(t, pe.Incomplete, true, "Incomplete for "+tc.src)
	}
}
