import sys
import unittest
import weakref
sys.path.insert(0, '..')
import pycparser.c_ast as c_ast
from pycparser.c_parser import Coord

class Test_c_ast(unittest.TestCase):

    def test_BinaryOp(self):
        b1 = c_ast.BinaryOp(op='+', left=c_ast.Constant(type='int', value='6'), right=c_ast.ID(name='joe'))
        self.assertIsInstance(b1.left, c_ast.Constant)
        self.assertEqual(b1.left.type, 'int')
        self.assertEqual(b1.left.value, '6')
        self.assertIsInstance(b1.right, c_ast.ID)
        self.assertEqual(b1.right.name, 'joe')

    def test_weakref_works_on_nodes(self):
        c1 = c_ast.Constant(type='float', value='3.14')
        wr = weakref.ref(c1)
        cref = wr()
        self.assertIsNotNone(cref)
        assert cref is not None
        self.assertEqual(cref.type, 'float')
        self.assertEqual(weakref.getweakrefcount(c1), 1)

    def test_weakref_works_on_coord(self):
        coord = Coord(file='a', line=2)
        wr = weakref.ref(coord)
        cref = wr()
        self.assertIsNotNone(cref)
        assert cref is not None
        self.assertEqual(cref.line, 2)
        self.assertEqual(weakref.getweakrefcount(coord), 1)

class TestNodeVisitor(unittest.TestCase):

    class ConstantVisitor(c_ast.NodeVisitor):

        def __init__(self):
            self.values = []

        def visit_Constant(self, node):
            self.values.append(node.value)

    def test_scalar_children(self):
        b1 = c_ast.BinaryOp(op='+', left=c_ast.Constant(type='int', value='6'), right=c_ast.ID(name='joe'))
        cv = self.ConstantVisitor()
        cv.visit(b1)
        self.assertEqual(cv.values, ['6'])
        b2 = c_ast.BinaryOp(op='*', left=c_ast.Constant(type='int', value='111'), right=b1)
        b3 = c_ast.BinaryOp(op='^', left=b2, right=b1)
        cv = self.ConstantVisitor()
        cv.visit(b3)
        self.assertEqual(cv.values, ['111', '6', '6'])

    def tests_list_children(self):
        c1 = c_ast.Constant(type='float', value='5.6')
        c2 = c_ast.Constant(type='char', value='t')
        b1 = c_ast.BinaryOp(op='+', left=c1, right=c2)
        b2 = c_ast.BinaryOp(op='-', left=b1, right=c2)
        comp = c_ast.Compound(block_items=[b1, b2, c1, c2])
        cv = self.ConstantVisitor()
        cv.visit(comp)
        self.assertEqual(cv.values, ['5.6', 't', '5.6', 't', 't', '5.6', 't'])

    def test_repr(self):
        c1 = c_ast.Constant(type='float', value='5.6')
        c2 = c_ast.Constant(type='char', value='t')
        b1 = c_ast.BinaryOp(op='+', left=c1, right=c2)
        b2 = c_ast.BinaryOp(op='-', left=b1, right=c2)
        comp = c_ast.Compound(block_items=[b1, b2, c1, c2])
        children = list(comp.children())
        self.assertEqual([name for name, _ in children], [
            'block_items[0]', 'block_items[1]', 'block_items[2]', 'block_items[3]'
        ])
        self.assertIs(children[0][1], b1)
        self.assertIs(children[1][1], b2)
        self.assertIs(children[2][1], c1)
        self.assertIs(children[3][1], c2)
if __name__ == '__main__':
    unittest.main()
