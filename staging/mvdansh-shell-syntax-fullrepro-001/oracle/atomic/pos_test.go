// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// The Syntax Tree — positions
package atomic

import (
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

func TestNewPosAccessors(t *testing.T) {
	p := syntax.NewPos(5, 2, 3)
	wantEq(t, p.Offset(), uint(5), "Offset")
	wantEq(t, p.Line(), uint(2), "Line")
	wantEq(t, p.Col(), uint(3), "Col")
	wantEq(t, p.IsValid(), true, "IsValid")
	wantEq(t, p.IsRecovered(), false, "IsRecovered")
}

func TestZeroLinePosInvalid(t *testing.T) {
	p := syntax.NewPos(0, 0, 0)
	wantEq(t, p.IsValid(), false, "zero position validity")
	var zero syntax.Pos
	wantEq(t, zero.IsValid(), false, "zero value validity")
	wantEq(t, zero.Offset(), uint(0), "invalid Offset reports 0")
	wantEq(t, zero.Line(), uint(0), "invalid Line reports 0")
	wantEq(t, zero.Col(), uint(0), "invalid Col reports 0")
}

func TestPosString(t *testing.T) {
	wantEq(t, syntax.NewPos(5, 2, 3).String(), "2:3", "valid position")
	var zero syntax.Pos
	wantEq(t, zero.String(), "?:?", "invalid position")
}

func TestPosAfter(t *testing.T) {
	p1 := syntax.NewPos(5, 2, 3)
	p0 := syntax.NewPos(1, 1, 2)
	wantEq(t, p1.After(p0), true, "later after earlier")
	wantEq(t, p0.After(p1), false, "earlier not after later")
	wantEq(t, p1.After(p1), false, "not after itself")
	var zero syntax.Pos
	wantEq(t, zero.After(p0), false, "invalid receiver always false")
	wantEq(t, p1.After(zero), true, "valid receiver after invalid")
}

func TestStmtPositionField(t *testing.T) {
	f := parse(t, "  foo\n")
	st := f.Stmts[0]
	wantPos(t, st.Position, 2, 1, 3, "Position skips leading spaces")
	wantEq(t, st.Pos(), st.Position, "Pos agrees with Position field")
}
