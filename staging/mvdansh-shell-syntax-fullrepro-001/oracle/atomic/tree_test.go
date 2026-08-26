// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// The Syntax Tree
package atomic

import (
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

func TestWordLitConcatenation(t *testing.T) {
	f := parse(t, "foo 'q' foo${bar}x\n")
	ce := call(t, f, 0)
	wantEq(t, ce.Args[0].Lit(), "foo", "plain literal word")
	wantEq(t, ce.Args[1].Lit(), "", "quoted word has no Lit")
	wantEq(t, ce.Args[2].Lit(), "", "mixed word has no Lit")
}

func TestCallExprAssignsArgs(t *testing.T) {
	f := parse(t, "a=1 b=2 foo -x --y\n")
	ce := call(t, f, 0)
	wantEq(t, len(ce.Assigns), 2, "prefix assignments")
	wantEq(t, len(ce.Args), 3, "arguments")
	wantEq(t, ce.Assigns[0].Name.Value, "a", "first assign name")
	wantEq(t, ce.Assigns[0].Value.Lit(), "1", "first assign value")
}

func TestAssignForms(t *testing.T) {
	f := parse(t, "a+=b d= e\n")
	ce := call(t, f, 0)
	wantEq(t, len(ce.Assigns), 2, "assign count")
	wantEq(t, ce.Assigns[0].Append, true, "Append for +=")
	wantEq(t, ce.Assigns[0].Name.Value, "a", "append name")
	wantEq(t, ce.Assigns[1].Append, false, "plain assign")
	wantEq(t, ce.Assigns[1].Name.Value, "d", "empty-value name")
	if ce.Assigns[1].Value != nil {
		t.Fatalf("empty assignment Value = %v, want nil", ce.Assigns[1].Value)
	}
	wantEq(t, len(ce.Args), 1, "trailing word is an argument")
	wantEq(t, ce.Args[0].Lit(), "e", "argument value")
}

func TestStandaloneIndexedAssign(t *testing.T) {
	f := parse(t, "c[1]=x\n")
	ce := call(t, f, 0)
	a := ce.Assigns[0]
	wantEq(t, a.Name.Value, "c", "name")
	if a.Index == nil {
		t.Fatal("Index is nil")
	}
	w, ok := a.Index.(*syntax.Word)
	if !ok {
		t.Fatalf("Index is %T, want *syntax.Word", a.Index)
	}
	wantEq(t, w.Lit(), "1", "index expression")
	wantEq(t, a.Value.Lit(), "x", "value")
}

func TestInlineIndexedAssignError(t *testing.T) {
	err := parseErr(t, "c[1]=x foo\n")
	pe, ok := err.(syntax.ParseError)
	if !ok {
		t.Fatalf("error type %T, want syntax.ParseError", err)
	}
	wantEq(t, pe.Text, "inline variables cannot be arrays", "error text")
}

func TestArrayExpr(t *testing.T) {
	f := parse(t, "a=(1 2 [k]=v)\n")
	ce := call(t, f, 0)
	arr := ce.Assigns[0].Array
	if arr == nil {
		t.Fatal("Array is nil")
	}
	wantEq(t, len(arr.Elems), 3, "element count")
	wantEq(t, arr.Elems[0].Value.Lit(), "1", "first element")
	if arr.Elems[2].Index == nil {
		t.Fatal("third element Index is nil")
	}
	wantEq(t, arr.Elems[2].Value.Lit(), "v", "keyed element value")
	wantEq(t, arr.Lparen.IsValid() && arr.Rparen.IsValid(), true, "paren positions valid")
}

func TestSglQuotedDollar(t *testing.T) {
	f := parse(t, `echo $'a\tb' 'plain'`)
	ce := call(t, f, 0)
	sq, ok := ce.Args[1].Parts[0].(*syntax.SglQuoted)
	if !ok {
		t.Fatalf("part is %T, want *syntax.SglQuoted", ce.Args[1].Parts[0])
	}
	wantEq(t, sq.Dollar, true, "Dollar for $'...'")
	wantEq(t, sq.Value, `a\tb`, "escapes preserved verbatim")
	sq2 := ce.Args[2].Parts[0].(*syntax.SglQuoted)
	wantEq(t, sq2.Dollar, false, "plain single quotes")
	wantEq(t, sq2.Value, "plain", "plain value")
}

func TestDblQuotedDollarAndParts(t *testing.T) {
	f := parse(t, `echo $"loc" "d$x"`)
	ce := call(t, f, 0)
	dq := ce.Args[1].Parts[0].(*syntax.DblQuoted)
	wantEq(t, dq.Dollar, true, "Dollar for $\"...\"")
	dq2 := ce.Args[2].Parts[0].(*syntax.DblQuoted)
	wantEq(t, dq2.Dollar, false, "plain double quotes")
	wantEq(t, len(dq2.Parts), 2, "inner parts")
	if _, ok := dq2.Parts[1].(*syntax.ParamExp); !ok {
		t.Fatalf("part 1 is %T, want *syntax.ParamExp", dq2.Parts[1])
	}
	wantPos(t, dq2.Left, 12, 1, 13, "Left quote pos")
	wantPos(t, dq2.Right, 16, 1, 17, "Right quote pos")
}

func TestCmdSubstBackquotes(t *testing.T) {
	f := parse(t, "echo `foo`\n")
	ce := call(t, f, 0)
	cs, ok := ce.Args[1].Parts[0].(*syntax.CmdSubst)
	if !ok {
		t.Fatalf("part is %T, want *syntax.CmdSubst", ce.Args[1].Parts[0])
	}
	wantEq(t, cs.Backquotes, true, "Backquotes")
	wantEq(t, len(cs.Stmts), 1, "inner statements")
	f2 := parse(t, "echo $(foo)\n")
	cs2 := call(t, f2, 0).Args[1].Parts[0].(*syntax.CmdSubst)
	wantEq(t, cs2.Backquotes, false, "dollar form")
}

func TestMkshCmdSubstForms(t *testing.T) {
	f := parse(t, "x=${ foo;}\n", syntax.Variant(syntax.LangMirBSDKorn))
	cs := call(t, f, 0).Assigns[0].Value.Parts[0].(*syntax.CmdSubst)
	wantEq(t, cs.TempFile, true, "TempFile for ${ foo;}")
	wantEq(t, cs.ReplyVar, false, "ReplyVar unset")
	f2 := parse(t, "x=${|foo;}\n", syntax.Variant(syntax.LangMirBSDKorn))
	cs2 := call(t, f2, 0).Assigns[0].Value.Parts[0].(*syntax.CmdSubst)
	wantEq(t, cs2.ReplyVar, true, "ReplyVar for ${|foo;}")
	wantEq(t, cs2.TempFile, false, "TempFile unset")
}

func TestArithmExpBracket(t *testing.T) {
	f := parse(t, "echo $((x)) $[y]\n")
	ce := call(t, f, 0)
	ae := ce.Args[1].Parts[0].(*syntax.ArithmExp)
	wantEq(t, ae.Bracket, false, "modern form")
	ae2 := ce.Args[2].Parts[0].(*syntax.ArithmExp)
	wantEq(t, ae2.Bracket, true, "deprecated $[...] form")
}

func TestProcSubst(t *testing.T) {
	f := parse(t, "diff <(a) >(b)\n")
	ce := call(t, f, 0)
	ps := ce.Args[1].Parts[0].(*syntax.ProcSubst)
	wantEq(t, ps.Op, syntax.CmdIn, "input op")
	wantEq(t, len(ps.Stmts), 1, "inner statements")
	ps2 := ce.Args[2].Parts[0].(*syntax.ProcSubst)
	wantEq(t, ps2.Op, syntax.CmdOut, "output op")
}

func TestExtGlobNode(t *testing.T) {
	f := parse(t, "echo @(a|b) ?(c)\n")
	ce := call(t, f, 0)
	eg := ce.Args[1].Parts[0].(*syntax.ExtGlob)
	wantEq(t, eg.Op, syntax.GlobOne, "operator")
	wantEq(t, eg.Pattern.Value, "a|b", "raw pattern")
	eg2 := ce.Args[2].Parts[0].(*syntax.ExtGlob)
	wantEq(t, eg2.Op, syntax.GlobZeroOrOne, "zero-or-one operator")
}

func paramExp(t *testing.T, src string, opts ...syntax.ParserOption) *syntax.ParamExp {
	t.Helper()
	f := parse(t, "echo "+src, opts...)
	pe, ok := call(t, f, 0).Args[1].Parts[0].(*syntax.ParamExp)
	if !ok {
		t.Fatalf("%s: part is %T, want *syntax.ParamExp", src, call(t, f, 0).Args[1].Parts[0])
	}
	return pe
}

func TestParamExpBasics(t *testing.T) {
	pe := paramExp(t, "$a")
	wantEq(t, pe.Short, true, "Short for $a")
	wantEq(t, pe.Param.Value, "a", "param name")
	pe2 := paramExp(t, "${a}")
	wantEq(t, pe2.Short, false, "braced form")
	pe3 := paramExp(t, "${#a}")
	wantEq(t, pe3.Length, true, "Length for ${#a}")
	pe4 := paramExp(t, "${!a}")
	wantEq(t, pe4.Excl, true, "Excl for ${!a}")
	pe5 := paramExp(t, "${%a}", syntax.Variant(syntax.LangMirBSDKorn))
	wantEq(t, pe5.Width, true, "Width for mksh ${%a}")
}

func TestParamExpExpansionOp(t *testing.T) {
	pe := paramExp(t, "${a:-def}")
	if pe.Exp == nil {
		t.Fatal("Exp is nil")
	}
	wantEq(t, pe.Exp.Op, syntax.DefaultUnsetOrNull, "operator")
	wantEq(t, pe.Exp.Word.Lit(), "def", "operand word")
	pe2 := paramExp(t, "${a##pat}")
	wantEq(t, pe2.Exp.Op, syntax.RemLargePrefix, "remove-prefix operator")
	pe3 := paramExp(t, "${a^^}")
	wantEq(t, pe3.Exp.Op, syntax.UpperAll, "upper-all operator")
	if pe3.Exp.Word != nil {
		t.Fatalf("UpperAll word = %v, want nil", pe3.Exp.Word)
	}
}

func TestParamExpReplace(t *testing.T) {
	pe := paramExp(t, "${a/x/y}")
	if pe.Repl == nil {
		t.Fatal("Repl is nil")
	}
	wantEq(t, pe.Repl.All, false, "single replace")
	wantEq(t, pe.Repl.Orig.Lit(), "x", "orig")
	wantEq(t, pe.Repl.With.Lit(), "y", "with")
	pe2 := paramExp(t, "${a//x/y}")
	wantEq(t, pe2.Repl.All, true, "replace all")
}

func TestParamExpSlice(t *testing.T) {
	pe := paramExp(t, "${a:1:2}")
	if pe.Slice == nil {
		t.Fatal("Slice is nil")
	}
	off, ok := pe.Slice.Offset.(*syntax.Word)
	if !ok {
		t.Fatalf("Offset is %T, want *syntax.Word", pe.Slice.Offset)
	}
	wantEq(t, off.Lit(), "1", "offset")
	wantEq(t, pe.Slice.Length.(*syntax.Word).Lit(), "2", "length")
}

func TestParamExpNames(t *testing.T) {
	pe := paramExp(t, "${!pre*}")
	wantEq(t, pe.Excl, true, "Excl set")
	wantEq(t, pe.Names, syntax.NamesPrefix, "star form")
	pe2 := paramExp(t, "${!pre@}")
	wantEq(t, pe2.Names, syntax.NamesPrefixWords, "at form")
}

func TestParamExpIndex(t *testing.T) {
	pe := paramExp(t, "${a[3]}")
	if pe.Index == nil {
		t.Fatal("Index is nil")
	}
	wantEq(t, pe.Index.(*syntax.Word).Lit(), "3", "index word")
}

func TestParamExpBadOpError(t *testing.T) {
	err := parseErr(t, "echo ${a!}")
	pe, ok := err.(syntax.ParseError)
	if !ok {
		t.Fatalf("error type %T, want syntax.ParseError", err)
	}
	wantEq(t, pe.Text, "not a valid parameter expansion operator: `!`", "error text")
}

func TestIfElifElseChain(t *testing.T) {
	f := parse(t, "if a; then b; elif c; then d; else e; fi")
	ic, ok := f.Stmts[0].Cmd.(*syntax.IfClause)
	if !ok {
		t.Fatalf("command is %T, want *syntax.IfClause", f.Stmts[0].Cmd)
	}
	wantPos(t, ic.Position, 0, 1, 1, "if position")
	wantEq(t, ic.ThenPos.IsValid(), true, "if ThenPos")
	wantPos(t, ic.FiPos, 38, 1, 39, "FiPos")
	el := ic.Else
	if el == nil {
		t.Fatal("Else is nil")
	}
	wantPos(t, el.Position, 14, 1, 15, "elif position")
	wantEq(t, el.ThenPos.IsValid(), true, "elif ThenPos valid")
	wantEq(t, el.FiPos, ic.FiPos, "FiPos shared by elif")
	el2 := el.Else
	if el2 == nil {
		t.Fatal("final else is nil")
	}
	wantEq(t, el2.ThenPos.IsValid(), false, "else has no ThenPos")
	wantEq(t, el2.FiPos, ic.FiPos, "FiPos shared by else")
	if el2.Else != nil {
		t.Fatal("chain continues past else")
	}
}

func TestWhileUntil(t *testing.T) {
	f := parse(t, "while a; do b; done\nuntil c; do d; done\n")
	wc := f.Stmts[0].Cmd.(*syntax.WhileClause)
	wantEq(t, wc.Until, false, "while")
	wantEq(t, len(wc.Cond), 1, "cond statements")
	wantEq(t, len(wc.Do), 1, "do statements")
	uc := f.Stmts[1].Cmd.(*syntax.WhileClause)
	wantEq(t, uc.Until, true, "until")
}

func TestForWordIter(t *testing.T) {
	f := parse(t, "for x in a b; do foo; done")
	fc := f.Stmts[0].Cmd.(*syntax.ForClause)
	wantEq(t, fc.Select, false, "plain for")
	wi := fc.Loop.(*syntax.WordIter)
	wantEq(t, wi.Name.Value, "x", "variable name")
	wantEq(t, wi.InPos.IsValid(), true, "in present")
	wantEq(t, len(wi.Items), 2, "item count")
	// Missing "in" ranges over positional parameters.
	f2 := parse(t, "for x; do foo; done")
	wi2 := f2.Stmts[0].Cmd.(*syntax.ForClause).Loop.(*syntax.WordIter)
	wantEq(t, wi2.InPos.IsValid(), false, "missing in token")
	wantEq(t, len(wi2.Items), 0, "no items")
	// Present but empty "in" list is distinct.
	f3 := parse(t, "for x in; do foo; done")
	wi3 := f3.Stmts[0].Cmd.(*syntax.ForClause).Loop.(*syntax.WordIter)
	wantEq(t, wi3.InPos.IsValid(), true, "empty in list keeps token position")
	wantEq(t, len(wi3.Items), 0, "empty items")
}

func TestCStyleLoop(t *testing.T) {
	f := parse(t, "for ((i=0; i<3; i++)); do foo; done")
	cl := f.Stmts[0].Cmd.(*syntax.ForClause).Loop.(*syntax.CStyleLoop)
	if _, ok := cl.Init.(*syntax.BinaryArithm); !ok {
		t.Fatalf("Init is %T, want *syntax.BinaryArithm", cl.Init)
	}
	if _, ok := cl.Cond.(*syntax.BinaryArithm); !ok {
		t.Fatalf("Cond is %T, want *syntax.BinaryArithm", cl.Cond)
	}
	ua, ok := cl.Post.(*syntax.UnaryArithm)
	if !ok {
		t.Fatalf("Post is %T, want *syntax.UnaryArithm", cl.Post)
	}
	wantEq(t, ua.Op, syntax.Inc, "post operator")
	wantEq(t, ua.Post, true, "postfix increment")
}

func TestSelectClause(t *testing.T) {
	f := parse(t, "select x in a b; do foo; done")
	fc := f.Stmts[0].Cmd.(*syntax.ForClause)
	wantEq(t, fc.Select, true, "Select flag")
	if _, ok := fc.Loop.(*syntax.WordIter); !ok {
		t.Fatalf("Loop is %T, want *syntax.WordIter", fc.Loop)
	}
}

func TestCaseItems(t *testing.T) {
	f := parse(t, "case x in\na) f1 ;;\nb) f2 ;&\nc) f3 ;;&\nd) f4\nesac\n")
	cc := f.Stmts[0].Cmd.(*syntax.CaseClause)
	wantEq(t, cc.Word.Lit(), "x", "selector")
	wantEq(t, len(cc.Items), 4, "item count")
	wantEq(t, cc.Items[0].Op, syntax.Break, "double-semicolon")
	wantEq(t, cc.Items[1].Op, syntax.Fallthrough, "fallthrough")
	wantEq(t, cc.Items[2].Op, syntax.Resume, "resume")
	wantEq(t, cc.Items[0].OpPos.IsValid(), true, "explicit operator position")
	wantEq(t, cc.Items[3].OpPos.IsValid(), false, "esac-closed item has no OpPos")
	wantEq(t, cc.Items[0].Patterns[0].Lit(), "a", "pattern")
}

func TestBlockSubshell(t *testing.T) {
	f := parse(t, "{ foo; bar; }\n(baz)\n")
	bl := f.Stmts[0].Cmd.(*syntax.Block)
	wantEq(t, len(bl.Stmts), 2, "block statements")
	wantEq(t, bl.Lbrace.IsValid() && bl.Rbrace.IsValid(), true, "brace positions")
	sub := f.Stmts[1].Cmd.(*syntax.Subshell)
	wantEq(t, len(sub.Stmts), 1, "subshell statements")
}

func TestBinaryCmdOps(t *testing.T) {
	f := parse(t, "a && b || c\n")
	top := f.Stmts[0].Cmd.(*syntax.BinaryCmd)
	wantEq(t, top.Op, syntax.OrStmt, "top operator is the last one")
	left := top.X.Cmd.(*syntax.BinaryCmd)
	wantEq(t, left.Op, syntax.AndStmt, "left-nested and")
	f2 := parse(t, "a | b\n")
	wantEq(t, f2.Stmts[0].Cmd.(*syntax.BinaryCmd).Op, syntax.Pipe, "pipe")
}

func TestFuncDeclForms(t *testing.T) {
	cases := []struct {
		src    string
		rsrv   bool
		parens bool
	}{
		{"f() { x; }", false, true},
		{"function f { x; }", true, false},
		{"function f() { x; }", true, true},
	}
	for _, tc := range cases {
		f := parse(t, tc.src)
		fd, ok := f.Stmts[0].Cmd.(*syntax.FuncDecl)
		if !ok {
			t.Fatalf("%q: command is %T, want *syntax.FuncDecl", tc.src, f.Stmts[0].Cmd)
		}
		wantEq(t, fd.RsrvWord, tc.rsrv, "RsrvWord for "+tc.src)
		wantEq(t, fd.Parens, tc.parens, "Parens for "+tc.src)
		wantEq(t, fd.Name.Value, "f", "name for "+tc.src)
	}
	f := parse(t, "f() ( x )")
	fd := f.Stmts[0].Cmd.(*syntax.FuncDecl)
	if _, ok := fd.Body.Cmd.(*syntax.Subshell); !ok {
		t.Fatalf("body is %T, want *syntax.Subshell", fd.Body.Cmd)
	}
}

func TestDeclClause(t *testing.T) {
	f := parse(t, "declare -a x=(1 2) y\n")
	dc := f.Stmts[0].Cmd.(*syntax.DeclClause)
	wantEq(t, dc.Variant.Value, "declare", "variant")
	wantEq(t, len(dc.Args), 3, "arg count")
	wantEq(t, dc.Args[0].Naked, true, "option arg is naked")
	if dc.Args[0].Name != nil {
		t.Fatalf("option arg Name = %v, want nil", dc.Args[0].Name)
	}
	wantEq(t, dc.Args[0].Value.Lit(), "-a", "option text")
	wantEq(t, dc.Args[1].Name.Value, "x", "array assign name")
	if dc.Args[1].Array == nil {
		t.Fatal("array assign has nil Array")
	}
	wantEq(t, dc.Args[2].Naked, true, "bare name is naked")
	wantEq(t, dc.Args[2].Name.Value, "y", "bare name")
	f2 := parse(t, "local v=1\n")
	wantEq(t, f2.Stmts[0].Cmd.(*syntax.DeclClause).Variant.Value, "local", "local variant")
}

func TestLetClause(t *testing.T) {
	f := parse(t, "let x=1 y++\n")
	lc := f.Stmts[0].Cmd.(*syntax.LetClause)
	wantEq(t, len(lc.Exprs), 2, "expression count")
	if _, ok := lc.Exprs[0].(*syntax.BinaryArithm); !ok {
		t.Fatalf("expr 0 is %T, want *syntax.BinaryArithm", lc.Exprs[0])
	}
	if _, ok := lc.Exprs[1].(*syntax.UnaryArithm); !ok {
		t.Fatalf("expr 1 is %T, want *syntax.UnaryArithm", lc.Exprs[1])
	}
}

func TestTimeClause(t *testing.T) {
	f := parse(t, "time -p foo\n")
	tc := f.Stmts[0].Cmd.(*syntax.TimeClause)
	wantEq(t, tc.PosixFormat, true, "PosixFormat for -p")
	if _, ok := tc.Stmt.Cmd.(*syntax.CallExpr); !ok {
		t.Fatalf("timed stmt is %T, want *syntax.CallExpr", tc.Stmt.Cmd)
	}
	f2 := parse(t, "time foo\n")
	wantEq(t, f2.Stmts[0].Cmd.(*syntax.TimeClause).PosixFormat, false, "plain time")
}

func TestCoprocClause(t *testing.T) {
	f := parse(t, "coproc foo bar\n")
	cp := f.Stmts[0].Cmd.(*syntax.CoprocClause)
	if cp.Name != nil {
		t.Fatalf("Name = %v, want nil for unnamed coproc", cp.Name)
	}
	ce := cp.Stmt.Cmd.(*syntax.CallExpr)
	wantEq(t, len(ce.Args), 2, "whole tail is the command")
	f2 := parse(t, "coproc NAME { foo; }\n")
	cp2 := f2.Stmts[0].Cmd.(*syntax.CoprocClause)
	wantEq(t, cp2.Name.Lit(), "NAME", "named coproc")
	if _, ok := cp2.Stmt.Cmd.(*syntax.Block); !ok {
		t.Fatalf("body is %T, want *syntax.Block", cp2.Stmt.Cmd)
	}
}

func TestTestClauseRightAssociative(t *testing.T) {
	f := parse(t, "[[ a == a && b == b || c == c ]]")
	tc := f.Stmts[0].Cmd.(*syntax.TestClause)
	top := tc.X.(*syntax.BinaryTest)
	wantEq(t, top.Op, syntax.AndTest, "top operator")
	right := top.Y.(*syntax.BinaryTest)
	wantEq(t, right.Op, syntax.OrTest, "or nested on the right")
	f2 := parse(t, "[[ a == a || b == b && c == c ]]")
	top2 := f2.Stmts[0].Cmd.(*syntax.TestClause).X.(*syntax.BinaryTest)
	wantEq(t, top2.Op, syntax.OrTest, "top or")
	wantEq(t, top2.Y.(*syntax.BinaryTest).Op, syntax.AndTest, "and nested on the right")
}

func TestTestClauseOperators(t *testing.T) {
	f := parse(t, "[[ -n $x && ( $y =~ ^b ) ]]")
	tc := f.Stmts[0].Cmd.(*syntax.TestClause)
	top := tc.X.(*syntax.BinaryTest)
	ut := top.X.(*syntax.UnaryTest)
	wantEq(t, ut.Op, syntax.TsNempStr, "unary -n")
	pt := top.Y.(*syntax.ParenTest)
	bt := pt.X.(*syntax.BinaryTest)
	wantEq(t, bt.Op, syntax.TsReMatch, "regex match operator")
	f2 := parse(t, "[[ a = b ]]")
	wantEq(t, f2.Stmts[0].Cmd.(*syntax.TestClause).X.(*syntax.BinaryTest).Op, syntax.TsMatchShort, "single equals")
}

func TestArithmCmdAndTernary(t *testing.T) {
	f := parse(t, "((x > 3))")
	ac := f.Stmts[0].Cmd.(*syntax.ArithmCmd)
	ba := ac.X.(*syntax.BinaryArithm)
	wantEq(t, ba.Op, syntax.Gtr, "greater-than")
	f2 := parse(t, "echo $((a > 1 ? b : c))")
	ae := call(t, f2, 0).Args[1].Parts[0].(*syntax.ArithmExp)
	tern := ae.X.(*syntax.BinaryArithm)
	wantEq(t, tern.Op, syntax.TernQuest, "ternary question")
	inner := tern.Y.(*syntax.BinaryArithm)
	wantEq(t, inner.Op, syntax.TernColon, "ternary colon nested in Y")
}

func TestArithmAssignRequiresName(t *testing.T) {
	f := parse(t, "echo $((x += 2))")
	ae := call(t, f, 0).Args[1].Parts[0].(*syntax.ArithmExp)
	asn := ae.X.(*syntax.BinaryArithm)
	wantEq(t, asn.Op, syntax.AddAssgn, "compound assign operator")
	err := parseErr(t, "echo $((1 += 2))")
	pe := err.(syntax.ParseError)
	wantEq(t, pe.Text, "`+=` must follow a name", "error text")
}

func TestEscapedNewlineLit(t *testing.T) {
	f := parse(t, "echo fo\\\no\n")
	ce := call(t, f, 0)
	l := ce.Args[1].Parts[0].(*syntax.Lit)
	wantEq(t, l.Value, "foo", "joined value")
	wantPos(t, l.ValuePos, 5, 1, 6, "ValuePos")
	wantEq(t, l.ValueEnd.Line(), uint(2), "ValueEnd crosses the escaped newline")
	wantEq(t, ce.Args[1].Lit(), "foo", "word literal")
}

func TestValidName(t *testing.T) {
	cases := []struct {
		in   string
		want bool
	}{
		{"foo", true}, {"_foo", true}, {"foo1", true},
		{"1foo", false}, {"foo-bar", false}, {"", false},
	}
	for _, tc := range cases {
		wantEq(t, syntax.ValidName(tc.in), tc.want, "ValidName("+tc.in+")")
	}
}

func TestIsKeyword(t *testing.T) {
	for _, kw := range []string{"if", "then", "done", "function", "select", "coproc", "time", "[[", "!"} {
		wantEq(t, syntax.IsKeyword(kw), true, "IsKeyword("+kw+")")
	}
	for _, w := range []string{"foo", "echo", "ls"} {
		wantEq(t, syntax.IsKeyword(w), false, "IsKeyword("+w+")")
	}
}
