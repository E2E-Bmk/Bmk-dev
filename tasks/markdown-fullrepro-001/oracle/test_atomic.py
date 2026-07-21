"""
Python Markdown

A Python implementation of John Gruber's Markdown.

Documentation: https://python-markdown.github.io/
GitHub: https://github.com/Python-Markdown/markdown/
PyPI: https://pypi.org/project/Markdown/

Started by Manfred Stienstra (http://www.dwerg.net/).
Maintained for a few years by Yuri Takhteyev (http://www.freewisdom.org).
Currently maintained by Waylan Limberg (https://github.com/waylan),
Dmitry Shachnev (https://github.com/mitya57) and Isaac Muse (https://github.com/facelessuser).

Copyright 2007-2023 The Python Markdown Project (v. 1.7 and later)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE.md for details).

Python-Markdown Regression Tests
================================

Tests of the various APIs with the Python Markdown library.
"""
import unittest
import sys
import os
import markdown
from markdown import inlinepatterns
import tempfile
from io import BytesIO, StringIO, TextIOWrapper
import xml.etree.ElementTree as etree

class TestMarkdownBasics(unittest.TestCase):
    """ Tests basics of the Markdown class. """

    def setUp(self):
        """ Create instance of Markdown. """
        self.md = markdown.Markdown()

    def testBlankInput(self):
        """ Test blank input. """
        self.assertEqual(self.md.convert(''), '')

    def testWhitespaceOnly(self):
        """ Test input of only whitespace. """
        self.assertEqual(self.md.convert(' '), '')

    def testSimpleInput(self):
        """ Test simple input. """
        self.assertEqual(self.md.convert('foo'), '<p>foo</p>')

    def testInstanceExtension(self):
        """ Test Extension loading with a class instance. """
        from markdown.extensions.footnotes import FootnoteExtension
        markdown.Markdown(extensions=[FootnoteExtension()])

    def testEntryPointExtension(self):
        """ Test Extension loading with an entry point. """
        markdown.Markdown(extensions=['footnotes'])

    def testDotNotationExtension(self):
        """ Test Extension loading with Name (`path.to.module`). """
        markdown.Markdown(extensions=['markdown.extensions.footnotes'])

    def testDotNotationExtensionWithClass(self):
        """ Test Extension loading with class name (`path.to.module:Class`). """
        markdown.Markdown(extensions=['markdown.extensions.footnotes:FootnoteExtension'])

class TestConvertFile(unittest.TestCase):
    """ Tests of ConvertFile. """

    def setUp(self):
        self.saved = (sys.stdin, sys.stdout)
        sys.stdin = StringIO('foo')
        sys.stdout = TextIOWrapper(BytesIO())

    def tearDown(self):
        (sys.stdin, sys.stdout) = self.saved

    def getTempFiles(self, src):
        """ Return the file names for two temp files. """
        (infd, infile) = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(infd, 'w') as fp:
            fp.write(src)
        (outfd, outfile) = tempfile.mkstemp(suffix='.html')
        return (infile, outfile, outfd)

    def testFileNames(self):
        (infile, outfile, outfd) = self.getTempFiles('foo')
        markdown.markdownFromFile(input=infile, output=outfile)
        with os.fdopen(outfd, 'r') as fp:
            output = fp.read()
        self.assertEqual(output, '<p>foo</p>')

    def testFileObjects(self):
        infile = BytesIO(bytes('foo', encoding='utf-8'))
        outfile = BytesIO()
        markdown.markdownFromFile(input=infile, output=outfile)
        outfile.seek(0)
        self.assertEqual(outfile.read().decode('utf-8'), '<p>foo</p>')

    def testStdinStdout(self):
        markdown.markdownFromFile()
        sys.stdout.seek(0)
        self.assertEqual(sys.stdout.read(), '<p>foo</p>')

class TestBlockParser(unittest.TestCase):
    """ Tests of the BlockParser class. """

    def setUp(self):
        """ Create instance of BlockParser. """
        self.parser = markdown.Markdown().parser

    def testParseChunk(self):
        """ Test `BlockParser.parseChunk`. """
        root = etree.Element('div')
        text = 'foo'
        self.parser.parseChunk(root, text)
        self.assertEqual(markdown.serializers.to_xhtml_string(root), '<div><p>foo</p></div>')

    def testParseDocument(self):
        """ Test `BlockParser.parseDocument`. """
        lines = ['#foo', '', 'bar', '', '    baz']
        tree = self.parser.parseDocument(lines)
        self.assertIsInstance(tree, etree.ElementTree)
        self.assertIs(etree.iselement(tree.getroot()), True)
        self.assertEqual(markdown.serializers.to_xhtml_string(tree.getroot()), '<div><h1>foo</h1><p>bar</p><pre><code>baz\n</code></pre></div>')

