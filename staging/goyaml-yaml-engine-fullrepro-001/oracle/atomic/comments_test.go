package atomic

import (
	"reflect"
	"testing"

	yaml "github.com/goccy/go-yaml"
)

// Verifies: Comment Association > Collecting (head and line positions, path
// keys, text preserved including the leading space).
func TestCommentToMapCollectsPositions(t *testing.T) {
	cm := yaml.CommentMap{}
	var v interface{}
	src := "# head a\na: 1\nb:\n  c: 2 # line c\n"
	if err := unmarshalInto(t, src, &v, yaml.CommentToMap(cm)); err != nil {
		t.Fatal(err)
	}
	headA, ok := cm["$.a"]
	if !ok || len(headA) != 1 {
		t.Fatalf("no comment collected at $.a: %v", cm)
	}
	if !reflect.DeepEqual(headA[0], yaml.HeadComment(" head a")) {
		t.Fatalf("comment at $.a = %#v, want head comment with text \" head a\"", headA[0])
	}
	lineC, ok := cm["$.b.c"]
	if !ok || len(lineC) != 1 {
		t.Fatalf("no comment collected at $.b.c: %v", cm)
	}
	if !reflect.DeepEqual(lineC[0], yaml.LineComment(" line c")) {
		t.Fatalf("comment at $.b.c = %#v, want line comment with text \" line c\"", lineC[0])
	}
}

// Verifies: Comment Association > Collecting (comment below the last value
// collects with the foot position).
func TestCommentToMapCollectsFootPosition(t *testing.T) {
	cm := yaml.CommentMap{}
	var v interface{}
	if err := unmarshalInto(t, "a: 1\n# below\n", &v, yaml.CommentToMap(cm)); err != nil {
		t.Fatal(err)
	}
	got, ok := cm["$.a"]
	if !ok || len(got) != 1 {
		t.Fatalf("no comment collected at $.a: %v", cm)
	}
	if !reflect.DeepEqual(got[0], yaml.FootComment(" below")) {
		t.Fatalf("comment = %#v, want foot comment with text \" below\"", got[0])
	}
}

// Verifies: Comment Association > Emitting (constructors and CommentPosition).
func TestCommentConstructorsEmit(t *testing.T) {
	cm := yaml.CommentMap{
		"$.a": []*yaml.Comment{yaml.HeadComment(" above")},
		"$.b": []*yaml.Comment{yaml.LineComment(" beside")},
		"$.c": []*yaml.Comment{yaml.FootComment(" under")},
	}
	val := yaml.MapSlice{
		yaml.MapItem{Key: "a", Value: 1},
		yaml.MapItem{Key: "b", Value: 2},
		yaml.MapItem{Key: "c", Value: 3},
	}
	out := mustMarshal(t, val, yaml.WithComment(cm))
	want := "# above\na: 1\nb: 2 # beside\nc: 3\n# under\n"
	if out != want {
		t.Fatalf("WithComment encode = %q, want %q", out, want)
	}

	// The position kind of a collected comment is exposed via
	// CommentPosition and matches the constructor used.
	var head, line yaml.CommentPosition = yaml.HeadComment("x").Position, yaml.LineComment("x").Position
	if head == line {
		t.Fatal("HeadComment and LineComment must carry distinct positions")
	}
}

// Verifies: Comment Association > Emitting (multi-line head comments each on
// their own line).
func TestMultiLineHeadComment(t *testing.T) {
	cm := yaml.CommentMap{
		"$.a": []*yaml.Comment{yaml.HeadComment(" first", " second")},
	}
	out := mustMarshal(t, yaml.MapSlice{yaml.MapItem{Key: "a", Value: 1}}, yaml.WithComment(cm))
	want := "# first\n# second\na: 1\n"
	if out != want {
		t.Fatalf("multi-line head comment = %q, want %q", out, want)
	}
}
