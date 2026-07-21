import os
import io
import unittest
from pycparser import c_parser
from pycparser.c_ast import *
ParseError = c_parser.ParseError
_c_parser = c_parser.CParser()

def expand_decl(decl):
    """Converts the declaration into a nested list."""
    typ = type(decl)
    if typ == TypeDecl:
        return ['TypeDecl', expand_decl(decl.type)]
    elif typ == IdentifierType:
        return ['IdentifierType', decl.names]
    elif typ == ID:
        return ['ID', decl.name]
    elif typ in [Struct, Union]:
        decls = [expand_decl(d) for d in decl.decls or []]
        return [typ.__name__, decl.name, decls]
    elif typ == Enum:
        if decl.values is None:
            values = None
        else:
            assert isinstance(decl.values, EnumeratorList)
            values = [enum.name for enum in decl.values.enumerators]
        return ['Enum', decl.name, values]
    elif typ == Alignas:
        return ['Alignas', expand_init(decl.alignment)]
    elif typ == StaticAssert:
        if decl.message:
            return ['StaticAssert', decl.cond.value, decl.message.value]
        else:
            return ['StaticAssert', decl.cond.value]
    else:
        nested = expand_decl(decl.type)
        if typ == Decl:
            r = ['Decl']
            if decl.quals:
                r.append(decl.quals)
            if decl.align:
                r.append(expand_decl(decl.align[0]))
            r.extend([decl.name, nested])
            return r
        elif typ == Typename:
            if decl.quals:
                return ['Typename', decl.quals, nested]
            else:
                return ['Typename', nested]
        elif typ == ArrayDecl:
            dimval = decl.dim.value if decl.dim else ''
            return ['ArrayDecl', dimval, decl.dim_quals, nested]
        elif typ == PtrDecl:
            if decl.quals:
                return ['PtrDecl', decl.quals, nested]
            else:
                return ['PtrDecl', nested]
        elif typ == Typedef:
            return ['Typedef', decl.name, nested]
        elif typ == FuncDecl:
            if decl.args:
                params = [expand_decl(param) for param in decl.args.params]
            else:
                params = []
            return ['FuncDecl', params, nested]

def expand_init(init):
    """Converts an initialization into a nested list"""
    typ = type(init)
    if typ == NamedInitializer:
        des = [expand_init(dp) for dp in init.name]
        return (des, expand_init(init.expr))
    elif typ in (InitList, ExprList):
        return [expand_init(expr) for expr in init.exprs]
    elif typ == Constant:
        return ['Constant', init.type, init.value]
    elif typ == ID:
        return ['ID', init.name]
    elif typ == Decl:
        return ['Decl', init.name]
    elif typ == UnaryOp:
        return ['UnaryOp', init.op, expand_decl(init.expr)]
    elif typ == BinaryOp:
        return ['BinaryOp', expand_init(init.left), init.op, expand_init(init.right)]
    elif typ == Compound:
        blocks = []
        if init.block_items:
            blocks = [expand_init(i) for i in init.block_items]
        return ['Compound', blocks]
    elif typ == Typename:
        return expand_decl(init)
    else:
        return [typ.__name__]

class TestCParser_base(unittest.TestCase):

    def parse(self, txt, filename=''):
        return self.cparser.parse(txt, filename)

    def setUp(self):
        self.cparser = _c_parser

    def assert_coord(self, node, line, column=None, file=None):
        self.assertEqual(node.coord.line, line)
        if column is not None:
            self.assertEqual(node.coord.column, column)
        if file:
            self.assertEqual(node.coord.file, file)