class TestBlockParserState(unittest.TestCase):
    """ Tests of the State class for `BlockParser`. """

    def setUp(self):
        self.state = markdown.blockparser.State()

    def testBlankState(self):
        """ Test State when empty. """
        self.assertEqual(self.state, [])

    def testSetSate(self):
        """ Test State.set(). """
        self.state.set('a_state')
        self.assertEqual(self.state, ['a_state'])
        self.state.set('state2')
        self.assertEqual(self.state, ['a_state', 'state2'])

    def testIsSate(self):
        """ Test `State.isstate()`. """
        self.assertEqual(self.state.isstate('anything'), False)
        self.state.set('a_state')
        self.assertEqual(self.state.isstate('a_state'), True)
        self.state.set('state2')
        self.assertEqual(self.state.isstate('state2'), True)
        self.assertEqual(self.state.isstate('a_state'), False)
        self.assertEqual(self.state.isstate('missing'), False)

    def testReset(self):
        """ Test `State.reset()`. """
        self.state.set('a_state')
        self.state.reset()
        self.assertEqual(self.state, [])
        self.state.set('state1')
        self.state.set('state2')
        self.state.reset()
        self.assertEqual(self.state, ['state1'])

class TestHtmlStash(unittest.TestCase):
    """ Test Markdown's `HtmlStash`. """

    def setUp(self):
        self.stash = markdown.util.HtmlStash()
        self.placeholder = self.stash.store('foo')

    def testSimpleStore(self):
        """ Test `HtmlStash.store`. """
        self.assertEqual(self.placeholder, self.stash.get_placeholder(0))
        self.assertEqual(self.stash.html_counter, 1)
        self.assertEqual(self.stash.rawHtmlBlocks, ['foo'])

    def testStoreMore(self):
        """ Test `HtmlStash.store` with additional blocks. """
        placeholder = self.stash.store('bar')
        self.assertEqual(placeholder, self.stash.get_placeholder(1))
        self.assertEqual(self.stash.html_counter, 2)
        self.assertEqual(self.stash.rawHtmlBlocks, ['foo', 'bar'])

    def testReset(self):
        """ Test `HtmlStash.reset`. """
        self.stash.reset()
        self.assertEqual(self.stash.html_counter, 0)
        self.assertEqual(self.stash.rawHtmlBlocks, [])

class Item:
    """ A dummy `Registry` item object for testing. """

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return repr(self.data)

    def __eq__(self, other):
        return self.data == other

class RegistryTests(unittest.TestCase):
    """ Test the processor registry. """

    def testCreateRegistry(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        self.assertEqual(len(r), 1)
        self.assertIsInstance(r, markdown.util.Registry)

    def testRegisterWithoutPriority(self):
        r = markdown.util.Registry()
        with self.assertRaises(TypeError):
            r.register(Item('a'))

    def testIsSorted(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 21)
        self.assertEqual(list(r), ['b', 'a'])

        r.register(Item('c'), 'c', 20.5)
        self.assertEqual(list(r), ['b', 'c', 'a'])
        self.assertEqual(r['a'], 'a')
        self.assertEqual(r.get_index_for_name('c'), 1)
        self.assertEqual(list(r), ['b', 'c', 'a'])

    def testDeregister(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        r.register(Item('c'), 'c', 40)
        self.assertEqual(len(r), 3)
        r.deregister('b')
        self.assertEqual(len(r), 2)
        r.deregister('c', strict=False)
        self.assertEqual(len(r), 1)
        r.deregister('d', strict=False)
        self.assertEqual(len(r), 1)
        with self.assertRaises(ValueError):
            r.deregister('e')
        self.assertEqual(list(r), ['a'])

    def testRegistryContains(self):
        r = markdown.util.Registry()
        item = Item('a')
        r.register(item, 'a', 20)
        self.assertIs('a' in r, True)
        self.assertIn(item, r)
        self.assertNotIn('b', r)

    def testRegistryIter(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(list(r), ['b', 'a'])

    def testRegistryGetItemByIndex(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r[0], 'b')
        self.assertEqual(r[1], 'a')
        with self.assertRaises(IndexError):
            r[3]

    def testRegistryGetItemByItem(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r['a'], 'a')
        self.assertEqual(r['b'], 'b')
        with self.assertRaises(KeyError):
            r['c']

    def testRegistryDelItem(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        with self.assertRaises(TypeError):
            del r[0]
        with self.assertRaises(TypeError):
            del r['a']

    def testGetIndexForName(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b'), 'b', 30)
        self.assertEqual(r.get_index_for_name('a'), 1)
        self.assertEqual(r.get_index_for_name('b'), 0)
        with self.assertRaises(ValueError):
            r.get_index_for_name('c')

    def testRegisterDupplicate(self):
        r = markdown.util.Registry()
        r.register(Item('a'), 'a', 20)
        r.register(Item('b1'), 'b', 10)
        self.assertEqual(list(r), ['a', 'b1'])
        self.assertEqual(len(r), 2)
        r.register(Item('b2'), 'b', 30)
        self.assertEqual(len(r), 2)
        self.assertEqual(list(r), ['b2', 'a'])

class _InlineProcessorThatReturnsAtomicString(inlinepatterns.InlineProcessor):
    """ Return a simple text of `group(1)` of a Pattern. """

    def handleMatch(self, m, data):
        return (markdown.util.AtomicString('<b>atomic</b>'), m.start(0), m.end(0))
