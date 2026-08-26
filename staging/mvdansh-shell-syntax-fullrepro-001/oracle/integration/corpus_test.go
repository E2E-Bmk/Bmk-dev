package integration

import (
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

// Shell source corpora used across the integration tests. Each entry must
// parse cleanly under the dialect its corpus is named after.
var bashCorpus = []string{
	"if [[ -n $x && $y == y* ]]; then\n\techo hi >f 2>&1\nelif [ -e f ]; then\n\ttrue\nelse\n\tfalse\nfi\n",
	"for i in a b c; do\n\tfoo \"$i\" &\ndone\nwait\n",
	"case $1 in\nfoo | bar)\n\techo one\n\t;;\nbaz)\n\techo two\n\t;&\nqux)\n\techo three\n\t;;&\n*)\n\techo other\n\t;;\nesac\n",
	"f() {\n\tlocal a=$((1 + 2 * 3))\n\treturn $a\n}\nfunction g {\n\tf\n}\ng\n",
	"x=$(cat <<-EOF\n\thello $USER\n\tEOF\n)\ncat <<'RAW'\n$notexpanded\nRAW\ngrep foo <<<\"$x\"\n",
	"while read -r line; do\n\tprintf '%s\\n' \"${line##* }\" \"${line%%.*}\" \"${line/a/b}\"\ndone <input.txt\n",
	"a=(1 2 3)\na[5]=six\necho \"${a[@]:1:2}\" \"${!a[*]}\" \"${a[0]^^}\" \"${#a[@]}\" \"${a[1]:-def}\"\n",
	"echo $((x++ + --y ? 1 : 0)) $(< file) <(sort a) >(tee b) `date`\n",
	"echo 'uni•code' \"weiß\" über\n",
	"foo && bar |\n\tbaz || ! qux\nfoo |& bar\n",
	"select opt in x y; do break; done\ntime -p sleep 1\nlet a=1 'b = 2'\ndeclare -r c=3 d\n",
	"coproc worker { sort; }\nuntil test -f done; do sleep 1; done\n",
	"(\n\tcd /tmp && pwd\n)\n{\n\tumask 022\n\tls ?(a|b) ~/x\n}\n",
	"echo \"${var:-$(basename \"$0\" .sh)}\" ${x:+yes} ${#name} ${!ref}\n",
}

var posixCorpus = []string{
	"if [ \"$1\" = go ]; then\n\techo yes\nfi\n",
	"i=0\nwhile [ \"$i\" -lt 3 ]; do\n\ti=$((i + 1))\ndone\n",
	"case $x in\na) echo a ;;\n*) echo other ;;\nesac\n",
	"f() {\n\tprintf '%s\\n' \"$@\"\n}\nf 1 2\n",
	"cat <<EOF >out.txt\nbody $HOME\nEOF\n",
}

var mkshCorpus = []string{
	"function f {\n\techo \"${%name}\"\n}\n",
	"case $1 in\na)\n\techo a\n\t;;\n*)\n\techo other\n\t;;\nesac\n",
	"echo ${x:-fallback} $((1 << 4))\n",
}

var batsCorpus = []string{
	"@test \"addition works\" {\n\trun expr 1 + 1\n\t[ \"$output\" = 2 ]\n}\n",
	"setup() {\n\ttmp=$(mktemp -d)\n}\n@test \"uses tmp\" {\n\t[ -d \"$tmp\" ]\n}\n",
}

func dialectCorpora() map[syntax.LangVariant][]string {
	return map[syntax.LangVariant][]string{
		syntax.LangBash:       bashCorpus,
		syntax.LangPOSIX:      posixCorpus,
		syntax.LangMirBSDKorn: mkshCorpus,
		syntax.LangBats:       batsCorpus,
	}
}

func mustParse(t *testing.T, src string, lang syntax.LangVariant, opts ...syntax.ParserOption) *syntax.File {
	t.Helper()
	all := append([]syntax.ParserOption{syntax.Variant(lang)}, opts...)
	f, err := syntax.NewParser(all...).Parse(strings.NewReader(src), "")
	if err != nil {
		t.Fatalf("parse %q under %v: %v", src, lang, err)
	}
	if len(f.Stmts) == 0 {
		t.Fatalf("parse %q under %v produced no statements", src, lang)
	}
	return f
}

func printWith(t *testing.T, node syntax.Node, opts ...syntax.PrinterOption) string {
	t.Helper()
	var sb strings.Builder
	if err := syntax.NewPrinter(opts...).Print(&sb, node); err != nil {
		t.Fatalf("print: %v", err)
	}
	return sb.String()
}

// lineColFromOffset computes the 1-based line and byte column of a byte
// offset within src, the way the spec defines position agreement.
func lineColFromOffset(src string, offset int) (line, col int) {
	line = 1
	lastNL := -1
	for i := 0; i < offset; i++ {
		if src[i] == '\n' {
			line++
			lastNL = i
		}
	}
	return line, offset - lastNL
}