class TestCParser_fundamentals(TestCParser_base):

    def get_decl(self, txt, index=0):
        """Given a source and an index returns the expanded
        declaration at that index.

        FileAST holds a list of 'external declarations'.
        index is the offset of the desired declaration in that
        list.
        """
        t = self.parse(txt).ext[index]
        return expand_decl(t)

    def get_decl_init(self, txt, index=0):
        """Returns the expanded initializer of the declaration
        at index.
        """
        t = self.parse(txt).ext[index]
        return expand_init(t.init)

    def test_FileAST(self):
        t = self.parse('int a; char c;')
        self.assertIsInstance(t, FileAST)
        self.assertEqual(len(t.ext), 2)
        t2 = self.parse('')
        self.assertIsInstance(t2, FileAST)
        self.assertEqual(len(t2.ext), 0)

    def test_empty_toplevel_decl(self):
        code = 'int foo;;'
        t = self.parse(code)
        self.assertIsInstance(t, FileAST)
        self.assertEqual(len(t.ext), 1)
        self.assertEqual(self.get_decl(code), ['Decl', 'foo', ['TypeDecl', ['IdentifierType', ['int']]]])

    def test_initial_semi(self):
        t = self.parse(';')
        self.assertEqual(len(t.ext), 0)
        t = self.parse(';int foo;')
        self.assertEqual(len(t.ext), 1)
        self.assertEqual(expand_decl(t.ext[0]), ['Decl', 'foo', ['TypeDecl', ['IdentifierType', ['int']]]])

    def test_line_directive_update_in_errors(self):
        s1 = '\n        \t # \t line \t 8 \t "baz.c" \t\n\n        some syntax error here\n        '
        self.assertRaisesRegex(ParseError, 'baz.c:9', self.parse, s1)
        s2 = '\n        \t # \t 8 \t "baz.c" \t\n\n\n        some syntax error here\n        '
        self.assertRaisesRegex(ParseError, 'baz.c:10', self.parse, s2)
        s3 = ' #line 5 "foo.c"\n        extern int xx;\n        #line 6 "bar.c"\n        extern int yy;\n        #line 7 "baz.c"\n        some syntax error here\n        #line 8 "yadda.c"\n        extern int zz;\n        '
        self.assertRaisesRegex(ParseError, 'baz.c:7', self.parse, s3)

    def test_coords(self):
        self.assert_coord(self.parse('int a;').ext[0], 1, 5)
        t1 = '\n        int a;\n        int b;\n\n\n        int c;\n        '
        f1 = self.parse(t1, filename='test.c')
        self.assert_coord(f1.ext[0], 2, 13, 'test.c')
        self.assert_coord(f1.ext[1], 3, 13, 'test.c')
        self.assert_coord(f1.ext[2], 6, 13, 'test.c')
        t1_1 = '\n        int main() {\n            k = p;\n            printf("%d", b);\n            return 0;\n        }'
        f1_1 = self.parse(t1_1, filename='test.c')
        self.assert_coord(f1_1.ext[0].body.block_items[0], 3, 13, 'test.c')
        self.assert_coord(f1_1.ext[0].body.block_items[1], 4, 13, 'test.c')
        t1_2 = '\n        int main () {\n            int p = (int) k;\n        }'
        f1_2 = self.parse(t1_2, filename='test.c')
        self.assert_coord(f1_2.ext[0].body.block_items[0].init, 3, 21, file='test.c')
        t2 = '\n        #line 99\n        int c;\n        '
        self.assert_coord(self.parse(t2).ext[0], 99, 13)
        t3 = '\n        int dsf;\n        char p;\n        #line 3000 "in.h"\n        char d;\n        '
        f3 = self.parse(t3, filename='test.c')
        self.assert_coord(f3.ext[0], 2, 13, 'test.c')
        self.assert_coord(f3.ext[1], 3, 14, 'test.c')
        self.assert_coord(f3.ext[2], 3000, 14, 'in.h')
        t4 = '\n        #line 20 "restore.h"\n        int maydler(char);\n\n        #line 30 "includes/daween.ph"\n        long j, k;\n\n        #line 50000\n        char* ro;\n        '
        f4 = self.parse(t4, filename='myb.c')
        self.assert_coord(f4.ext[0], 20, 13, 'restore.h')
        self.assert_coord(f4.ext[1], 30, 14, 'includes/daween.ph')
        self.assert_coord(f4.ext[2], 30, 17, 'includes/daween.ph')
        self.assert_coord(f4.ext[3], 50000, 13, 'includes/daween.ph')
        t5 = '\n        int\n        #line 99\n        c;\n        '
        self.assert_coord(self.parse(t5).ext[0], 99, 9)
        t6 = '\n        int foo(int j,\n                ...) {\n        }'
        self.assert_coord(self.parse(t6).ext[0].decl.type.args.params[1], 3, 17)
        t7 = '\n        typedef _Atomic(char) atomic_char;\n        '
        self.assert_coord(self.parse(t7).ext[0], 2, 31)
        self.assert_coord(self.parse(t7).ext[0].type, 2, 31)

    def test_forloop_coord(self):
        t = '        void foo() {\n            for(int z=0; z<4;\n                z++){}\n        }\n        '
        s = self.parse(t, filename='f.c')
        forloop = s.ext[0].body.block_items[0]
        self.assert_coord(forloop.init, 2, 13, 'f.c')
        self.assert_coord(forloop.cond, 2, 26, 'f.c')
        self.assert_coord(forloop.next, 3, 17, 'f.c')

    def test_int128(self):
        self.assertEqual(self.get_decl('__int128 a;'), ['Decl', 'a', ['TypeDecl', ['IdentifierType', ['__int128']]]])

    def test_nested_decls(self):
        self.assertEqual(self.get_decl('char** ar2D;'), ['Decl', 'ar2D', ['PtrDecl', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]])
        self.assertEqual(self.get_decl('int (*a)[1][2];'), ['Decl', 'a', ['PtrDecl', ['ArrayDecl', '1', [], ['ArrayDecl', '2', [], ['TypeDecl', ['IdentifierType', ['int']]]]]]])
        self.assertEqual(self.get_decl('int *a[1][2];'), ['Decl', 'a', ['ArrayDecl', '1', [], ['ArrayDecl', '2', [], ['PtrDecl', ['TypeDecl', ['IdentifierType', ['int']]]]]]])
        self.assertEqual(self.get_decl('char* const* p;'), ['Decl', 'p', ['PtrDecl', ['PtrDecl', ['const'], ['TypeDecl', ['IdentifierType', ['char']]]]]])
        self.assertEqual(self.get_decl('const char* const* p;'), ['Decl', ['const'], 'p', ['PtrDecl', ['PtrDecl', ['const'], ['TypeDecl', ['IdentifierType', ['char']]]]]])
        self.assertEqual(self.get_decl('char* * const p;'), ['Decl', 'p', ['PtrDecl', ['const'], ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]])
        self.assertEqual(self.get_decl('char ***ar3D[40];'), ['Decl', 'ar3D', ['ArrayDecl', '40', [], ['PtrDecl', ['PtrDecl', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]]]])
        self.assertEqual(self.get_decl('char (***ar3D)[40];'), ['Decl', 'ar3D', ['PtrDecl', ['PtrDecl', ['PtrDecl', ['ArrayDecl', '40', [], ['TypeDecl', ['IdentifierType', ['char']]]]]]]])
        self.assertEqual(self.get_decl('int (*const*const x)(char, int);'), ['Decl', 'x', ['PtrDecl', ['const'], ['PtrDecl', ['const'], ['FuncDecl', [['Typename', ['TypeDecl', ['IdentifierType', ['char']]]], ['Typename', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]]])
        self.assertEqual(self.get_decl('int (*x[4])(char, int);'), ['Decl', 'x', ['ArrayDecl', '4', [], ['PtrDecl', ['FuncDecl', [['Typename', ['TypeDecl', ['IdentifierType', ['char']]]], ['Typename', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]]])
        self.assertEqual(self.get_decl('char *(*(**foo [][8])())[];'), ['Decl', 'foo', ['ArrayDecl', '', [], ['ArrayDecl', '8', [], ['PtrDecl', ['PtrDecl', ['FuncDecl', [], ['PtrDecl', ['ArrayDecl', '', [], ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]]]]]]]])
        self.assertEqual(self.get_decl('int (*k)(int);'), ['Decl', 'k', ['PtrDecl', ['FuncDecl', [['Typename', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        self.assertEqual(self.get_decl('int (*k)(const int);'), ['Decl', 'k', ['PtrDecl', ['FuncDecl', [['Typename', ['const'], ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        self.assertEqual(self.get_decl('int (*k)(int q);'), ['Decl', 'k', ['PtrDecl', ['FuncDecl', [['Decl', 'q', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        self.assertEqual(self.get_decl('int (*k)(const volatile int q);'), ['Decl', 'k', ['PtrDecl', ['FuncDecl', [['Decl', ['const', 'volatile'], 'q', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        self.assertEqual(self.get_decl('int (*k)(_Atomic volatile int q);'), ['Decl', 'k', ['PtrDecl', ['FuncDecl', [['Decl', ['_Atomic', 'volatile'], 'q', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        self.assertEqual(self.get_decl('int (*k)(const volatile int* q);'), ['Decl', 'k', ['PtrDecl', ['FuncDecl', [['Decl', ['const', 'volatile'], 'q', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['int']]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        self.assertEqual(self.get_decl('int (*k)(restrict int* q);'), ['Decl', 'k', ['PtrDecl', ['FuncDecl', [['Decl', ['restrict'], 'q', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['int']]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])

    def test_func_decls_with_array_dim_qualifiers(self):
        self.assertEqual(self.get_decl('int zz(int p[static 10]);'), ['Decl', 'zz', ['FuncDecl', [['Decl', 'p', ['ArrayDecl', '10', ['static'], ['TypeDecl', ['IdentifierType', ['int']]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int [static 10]);'), ['Decl', 'zz', ['FuncDecl', [['Typename', ['ArrayDecl', '10', ['static'], ['TypeDecl', ['IdentifierType', ['int']]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int [static const restrict 10]);'), ['Decl', 'zz', ['FuncDecl', [['Typename', ['ArrayDecl', '10', ['static', 'const', 'restrict'], ['TypeDecl', ['IdentifierType', ['int']]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int p[const 10]);'), ['Decl', 'zz', ['FuncDecl', [['Decl', 'p', ['ArrayDecl', '10', ['const'], ['TypeDecl', ['IdentifierType', ['int']]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int p[restrict][5]);'), ['Decl', 'zz', ['FuncDecl', [['Decl', 'p', ['ArrayDecl', '', ['restrict'], ['ArrayDecl', '5', [], ['TypeDecl', ['IdentifierType', ['int']]]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int p[const restrict static 10][5]);'), ['Decl', 'zz', ['FuncDecl', [['Decl', 'p', ['ArrayDecl', '10', ['const', 'restrict', 'static'], ['ArrayDecl', '5', [], ['TypeDecl', ['IdentifierType', ['int']]]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int [const 10]);'), ['Decl', 'zz', ['FuncDecl', [['Typename', ['ArrayDecl', '10', ['const'], ['TypeDecl', ['IdentifierType', ['int']]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int [restrict][5]);'), ['Decl', 'zz', ['FuncDecl', [['Typename', ['ArrayDecl', '', ['restrict'], ['ArrayDecl', '5', [], ['TypeDecl', ['IdentifierType', ['int']]]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('int zz(int [const restrict volatile 10][5]);'), ['Decl', 'zz', ['FuncDecl', [['Typename', ['ArrayDecl', '10', ['const', 'restrict', 'volatile'], ['ArrayDecl', '5', [], ['TypeDecl', ['IdentifierType', ['int']]]]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])

    def test_qualifiers_storage_specifiers(self):

        def assert_qs(txt, index, quals, storage):
            d = self.parse(txt).ext[index]
            self.assertEqual(d.quals, quals)
            self.assertEqual(d.storage, storage)
        assert_qs('extern int p;', 0, [], ['extern'])
        assert_qs('_Thread_local int p;', 0, [], ['_Thread_local'])
        assert_qs('const long p = 6;', 0, ['const'], [])
        assert_qs('_Atomic int p;', 0, ['_Atomic'], [])
        assert_qs('_Atomic restrict int* p;', 0, ['_Atomic', 'restrict'], [])
        d1 = 'static const int p, q, r;'
        for i in range(3):
            assert_qs(d1, i, ['const'], ['static'])
        d2 = 'static char * const p;'
        assert_qs(d2, 0, [], ['static'])
        pdecl = self.parse(d2).ext[0].type
        self.assertIsInstance(pdecl, PtrDecl)
        self.assertEqual(pdecl.quals, ['const'])

    def test_atomic_specifier(self):
        self.assertEqual(self.get_decl('_Atomic(int) ai;'), ['Decl', ['_Atomic'], 'ai', ['TypeDecl', ['IdentifierType', ['int']]]])
        self.assertEqual(self.get_decl('_Atomic(int*) ai;'), ['Decl', 'ai', ['PtrDecl', ['_Atomic'], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl('_Atomic(_Atomic(int)*) aai;'), ['Decl', ['_Atomic'], 'aai', ['PtrDecl', ['_Atomic'], ['TypeDecl', ['IdentifierType', ['int']]]]])
        s = '_Atomic(int) foo, bar;'
        self.assertEqual(self.get_decl(s, 0), ['Decl', ['_Atomic'], 'foo', ['TypeDecl', ['IdentifierType', ['int']]]])
        self.assertEqual(self.get_decl(s, 1), ['Decl', ['_Atomic'], 'bar', ['TypeDecl', ['IdentifierType', ['int']]]])
        s = 'typedef _Atomic(int) atomic_int;'
        self.assertEqual(self.get_decl(s, 0), ['Typedef', 'atomic_int', ['TypeDecl', ['IdentifierType', ['int']]]])
        s = 'typedef _Atomic(_Bool) atomic_bool;'
        self.assertEqual(self.get_decl(s, 0), ['Typedef', 'atomic_bool', ['TypeDecl', ['IdentifierType', ['_Bool']]]])
        s = 'typedef _Atomic(_Atomic(_Atomic(int (*)(void)) *) *) t;'
        self.assertEqual(self.get_decl(s, 0), ['Typedef', 't', ['PtrDecl', ['_Atomic'], ['PtrDecl', ['_Atomic'], ['PtrDecl', ['_Atomic'], ['FuncDecl', [['Typename', ['TypeDecl', ['IdentifierType', ['void']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]]]])

    def test_alignof(self):
        r = self.parse('int a = _Alignof(int);')
        self.assertEqual(expand_decl(r.ext[0]), ['Decl', 'a', ['TypeDecl', ['IdentifierType', ['int']]]])
        self.assertEqual(expand_init(r.ext[0].init), ['UnaryOp', '_Alignof', ['Typename', ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(expand_decl(self.parse('_Alignas(_Alignof(int)) char a;').ext[0]), ['Decl', ['Alignas', ['UnaryOp', '_Alignof', ['Typename', ['TypeDecl', ['IdentifierType', ['int']]]]]], 'a', ['TypeDecl', ['IdentifierType', ['char']]]])
        self.assertEqual(expand_decl(self.parse('_Alignas(4) char a;').ext[0]), ['Decl', ['Alignas', ['Constant', 'int', '4']], 'a', ['TypeDecl', ['IdentifierType', ['char']]]])
        self.assertEqual(expand_decl(self.parse('_Alignas(int) char a;').ext[0]), ['Decl', ['Alignas', ['Typename', ['TypeDecl', ['IdentifierType', ['int']]]]], 'a', ['TypeDecl', ['IdentifierType', ['char']]]])

    def test_alignas_with_typedef_in_struct(self):
        s = '\n            typedef int test_int;\n            typedef struct {\n                _Alignas(int) test_int a1;\n            } test_struct;\n        '
        ast = self.parse(s)
        field = ast.ext[1].type.type.decls[0]
        self.assertEqual(field.name, 'a1')
        self.assertTrue(hasattr(field, 'align') and field.align is not None)
        self.assertEqual(expand_decl(field), ['Decl', ['Alignas', ['Typename', ['TypeDecl', ['IdentifierType', ['int']]]]], 'a1', ['TypeDecl', ['IdentifierType', ['test_int']]]])

    def test_offsetof(self):

        def expand_ref(n):
            if isinstance(n, StructRef):
                return ['StructRef', expand_ref(n.name), expand_ref(n.field)]
            elif isinstance(n, ArrayRef):
                return ['ArrayRef', expand_ref(n.name), expand_ref(n.subscript)]
            elif isinstance(n, ID):
                return ['ID', n.name]
            elif isinstance(n, Constant):
                return ['Constant', n.type, n.value]
            else:
                raise TypeError('Unexpected type ' + n.__class__.__name__)
        e = '\n            void foo() {\n                int a = offsetof(struct S, p);\n                a.b = offsetof(struct sockaddr, sp) + strlen(bar);\n                int a = offsetof(struct S, p.q.r);\n                int a = offsetof(struct S, p[5].q[4][5]);\n            }\n            '
        compound = self.parse(e).ext[0].body
        s1 = compound.block_items[0].init
        self.assertIsInstance(s1, FuncCall)
        self.assertIsInstance(s1.name, ID)
        self.assertEqual(s1.name.name, 'offsetof')
        self.assertIsInstance(s1.args.exprs[0], Typename)
        self.assertIsInstance(s1.args.exprs[1], ID)
        s3 = compound.block_items[2].init
        self.assertIsInstance(s3.args.exprs[1], StructRef)
        self.assertEqual(expand_ref(s3.args.exprs[1]), ['StructRef', ['StructRef', ['ID', 'p'], ['ID', 'q']], ['ID', 'r']])
        s4 = compound.block_items[3].init
        self.assertIsInstance(s4.args.exprs[1], ArrayRef)
        self.assertEqual(expand_ref(s4.args.exprs[1]), ['ArrayRef', ['ArrayRef', ['StructRef', ['ArrayRef', ['ID', 'p'], ['Constant', 'int', '5']], ['ID', 'q']], ['Constant', 'int', '4']], ['Constant', 'int', '5']])

    def test_compound_statement(self):
        e = '\n            void foo() {\n            }\n            '
        compound = self.parse(e).ext[0].body
        self.assertIsInstance(compound, Compound)
        self.assert_coord(compound, 2)

    def test_compound_literals(self):
        ps1 = self.parse('\n            void foo() {\n                p = (long long){k};\n                tc = (struct jk){.a = {1, 2}, .b[0] = t};\n            }')
        compound = ps1.ext[0].body.block_items[0].rvalue
        self.assertEqual(expand_decl(compound.type), ['Typename', ['TypeDecl', ['IdentifierType', ['long', 'long']]]])
        self.assertEqual(expand_init(compound.init), [['ID', 'k']])
        compound = ps1.ext[0].body.block_items[1].rvalue
        self.assertEqual(expand_decl(compound.type), ['Typename', ['TypeDecl', ['Struct', 'jk', []]]])
        self.assertEqual(expand_init(compound.init), [([['ID', 'a']], [['Constant', 'int', '1'], ['Constant', 'int', '2']]), ([['ID', 'b'], ['Constant', 'int', '0']], ['ID', 't'])])

    def test_parenthesized_compounds(self):
        e = self.parse('\n        void foo() {\n            int a;\n            ({});\n            ({ 1; });\n            ({ 1; 2; });\n            int b = ({ 1; });\n            int c, d = ({ int x = 1; x + 2; });\n            a = ({ int x = 1; 2 * x; });\n        }')
        body = e.ext[0].body.block_items
        self.assertIsInstance(body[1], Compound)
        self.assertEqual(body[1].block_items, None)
        self.assertIsInstance(body[2], Compound)
        self.assertEqual(len(body[2].block_items), 1)
        self.assertIsInstance(body[2].block_items[0], Constant)
        self.assertIsInstance(body[3], Compound)
        self.assertEqual(len(body[3].block_items), 2)
        self.assertIsInstance(body[3].block_items[0], Constant)
        self.assertIsInstance(body[3].block_items[1], Constant)
        self.assertIsInstance(body[4], Decl)
        self.assertEqual(expand_init(body[4].init), ['Compound', [['Constant', 'int', '1']]])
        self.assertIsInstance(body[5], Decl)
        self.assertEqual(body[5].init, None)
        self.assertIsInstance(body[6], Decl)
        self.assertEqual(expand_init(body[6].init), ['Compound', [['Decl', 'x'], ['BinaryOp', ['ID', 'x'], '+', ['Constant', 'int', '2']]]])
        self.assertIsInstance(body[7], Assignment)
        self.assertIsInstance(body[7].rvalue, Compound)
        self.assertEqual(expand_init(body[7].rvalue), ['Compound', [['Decl', 'x'], ['BinaryOp', ['Constant', 'int', '2'], '*', ['ID', 'x']]]])

    def test_enums(self):
        e1 = 'enum mycolor op;'
        e1_type = self.parse(e1).ext[0].type.type
        self.assertIsInstance(e1_type, Enum)
        self.assertEqual(e1_type.name, 'mycolor')
        self.assertEqual(e1_type.values, None)
        e2 = 'enum mysize {large=20, small, medium} shoes;'
        e2_type = self.parse(e2).ext[0].type.type
        self.assertIsInstance(e2_type, Enum)
        self.assertEqual(e2_type.name, 'mysize')
        e2_elist = e2_type.values
        self.assertIsInstance(e2_elist, EnumeratorList)
        for e2_eval in e2_elist.enumerators:
            self.assertIsInstance(e2_eval, Enumerator)
        self.assertEqual(e2_elist.enumerators[0].name, 'large')
        self.assertEqual(e2_elist.enumerators[0].value.value, '20')
        self.assertEqual(e2_elist.enumerators[2].name, 'medium')
        self.assertEqual(e2_elist.enumerators[2].value, None)
        e3 = '\n            enum\n            {\n                red,\n                blue,\n                green,\n            } color;\n            '
        e3_type = self.parse(e3).ext[0].type.type
        self.assertIsInstance(e3_type, Enum)
        e3_elist = e3_type.values
        self.assertIsInstance(e3_elist, EnumeratorList)
        for e3_eval in e3_elist.enumerators:
            self.assertIsInstance(e3_eval, Enumerator)
        self.assertEqual(e3_elist.enumerators[0].name, 'red')
        self.assertEqual(e3_elist.enumerators[0].value, None)
        self.assertEqual(e3_elist.enumerators[1].name, 'blue')
        self.assertEqual(e3_elist.enumerators[2].name, 'green')

    def test_anonymous_struct_union(self):
        s1 = '\n            union\n            {\n                union\n                {\n                    int i;\n                    long l;\n                };\n\n                struct\n                {\n                    int type;\n                    int intnode;\n                };\n            } u;\n        '
        self.assertEqual(expand_decl(self.parse(s1).ext[0]), ['Decl', 'u', ['TypeDecl', ['Union', None, [['Decl', None, ['Union', None, [['Decl', 'i', ['TypeDecl', ['IdentifierType', ['int']]]], ['Decl', 'l', ['TypeDecl', ['IdentifierType', ['long']]]]]]], ['Decl', None, ['Struct', None, [['Decl', 'type', ['TypeDecl', ['IdentifierType', ['int']]]], ['Decl', 'intnode', ['TypeDecl', ['IdentifierType', ['int']]]]]]]]]]])
        s2 = '\n            struct\n            {\n                int i;\n                union\n                {\n                    int id;\n                    char* name;\n                };\n                float f;\n            } joe;\n            '
        self.assertEqual(expand_decl(self.parse(s2).ext[0]), ['Decl', 'joe', ['TypeDecl', ['Struct', None, [['Decl', 'i', ['TypeDecl', ['IdentifierType', ['int']]]], ['Decl', None, ['Union', None, [['Decl', 'id', ['TypeDecl', ['IdentifierType', ['int']]]], ['Decl', 'name', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]]]], ['Decl', 'f', ['TypeDecl', ['IdentifierType', ['float']]]]]]]])
        s3 = '\n            struct v {\n                union {\n                    struct { int i, j; };\n                    struct { long k, l; } w;\n                };\n                int m;\n            } v1;\n            '
        self.assertEqual(expand_decl(self.parse(s3).ext[0]), ['Decl', 'v1', ['TypeDecl', ['Struct', 'v', [['Decl', None, ['Union', None, [['Decl', None, ['Struct', None, [['Decl', 'i', ['TypeDecl', ['IdentifierType', ['int']]]], ['Decl', 'j', ['TypeDecl', ['IdentifierType', ['int']]]]]]], ['Decl', 'w', ['TypeDecl', ['Struct', None, [['Decl', 'k', ['TypeDecl', ['IdentifierType', ['long']]]], ['Decl', 'l', ['TypeDecl', ['IdentifierType', ['long']]]]]]]]]]], ['Decl', 'm', ['TypeDecl', ['IdentifierType', ['int']]]]]]]])
        s4 = '\n            struct v {\n                int i;\n                float;\n            } v2;'
        self.parse(s4)

    def test_multi_decls(self):
        d1 = 'int a, b;'
        self.assertEqual(self.get_decl(d1, 0), ['Decl', 'a', ['TypeDecl', ['IdentifierType', ['int']]]])
        self.assertEqual(self.get_decl(d1, 1), ['Decl', 'b', ['TypeDecl', ['IdentifierType', ['int']]]])
        d2 = 'char* p, notp, ar[4];'
        self.assertEqual(self.get_decl(d2, 0), ['Decl', 'p', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]])
        self.assertEqual(self.get_decl(d2, 1), ['Decl', 'notp', ['TypeDecl', ['IdentifierType', ['char']]]])
        self.assertEqual(self.get_decl(d2, 2), ['Decl', 'ar', ['ArrayDecl', '4', [], ['TypeDecl', ['IdentifierType', ['char']]]]])

    def test_invalid_multiple_types_error(self):
        bad = ['int enum {ab, cd} fubr;', 'enum kid char brbr;']
        for b in bad:
            self.assertRaises(ParseError, self.parse, b)

    def test_invalid_typedef_storage_qual_error(self):
        """Tests that using typedef as a storage qualifier is correctly flagged
        as an error.
        """
        bad = 'typedef const int foo(int a) { return 0; }'
        self.assertRaises(ParseError, self.parse, bad)

    def test_duplicate_typedef(self):
        """Tests that redeclarations of existing types are parsed correctly.
        This is non-standard, but allowed by many compilers.
        """
        d1 = '\n            typedef int numbertype;\n            typedef int numbertype;\n        '
        self.assertEqual(self.get_decl(d1, 0), ['Typedef', 'numbertype', ['TypeDecl', ['IdentifierType', ['int']]]])
        self.assertEqual(self.get_decl(d1, 1), ['Typedef', 'numbertype', ['TypeDecl', ['IdentifierType', ['int']]]])
        d2 = '\n            typedef int (*funcptr)(int x);\n            typedef int (*funcptr)(int x);\n        '
        self.assertEqual(self.get_decl(d2, 0), ['Typedef', 'funcptr', ['PtrDecl', ['FuncDecl', [['Decl', 'x', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        self.assertEqual(self.get_decl(d2, 1), ['Typedef', 'funcptr', ['PtrDecl', ['FuncDecl', [['Decl', 'x', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]]])
        d3 = '\n            typedef int numberarray[5];\n            typedef int numberarray[5];\n        '
        self.assertEqual(self.get_decl(d3, 0), ['Typedef', 'numberarray', ['ArrayDecl', '5', [], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(self.get_decl(d3, 1), ['Typedef', 'numberarray', ['ArrayDecl', '5', [], ['TypeDecl', ['IdentifierType', ['int']]]]])

    def test_decl_inits(self):
        d1 = 'int a = 16;'
        self.assertEqual(self.get_decl(d1), ['Decl', 'a', ['TypeDecl', ['IdentifierType', ['int']]]])
        self.assertEqual(self.get_decl_init(d1), ['Constant', 'int', '16'])
        d1_1 = 'float f = 0xEF.56p1;'
        self.assertEqual(self.get_decl_init(d1_1), ['Constant', 'double', '0xEF.56p1'])
        d1_2 = 'int bitmask = 0b1001010;'
        self.assertEqual(self.get_decl_init(d1_2), ['Constant', 'int', '0b1001010'])
        d2 = 'long ar[] = {7, 8, 9};'
        self.assertEqual(self.get_decl(d2), ['Decl', 'ar', ['ArrayDecl', '', [], ['TypeDecl', ['IdentifierType', ['long']]]]])
        self.assertEqual(self.get_decl_init(d2), [['Constant', 'int', '7'], ['Constant', 'int', '8'], ['Constant', 'int', '9']])
        d21 = 'long ar[4] = {};'
        self.assertEqual(self.get_decl_init(d21), [])
        d3 = 'char p = j;'
        self.assertEqual(self.get_decl(d3), ['Decl', 'p', ['TypeDecl', ['IdentifierType', ['char']]]])
        self.assertEqual(self.get_decl_init(d3), ['ID', 'j'])
        d4 = "char x = 'c', *p = {0, 1, 2, {4, 5}, 6};"
        self.assertEqual(self.get_decl(d4, 0), ['Decl', 'x', ['TypeDecl', ['IdentifierType', ['char']]]])
        self.assertEqual(self.get_decl_init(d4, 0), ['Constant', 'char', "'c'"])
        self.assertEqual(self.get_decl(d4, 1), ['Decl', 'p', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]])
        self.assertEqual(self.get_decl_init(d4, 1), [['Constant', 'int', '0'], ['Constant', 'int', '1'], ['Constant', 'int', '2'], [['Constant', 'int', '4'], ['Constant', 'int', '5']], ['Constant', 'int', '6']])
        d5 = 'float d = 1.0;'
        self.assertEqual(self.get_decl_init(d5), ['Constant', 'double', '1.0'])
        d51 = 'float ld = 1.0l;'
        self.assertEqual(self.get_decl_init(d51), ['Constant', 'long double', '1.0l'])
        d52 = 'float ld = 1.0L;'
        self.assertEqual(self.get_decl_init(d52), ['Constant', 'long double', '1.0L'])
        d53 = 'float ld = 1.0f;'
        self.assertEqual(self.get_decl_init(d53), ['Constant', 'float', '1.0f'])
        d54 = 'float ld = 1.0F;'
        self.assertEqual(self.get_decl_init(d54), ['Constant', 'float', '1.0F'])
        d55 = 'float ld = 0xDE.38p0;'
        self.assertEqual(self.get_decl_init(d55), ['Constant', 'double', '0xDE.38p0'])
        d56 = 'float ld = 0xDE.38p0f;'
        self.assertEqual(self.get_decl_init(d56), ['Constant', 'float', '0xDE.38p0f'])
        d57 = 'float ld = 0xDE.38p0F;'
        self.assertEqual(self.get_decl_init(d57), ['Constant', 'float', '0xDE.38p0F'])
        d58 = 'float ld = 0xDE.38p0l;'
        self.assertEqual(self.get_decl_init(d58), ['Constant', 'long double', '0xDE.38p0l'])
        d59 = 'float ld = 0xDE.38p0L;'
        self.assertEqual(self.get_decl_init(d59), ['Constant', 'long double', '0xDE.38p0L'])
        d6 = 'int i = 1;'
        self.assertEqual(self.get_decl_init(d6), ['Constant', 'int', '1'])
        d61 = 'long int li = 1l;'
        self.assertEqual(self.get_decl_init(d61), ['Constant', 'long int', '1l'])
        d62 = 'unsigned int ui = 1u;'
        self.assertEqual(self.get_decl_init(d62), ['Constant', 'unsigned int', '1u'])
        d63 = 'unsigned long long int ulli = 1LLU;'
        self.assertEqual(self.get_decl_init(d63), ['Constant', 'unsigned long long int', '1LLU'])

    def test_decl_named_inits(self):
        d1 = 'int a = {.k = 16};'
        self.assertEqual(self.get_decl_init(d1), [([['ID', 'k']], ['Constant', 'int', '16'])])
        d2 = 'int a = { [0].a = {1}, [1].a[0] = 2 };'
        self.assertEqual(self.get_decl_init(d2), [([['Constant', 'int', '0'], ['ID', 'a']], [['Constant', 'int', '1']]), ([['Constant', 'int', '1'], ['ID', 'a'], ['Constant', 'int', '0']], ['Constant', 'int', '2'])])
        d3 = 'int a = { .a = 1, .c = 3, 4, .b = 5};'
        self.assertEqual(self.get_decl_init(d3), [([['ID', 'a']], ['Constant', 'int', '1']), ([['ID', 'c']], ['Constant', 'int', '3']), ['Constant', 'int', '4'], ([['ID', 'b']], ['Constant', 'int', '5'])])

    def test_function_definitions(self):

        def parse_fdef(str):
            return self.parse(str).ext[0]

        def fdef_decl(fdef):
            return expand_decl(fdef.decl)
        f1 = parse_fdef('\n        int factorial(int p)\n        {\n            return 3;\n        }\n        ')
        self.assertEqual(fdef_decl(f1), ['Decl', 'factorial', ['FuncDecl', [['Decl', 'p', ['TypeDecl', ['IdentifierType', ['int']]]]], ['TypeDecl', ['IdentifierType', ['int']]]]])
        self.assertEqual(type(f1.body.block_items[0]), Return)
        f2 = parse_fdef('\n        char* zzz(int p, char* c)\n        {\n            int a;\n            char b;\n\n            a = b + 2;\n            return 3;\n        }\n        ')
        self.assertEqual(fdef_decl(f2), ['Decl', 'zzz', ['FuncDecl', [['Decl', 'p', ['TypeDecl', ['IdentifierType', ['int']]]], ['Decl', 'c', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]], ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]])
        self.assertEqual(list(map(type, f2.body.block_items)), [Decl, Decl, Assignment, Return])
        f3 = parse_fdef('\n        char* zzz(p, c)\n        long p, *c;\n        {\n            int a;\n            char b;\n\n            a = b + 2;\n            return 3;\n        }\n        ')
        self.assertEqual(fdef_decl(f3), ['Decl', 'zzz', ['FuncDecl', [['ID', 'p'], ['ID', 'c']], ['PtrDecl', ['TypeDecl', ['IdentifierType', ['char']]]]]])
        self.assertEqual(list(map(type, f3.body.block_items)), [Decl, Decl, Assignment, Return])
        self.assertEqual(expand_decl(f3.param_decls[0]), ['Decl', 'p', ['TypeDecl', ['IdentifierType', ['long']]]])
        self.assertEqual(expand_decl(f3.param_decls[1]), ['Decl', 'c', ['PtrDecl', ['TypeDecl', ['IdentifierType', ['long']]]]])
        f4 = parse_fdef('\n        que(p)\n        {\n            return 3;\n        }\n        ')
        self.assertEqual(fdef_decl(f4), ['Decl', 'que', ['FuncDecl', [['ID', 'p']], ['TypeDecl', ['IdentifierType', ['int']]]]])

    def test_inline_specifier(self):
        ps2 = self.parse('static inline void inlinefoo(void);')
        self.assertEqual(ps2.ext[0].funcspec, ['inline'])

    def test_noreturn_specifier(self):
        ps2 = self.parse('static _Noreturn void noreturnfoo(void);')
        self.assertEqual(ps2.ext[0].funcspec, ['_Noreturn'])

    def test_pragma(self):
        s1 = '\n            #pragma bar\n            void main() {\n                #pragma foo\n                for(;;) {}\n                #pragma baz\n                {\n                    int i = 0;\n                }\n                #pragma\n            }\n            struct s {\n            #pragma baz\n            } s;\n            _Pragma("other \\"string\\"")\n            '
        s1_ast = self.parse(s1)
        self.assertIsInstance(s1_ast.ext[0], Pragma)
        self.assertEqual(s1_ast.ext[0].string, 'bar')
        self.assertEqual(s1_ast.ext[0].coord.line, 2)
        self.assertIsInstance(s1_ast.ext[1].body.block_items[0], Pragma)
        self.assertEqual(s1_ast.ext[1].body.block_items[0].string, 'foo')
        self.assertEqual(s1_ast.ext[1].body.block_items[0].coord.line, 4)
        self.assertIsInstance(s1_ast.ext[1].body.block_items[2], Pragma)
        self.assertEqual(s1_ast.ext[1].body.block_items[2].string, 'baz')
        self.assertEqual(s1_ast.ext[1].body.block_items[2].coord.line, 6)
        self.assertIsInstance(s1_ast.ext[1].body.block_items[4], Pragma)
        self.assertEqual(s1_ast.ext[1].body.block_items[4].string, '')
        self.assertEqual(s1_ast.ext[1].body.block_items[4].coord.line, 10)
        self.assertIsInstance(s1_ast.ext[2].type.type.decls[0], Pragma)
        self.assertEqual(s1_ast.ext[2].type.type.decls[0].string, 'baz')
        self.assertEqual(s1_ast.ext[2].type.type.decls[0].coord.line, 13)
        self.assertIsInstance(s1_ast.ext[3], Pragma)
        self.assertEqual(s1_ast.ext[3].string.value, '"other \\"string\\""')
        self.assertEqual(s1_ast.ext[3].coord.line, 15)

    def test_pragmacomp_or_statement(self):
        s1 = '\n            void main() {\n                int sum = 0;\n                for (int i; i < 3; i++)\n                    #pragma omp critical\n                    sum += 1;\n\n                while(sum < 10)\n                    #pragma omp critical\n                    sum += 1;\n\n                mylabel:\n                    #pragma foo\n                    sum += 10;\n\n                if (sum > 10)\n                    #pragma bar\n                    #pragma baz\n                    sum = 10;\n\n                switch (sum)\n                case 10:\n                    #pragma foo\n                    sum = 20;\n            }\n        '
        s1_ast = self.parse(s1)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[1], For)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[1].stmt, Compound)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[1].stmt.block_items[0], Pragma)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[1].stmt.block_items[1], Assignment)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[2], While)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[2].stmt, Compound)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[2].stmt.block_items[0], Pragma)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[2].stmt.block_items[1], Assignment)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[3], Label)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[3].stmt, Compound)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[3].stmt.block_items[0], Pragma)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[3].stmt.block_items[1], Assignment)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[4], If)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[4].iftrue, Compound)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[4].iftrue.block_items[0], Pragma)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[4].iftrue.block_items[1], Pragma)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[4].iftrue.block_items[2], Assignment)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[5], Switch)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[5].stmt.stmts[0], Compound)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[5].stmt.stmts[0].block_items[0], Pragma)
        self.assertIsInstance(s1_ast.ext[0].body.block_items[5].stmt.stmts[0].block_items[1], Assignment)
if __name__ == '__main__':
    unittest.main()
