import collections
import contextlib
import datetime
import random
import re
import shlex
import sys
import sysconfig
import warnings
from types import SimpleNamespace
from io import StringIO
from textwrap import dedent
from typing import Any
import unittest
from unittest.mock import patch, mock_open
import subprocess
import tempfile
import pyparsing as pp
from pyparsing import ParserElement, ParseException, ParseFatalException, PyparsingDeprecationWarning
import platform
python_full_version = sys.version_info
python_version = python_full_version[:2]
ppc = pp.pyparsing_common
ppt = pp.pyparsing_test
python_impl = platform.python_implementation()
CPYTHON_ENV = python_impl == 'CPython'
IRON_PYTHON_ENV = python_impl == 'IronPython'
JYTHON_ENV = python_impl == 'Jython'
PYPY_ENV = python_impl == 'PyPy'
_config_vars = sysconfig.get_config_vars()
_config_args = set(shlex.split(_config_vars.get('CONFIG_ARGS', '')))
PYTHON_JIT_ENABLED = '--enable-experimental-jit' in _config_args
PYTHON_FREE_THREADED = _config_vars.get('Py_GIL_DISABLED', 0) == 1
pp.ParserElement.verbose_stacktrace = True

def flatten(nested_list):
    if not isinstance(nested_list, list):
        return [nested_list]
    if not nested_list:
        return nested_list
    return flatten(nested_list[0]) + flatten(nested_list[1:])

class resetting:

    def __init__(self, ob, attrname: str, *attrnames):
        self.ob = ob
        self.unset_attr = object()
        self.save_attrs = [attrname, *attrnames]
        self.save_values = [getattr(ob, name, self.unset_attr) for name in self.save_attrs]

    def __enter__(self):
        pass

    def __exit__(self, *args):
        for (attr, value) in zip(self.save_attrs, self.save_values):
            if value is not self.unset_attr:
                setattr(self.ob, attr, value)
            else:
                delattr(self.ob, attr)

def find_all_re_matches(patt, s):
    ret = []
    start = 0
    if isinstance(patt, str):
        patt = re.compile(patt)
    while True:
        found = patt.search(s, pos=start)
        if found:
            ret.append(found)
            start = found.end()
        else:
            break
    return ret

def current_method_name(level=2):
    import traceback
    stack = traceback.extract_stack(limit=level)
    return stack[0].name

def __():
    return f'{current_method_name(3)}: '

class TestCase(unittest.TestCase):

    @contextlib.contextmanager
    def assertRaisesParseException(self, exc_type=ParseException, expected_msg=None, msg=None):
        if expected_msg is None:
            with self.assertRaises(exc_type, msg=msg) as ctx:
                yield ctx
            return
        pattern = re.escape(expected_msg) if isinstance(expected_msg, str) else expected_msg
        with self.assertRaisesRegex(exc_type, pattern, msg=msg) as ctx:
            yield ctx

    @contextlib.contextmanager
    def assertRaises(self, expected_exception_type: Any, msg: Any=None):
        """
        Simple wrapper to print out the exceptions raised after assertRaises
        """
        with super().assertRaises(expected_exception_type, msg=msg) as ar:
            yield
        if getattr(ar, 'exception', None) is not None:
            print(f'Raised expected exception: {type(ar.exception).__name__}: {ar.exception}')
        else:
            print(f'Expected {expected_exception_type.__name__} exception not raised')
        return ar

    @contextlib.contextmanager
    def assertWarns(self, expected_warning_type: Any, msg: Any=None):
        """
        Simple wrapper to print out the warnings raised after assertWarns
        """
        with super().assertWarns(expected_warning_type, msg=msg) as ar:
            yield
        if getattr(ar, 'warning', None) is not None:
            print(f'Raised expected warning: {type(ar.warning).__name__}: {ar.warning}')
        else:
            print(f'Expected {expected_warning_type.__name__} warning not raised')
        return ar

    @contextlib.contextmanager
    def assertDoesNotWarn(self, warning_type: type=UserWarning, msg: str=None):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('error')
            try:
                yield
            except Exception as e:
                if msg is None:
                    msg = f'unexpected warning {e} raised'
                if isinstance(e, warning_type):
                    self.fail(f'{msg}: {e}')
                else:
                    raise
            finally:
                warnings.simplefilter('default')

class Test02_WithoutPackrat(TestCase, ppt.TestParseResultsAsserts):
    suite_context = None
    save_suite_context = None

    def setUp(self):
        self.suite_context.restore()

    def testScanStringWithOverlap(self):
        parser = pp.Word(pp.alphas, exact=3)
        without_overlaps = sum((t for (t, s, e) in parser.scan_string('ABCDEFGHI'))).as_list()
        self.assertEqual(['ABC', 'DEF', 'GHI'], without_overlaps, msg='scan_string without overlaps failed')
        with_overlaps = sum((t for (t, s, e) in parser.scan_string('ABCDEFGHI', overlap=True))).as_list()
        self.assertEqual(['ABC', 'BCD', 'CDE', 'DEF', 'EFG', 'FGH', 'GHI'], with_overlaps, msg='scan_string with overlaps failed')

    def testCombineWithResultsNames(self):
        from pyparsing import White, alphas, Word
        parser = White(' \t').set_results_name('indent') + Word(alphas).set_results_name('word')
        result = parser.parse_string('    test')
        print(result.dump())
        self.assertParseResultsEquals(result, ['    ', 'test'], {'indent': '    ', 'word': 'test'})
        parser = White(' \t') + Word(alphas).set_results_name('word')
        result = parser.parse_string('    test')
        print(result.dump())
        self.assertParseResultsEquals(result, ['    ', 'test'], {'word': 'test'})

    def testTransformString(self):
        make_int_with_commas = ppc.integer().add_parse_action(lambda t: f'{t[0]:,}')
        lower_case_words = pp.Word(pp.alphas.lower(), as_keyword=True) + pp.Optional(pp.White())
        nested_list = pp.nested_expr().add_parse_action(pp.ParseResults.as_list)
        transformer = make_int_with_commas | nested_list | lower_case_words.suppress()
        in_string = 'I wish to buy 12345 shares of Acme Industries (as a gift to my (ex)wife)'
        print(in_string)
        out_string = transformer.transform_string(in_string)
        print(out_string)
        self.assertEqual('I 12,345 Acme Industries asagifttomyexwife', out_string, msg='failure in transform_string')

    def testTransformStringWithLeadingWhitespace(self):
        sample = '\n\ncheck'
        sample = '    check'
        keywords = pp.one_of('aaa bbb', as_keyword=True)
        ident = ~keywords + pp.Word(pp.alphas)
        ident = pp.Combine(~keywords + pp.Word(pp.alphas))
        ident.add_parse_action(ppc.upcase_tokens)
        transformed = ident.transform_string(sample)
        self.assertEqual(sample.replace('check', 'CHECK'), transformed)

    def testTransformStringWithLeadingNotAny(self):
        sample = 'print a100'
        keywords = set('print read'.split())
        ident = pp.Word(pp.alphas, pp.alphanums).add_condition(lambda t: t[0] not in keywords)
        print(ident.search_string(sample))

    def testTransformStringWithExpectedLeadingWhitespace(self):
        sample1 = '\n\ncheck aaa'
        sample2 = '    check aaa'
        keywords = pp.one_of('aaa bbb', as_keyword=True)
        ident = pp.Word(pp.alphas)
        ident.add_parse_action(ppc.upcase_tokens)
        for sample in (sample1, sample2):
            transformed = (keywords | ident).transform_string(sample)
            self.assertEqual(sample.replace('check', 'CHECK'), transformed)
            print()

    def testTransformStringWithLeadingWhitespaceFromTranslateProject(self):
        from pyparsing import Keyword, Word, alphas, alphanums, Combine
        block_start = (Keyword('{') | Keyword('BEGIN')).set_name('block_start')
        block_end = (Keyword('}') | Keyword('END')).set_name('block_end')
        reserved_words = block_start | block_end
        name_id = Word(alphas, alphanums + '_').set_name('name_id')
        dialog = name_id('block_id') + (Keyword('DIALOGEX') | Keyword('DIALOG'))('block_type')
        string_table = Keyword('STRINGTABLE')('block_type')
        test_string = '\r\nSTRINGTABLE\r\nBEGIN\r\n// Comment\r\nIDS_1 "Copied"\r\nEND\r\n'
        print('Original:')
        print(repr(test_string))
        print('Should match:')
        for parser in (dialog ^ string_table, dialog | string_table):
            result = (reserved_words | parser).transform_string(test_string)
            print(repr(result))
            self.assertEqual(test_string, result, 'Failed whitespace skipping with NotAny and MatchFirst/Or')

    def testCuneiformTransformString(self):

        class Cuneiform(pp.unicode_set):
            """Unicode set for Cuneiform Character Range"""
            _ranges: list[tuple[int, ...]] = [(66432, 66517), (73728, 74751), (74752, 74879)]
        (LPAR, RPAR, COLON, EQ) = map(pp.Suppress, '():=')
        def_ = pp.Keyword('𒁴𒈫', ident_chars=Cuneiform.identbodychars).set_name('def')
        any_keyword = def_
        ident = ~any_keyword + pp.Word(Cuneiform.identchars, Cuneiform.identbodychars, as_keyword=True)
        str_expr = pp.infix_notation(pp.QuotedString('"') | pp.common.integer, [('*', 2, pp.OpAssoc.LEFT), ('+', 2, pp.OpAssoc.LEFT)])
        rvalue = pp.Forward()
        fn_call = (ident + pp.Group(LPAR + pp.Optional(rvalue) + RPAR)).set_name('fn_call')
        rvalue <<= fn_call | ident | str_expr | pp.common.number
        assignment_stmt = ident + EQ + rvalue
        stmt = pp.Group(fn_call | assignment_stmt).set_name('stmt')
        fn_def = pp.Group(def_ + ident + pp.Group(LPAR + pp.Optional(rvalue) + RPAR) + COLON).set_name('fn_def')
        fn_body = pp.IndentedBlock(stmt).set_name('fn_body')
        fn_expr = pp.Group(fn_def + pp.Group(fn_body))
        script = fn_expr[...] + stmt[...]
        cuneiform_hello_world = dedent('\n        𒁴𒈫 𒀄𒂖𒆷𒁎():\n            𒀁 = "𒀄𒂖𒆷𒁎, 𒍟𒁎𒉿𒆷𒀳!\\n" * 3\n            𒄑𒉿𒅔𒋫(𒀁)\n\n        𒀄𒂖𒆷𒁎()\n        ')
        names_map = {'𒄑𒉿𒅔𒋫': 'print'}
        ident.add_parse_action(lambda t: names_map.get(t[0], t[0]))
        def_.add_parse_action(lambda : 'def')
        print('\nconvert Cuneiform Python to executable Python')
        transformed = (def_ | ident).ignore(pp.quoted_string).transform_string(cuneiform_hello_world)
        expected = dedent('\n        def 𒀄𒂖𒆷𒁎():\n            𒀁 = "𒀄𒂖𒆷𒁎, 𒍟𒁎𒉿𒆷𒀳!\\n" * 3\n            print(𒀁)\n\n        𒀄𒂖𒆷𒁎()\n        ')
        print('=================\n' + cuneiform_hello_world + '\n=================\n' + transformed + '\n=================\n')
        self.assertEqual(expected, transformed)

    def testUpdateDefaultWhitespace(self):
        prev_default_whitespace_chars = pp.ParserElement.DEFAULT_WHITE_CHARS
        try:
            pp.dbl_quoted_string.copyDefaultWhiteChars = False
            pp.ParserElement.set_default_whitespace_chars(' \t')
            self.assertEqual(set(' \t'), set(pp.sgl_quoted_string.whiteChars), 'set_default_whitespace_chars did not update sgl_quoted_string')
            self.assertEqual(set(prev_default_whitespace_chars), set(pp.dbl_quoted_string.whiteChars), 'set_default_whitespace_chars updated dbl_quoted_string but should not')
        finally:
            pp.dbl_quoted_string.copyDefaultWhiteChars = True
            pp.ParserElement.set_default_whitespace_chars(prev_default_whitespace_chars)
            self.assertEqual(set(prev_default_whitespace_chars), set(pp.dbl_quoted_string.whiteChars), 'set_default_whitespace_chars updated dbl_quoted_string')
        with ppt.reset_pyparsing_context():
            pp.ParserElement.set_default_whitespace_chars(' \t')
            self.assertNotEqual(set(prev_default_whitespace_chars), set(pp.dbl_quoted_string.whiteChars), 'set_default_whitespace_chars updated dbl_quoted_string but should not')
            EOL = pp.LineEnd().suppress().set_name('EOL')
            identifier = pp.Combine(pp.Word(pp.alphas) + pp.Optional('$'))
            literal = ppc.number | pp.dbl_quoted_string
            expression = literal | identifier
            line_number = ppc.integer
            PRINT = pp.CaselessKeyword('print')
            print_stmt = PRINT - pp.ZeroOrMore(expression | ';')
            statement = print_stmt
            code_line = pp.Group(line_number + statement + EOL)
            program = pp.ZeroOrMore(code_line)
            test = '            10 print 123;\n            20 print 234; 567;\n            30 print 890\n            '
            parsed_program = program.parse_string(test, parse_all=True)
            print(parsed_program.dump())
            self.assertEqual(3, len(parsed_program), 'failed to apply new whitespace chars to existing builtins')

    def testUpdateDefaultWhitespace2(self):
        with ppt.reset_pyparsing_context():
            expr_tests = [(pp.dbl_quoted_string, '"abc"'), (pp.sgl_quoted_string, "'def'"), (ppc.integer, '123'), (ppc.number, '4.56'), (ppc.identifier, 'a_bc')]
            NL = pp.LineEnd()
            for (expr, test_str) in expr_tests:
                parser = pp.Group(expr[1, ...] + pp.Optional(NL))[1, ...]
                test_string = '\n'.join([test_str] * 3)
                result = parser.parse_string(test_string, parse_all=True)
                print(result.dump())
                self.assertEqual(1, len(result), f'failed {test_string!r}')
            pp.ParserElement.set_default_whitespace_chars(' \t')
            for (expr, test_str) in expr_tests:
                parser = pp.Group(expr[1, ...] + pp.Optional(NL))[1, ...]
                test_string = '\n'.join([test_str] * 3)
                result = parser.parse_string(test_string, parse_all=True)
                print(result.dump())
                self.assertEqual(3, len(result), f'failed {test_string!r}')
            pp.ParserElement.set_default_whitespace_chars(' \n\t')
            for (expr, test_str) in expr_tests:
                parser = pp.Group(expr[1, ...] + pp.Optional(NL))[1, ...]
                test_string = '\n'.join([test_str] * 3)
                result = parser.parse_string(test_string, parse_all=True)
                print(result.dump())
                self.assertEqual(1, len(result), f'failed {test_string!r}')

    def testParseCommaSeparatedValues(self):
        testData = ['a,b,c,100.2,,3', 'd, e, j k , m  ', "'Hello, World', f, g , , 5.1,x", 'John Doe, 123 Main St., Cleveland, Ohio', 'Jane Doe, 456 St. James St., Los Angeles , California   ', '']
        testVals = [[(3, '100.2'), (4, ''), (5, '3')], [(2, 'j k'), (3, 'm')], [(0, "'Hello, World'"), (2, 'g'), (3, '')], [(0, 'John Doe'), (1, '123 Main St.'), (2, 'Cleveland'), (3, 'Ohio')], [(0, 'Jane Doe'), (1, '456 St. James St.'), (2, 'Los Angeles'), (3, 'California')]]
        for (line, tests) in zip(testData, testVals):
            print(f'Parsing: {line!r} ->', end=' ')
            results = ppc.comma_separated_list.parse_string(line, parse_all=True)
            print(results)
            for t in tests:
                if not (len(results) > t[0] and results[t[0]] == t[1]):
                    print('$$$', results.dump())
                    print('$$$', results[0])
                self.assertTrue(len(results) > t[0] and results[t[0]] == t[1], f"failed on {line}, item {t[0]:d} s/b '{t[1]}', got '{results.as_list()}'")

    def testScanString(self):
        testdata = '\n            <table border="0" cellpadding="3" cellspacing="3" frame="" width="90%">\n                <tr align="left" valign="top">\n                        <td><b>Name</b></td>\n                        <td><b>IP Address</b></td>\n                        <td><b>Location</b></td>\n                </tr>\n                <tr align="left" valign="top" bgcolor="#c7efce">\n                        <td>time-a.nist.gov</td>\n                        <td>129.6.15.28</td>\n                        <td>NIST, Gaithersburg, Maryland</td>\n                </tr>\n                <tr align="left" valign="top">\n                        <td>time-b.nist.gov</td>\n                        <td>129.6.15.29</td>\n                        <td>NIST, Gaithersburg, Maryland</td>\n                </tr>\n                <tr align="left" valign="top" bgcolor="#c7efce">\n                        <td>time-a.timefreq.bldrdoc.gov</td>\n                        <td>132.163.4.101</td>\n                        <td>NIST, Boulder, Colorado</td>\n                </tr>\n                <tr align="left" valign="top">\n                        <td>time-b.timefreq.bldrdoc.gov</td>\n                        <td>132.163.4.102</td>\n                        <td>NIST, Boulder, Colorado</td>\n                </tr>\n                <tr align="left" valign="top" bgcolor="#c7efce">\n                        <td>time-c.timefreq.bldrdoc.gov</td>\n                        <td>132.163.4.103</td>\n                        <td>NIST, Boulder, Colorado</td>\n                </tr>\n            </table>\n            '
        integer = pp.Word(pp.nums)
        ipAddress = pp.Combine(integer + '.' + integer + '.' + integer + '.' + integer)
        tdStart = pp.Suppress('<td>')
        tdEnd = pp.Suppress('</td>')
        timeServerPattern = tdStart + ipAddress('ipAddr') + tdEnd + tdStart + pp.CharsNotIn('<')('loc') + tdEnd
        servers = [srvr.ipAddr for (srvr, startloc, endloc) in timeServerPattern.scan_string(testdata)]
        print(servers)
        self.assertEqual(['129.6.15.28', '129.6.15.29', '132.163.4.101', '132.163.4.102', '132.163.4.103'], servers, 'failed scan_string()')
        servers = [srvr.ipAddr for (srvr, startloc, endloc) in timeServerPattern.scan_string(testdata, max_matches=3)]
        self.assertEqual(['129.6.15.28', '129.6.15.29', '132.163.4.101'], servers, 'failed scan_string() with max_matches=3')
        foundStringEnds = [r for r in pp.StringEnd().scan_string('xyzzy')]
        print(foundStringEnds)
        self.assertTrue(foundStringEnds, 'Failed to find StringEnd in scan_string')

    def testQuotedStrings(self):
        testData = '\n                \'a valid single quoted string\'\n                \'an invalid single quoted string\n                 because it spans lines\'\n                "a valid double quoted string"\n                "an invalid double quoted string\n                 because it spans lines"\n            '
        print(testData)
        with self.subTest():
            sglStrings = [(t[0], b, e) for (t, b, e) in pp.sgl_quoted_string.scan_string(testData)]
            print(sglStrings)
            self.assertTrue(len(sglStrings) == 1 and (sglStrings[0][1] == 17 and sglStrings[0][2] == 47), 'single quoted string failure')
        with self.subTest():
            dblStrings = [(t[0], b, e) for (t, b, e) in pp.dbl_quoted_string.scan_string(testData)]
            print(dblStrings)
            self.assertTrue(len(dblStrings) == 1 and (dblStrings[0][1] == 154 and dblStrings[0][2] == 184), 'double quoted string failure')
        with self.subTest():
            allStrings = [(t[0], b, e) for (t, b, e) in pp.quoted_string.scan_string(testData)]
            print(allStrings)
            self.assertTrue(len(allStrings) == 2 and (allStrings[0][1] == 17 and allStrings[0][2] == 47) and (allStrings[1][1] == 154 and allStrings[1][2] == 184), 'quoted string failure')
        escapedQuoteTest = '\n                \'This string has an escaped (\\\') quote character\'\n                "This string has an escaped (\\") quote character"\n            '
        with self.subTest():
            sglStrings = [(t[0], b, e) for (t, b, e) in pp.sgl_quoted_string.scan_string(escapedQuoteTest)]
            print(sglStrings)
            self.assertTrue(len(sglStrings) == 1 and (sglStrings[0][1] == 17 and sglStrings[0][2] == 66), f'single quoted string escaped quote failure ({sglStrings[0]})')
        with self.subTest():
            dblStrings = [(t[0], b, e) for (t, b, e) in pp.dbl_quoted_string.scan_string(escapedQuoteTest)]
            print(dblStrings)
            self.assertTrue(len(dblStrings) == 1 and (dblStrings[0][1] == 83 and dblStrings[0][2] == 132), f'double quoted string escaped quote failure ({dblStrings[0]})')
        with self.subTest():
            allStrings = [(t[0], b, e) for (t, b, e) in pp.quoted_string.scan_string(escapedQuoteTest)]
            print(allStrings)
            self.assertTrue(len(allStrings) == 2 and (allStrings[0][1] == 17 and allStrings[0][2] == 66 and (allStrings[1][1] == 83) and (allStrings[1][2] == 132)), f'quoted string escaped quote failure ({[str(s[0]) for s in allStrings]})')
        dblQuoteTest = '\n                \'This string has an doubled (\'\') quote character\'\n                "This string has an doubled ("") quote character"\n            '
        with self.subTest():
            sglStrings = [(t[0], b, e) for (t, b, e) in pp.sgl_quoted_string.scan_string(dblQuoteTest)]
            print(sglStrings)
            self.assertTrue(len(sglStrings) == 1 and (sglStrings[0][1] == 17 and sglStrings[0][2] == 66), f'single quoted string escaped quote failure ({sglStrings[0]})')
        with self.subTest():
            dblStrings = [(t[0], b, e) for (t, b, e) in pp.dbl_quoted_string.scan_string(dblQuoteTest)]
            print(dblStrings)
            self.assertTrue(len(dblStrings) == 1 and (dblStrings[0][1] == 83 and dblStrings[0][2] == 132), f'double quoted string escaped quote failure ({dblStrings[0]})')
        with self.subTest():
            allStrings = [(t[0], b, e) for (t, b, e) in pp.quoted_string.scan_string(dblQuoteTest)]
            print(allStrings)
            self.assertTrue(len(allStrings) == 2 and (allStrings[0][1] == 17 and allStrings[0][2] == 66 and (allStrings[1][1] == 83) and (allStrings[1][2] == 132)), f'quoted string escaped quote failure ({[str(s[0]) for s in allStrings]})')
        with self.subTest():
            with self.assertRaises(ValueError, msg='issue raising error for invalid end_quote_char'):
                expr = pp.QuotedString('"', end_quote_char=' ')
        with self.subTest():
            source = '\n                \'\'\'\n                multiline quote with comment # this is a comment\n                \'\'\'\n                """\n                multiline quote with comment # this is a comment\n                """\n                "single line quote with comment # this is a comment"\n                \'single line quote with comment # this is a comment\'\n            '
            stripped = pp.python_style_comment.ignore(pp.python_quoted_string).suppress().transform_string(source)
            self.assertEqual(source, stripped)

    def testQuotedStringUnquotesAndConvertWhitespaceEscapes(self):
        backslash = chr(92)
        tab = '\t'
        newline = '\n'
        test_string_0 = f'"{backslash}{backslash}n"'
        test_string_1 = f'"{backslash}t{backslash}{backslash}n"'
        test_string_2 = f'"a{backslash}tb"'
        test_string_3 = f'"{backslash}{backslash}{backslash}n"'
        (T, F) = (True, False)
        for test_parameters in ((T, T, test_string_0, [backslash, 'n']), (T, F, test_string_0, [backslash, 'n']), (F, F, test_string_0, ['"', backslash, backslash, 'n', '"']), (T, T, test_string_1, [tab, backslash, 'n']), (T, F, test_string_1, ['t', backslash, 'n']), (F, F, test_string_1, ['"', backslash, 't', backslash, backslash, 'n', '"']), (T, T, test_string_2, ['a', tab, 'b']), (T, F, test_string_2, ['a', 't', 'b']), (F, F, test_string_2, ['"', 'a', backslash, 't', 'b', '"']), (T, T, test_string_3, [backslash, newline]), (T, F, test_string_3, [backslash, 'n']), (F, F, test_string_3, ['"', backslash, backslash, backslash, 'n', '"'])):
            (unquote_results, convert_ws_escapes, test_string, expected_list) = test_parameters
            test_description = f'Testing with parameters {test_parameters}'
            with self.subTest(msg=test_description):
                print(test_description)
                print(f'unquote_results: {unquote_results}\nconvert_whitespace_escapes: {convert_ws_escapes}')
                qs_expr = pp.QuotedString(quote_char='"', esc_char='\\', unquote_results=unquote_results, convert_whitespace_escapes=convert_ws_escapes)
                result = qs_expr.parse_string(test_string)
                print('Results:')
                control_chars = {newline: '<NEWLINE>', backslash: '<BACKSLASH>', tab: '<TAB>'}
                print(f"[{', '.join((control_chars.get(c, repr(c)) for c in result[0]))}]")
                self.assertEqual(expected_list, list(result[0]))
                print()

    def testPythonQuotedStrings(self):
        (success1, _) = pp.python_quoted_string.run_tests(['"""xyz"""', '"""xyz\n            """', '"""xyz "" """', '"""xyz ""\n            """', '"""xyz " """', '"""xyz "\n            """', '"""xyz \\"""\n\n            """', "'''xyz'''", "'''xyz\n            '''", "'''xyz '' '''", "'''xyz ''\n            '''", "'''xyz ' '''", "'''xyz '\n            '''", "'''xyz \\'''\n            '''"])
        print('\n\nFailure tests')
        (success2, _) = pp.python_quoted_string.run_tests(['"xyz"""'], failure_tests=True)
        self.assertTrue(success1 and success2, 'Python quoted string matching failure')

    def testCaselessOneOf(self):
        caseless1 = pp.one_of('d a b c aA B A C', caseless=True)
        caseless2 = pp.one_of('d a b c Aa B A C', caseless=True)
        for expression in (caseless1, caseless2):
            result = expression[...].parse_string('AAaaAaaA', parse_all=True)
            self.assertEqual(['aa'] * 4, [token.casefold() for token in result], 'caseless one_of failed')

    def testCStyleCommentParser(self):
        print('verify processing of C-style /* */ comments')
        testdata = f"\n        /* */\n        /** **/\n        /**/\n        /*{'*' * 1000000}*/\n        /****/\n        /* /*/\n        /** /*/\n        /*** /*/\n        /*\n         ablsjdflj\n         */\n        "
        for test_expr in (pp.c_style_comment, pp.cpp_style_comment, pp.java_style_comment):
            with self.subTest('parse test - /* */ comments', test_expr=test_expr):
                found_matches = [len(t[0]) for (t, s, e) in test_expr.scan_string(testdata)]
                self.assertEqual([5, 7, 4, 1000004, 6, 6, 7, 8, 33], found_matches, f'only found {test_expr} lengths {found_matches}')
                found_lines = [pp.lineno(s, testdata) for (t, s, e) in test_expr.scan_string(testdata)]
                self.assertEqual([2, 3, 4, 5, 6, 7, 8, 9, 10], found_lines, f'only found {test_expr} on lines {found_lines}')

    def testHtmlCommentParser(self):
        print('verify processing of HTML comments')
        test_expr = pp.html_comment
        testdata = '\n        <!-- -->\n        <!--- --->\n        <!---->\n        <!----->\n        <!------>\n        <!-- /-->\n        <!--- /-->\n        <!---- /-->\n        <!---- /- ->\n        <!---- / -- >\n        <!--\n         ablsjdflj\n         -->\n        '
        found_matches = [len(t[0]) for (t, s, e) in test_expr.scan_string(testdata)]
        self.assertEqual([8, 10, 7, 8, 9, 9, 10, 11, 79], found_matches, f'only found {test_expr} lengths {found_matches}')
        found_lines = [pp.lineno(s, testdata) for (t, s, e) in pp.html_comment.scan_string(testdata)]
        self.assertEqual([2, 3, 4, 5, 6, 7, 8, 9, 10], found_lines, f'only found HTML comments on lines {found_lines}')

    def testDoubleSlashCommentParser(self):
        print('verify processing of C++ and Java comments - // comments')
        testdata = '\n            // comment1\n            // comment2 \\\n            still comment 2\n            // comment 3\n            '
        for test_expr in (pp.dbl_slash_comment, pp.cpp_style_comment, pp.java_style_comment):
            with self.subTest('parse test - // comments', test_expr=test_expr):
                found_matches = [len(t[0]) for (t, s, e) in test_expr.scan_string(testdata)]
                self.assertEqual([11, 41, 12], found_matches, f'only found {test_expr} lengths {found_matches}')
                found_lines = [pp.lineno(s, testdata) for (t, s, e) in test_expr.scan_string(testdata)]
                self.assertEqual([2, 3, 5], found_lines, f'only found {test_expr} on lines {found_lines}')

    def testParseExpressionResults(self):
        a = pp.Word('a', pp.alphas).set_name('A')
        b = pp.Word('b', pp.alphas).set_name('B')
        c = pp.Word('c', pp.alphas).set_name('C')
        ab = (a + b).set_name('AB')
        abc = (ab + c).set_name('ABC')
        word = pp.Word(pp.alphas).set_name('word')
        words = pp.Group(pp.OneOrMore(~a + word)).set_name('words')
        phrase = words('Head') + pp.Group(a + pp.Optional(b + pp.Optional(c)))('ABC') + words('Tail')
        results = phrase.parse_string('xavier yeti alpha beta charlie will beaver', parse_all=True)
        print(results, results.Head, results.ABC, results.Tail)
        for (key, ln) in [('Head', 2), ('ABC', 3), ('Tail', 2)]:
            self.assertEqual(ln, len(results[key]), f'expected {ln:d} elements in {key}, found {results[key]}')

    def testParseKeyword(self):
        kw = pp.Keyword('if')
        lit = pp.Literal('if')

        def test(s, litShouldPass, kwShouldPass):
            print('Test', s)
            print('Match Literal', end=' ')
            try:
                print(lit.parse_string(s, parse_all=False))
            except Exception:
                print('failed')
                if litShouldPass:
                    self.fail(f'Literal failed to match {s}, should have')
            else:
                if not litShouldPass:
                    self.fail(f'Literal matched {s}, should not have')
            print('Match Keyword', end=' ')
            try:
                print(kw.parse_string(s, parse_all=False))
            except Exception:
                print('failed')
                if kwShouldPass:
                    self.fail(f'Keyword failed to match {s}, should have')
            else:
                if not kwShouldPass:
                    self.fail(f'Keyword matched {s}, should not have')
        test('ifOnlyIfOnly', True, False)
        test('if(OnlyIfOnly)', True, True)
        test('if (OnlyIf Only)', True, True)
        kw = pp.Keyword('if', caseless=True)
        test('IFOnlyIfOnly', False, False)
        test('If(OnlyIfOnly)', False, True)
        test('iF (OnlyIf Only)', False, True)
        with self.assertRaises(ValueError, msg='failed to warn empty string passed to Keyword'):
            kw = pp.Keyword('')

    def testParseExpressionResultsAccumulate(self):
        num = pp.Word(pp.nums).set_name('num')('base10*')
        hexnum = pp.Combine('0x' + pp.Word(pp.nums)).set_name('hexnum')('hex*')
        name = pp.Word(pp.alphas).set_name('word')('word*')
        list_of_num = pp.DelimitedList(hexnum | num | name, ',')
        tokens = list_of_num.parse_string('1, 0x2, 3, 0x4, aaa', parse_all=True)
        print(tokens.dump())
        self.assertParseResultsEquals(tokens, expected_list=['1', '0x2', '3', '0x4', 'aaa'], expected_dict={'base10': ['1', '3'], 'hex': ['0x2', '0x4'], 'word': ['aaa']})
        lbrack = pp.Literal('(').suppress()
        rbrack = pp.Literal(')').suppress()
        integer = pp.Word(pp.nums).set_name('int')
        variable = pp.Word(pp.alphas, max=1).set_name('variable')
        relation_body_item = variable | integer | pp.quoted_string().set_parse_action(pp.remove_quotes)
        relation_name = pp.Word(pp.alphas + '_', pp.alphanums + '_')
        relation_body = lbrack + pp.Group(pp.DelimitedList(relation_body_item)) + rbrack
        Goal = pp.Dict(pp.Group(relation_name + relation_body))
        Comparison_Predicate = pp.Group(variable + pp.one_of('< >') + integer)('pred*')
        Query = Goal('head') + ':-' + pp.DelimitedList(Goal | Comparison_Predicate)
        test = 'Q(x,y,z):-Bloo(x,"Mitsis",y),Foo(y,z,1243),y>28,x<12,x>3'
        queryRes = Query.parse_string(test, parse_all=True)
        print(queryRes.dump())
        self.assertParseResultsEquals(queryRes.pred, expected_list=[['y', '>', '28'], ['x', '<', '12'], ['x', '>', '3']], msg=f'Incorrect list for attribute pred, {queryRes.pred.as_list()}')

    def testReStringRange(self):
        testCases = ('[A-Z]', '[A-A]', '[A-Za-z]', '[A-z]', '[\\ -\\~]', '[\\0x20-0]', '[\\0x21-\\0x7E]', '[\\0xa1-\\0xfe]', '[\\040-0]', '[A-Za-z0-9]', '[A-Za-z0-9_]', '[A-Za-z0-9_$]', '[A-Za-z0-9_$\\-]', '[^0-9\\\\]', '[a-zA-Z]', '[/\\^~]', '[=\\+\\-!]', '[A-]', '[-A]', '[\\x21]', '[а-яА-ЯёЁA-Z$_\\041α-ω]', '[\\0xc0-\\0xd6\\0xd8-\\0xf6\\0xf8-\\0xff]', '[\\0xa1-\\0xbf\\0xd7\\0xf7]', '[\\0xc0-\\0xd6\\0xd8-\\0xf6\\0xf8-\\0xff]', '[\\0xa1-\\0xbf\\0xd7\\0xf7]', '[\\\\[\\]\\/\\-\\*\\.\\$\\+\\^\\?()~ ]')
        expectedResults = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'A', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz', ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~', ' !"#$%&\'()*+,-./0', '!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~', '¡¢£¤¥¦§¨©ª«¬\xad®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ', ' !"#$%&\'()*+,-./0', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_$', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_$-', '0123456789\\', 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', '/^~', '=+-!', 'A-', '-A', '!', 'абвгдежзийклмнопрстуфхцчшщъыьэюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯёЁABCDEFGHIJKLMNOPQRSTUVWXYZ$_!αβγδεζηθικλμνξοπρςστυφχψω', 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ', '¡¢£¤¥¦§¨©ª«¬\xad®¯°±²³´µ¶·¸¹º»¼½¾¿×÷', pp.alphas8bit, pp.punc8bit, '\\[]/-*.$+^?()~ ')
        for test in zip(testCases, expectedResults):
            (t, exp) = test
            res = pp.srange(t)
            self.assertEqual(exp, res, f"srange error, srange({t!r})->'{res!r}', expected '{exp!r}'")

    def testSkipToParserTests(self):
        thingToFind = pp.Literal('working')
        testExpr = pp.SkipTo(pp.Literal(';'), include=True, ignore=pp.c_style_comment) + thingToFind

        def test_parse(someText):
            print(testExpr.parse_string(someText, parse_all=True))
        test_parse('some text /* comment with ; in */; working')
        test_parse('some text /* comment with ; in */some other stuff; working')
        testExpr = pp.SkipTo(pp.Literal(';'), include=True, ignore=pp.c_style_comment, fail_on='other') + thingToFind
        test_parse('some text /* comment with ; in */; working')
        with self.assertRaisesParseException():
            test_parse('some text /* comment with ; in */some other stuff; working')
        text = 'prefixDATAsuffix'
        data = pp.Literal('DATA')
        suffix = pp.Literal('suffix')
        expr = pp.SkipTo(data + suffix)('prefix') + data + suffix
        result = expr.parse_string(text, parse_all=True)
        self.assertTrue(isinstance(result.prefix, str), 'SkipTo created with wrong saveAsList attribute')
        alpha_word = (~pp.Literal('end') + pp.Word(pp.alphas, as_keyword=True)).set_name('alpha')
        num_word = pp.Word(pp.nums, as_keyword=True).set_name('int')

        def test(expr, test_string, expected_list, expected_dict):
            if (expected_list, expected_dict) == (None, None):
                with self.assertRaises(Exception, msg=f'{expr} failed to parse {test_string!r}'):
                    expr.parse_string(test_string, parse_all=True)
            else:
                result = expr.parse_string(test_string, parse_all=True)
                self.assertParseResultsEquals(result, expected_list=expected_list, expected_dict=expected_dict)
        e = ... + pp.Literal('end')
        test(e, 'start 123 end', ['start 123 ', 'end'], {'_skipped': ['start 123 ']})
        e = pp.Suppress(...) + pp.Literal('end')
        test(e, 'start 123 end', ['end'], {})
        e = pp.Literal('start') + ... + pp.Literal('end')
        test(e, 'start 123 end', ['start', '123 ', 'end'], {'_skipped': ['123 ']})
        e = ... + pp.Literal('middle') + ... + pp.Literal('end')
        test(e, 'start 123 middle 456 end', ['start 123 ', 'middle', '456 ', 'end'], {'_skipped': ['start 123 ', '456 ']})
        e = pp.Suppress(...) + pp.Literal('middle') + ... + pp.Literal('end')
        test(e, 'start 123 middle 456 end', ['middle', '456 ', 'end'], {'_skipped': ['456 ']})
        e = pp.Literal('start') + ...
        test(e, 'start 123 end', None, None)
        e = pp.And(['start', ..., 'end'])
        test(e, 'start 123 end', ['start', '123 ', 'end'], {'_skipped': ['123 ']})
        e = pp.And([..., 'end'])
        test(e, 'start 123 end', ['start 123 ', 'end'], {'_skipped': ['start 123 ']})
        e = 'start' + (num_word | ...) + 'end'
        test(e, 'start 456 end', ['start', '456', 'end'], {})
        test(e, 'start 123 456 end', ['start', '123', '456 ', 'end'], {'_skipped': ['456 ']})
        test(e, 'start end', ['start', '', 'end'], {'_skipped': ['missing <int>']})
        e = 'start' + (alpha_word[...] & num_word[...] | ...) + 'end'
        test(e, 'start 456 red end', ['start', '456', 'red', 'end'], {})
        test(e, 'start red 456 end', ['start', 'red', '456', 'end'], {})
        test(e, 'start 456 red + end', ['start', '456', 'red', '+ ', 'end'], {'_skipped': ['+ ']})
        test(e, 'start red end', ['start', 'red', 'end'], {})
        test(e, 'start 456 end', ['start', '456', 'end'], {})
        test(e, 'start end', ['start', 'end'], {})
        test(e, 'start 456 + end', ['start', '456', '+ ', 'end'], {'_skipped': ['+ ']})
        e = 'start' + (alpha_word[1, ...] & num_word[1, ...] | ...) + 'end'
        test(e, 'start 456 red end', ['start', '456', 'red', 'end'], {})
        test(e, 'start red 456 end', ['start', 'red', '456', 'end'], {})
        test(e, 'start 456 red + end', ['start', '456', 'red', '+ ', 'end'], {'_skipped': ['+ ']})
        test(e, 'start red end', ['start', 'red ', 'end'], {'_skipped': ['red ']})
        test(e, 'start 456 end', ['start', '456 ', 'end'], {'_skipped': ['456 ']})
        test(e, 'start end', ['start', '', 'end'], {'_skipped': ['missing <{{alpha}... & {int}...}>']})
        test(e, 'start 456 + end', ['start', '456 + ', 'end'], {'_skipped': ['456 + ']})
        e = 'start' + (alpha_word | ...) + (num_word | ...) + 'end'
        test(e, 'start red 456 end', ['start', 'red', '456', 'end'], {})
        test(e, 'start red end', ['start', 'red', '', 'end'], {'_skipped': ['missing <int>']})
        test(e, 'start 456 end', ['start', '', '456', 'end'], {'_skipped': ['missing <alpha>']})
        test(e, 'start end', ['start', '', '', 'end'], {'_skipped': ['missing <alpha>', 'missing <int>']})
        e = pp.Literal('start') + ... + '+' + ... + 'end'
        test(e, 'start red + 456 end', ['start', 'red ', '+', '456 ', 'end'], {'_skipped': ['red ', '456 ']})

    def testSkipToPreParseIgnoreExprs(self):
        from pyparsing import Word, alphanums, python_style_comment
        some_grammar = Word(alphanums) + ':=' + ... + ';'
        some_grammar.ignore(python_style_comment)
        try:
            result = some_grammar.parse_string('                var1 := 2 # 3; <== this semi-colon will match!\n                      + 1;\n                ', parse_all=True)
        except ParseException as pe:
            print(pe.explain())
            raise
        else:
            print(result.dump())

    def testSkipToIgnoreExpr2(self):
        (a, star) = pp.Literal.using_each('a*')
        wrapper = a + ... + a
        expr = star + pp.SkipTo(star, ignore=wrapper) + star
        self.assertParseAndCheckList(expr, '*a_*_a*', ['*', 'a_*_a', '*'])

    def testEllipsisRepetition(self):
        word = pp.Word(pp.alphas).set_name('word')
        num = pp.Word(pp.nums).set_name('num')
        exprs = [word[...] + num, word * ... + num, word[0, ...] + num, word[1, ...] + num, word[2, ...] + num, word[..., 3] + num, word[2] + num]
        expected_res = ['([abcd]+ )*\\d+', '([abcd]+ )*\\d+', '([abcd]+ )*\\d+', '([abcd]+ )+\\d+', '([abcd]+ ){2,}\\d+', '([abcd]+ ){0,3}\\d+', '([abcd]+ ){2}\\d+']
        tests = ['aa bb cc dd 123', 'bb cc dd 123', 'cc dd 123', 'dd 123', '123']
        all_success = True
        for (expr, expected_re) in zip(exprs, expected_res):
            successful_tests = [t for t in tests if re.match(expected_re, t)]
            failure_tests = [t for t in tests if not re.match(expected_re, t)]
            (success1, _) = expr.run_tests(successful_tests)
            (success2, _) = expr.run_tests(failure_tests, failure_tests=True)
            all_success = all_success and success1 and success2
            if not all_success:
                print('Failed expression:', expr)
                break
        self.assertTrue(all_success, 'failed getItem_ellipsis test')

    def testEllipsisRepetitionWithResultsNames(self):
        label = pp.Word(pp.alphas)
        val = ppc.integer()
        parser = label('label') + pp.ZeroOrMore(val)('values')
        (_, results) = parser.run_tests('\n            a 1\n            b 1 2 3\n            c\n            ')
        expected = [(['a', 1], {'label': 'a', 'values': [1]}), (['b', 1, 2, 3], {'label': 'b', 'values': [1, 2, 3]}), (['c'], {'label': 'c', 'values': []})]
        for (obs, exp) in zip(results, expected):
            (test, result) = obs
            (exp_list, exp_dict) = exp
            self.assertParseResultsEquals(result, expected_list=exp_list, expected_dict=exp_dict)
        parser = label('label') + val[...]('values')
        (_, results) = parser.run_tests('\n            a 1\n            b 1 2 3\n            c\n            ')
        expected = [(['a', 1], {'label': 'a', 'values': [1]}), (['b', 1, 2, 3], {'label': 'b', 'values': [1, 2, 3]}), (['c'], {'label': 'c', 'values': []})]
        for (obs, exp) in zip(results, expected):
            (test, result) = obs
            (exp_list, exp_dict) = exp
            self.assertParseResultsEquals(result, expected_list=exp_list, expected_dict=exp_dict)
        pt = pp.Group(val('x') + pp.Suppress(',') + val('y'))
        parser = label('label') + pt[...]('points')
        (_, results) = parser.run_tests('\n            a 1,1\n            b 1,1 2,2 3,3\n            c\n            ')
        expected = [(['a', [1, 1]], {'label': 'a', 'points': [{'x': 1, 'y': 1}]}), (['b', [1, 1], [2, 2], [3, 3]], {'label': 'b', 'points': [{'x': 1, 'y': 1}, {'x': 2, 'y': 2}, {'x': 3, 'y': 3}]}), (['c'], {'label': 'c', 'points': []})]
        for (obs, exp) in zip(results, expected):
            (test, result) = obs
            (exp_list, exp_dict) = exp
            self.assertParseResultsEquals(result, expected_list=exp_list, expected_dict=exp_dict)

    def testCustomQuotes(self):
        testString = '\n            sdlfjs :sdf\\:jls::djf: sl:kfsjf\n            sdlfjs -sdf\\:jls::--djf: sl-kfsjf\n            sdlfjs -sdf\\:::jls::--djf: sl:::-kfsjf\n            sdlfjs ^sdf\\:jls^^--djf^ sl-kfsjf\n            sdlfjs ^^^==sdf\\:j=lz::--djf: sl=^^=kfsjf\n            sdlfjs ==sdf\\:j=ls::--djf: sl==kfsjf^^^\n        '
        print(testString)
        colonQuotes = pp.QuotedString(':', '\\', '::')
        dashQuotes = pp.QuotedString('-', '\\', '--')
        hatQuotes = pp.QuotedString('^', '\\')
        hatQuotes1 = pp.QuotedString('^', '\\', '^^')
        dblEqQuotes = pp.QuotedString('==', '\\')

        def test(label, quoteExpr, expected):
            print(label)
            print(quoteExpr.search_string(testString))
            print(quoteExpr.search_string(testString)[0][0])
            print(f'{expected}')
            self.assertEqual(expected, quoteExpr.search_string(testString)[0][0], f"failed to match {quoteExpr}, expected '{expected}', got '{quoteExpr.search_string(testString)[0]}'")
            print()
        test('colonQuotes', colonQuotes, 'sdf:jls:djf')
        test('dashQuotes', dashQuotes, 'sdf:jls::-djf: sl')
        test('hatQuotes', hatQuotes, 'sdf:jls')
        test('hatQuotes1', hatQuotes1, 'sdf:jls^--djf')
        test('dblEqQuotes', dblEqQuotes, 'sdf:j=ls::--djf: sl')
        test('::: quotes', pp.QuotedString(':::'), 'jls::--djf: sl')
        test('==-- quotes', pp.QuotedString('==', end_quote_char='--'), 'sdf\\:j=lz::')
        test('^^^ multiline quotes', pp.QuotedString('^^^', multiline=True), '==sdf\\:j=lz::--djf: sl=^^=kfsjf\n            sdlfjs ==sdf\\:j=ls::--djf: sl==kfsjf')
        with self.assertRaises(ValueError):
            pp.QuotedString('', '\\')

    def testCustomQuotes2(self):
        qs = pp.QuotedString(quote_char='.[', end_quote_char='].')
        self.assertParseAndCheckList(qs, '.[...].', ['...'])
        self.assertParseAndCheckList(qs, '.[].', [''])
        self.assertParseAndCheckList(qs, '.[]].', [']'])
        self.assertParseAndCheckList(qs, '.[]]].', [']]'])
        qs = pp.QuotedString(quote_char='+*', end_quote_char='*+')
        self.assertParseAndCheckList(qs, '+*...*+', ['...'])
        self.assertParseAndCheckList(qs, '+**+', [''])
        self.assertParseAndCheckList(qs, '+***+', ['*'])
        self.assertParseAndCheckList(qs, '+****+', ['**'])
        qs = pp.QuotedString(quote_char='*/', end_quote_char='/*')
        self.assertParseAndCheckList(qs, '*/.../*', ['...'])
        self.assertParseAndCheckList(qs, '*//*', [''])
        self.assertParseAndCheckList(qs, '*///*', ['/'])
        self.assertParseAndCheckList(qs, '*////*', ['//'])

    def testRepeater(self):
        first = pp.Word('abcdef').set_name('word1')
        bridge = pp.Word(pp.nums).set_name('number')
        second = pp.match_previous_literal(first).set_name('repeat(word1Literal)')
        seq = first + bridge + second
        tests = [('abc12abc', True), ('abc12aabc', False), ('abc12cba', True), ('abc12bca', True)]
        for (tst, expected) in tests:
            found = False
            for (tokens, start, end) in seq.scan_string(tst):
                (f, b, s) = tokens
                print(f, b, s)
                found = True
            if not found:
                print('No literal match in', tst)
            self.assertEqual(expected, found, f'Failed repeater for test: {tst}, matching {seq}')
        print()
        second = pp.match_previous_expr(first).set_name('repeat(word1expr)')
        seq = first + bridge + second
        tests = [('abc12abc', True), ('abc12cba', False), ('abc12abcdef', False)]
        for (tst, expected) in tests:
            found = False
            for (tokens, start, end) in seq.scan_string(tst):
                print(tokens)
                found = True
            if not found:
                print('No expression match in', tst)
            self.assertEqual(expected, found, f'Failed repeater for test: {tst}, matching {seq}')
        print()
        first = pp.Word('abcdef').set_name('word1')
        bridge = pp.Word(pp.nums).set_name('number')
        second = pp.match_previous_expr(first).set_name('repeat(word1)')
        seq = first + bridge + second
        csFirst = seq.set_name('word-num-word')
        csSecond = pp.match_previous_expr(csFirst)
        compoundSeq = csFirst + ':' + csSecond
        print(compoundSeq)
        tests = [('abc12abc:abc12abc', True), ('abc12cba:abc12abc', False), ('abc12abc:abc12abcdef', False)]
        for (tst, expected) in tests:
            found = False
            for (tokens, start, end) in compoundSeq.scan_string(tst):
                print('match:', tokens)
                found = True
                break
            if not found:
                print('No expression match in', tst)
            self.assertEqual(expected, found, f'Failed repeater for test: {tst}, matching {seq}')
        print()
        eFirst = pp.Word(pp.nums)
        eSecond = pp.match_previous_expr(eFirst)
        eSeq = eFirst + ':' + eSecond
        tests = [('1:1A', True), ('1:10', False)]
        for (tst, expected) in tests:
            found = False
            for (tokens, start, end) in eSeq.scan_string(tst):
                print(tokens)
                found = True
            if not found:
                print('No match in', tst)
            self.assertEqual(expected, found, f'Failed repeater for test: {tst}, matching {seq}')

    def testRepeater2(self):
        """test match_previous_literal with empty repeater"""
        first = pp.Optional(pp.Word('abcdef').set_name('words1'))
        bridge = pp.Word(pp.nums).set_name('number')
        second = pp.match_previous_literal(first).set_name('repeat(word1Literal)')
        seq = first + bridge + second
        tst = '12'
        expected = ['12']
        result = seq.parse_string(tst, parse_all=True)
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=expected)

    def testRepeater3(self):
        """test match_previous_literal with multiple repeater tokens"""
        first = pp.Word('a') + pp.Word('d')
        bridge = pp.Word(pp.nums).set_name('number')
        second = pp.match_previous_literal(first)
        seq = first + bridge + second
        tst = 'aaaddd12aaaddd'
        expected = ['aaa', 'ddd', '12', 'aaa', 'ddd']
        result = seq.parse_string(tst, parse_all=True)
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=expected)

    def testRepeater4(self):
        """test match_previous_expr with multiple repeater tokens"""
        first = pp.Group(pp.Word(pp.alphas) + pp.Word(pp.alphas))
        bridge = pp.Word(pp.nums)
        second = pp.match_previous_expr(first)
        expr = first + bridge.suppress() + second
        tst = 'aaa ddd 12 aaa ddd'
        expected = [['aaa', 'ddd'], ['aaa', 'ddd']]
        result = expr.parse_string(tst, parse_all=True)
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=expected)

    def testRepeater5(self):
        """a simplified testRepeater4 to examine match_previous_expr with a single repeater token"""
        first = pp.Word(pp.alphas)
        bridge = pp.Word(pp.nums)
        second = pp.match_previous_expr(first)
        expr = first + bridge.suppress() + second
        tst = 'aaa 12 aaa'
        expected = tst.replace('12', '').split()
        result = expr.parse_string(tst, parse_all=True)
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=expected)

    def testRecursiveCombine(self):
        testInput = 'myc(114)r(11)dd'
        stream = pp.Forward()
        stream <<= pp.Optional(pp.Word(pp.alphas)) + pp.Optional('(' + pp.Word(pp.nums) + ')' + stream)
        expected = [''.join(stream.parse_string(testInput, parse_all=True))]
        print(expected)
        stream = pp.Forward()
        stream << pp.Combine(pp.Optional(pp.Word(pp.alphas)) + pp.Optional('(' + pp.Word(pp.nums) + ')' + stream))
        testVal = stream.parse_string(testInput, parse_all=True)
        print(testVal)
        self.assertParseResultsEquals(testVal, expected_list=expected)

    def testRepeaterRecursiveWhitespace(self):
        """test match_previous_expr with recursive whitespace"""
        COLON = pp.Suppress(':').set_name(':')
        first = pp.Char(pp.nums)
        second = pp.match_previous_expr(first)
        expr = first + COLON + second
        expr.leave_whitespace(recursive=True)
        tests = [('1:1', True), ('1: 1', False), ('1:2', False), ('1:a', False)]
        for (tst, expected) in tests:
            if expected:
                expected_int_list = [t.strip() for t in tst.split(':')]
                self.assertParseAndCheckList(expr, tst, expected_int_list, msg=f'Failed recursive whitespace repeater test, expected pass:  expr={expr!r} tst={tst!r}')
            else:
                with self.assertRaisesParseException(msg=f'Failed recursive whitespace repeater test, expected fail:  expr={expr!r} tst={tst!r}'):
                    expr.parse_string(tst)

    def testRepeaterRecursiveFalse(self):
        """test match_previous_expr with recursive=False"""
        COLON = pp.Suppress(':').set_name(':')
        first = pp.Char(pp.nums)
        second = pp.match_previous_expr(first)
        expr = first + COLON + second
        expr.leave_whitespace(recursive=False)
        tests = [('1:1', True), ('1: 1', True), ('1:2', False)]
        for (tst, expected) in tests:
            if expected:
                expected_int_list = [t.strip() for t in tst.split(':')]
                self.assertParseAndCheckList(expr, tst, expected_int_list, msg=f'Failed recursive=False repeater test, expected pass: expr={expr!r} tst={tst!r}')
            else:
                with self.assertRaisesParseException(msg=f'Failed recursive=False repeater test, expected fail: expr={expr!r} tst={tst!r}'):
                    expr.parse_string(tst)

    def testRepeaterPreservesParseAction(self):
        """test match_previous_expr preserves existing parse actions"""
        COLON = pp.Suppress(':').set_name(':')
        first = ppc.integer
        second = pp.match_previous_expr(first)
        expr = first + COLON + second
        expr.leave_whitespace(recursive=True)
        tests = [('1:1', True), ('1: 1', False), ('1:2', False)]
        for (tst, expected) in tests:
            if expected:
                expected_int_list = [int(t) for t in tst.split(':')]
                self.assertParseAndCheckList(expr, tst, expected_int_list, msg=f'Failed parse action preservation repeater test, expected pass: expr={expr!r} tst={tst!r}')
            else:
                with self.assertRaisesParseException(msg=f'Failed parse action preservation repeater test, expected fail: expr={expr!r} tst={tst!r}'):
                    expr.parse_string(tst)

    def testSetNameToStrAndNone(self):
        wd = pp.Word(pp.alphas)
        with self.subTest():
            self.assertEqual('W:(A-Za-z)', wd.name)
        with self.subTest():
            wd.set_name('test_word')
            self.assertEqual('test_word', wd.name)
        with self.subTest():
            wd.set_name(None)
            self.assertEqual('W:(A-Za-z)', wd.name)
        with self.subTest():
            wd.name = 'test_word'
            self.assertEqual('test_word', wd.name)
        with self.subTest():
            wd.name = None
            self.assertEqual('W:(A-Za-z)', wd.name)

    def testCombineSetName(self):
        ab = pp.Combine(pp.Literal('a').set_name('AAA') | pp.Literal('b').set_name('BBB')).set_name('AB')
        self.assertEqual('AB', ab.name)
        self.assertEqual('AB', str(ab))
        with self.assertRaisesParseException(expected_msg='Expected AB'):
            ab.parse_string('C')

    def testHTMLEntities(self):
        html_source = dedent('            This &amp; that\n            2 &gt; 1\n            0 &lt; 1\n            Don&apos;t get excited!\n            I said &quot;Don&apos;t get excited!&quot;\n            Copyright &copy; 2021\n            Dot &longrightarrow; &dot;\n            ')
        transformer = pp.common_html_entity().add_parse_action(pp.replace_html_entity)
        transformed = transformer.transform_string(html_source)
        print(transformed)
        expected = dedent('            This & that\n            2 > 1\n            0 < 1\n            Don\'t get excited!\n            I said "Don\'t get excited!"\n            Copyright © 2021\n            Dot ⟶ ˙\n            ')
        self.assertEqual(expected, transformed)

    def testInfixNotationBasicArithEval(self):
        import ast
        integer = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        variable = pp.Word(pp.alphas, exact=1)
        operand = integer | variable
        expop = pp.Literal('^')
        signop = pp.one_of('+ -')
        multop = pp.one_of('* /')
        plusop = pp.one_of('+ -')
        factop = pp.Literal('!')
        expr = pp.infix_notation(operand, [(factop, 1, pp.OpAssoc.LEFT), (expop, 2, pp.OpAssoc.RIGHT), (signop, 1, pp.OpAssoc.RIGHT), (multop, 2, pp.OpAssoc.LEFT), (plusop, 2, pp.OpAssoc.LEFT)])
        test = ['9 + 2 + 3', '9 + 2 * 3', '(9 + 2) * 3', '(9 + -2) * 3', '(9 + --2) * 3', '(9 + -2) * 3^2^2', '(9! + -2) * 3^2^2', 'M*X + B', 'M*(X + B)', '1+2*-3^4*5+-+-6', '3!!']
        expected = "[[9, '+', 2, '+', 3]]\n                    [[9, '+', [2, '*', 3]]]\n                    [[[9, '+', 2], '*', 3]]\n                    [[[9, '+', ['-', 2]], '*', 3]]\n                    [[[9, '+', ['-', ['-', 2]]], '*', 3]]\n                    [[[9, '+', ['-', 2]], '*', [3, '^', [2, '^', 2]]]]\n                    [[[[9, '!'], '+', ['-', 2]], '*', [3, '^', [2, '^', 2]]]]\n                    [[['M', '*', 'X'], '+', 'B']]\n                    [['M', '*', ['X', '+', 'B']]]\n                    [[1, '+', [2, '*', ['-', [3, '^', 4]], '*', 5], '+', ['-', ['+', ['-', 6]]]]]\n                    [[3, '!', '!']]".split('\n')
        expected = [ast.literal_eval(x.strip()) for x in expected]
        for (test_str, exp_list) in zip(test, expected):
            self.assertParseAndCheckList(expr, test_str, exp_list, verbose=True)

    def testInfixNotationEvalBoolExprUsingAstClasses(self):
        boolVars = {'True': True, 'False': False}

        class BoolOperand:
            reprsymbol = ''

            def __init__(self, t):
                self.args = t[0][0::2]

            def __str__(self):
                sep = f' {self.reprsymbol} '
                return f'({sep.join(map(str, self.args))})'

        class BoolAnd(BoolOperand):
            reprsymbol = '&'

            def __bool__(self):
                for a in self.args:
                    if isinstance(a, str):
                        v = boolVars[a]
                    else:
                        v = bool(a)
                    if not v:
                        return False
                return True

        class BoolOr(BoolOperand):
            reprsymbol = '|'

            def __bool__(self):
                for a in self.args:
                    if isinstance(a, str):
                        v = boolVars[a]
                    else:
                        v = bool(a)
                    if v:
                        return True
                return False

        class BoolNot:

            def __init__(self, t):
                self.arg = t[0][1]

            def __str__(self):
                return f'~{self.arg}'

            def __bool__(self):
                if isinstance(self.arg, str):
                    v = boolVars[self.arg]
                else:
                    v = bool(self.arg)
                return not v
        boolOperand = pp.Word(pp.alphas, max=1, as_keyword=True) | pp.one_of('True False')
        boolExpr = pp.infix_notation(boolOperand, [('not', 1, pp.OpAssoc.RIGHT, BoolNot), ('and', 2, pp.OpAssoc.LEFT, BoolAnd), ('or', 2, pp.OpAssoc.LEFT, BoolOr)])
        test = ['p and not q', 'not not p', 'not(p and q)', 'q or not p and r', 'q or not p or not r', 'q or not (p and r)', 'p or q or r', 'p or q or r and False', '(p or q or r) and False']
        boolVars['p'] = True
        boolVars['q'] = False
        boolVars['r'] = True
        print('p =', boolVars['p'])
        print('q =', boolVars['q'])
        print('r =', boolVars['r'])
        print()
        for t in test:
            res = boolExpr.parse_string(t, parse_all=True)
            print(t, '\n', res[0], '=', bool(res[0]), '\n')
            expected = eval(t, {}, boolVars)
            self.assertEqual(expected, bool(res[0]), f'failed boolean eval test {t}')

    def testInfixNotationMinimalParseActionCalls(self):
        count = 0

        def evaluate_int(t):
            nonlocal count
            value = int(t[0])
            print('evaluate_int', value)
            count += 1
            return value
        integer = pp.Word(pp.nums).set_parse_action(evaluate_int)
        variable = pp.Word(pp.alphas, exact=1)
        operand = integer | variable
        expop = pp.Literal('^')
        signop = pp.one_of('+ -')
        multop = pp.one_of('* /')
        plusop = pp.one_of('+ -')
        factop = pp.Literal('!')
        expr = pp.infix_notation(operand, [(factop, 1, pp.OpAssoc.LEFT), (expop, 2, pp.OpAssoc.LEFT), (signop, 1, pp.OpAssoc.RIGHT), (multop, 2, pp.OpAssoc.LEFT), (plusop, 2, pp.OpAssoc.LEFT)])
        test = ['9']
        for t in test:
            count = 0
            print(f'{t!r} => {expr.parse_string(t, parse_all=True)} (count={count})')
            self.assertEqual(1, count, 'count evaluated too many times!')

    def testInfixNotationWithParseActions(self):
        word = pp.Word(pp.alphas)

        def supLiteral(s):
            """Returns the suppressed literal s"""
            return pp.Literal(s).suppress()

        def booleanExpr(atom):
            ops = [(supLiteral('!'), 1, pp.OpAssoc.RIGHT, lambda s, l, t: ['!', t[0][0]]), (pp.one_of('= !='), 2, pp.OpAssoc.LEFT), (supLiteral('&'), 2, pp.OpAssoc.LEFT, lambda s, l, t: ['&', t[0]]), (supLiteral('|'), 2, pp.OpAssoc.LEFT, lambda s, l, t: ['|', t[0]])]
            return pp.infix_notation(atom, ops)
        f = booleanExpr(word) + pp.StringEnd()
        tests = [('bar = foo', [['bar', '=', 'foo']]), ('bar = foo & baz = fee', ['&', [['bar', '=', 'foo'], ['baz', '=', 'fee']]])]
        for (test, expected) in tests:
            print(test)
            results = f.parse_string(test, parse_all=True)
            print(results)
            self.assertParseResultsEquals(results, expected_list=expected)
            print()

    def testInfixNotationGrammarTest5(self):
        expop = pp.Literal('**')
        signop = pp.one_of('+ -')
        multop = pp.one_of('* /')
        plusop = pp.one_of('+ -')

        class ExprNode:

            def __init__(self, tokens):
                self.tokens = tokens[0]

            def eval(self):
                return None

        class NumberNode(ExprNode):

            def eval(self):
                return self.tokens

        class SignOp(ExprNode):

            def eval(self):
                mult = {'+': 1, '-': -1}[self.tokens[0]]
                return mult * self.tokens[1].eval()

        class BinOp(ExprNode):
            opn_map = {}

            def eval(self):
                ret = self.tokens[0].eval()
                for (op, operand) in zip(self.tokens[1::2], self.tokens[2::2]):
                    ret = self.opn_map[op](ret, operand.eval())
                return ret

        class ExpOp(BinOp):
            opn_map = {'**': lambda a, b: b ** a}

        class MultOp(BinOp):
            import operator
            opn_map = {'*': operator.mul, '/': operator.truediv}

        class AddOp(BinOp):
            import operator
            opn_map = {'+': operator.add, '-': operator.sub}
        operand = ppc.number().set_parse_action(NumberNode)
        expr = pp.infix_notation(operand, [(expop, 2, pp.OpAssoc.LEFT, (lambda pr: [pr[0][::-1]], ExpOp)), (signop, 1, pp.OpAssoc.RIGHT, SignOp), (multop, 2, pp.OpAssoc.LEFT, MultOp), (plusop, 2, pp.OpAssoc.LEFT, AddOp)])
        tests = '            2+7\n            2**3\n            2**3**2\n            3**9\n            3**3**2\n            '
        for t in tests.splitlines():
            t = t.strip()
            if not t:
                continue
            parsed = expr.parse_string(t, parse_all=True)
            eval_value = parsed[0].eval()
            self.assertEqual(eval(t), eval_value, f'Error evaluating {t!r}, expected {eval(t)!r}, got {eval_value!r}')

    def testInfixNotationExceptions(self):
        num = pp.Word(pp.nums)
        with self.assertRaises(ValueError):
            expr = pp.infix_notation(num, [(None, 3, pp.OpAssoc.LEFT)])
        with self.assertRaises(ValueError):
            expr = pp.infix_notation(num, [(('+', '-', '*'), 3, pp.OpAssoc.LEFT)])
        with self.assertRaises(ValueError):
            expr = pp.infix_notation(num, [('*', 4, pp.OpAssoc.LEFT)])
        with self.assertRaises(ValueError):
            expr = pp.infix_notation(num, [('*', 4, pp.OpAssoc.RIGHT)])
        with self.assertRaises(ValueError):
            expr = pp.infix_notation(num, [('*', 2, 'LEFT')])

    def testInfixNotationWithNonOperators(self):
        num = pp.Word(pp.nums).add_parse_action(pp.token_map(int))
        ident = ppc.identifier()
        for assoc in (pp.OpAssoc.LEFT, pp.OpAssoc.RIGHT):
            expr = pp.infix_notation(num | ident, [(None, 2, assoc), ('+', 2, pp.OpAssoc.LEFT)])
            self.assertParseAndCheckList(expr, '3x+2', [[[3, 'x'], '+', 2]])

    def testInfixNotationTernaryOperator(self):
        num = pp.Word(pp.nums).add_parse_action(pp.token_map(int))
        for assoc in (pp.OpAssoc.LEFT, pp.OpAssoc.RIGHT):
            expr = pp.infix_notation(num, [('+', 2, pp.OpAssoc.LEFT), (('?', ':'), 3, assoc)])
            self.assertParseAndCheckList(expr, '3 + 2? 12: 13', [[[3, '+', 2], '?', 12, ':', 13]])

    def testInfixNotationWithAlternateParenSymbols(self):
        num = pp.Word(pp.nums).add_parse_action(pp.token_map(int))
        expr = pp.infix_notation(num, [('+', 2, pp.OpAssoc.LEFT)], lpar='(', rpar=')')
        self.assertParseAndCheckList(expr, '3 + (2 + 11)', [[3, '+', [2, '+', 11]]])
        expr = pp.infix_notation(num, [('+', 2, pp.OpAssoc.LEFT)], lpar='<', rpar='>')
        self.assertParseAndCheckList(expr, '3 + <2 + 11>', [[3, '+', [2, '+', 11]]])
        expr = pp.infix_notation(num, [('+', 2, pp.OpAssoc.LEFT)], lpar=pp.Literal('<'), rpar=pp.Literal('>'))
        self.assertParseAndCheckList(expr, '3 + <2 + 11>', [[3, '+', ['<', [2, '+', 11], '>']]])
        expr = pp.infix_notation(num, [('+', 2, pp.OpAssoc.LEFT)], lpar=pp.Literal('<<'), rpar=pp.Literal('>>'))
        self.assertParseAndCheckList(expr, '3 + <<2 + 11>>', [[3, '+', ['<<', [2, '+', 11], '>>']]])

    def testParseResultsInsertWithResultsNames(self):
        test_string = '1 2 3 dice rolled first try'
        wd = pp.Word(pp.alphas)
        num = ppc.number
        expr = pp.Group(num[1, ...])('nums') + wd('label') + pp.Group(wd[...])('additional')
        result = expr.parse_string(test_string, parse_all=True)
        print('Pre-insert')
        print(result.dump())
        result.insert(1, sum(result.nums))
        print('\nPost-insert')
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=[[1, 2, 3], 6, 'dice', ['rolled', 'first', 'try']], expected_dict={'additional': ['rolled', 'first', 'try'], 'label': 'dice', 'nums': [1, 2, 3]})

    def testParseResultsStringListUsingCombine(self):
        test_string = '1 2 3 dice rolled first try'
        wd = pp.Word(pp.alphas)
        num = ppc.number
        expr = pp.Combine(pp.Group(num[1, ...])('nums') + wd('label') + pp.Group(wd[...])('additional'), join_string='/', adjacent=False)
        self.assertEqual('123/dice/rolledfirsttry', expr.parse_string(test_string, parse_all=True)[0])

    def testParseResultsAcceptingACollectionTypeValue(self):
        results_with_int = pp.ParseResults(toklist=int, name='type_', aslist=False)
        self.assertEqual(int, results_with_int['type_'])
        results_with_tuple = pp.ParseResults(toklist=tuple, name='type_', aslist=False)
        self.assertEqual(tuple, results_with_tuple['type_'])

    def testParseResultsNamedResultWithEmptyString(self):
        for (test_value, expected_in_result_by_name) in [('x', True), ('', True), (True, True), (False, True), (1, True), (0, True), (None, True), (b'', True), (b'a', True), ([], False), ((), False)]:
            msg = f"value = {test_value!r}, expected X {('not ' if not expected_in_result_by_name else '')}in result"
            with self.subTest(msg):
                print(msg)
                grammar = (pp.Suppress('a') + pp.ZeroOrMore('x')).add_parse_action(lambda p: test_value).set_results_name('X')
                result = grammar.parse_string('a')
                print(result.dump())
                if expected_in_result_by_name:
                    self.assertIn('X', result, f'Expected X not found for parse action value {test_value!r}')
                    print(repr(result['X']))
                else:
                    self.assertNotIn('X', result, f'Unexpected X found for parse action value {test_value!r}')
                    with self.assertRaises(KeyError):
                        print(repr(result['X']))
                print()
        msg = 'value = <no parse action defined>, expected X in result'
        with self.subTest(msg):
            print(msg)
            grammar = (pp.Suppress('a') + pp.ZeroOrMore('x')).set_results_name('X')
            result = grammar.parse_string('a')
            print(result.dump())
            self.assertIn('X', result, f'Expected X not found with no parse action')
            print()
        print('Create empty string value directly')
        result = pp.ParseResults('', name='X')
        print(result.dump())
        self.assertIn('X', result, 'failed to construct ParseResults with named value using empty string')
        print(repr(result['X']))
        print()
        print('Create empty string value from a dict')
        result = pp.ParseResults.from_dict({'X': ''})
        print(result.dump())
        self.assertIn('X', result, 'failed to construct ParseResults with named value using from_dict')
        print(repr(result['X']))

    def testMatchOnlyAtCol(self):
        """successfully use match_only_at_col helper function"""
        expr = pp.Word(pp.nums)
        expr.set_parse_action(pp.match_only_at_col(5))
        largerExpr = pp.ZeroOrMore(pp.Word('A')) + expr + pp.ZeroOrMore(pp.Word('A'))
        res = largerExpr.parse_string('A A 3 A', parse_all=True)
        print(res.dump())

    def testMatchOnlyAtColErr(self):
        """raise a ParseException in match_only_at_col with incorrect col"""
        expr = pp.Word(pp.nums)
        expr.set_parse_action(pp.match_only_at_col(1))
        largerExpr = pp.ZeroOrMore(pp.Word('A')) + expr + pp.ZeroOrMore(pp.Word('A'))
        with self.assertRaisesParseException():
            largerExpr.parse_string('A A 3 A', parse_all=True)

    def testParseResultsWithNamedTuple(self):
        expr = pp.Literal('A')('Achar')
        expr.set_parse_action(pp.replace_with(tuple(['A', 'Z'])))
        res = expr.parse_string('A', parse_all=True)
        print(repr(res))
        print(res.Achar)
        self.assertParseResultsEquals(res, expected_dict={'Achar': ('A', 'Z')}, msg=f'Failed accessing named results containing a tuple, got {res.Achar!r}')

    def testParserElementAddOperatorWithOtherTypes(self):
        """test the overridden "+" operator with other data types"""
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second') + 'suf'
            result = expr.parse_string('spam eggs suf', parse_all=True)
            print(result)
            expected_l = ['spam', 'eggs', 'suf']
            self.assertParseResultsEquals(result, expected_l, msg='issue with ParserElement + str')
        with self.subTest():
            expr = 'pre' + pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second')
            result = expr.parse_string('pre spam eggs', parse_all=True)
            print(result)
            expected_l = ['pre', 'spam', 'eggs']
            self.assertParseResultsEquals(result, expected_l, msg='issue with str + ParserElement')
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn ParserElement + int'):
                expr = pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second') + 12
            self.assertEqual(expr, None)
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn int + ParserElement'):
                expr = 12 + pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second')
            self.assertEqual(expr, None)

    def testParserElementSubOperatorWithOtherTypes(self):
        """test the overridden "-" operator with other data types"""
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second') - 'suf'
            result = expr.parse_string('spam eggs suf', parse_all=True)
            print(result)
            expected = ['spam', 'eggs', 'suf']
            self.assertParseResultsEquals(result, expected, msg='issue with ParserElement - str')
        with self.subTest():
            expr = 'pre' - pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second')
            result = expr.parse_string('pre spam eggs', parse_all=True)
            print(result)
            expected = ['pre', 'spam', 'eggs']
            self.assertParseResultsEquals(result, expected, msg='issue with str - ParserElement')
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn ParserElement - int'):
                expr = pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second') - 12
            self.assertEqual(expr, None)
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn int - ParserElement'):
                expr = 12 - pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second')
            self.assertEqual(expr, None)

    def testParserElementMulOperatorWithTuples(self):
        """test ParserElement "*" with various tuples"""
        expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second*') * (None, 3)
        with self.subTest():
            results1 = expr.parse_string('spam', parse_all=True)
            print(results1.dump())
            expected = ['spam']
            self.assertParseResultsEquals(results1, expected, msg='issue with ParserElement * w/ optional matches')
        with self.subTest():
            results2 = expr.parse_string('spam 12 23 34', parse_all=True)
            print(results2.dump())
            expected = ['spam', '12', '23', '34']
            self.assertParseResultsEquals(results2, expected, msg='issue with ParserElement * w/ optional matches')
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second*') * (1, 1)
            results = expr.parse_string('spam 45', parse_all=True)
            print(results.dump())
            expected = ['spam', '45']
            self.assertParseResultsEquals(results, expected, msg='issue with ParserElement * (1, 1)')
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second*') * (1, 3)
            results1 = expr.parse_string('spam 100', parse_all=True)
            print(results1.dump())
            expected = ['spam', '100']
            self.assertParseResultsEquals(results1, expected, msg='issue with ParserElement * (1, 1+n)')
        with self.subTest():
            results2 = expr.parse_string('spam 100 200 300', parse_all=True)
            print(results2.dump())
            expected = ['spam', '100', '200', '300']
            self.assertParseResultsEquals(results2, expected, msg='issue with ParserElement * (1, 1+n)')
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second*') * (2, 3)
            results1 = expr.parse_string('spam 1 2', parse_all=True)
            print(results1.dump())
            expected = ['spam', '1', '2']
            self.assertParseResultsEquals(results1, expected, msg='issue with ParserElement * (lesser, greater)')
        with self.subTest():
            results2 = expr.parse_string('spam 1 2 3', parse_all=True)
            print(results2.dump())
            expected = ['spam', '1', '2', '3']
            self.assertParseResultsEquals(results2, expected, msg='issue with ParserElement * (lesser, greater)')
        with self.subTest():
            with self.assertRaises(ValueError, msg='ParserElement * (greater, lesser) should raise error'):
                expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second') * (3, 2)
        with self.subTest():
            with self.assertRaises(TypeError, msg='ParserElement * (str, str) should raise error'):
                expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second') * ('2', '3')

    def testParserElementMulByZero(self):
        alpwd = pp.Word(pp.alphas)
        numwd = pp.Word(pp.nums)
        test_string = 'abd def ghi jkl'
        with self.subTest():
            parser = alpwd * 2 + numwd * 0 + alpwd * 2
            self.assertParseAndCheckList(parser, test_string, expected_list=test_string.split())
        with self.subTest():
            parser = alpwd * 2 + numwd * (0, 0) + alpwd * 2
            self.assertParseAndCheckList(parser, test_string, expected_list=test_string.split())

    def testParserElementMulOperatorWithOtherTypes(self):
        """test the overridden "*" operator with other data types"""
        with self.subTest():
            with self.assertRaises(TypeError, msg='ParserElement * str should raise error'):
                expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second') * '3'
        with self.subTest():
            with self.assertRaises(TypeError, msg='str * ParserElement should raise error'):
                expr = pp.Word(pp.alphas)('first') + '3' * pp.Word(pp.nums)('second')
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + pp.Word(pp.nums)('second*') * 2
            results = expr.parse_string('spam 11 22', parse_all=True)
            print(results.dump())
            expected = ['spam', '11', '22']
            self.assertParseResultsEquals(results, expected, msg='issue with ParserElement * int')
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + 2 * pp.Word(pp.nums)('second*')
            results = expr.parse_string('spam 111 222', parse_all=True)
            print(results.dump())
            expected = ['spam', '111', '222']
            self.assertParseResultsEquals(results, expected, msg='issue with int * ParserElement')

    def testParserElementMatchFirstOperatorWithOtherTypes(self):
        """test the overridden "|" operator with other data types"""
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn ParserElement | int'):
                expr = pp.Word(pp.alphas)('first') + (pp.Word(pp.alphas)('second') | 12)
            self.assertEqual(expr, None)
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn int | ParserElement'):
                expr = pp.Word(pp.alphas)('first') + (12 | pp.Word(pp.alphas)('second'))
            self.assertEqual(expr, None)

    def testParserElementMatchLongestWithOtherTypes(self):
        """test the overridden "^" operator with other data types"""
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + (pp.Word(pp.nums)('second') ^ 'eggs')
            result = expr.parse_string('spam eggs', parse_all=True)
            print(result)
            expected = ['spam', 'eggs']
            self.assertParseResultsEquals(result, expected, msg='issue with ParserElement ^ str')
        with self.subTest():
            expr = ('pre' ^ pp.Word('pr')('first')) + pp.Word(pp.alphas)('second')
            result = expr.parse_string('pre eggs', parse_all=True)
            print(result)
            expected = ['pre', 'eggs']
            self.assertParseResultsEquals(result, expected, msg='issue with str ^ ParserElement')
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn ParserElement ^ int'):
                expr = pp.Word(pp.alphas)('first') + (pp.Word(pp.alphas)('second') ^ 54)
            self.assertEqual(expr, None)
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn int ^ ParserElement'):
                expr = pp.Word(pp.alphas)('first') + (65 ^ pp.Word(pp.alphas)('second'))
            self.assertEqual(expr, None)

    def testParserElementEachOperatorWithOtherTypes(self):
        """test the overridden "&" operator with other data types"""
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + (pp.Word(pp.alphas)('second') & 'and')
            with self.assertRaisesParseException(msg='issue with ParserElement & str'):
                result = expr.parse_string('spam and eggs', parse_all=True)
        with self.subTest():
            expr = pp.Word(pp.alphas)('first') + ('and' & pp.Word(pp.alphas)('second'))
            result = expr.parse_string('spam and eggs', parse_all=True)
            print(result.dump())
            expected_l = ['spam', 'and', 'eggs']
            expected_d = {'first': 'spam', 'second': 'eggs'}
            self.assertParseResultsEquals(result, expected_list=expected_l, expected_dict=expected_d, msg='issue with str & ParserElement')
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn ParserElement & int'):
                expr = pp.Word(pp.alphas)('first') + (pp.Word(pp.alphas) & 78)
            self.assertEqual(expr, None)
        with self.subTest():
            expr = None
            with self.assertRaises(TypeError, msg='failed to warn int & ParserElement'):
                expr = pp.Word(pp.alphas)('first') + (89 & pp.Word(pp.alphas))
            self.assertEqual(expr, None)

    def testParserElementPassedThreeArgsToMultiplierShorthand(self):
        """test the ParserElement form expr[m,n,o]"""
        with self.assertRaises(TypeError, msg='failed to warn three index arguments to expr[m, n, o]'):
            expr = pp.Word(pp.alphas)[2, 3, 4]

    def testParserElementPassedStrToMultiplierShorthand(self):
        """test the ParserElement form expr[str]"""
        with self.assertRaises(TypeError, msg='failed to raise expected error using string multiplier'):
            expr2 = pp.Word(pp.alphas)['2']

    def testParseResultsNewEdgeCases(self):
        """test less common paths of ParseResults.__new__()"""
        parser = pp.Word(pp.alphas)[...]
        result = parser.parse_string('sldkjf sldkjf', parse_all=True)
        self.assertFalse('A' in result)
        result1 = pp.ParseResults(None)
        print(result1.dump())
        self.assertParseResultsEquals(result1, [], msg='ParseResults(None) should return empty ParseResults')
        result2 = pp.ParseResults(name=12)
        print(result2.dump())
        self.assertEqual('12', result2.get_name(), 'ParseResults int name should be accepted and converted to str')
        gen = (a for a in range(1, 6))
        result3 = pp.ParseResults(gen)
        print(result3.dump())
        expected3 = [1, 2, 3, 4, 5]
        self.assertParseResultsEquals(result3, expected3, msg='issue initializing ParseResults w/ gen type')

    def testParseResultsReversed(self):
        """test simple case of reversed(ParseResults)"""
        tst = '1 2 3 4 5'
        expr = pp.OneOrMore(pp.Word(pp.nums))
        result = expr.parse_string(tst, parse_all=True)
        reversed_list = [ii for ii in reversed(result)]
        print(reversed_list)
        expected = ['5', '4', '3', '2', '1']
        self.assertEqual(expected, reversed_list, msg='issue calling reversed(ParseResults)')

    def testParseResultsValues(self):
        """test simple case of ParseResults.values()"""
        expr = pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second')
        result = expr.parse_string('spam eggs', parse_all=True)
        values_set = set(result.values())
        print(values_set)
        expected = {'spam', 'eggs'}
        self.assertEqual(expected, values_set, msg='issue calling ParseResults.values()')

    def testParseResultsAppend(self):
        """test simple case of ParseResults.append()"""

        def append_sum(tokens):
            tokens.append(sum(map(int, tokens)))
        expr = pp.OneOrMore(pp.Word(pp.nums)).add_parse_action(append_sum)
        result = expr.parse_string('0 123 321', parse_all=True)
        expected = ['0', '123', '321', 444]
        print(result.dump())
        self.assertParseResultsEquals(result, expected, msg='issue with ParseResults.append()')

    def testParseResultsArithmeticContract(self):
        """test ParseResults.__add__ and __radd__ arithmetic contract"""
        import operator
        pr = pp.ParseResults(['a', 'b'])
        pr_sum = pr + pp.ParseResults(['c'])
        self.assertEqual(['a', 'b', 'c'], list(pr_sum))
        with self.assertRaises(TypeError, msg='ParseResults + int should raise TypeError, not AttributeError'):
            pr + 1
        with self.assertRaises(TypeError, msg='ParseResults + str should raise TypeError'):
            pr + 'extra'
        with self.assertRaises(TypeError, msg='non-zero int + ParseResults should raise TypeError, not RecursionError'):
            1 + pr
        with self.assertRaises(TypeError, msg='float + ParseResults should raise TypeError'):
            1.5 + pr
        with self.assertRaises(TypeError, msg='str + ParseResults should raise TypeError'):
            'x' + pr
        zero_sum = 0 + pr
        self.assertEqual(['a', 'b'], list(zero_sum))
        total = sum([pp.ParseResults(['x']), pp.ParseResults(['y']), pp.ParseResults(['z'])])
        self.assertEqual(['x', 'y', 'z'], list(total))
        import functools
        reduced = functools.reduce(operator.add, [pp.ParseResults(['m']), pp.ParseResults(['n'])])
        self.assertEqual(['m', 'n'], list(reduced))

    def testParseResultsClear(self):
        """test simple case of ParseResults.clear()"""
        tst = 'spam eggs'
        expr = pp.Word(pp.alphas)('first') + pp.Word(pp.alphas)('second')
        result = expr.parse_string(tst, parse_all=True)
        print(result.dump())
        self.assertParseResultsEquals(result, ['spam', 'eggs'], msg='issue with ParseResults before clear()')
        result.clear()
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=[], expected_dict={}, msg='issue with ParseResults.clear()')

    def testParseResultsExtendWithString(self):
        """test ParseResults.extend() with input of type str"""

        def make_palindrome(tokens):
            tokens.extend(reversed([t[::-1] for t in tokens]))
        tst = 'abc def ghi'
        expr = pp.OneOrMore(pp.Word(pp.alphas))
        result = expr.add_parse_action(make_palindrome).parse_string(tst, parse_all=True)
        print(result.dump())
        expected = ['abc', 'def', 'ghi', 'ihg', 'fed', 'cba']
        self.assertParseResultsEquals(result, expected, msg='issue with ParseResults.extend(str)')

    def testParseResultsExtendWithParseResults(self):
        """test ParseResults.extend() with input of type ParseResults"""
        expr = pp.OneOrMore(pp.Word(pp.alphas))
        result1 = expr.parse_string('spam eggs', parse_all=True)
        result2 = expr.parse_string('foo bar', parse_all=True)
        result1.extend(result2)
        print(result1.dump())
        expected = ['spam', 'eggs', 'foo', 'bar']
        self.assertParseResultsEquals(result1, expected, msg='issue with ParseResults.extend(ParseResults)')

    def testQuotedStringLoc(self):
        expr = pp.QuotedString("'")
        expr.add_parse_action(lambda t: t[0].upper())
        test_string = "Using 'quotes' for 'sarcasm' or 'emphasis' is not good 'style'."
        transformed = expr.transform_string(test_string)
        print(test_string)
        print(transformed)
        expected = re.sub("'([^']+)'", lambda match: match[1].upper(), test_string)
        self.assertEqual(expected, transformed)

    def testParseResultsWithNestedNames(self):
        from pyparsing import Dict, Literal, Group, Optional, Regex, QuotedString, one_of, Or, CaselessKeyword, ZeroOrMore
        RELATION_SYMBOLS = '= > < >= <= <> =='

        def _set_info(string, location, tokens):
            for t in tokens:
                try:
                    t['_info_'] = (string, location)
                except TypeError:
                    pass
            tokens['_info_'] = (string, location)

        def keywords(name):
            words = 'any all within encloses adj'.split()
            return Or(map(CaselessKeyword, words))
        charString1 = Group(Regex('[^()=<>"/\\s]+'))('identifier')
        charString1.add_parse_action(_set_info)
        charString2 = Group(QuotedString('"', '\\'))('quoted')
        charString2.add_parse_action(_set_info)
        term = Group(charString1 | charString2)
        modifier_key = charString1
        comparitor_symbol = one_of(RELATION_SYMBOLS)
        named_comparitors = keywords('comparitors')
        comparitor = Group(comparitor_symbol | named_comparitors)('comparitor')
        comparitor.add_parse_action(_set_info)

        def modifier_list1(key):
            modifier = Dict(Literal('/') + Group(modifier_key(key))('name') + Optional(comparitor_symbol('symbol') + term('value')))('modifier')
            modifier.add_parse_action(_set_info)
            return ZeroOrMore(modifier)('modifier_list')

        def modifier_list2(key):
            modifier = Dict(Literal('/') + Group(modifier_key(key))('name') + Optional(comparitor_symbol('symbol') + term('value')), asdict=True)('modifier')
            modifier.add_parse_action(_set_info)
            return ZeroOrMore(modifier)('modifier_list')

        def modifier_list3(key):
            modifier = Group(Dict(Literal('/') + Group(modifier_key(key))('name') + Optional(comparitor_symbol('symbol') + term('value'))))
            modifier.add_parse_action(_set_info)
            return ZeroOrMore(modifier)('modifier_list')

        def modifier_list4(key):
            modifier = Dict(Literal('/') + Group(modifier_key(key))('name') + Optional(comparitor_symbol('symbol') + term('value')), asdict=True)
            modifier.add_parse_action(_set_info)
            return ZeroOrMore(modifier)('modifier_list')
        for modifier_list_fn in (modifier_list1, modifier_list2, modifier_list3, modifier_list4):
            modifier_parser = modifier_list_fn('default')
            result = modifier_parser.parse_string('/respectaccents/ignoreaccents', parse_all=True)
            for r in result:
                print(r)
                print(r.get('_info_'))
            self.assertEqual([0, 15], [r['_info_'][1] for r in result])

    def testParseResultsFromDict(self):
        """test helper classmethod ParseResults.from_dict()"""
        dict = {'first': '123', 'second': 456, 'third': {'threeStr': '789', 'threeInt': 789}}
        name = 'trios'
        result = pp.ParseResults.from_dict(dict, name=name)
        print(result.dump())
        expected = {name: dict}
        self.assertParseResultsEquals(result, expected_dict=expected, msg='issue creating ParseResults.from _dict()')

    def testParseResultsInsert(self):
        """test ParseResults.insert() with named tokens"""
        from random import randint
        result = pp.Word(pp.alphas)[...].parse_string('A B C D E F G H I J', parse_all=True)
        compare_list = result.as_list()
        print(result)
        print(compare_list)
        for s in 'abcdefghij':
            index = randint(-5, 5)
            result.insert(index, s)
            compare_list.insert(index, s)
        print(result)
        print(compare_list)
        self.assertParseResultsEquals(result, compare_list, msg='issue with ParseResults.insert()')

    def testParseResultsAddingSuppressedTokenWithResultsName(self):
        parser = 'aaa' + (pp.NoMatch() | pp.Suppress('-'))('B')
        try:
            dd = parser.parse_string('aaa -').as_dict()
        except RecursionError:
            self.fail('fail getting named result when empty')

    def testParseResultsBool(self):
        result = pp.Word(pp.alphas)[...].parse_string('AAA', parse_all=True)
        self.assertTrue(result, 'non-empty ParseResults evaluated as False')
        result = pp.Word(pp.alphas)[...].parse_string('', parse_all=True)
        self.assertFalse(result, 'empty ParseResults evaluated as True')
        result['A'] = 0
        self.assertTrue(result, 'ParseResults with empty list but containing a results name evaluated as False')

    def testParseResultsWithAsListWithAndWithoutFlattening(self):
        ppc = pp.common
        (LPAR, RPAR) = pp.Suppress.using_each('()')
        fn_call = pp.Forward()
        fn_arg = fn_call | ppc.identifier | ppc.number
        fn_call <<= ppc.identifier + pp.Group(LPAR + pp.Optional(pp.DelimitedList(fn_arg)) + RPAR)
        tests = [('random()', ['random', []]), ('sin(theta)', ['sin', ['theta']]), ('sin(rad(30))', ['sin', ['rad', [30]]]), ('sin(rad(30), rad(60, 180))', ['sin', ['rad', [30], 'rad', [60, 180]]]), ('sin(rad(30), rad(60, 180), alpha)', ['sin', ['rad', [30], 'rad', [60, 180], 'alpha']])]
        for (test_string, expected) in tests:
            with self.subTest():
                print(test_string)
                observed = fn_call.parse_string(test_string, parse_all=True)
                print(observed.as_list())
                self.assertEqual(expected, observed.as_list())
                print(observed.as_list(flatten=True))
                self.assertEqual(flatten(expected), observed.as_list(flatten=True))
                print()

    def testParseResultsCopy(self):
        expr = pp.Word(pp.nums) + pp.Group(pp.Word(pp.alphas)('key') + '=' + pp.Word(pp.nums)('value'))[...]
        result = expr.parse_string('1 a=100 b=200 c=300')
        print(result.dump())
        r2 = result.copy()
        print(r2.dump())
        self.assertFalse(r2 is result, 'copy failed')
        self.assertTrue(r2[1] is result[1], 'shallow copy failed')
        result[1][0] = 'z'
        self.assertParseResultsEquals(result, expected_list=['1', ['z', '=', '100'], ['b', '=', '200'], ['c', '=', '300']])
        result[1][0] = result[1]['key'] = 'q'
        result[1]['xyz'] = 1000
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=['1', ['q', '=', '100'], ['b', '=', '200'], ['c', '=', '300']])
        self.assertParseResultsEquals(result[1], expected_dict={'key': 'q', 'value': '100', 'xyz': 1000})
        self.assertParseResultsEquals(r2, expected_list=['1', ['q', '=', '100'], ['b', '=', '200'], ['c', '=', '300']])
        self.assertParseResultsEquals(r2[1], expected_dict={'key': 'q', 'value': '100', 'xyz': 1000})

    def testParseResultsDeepcopy(self):
        expr = pp.Word(pp.nums) + pp.Group(pp.Word(pp.alphas)('key') + '=' + pp.Word(pp.nums)('value'))[...]
        result = expr.parse_string('1 a=100 b=200 c=300')
        r2 = result.deepcopy()
        print(r2.dump())
        self.assertFalse(r2 is result, 'copy failed')
        self.assertFalse(r2[1] is result[1], 'deep copy failed')
        self.assertEqual(result.as_dict(), r2.as_dict())
        self.assertEqual(result.as_list(), r2.as_list())
        result[1][0] = result[1]['key'] = 'q'
        result[1]['xyz'] = 1000
        print(result.dump())
        self.assertParseResultsEquals(r2, expected_list=['1', ['a', '=', '100'], ['b', '=', '200'], ['c', '=', '300']])
        self.assertParseResultsEquals(r2[1], expected_dict={'key': 'a', 'value': '100'})

    def testParseResultsDeepcopy2(self):
        expr = pp.Word(pp.nums) + pp.Group(pp.Word(pp.alphas)('key') + '=' + pp.Word(pp.nums)('value'), aslist=True)[...]
        result = expr.parse_string('1 a=100 b=200 c=300')
        r2 = result.deepcopy()
        print(r2.dump())
        self.assertFalse(r2 is result, 'copy failed')
        self.assertFalse(r2[1] is result[1], 'deep copy failed')
        result[1][0] = 'q'
        print(result.dump())
        self.assertParseResultsEquals(r2, expected_list=['1', ['a', '=', '100'], ['b', '=', '200'], ['c', '=', '300']])

    def testParseResultsDeepcopy3(self):
        expr = pp.Word(pp.nums) + pp.Group((pp.Word(pp.alphas)('key') + '=' + pp.Word(pp.nums)('value')).add_parse_action(lambda t: tuple(t)))[...]
        result = expr.parse_string('1 a=100 b=200 c=300')
        r2 = result.deepcopy()
        print(r2.dump())
        self.assertFalse(r2 is result, 'copy failed')
        self.assertFalse(r2[1] is result[1], 'deep copy failed')
        result[1][0] = 'q'
        print(result.dump())
        self.assertParseResultsEquals(r2, expected_list=['1', [('a', '=', '100')], [('b', '=', '200')], [('c', '=', '300')]])

    def testIgnoreString(self):
        """test ParserElement.ignore() passed a string arg"""
        tst = 'I like totally like love pickles'
        expr = pp.Word(pp.alphas)[...].ignore('like')
        result = expr.parse_string(tst, parse_all=True)
        print(result)
        expected = ['I', 'totally', 'love', 'pickles']
        self.assertParseResultsEquals(result, expected, msg='issue with ignore(string)')

    def testParseHTMLTags(self):
        test = '\n            <BODY>\n            <BODY BGCOLOR="#00FFCC">\n            <BODY BGCOLOR="#00FFAA"/>\n            <BODY BGCOLOR=\'#00FFBB\' FGCOLOR=black>\n            <BODY/>\n            </BODY>\n        '
        results = [('startBody', False, '', ''), ('startBody', False, '#00FFCC', ''), ('startBody', True, '#00FFAA', ''), ('startBody', False, '#00FFBB', 'black'), ('startBody', True, '', ''), ('endBody', False, '', '')]
        (bodyStart, bodyEnd) = pp.make_html_tags('BODY')
        resIter = iter(results)
        for (t, s, e) in (bodyStart | bodyEnd).scan_string(test):
            print(test[s:e], '->', t)
            (expectedType, expectedEmpty, expectedBG, expectedFG) = next(resIter)
            print(t.dump())
            if 'startBody' in t:
                self.assertEqual(expectedEmpty, bool(t.empty), f"expected {expectedEmpty and 'empty' or 'not empty'} token, got {t.empty and 'empty' or 'not empty'}")
                self.assertEqual(expectedBG, t.bgcolor, f'failed to match BGCOLOR, expected {expectedBG}, got {t.bgcolor}')
                self.assertEqual(expectedFG, t.fgcolor, f'failed to match FGCOLOR, expected {expectedFG}, got {t.bgcolor}')
            elif 'endBody' in t:
                print('end tag')
                pass
            else:
                print('BAD!!!')

    def testSetParseActionUncallableErr(self):
        """raise a TypeError in set_parse_action() by adding uncallable arg"""
        expr = pp.Literal('A')('Achar')
        uncallable = 12
        with self.assertRaises(TypeError):
            expr.set_parse_action(uncallable)
        res = expr.parse_string('A', parse_all=True)
        print(res.dump())

    def testMulWithNegativeNumber(self):
        """raise a ValueError in __mul__ by multiplying a negative number"""
        with self.assertRaises(ValueError):
            pp.Literal('A')('Achar') * -1

    def testMulWithEllipsis(self):
        """multiply an expression with Ellipsis as ``expr * ...`` to match ZeroOrMore"""
        expr = pp.Literal('A')('Achar') * ...
        res = expr.parse_string('A', parse_all=True)
        self.assertEqual(['A'], res.as_list(), 'expected expr * ... to match ZeroOrMore')
        print(res.dump())

    def testUpcaseDowncaseUnicode(self):
        import sys
        ppu = pp.pyparsing_unicode
        a = '¿Cómo esta usted?'
        if not JYTHON_ENV:
            ualphas = ppu.alphas
        else:
            ualphas = ''.join((chr(i) for i in list(range(55296)) + list(range(57344, sys.maxunicode)) if chr(i).isalpha()))
        uword = pp.Word(ualphas).set_parse_action(ppc.upcase_tokens)
        print = lambda *args: None
        print(uword.search_string(a))
        uword = pp.Word(ualphas).set_parse_action(ppc.downcase_tokens)
        print(uword.search_string(a))
        kw = pp.Keyword('mykey', caseless=True).set_parse_action(ppc.upcase_tokens)('rname')
        ret = kw.parse_string('mykey', parse_all=True)
        print(ret.rname)
        self.assertEqual('MYKEY', ret.rname, 'failed to upcase with named result (pyparsing_common)')
        kw = pp.Keyword('MYKEY', caseless=True).set_parse_action(ppc.downcase_tokens)('rname')
        ret = kw.parse_string('mykey', parse_all=True)
        print(ret.rname)
        self.assertEqual('mykey', ret.rname, 'failed to upcase with named result')
        if not IRON_PYTHON_ENV:
            html = '<TR class=maintxt bgColor=#ffffff>                 <TD vAlign=top>Производитель, модель</TD>                 <TD vAlign=top><STRONG>BenQ-Siemens CF61</STRONG></TD>             '
            text_manuf = 'Производитель, модель'
            manufacturer = pp.Literal(text_manuf)
            (td_start, td_end) = pp.make_html_tags('td')
            manuf_body = td_start.suppress() + manufacturer + pp.SkipTo(td_end)('cells*') + td_end.suppress()

    def testRegexDeferredCompile(self):
        """test deferred compilation of Regex patterns"""
        re_expr = pp.Regex('[A-Z]*')
        self.assertIsNone(re_expr._may_return_empty, 'failed to initialize _may_return_empty flag to None')
        self.assertEqual(re_expr._re, None)
        compiled = re_expr.re
        self.assertTrue(re_expr._may_return_empty, 'failed to set _may_return_empty flag to True')
        self.assertEqual(re_expr._re, compiled)
        non_empty_re_expr = pp.Regex('[A-Z]+')
        self.assertIsNone(non_empty_re_expr._may_return_empty, 'failed to initialize _may_return_empty flag to None')
        self.assertEqual(non_empty_re_expr._re, None)
        compiled = non_empty_re_expr.re
        self.assertFalse(non_empty_re_expr._may_return_empty, 'failed to set _may_return_empty flag to False')
        self.assertEqual(non_empty_re_expr._re, compiled)

    def testRegexDeferredCompileCommonHtmlEntity(self):
        perf_test_common_html_entity = pp.common_html_entity()
        perf_test_common_html_entity._re = None
        from time import perf_counter
        start = perf_counter()
        perf_test_common_html_entity.re
        elapsed = perf_counter() - start
        print(f'elapsed time to compile common_html_entity: {elapsed:.4f} sec')

    def testParseUsingRegex(self):
        signedInt = pp.Regex('[-+][0-9]+')
        unsignedInt = pp.Regex('[0-9]+')
        simpleString = pp.Regex('("[^\\"]*")|(\\\'[^\\\']*\\\')')
        namedGrouping = pp.Regex('("(?P<content>[^\\"]*)")')
        compiledRE = pp.Regex(re.compile('[A-Z]+'))

        def testMatch(expression, instring, shouldPass, expectedString=None):
            if shouldPass:
                try:
                    result = expression.parse_string(instring, parse_all=False)
                    print(f'{repr(expression)} correctly matched {repr(instring)}')
                    if expectedString != result[0]:
                        print('\tbut failed to match the pattern as expected:')
                        print(f'\tproduced {repr(result[0])} instead of {repr(expectedString)}')
                        return False
                    return True
                except pp.ParseException:
                    print(f'{expression!r} incorrectly failed to match {instring!r}')
            else:
                try:
                    result = expression.parse_string(instring, parse_all=False)
                    print(f'{expression!r} incorrectly matched {instring!r}')
                    print(f'\tproduced {result[0]!r} as a result')
                except pp.ParseException:
                    print(f'{expression!r} correctly failed to match {instring!r}')
                    return True
            return False
        for (i, (test_expr, test_string)) in enumerate([(signedInt, '1234 foo'), (signedInt, '    +foo'), (unsignedInt, 'abc'), (unsignedInt, '+123 foo'), (simpleString, 'foo'), (simpleString, '"foo bar\''), (simpleString, '\'foo bar"'), (compiledRE, 'blah')], start=1):
            with self.subTest(test_expr=test_expr, test_string=test_string):
                self.assertTrue(testMatch(test_expr, test_string, False), f'Re: ({i}) passed, expected fail')
        for (i, (test_expr, test_string, expected_match)) in enumerate([(signedInt, '   +123', '+123'), (signedInt, '+123', '+123'), (signedInt, '+123 foo', '+123'), (signedInt, '-0 foo', '-0'), (unsignedInt, '123 foo', '123'), (unsignedInt, '0 foo', '0'), (simpleString, '"foo"', '"foo"'), (simpleString, "'foo bar' baz", "'foo bar'"), (compiledRE, 'BLAH', 'BLAH'), (namedGrouping, '"foo bar" baz', '"foo bar"')], start=i + 1):
            with self.subTest(test_expr=test_expr, test_string=test_string):
                self.assertTrue(testMatch(test_expr, test_string, True, expected_match), f'Re: ({i}) failed, expected pass')
        ret = namedGrouping.parse_string('"zork" blah', parse_all=False)
        print(ret)
        print(list(ret.items()))
        print(ret.content)
        self.assertEqual('zork', ret.content, 'named group lookup failed')
        self.assertEqual(simpleString.parse_string('"zork" blah', parse_all=False)[0], ret[0], 'Regex not properly returning ParseResults for named vs. unnamed groups')

    def testRegexAsType(self):
        test_str = 'sldkjfj 123 456 lsdfkj'
        print('return as list of match groups')
        expr = pp.Regex('\\w+ (\\d+) (\\d+) (\\w+)', as_group_list=True)
        expected_group_list = [tuple(test_str.split()[1:])]
        result = expr.parse_string(test_str, parse_all=True)
        print(result.dump())
        print(expected_group_list)
        self.assertParseResultsEquals(result, expected_list=expected_group_list, msg='incorrect group list returned by Regex)')
        print('return as re.match instance')
        expr = pp.Regex('\\w+ (?P<num1>\\d+) (?P<num2>\\d+) (?P<last_word>\\w+)', as_match=True)
        result = expr.parse_string(test_str, parse_all=True)
        print(result.dump())
        print(result[0].groups())
        print(expected_group_list)
        self.assertEqual({'num1': '123', 'num2': '456', 'last_word': 'lsdfkj'}, result[0].groupdict(), 'invalid group dict from Regex(as_match=True)')
        self.assertEqual(expected_group_list[0], result[0].groups(), 'incorrect group list returned by Regex(as_match)')

    def testRegexSub(self):
        print('test sub with string')
        expr = pp.Regex('<title>').sub("'Richard III'")
        result = expr.transform_string('This is the title: <title>')
        print(result)
        self.assertEqual("This is the title: 'Richard III'", result, 'incorrect Regex.sub result with simple string')
        print('test sub with re string')
        expr = pp.Regex('([Hh]\\d):\\s*(.*)').sub('<\\1>\\2</\\1>')
        result = expr.transform_string('h1: This is the main heading\nh2: This is the sub-heading')
        print(result)
        self.assertEqual('<h1>This is the main heading</h1>\n<h2>This is the sub-heading</h2>', result, 'incorrect Regex.sub result with re string')
        print('test sub with re string (Regex returns re.match)')
        expr = pp.Regex('([Hh]\\d):\\s*(.*)', as_match=True).sub('<\\1>\\2</\\1>')
        result = expr.transform_string('h1: This is the main heading\nh2: This is the sub-heading')
        print(result)
        self.assertEqual('<h1>This is the main heading</h1>\n<h2>This is the sub-heading</h2>', result, 'incorrect Regex.sub result with re string')
        print('test sub with callable that return str')
        expr = pp.Regex('<(.*?)>').sub(lambda m: m.group(1).upper())
        result = expr.transform_string('I want this in upcase: <what? what?>')
        print(result)
        self.assertEqual('I want this in upcase: WHAT? WHAT?', result, 'incorrect Regex.sub result with callable')
        with self.assertRaises(TypeError):
            pp.Regex('<(.*?)>', as_match=True).sub(lambda m: m.group(1).upper())
        with self.assertRaises(TypeError):
            pp.Regex('<(.*?)>', as_group_list=True).sub(lambda m: m.group(1).upper())
        with self.assertRaises(TypeError):
            pp.Regex('<(.*?)>', as_group_list=True).sub('')

    def testRegexInvalidType(self):
        """test Regex of an invalid type"""
        with self.assertRaises(TypeError, msg='issue with Regex of type int'):
            expr = pp.Regex(12)

    def testRegexLoopPastEndOfString(self):
        """test Regex matching after end of string"""
        NL = pp.LineEnd().suppress()
        empty_line = pp.rest_of_line() + NL
        result = empty_line[1, 10].parse_string('\n\n')
        self.assertEqual(3, len(result))

    def testPrecededBy(self):
        num = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        interesting_num = pp.PrecededBy(pp.Char('abc')('prefix*')) + num
        semi_interesting_num = pp.PrecededBy('_') + num
        crazy_num = pp.PrecededBy(pp.Word('^', '$%^')('prefix*'), 10) + num
        boring_num = ~pp.PrecededBy(pp.Char('abc_$%^' + pp.nums)) + num
        very_boring_num = pp.PrecededBy(pp.WordStart()) + num
        finicky_num = pp.PrecededBy(pp.Word('^', '$%^'), retreat=3) + num
        s = 'c384 b8324 _9293874 _293 404 $%^$^%$2939'
        print(s)
        for (expr, expected_list, expected_dict) in [(interesting_num, [384, 8324], {'prefix': ['c', 'b']}), (semi_interesting_num, [9293874, 293], {}), (boring_num, [404], {}), (crazy_num, [2939], {'prefix': ['^%$']}), (finicky_num, [2939], {}), (very_boring_num, [404], {})]:
            result = sum(expr.search_string(s))
            print(result.dump())
            self.assertParseResultsEquals(result, expected_list, expected_dict)
        string_test = 'notworking'
        negs_pb = pp.PrecededBy('not', retreat=100)('negs_lb')
        pattern = (negs_pb + pp.Literal('working'))('main')
        results = pattern.search_string(string_test)
        try:
            print(results.dump())
        except RecursionError:
            self.fail('got maximum excursion limit exception')
        else:
            print('got maximum excursion limit exception')

    def testCountedArray(self):
        testString = '2 5 7 6 0 1 2 3 4 5 0 3 5 4 3'
        integer = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        countedField = pp.counted_array(integer)
        r = pp.OneOrMore(pp.Group(countedField)).parse_string(testString, parse_all=True)
        print(testString)
        print(r)
        self.assertParseResultsEquals(r, expected_list=[[5, 7], [0, 1, 2, 3, 4, 5], [], [5, 4, 3]])

    def testCountedArrayTest2(self):
        testString = '2 5 7 6 0 1 2 3 4 5 0 3 5 4 3'
        integer = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        countedField = pp.counted_array(integer)
        dummy = pp.Word('A')
        r = pp.OneOrMore(pp.Group(dummy ^ countedField)).parse_string(testString, parse_all=True)
        print(testString)
        print(r)
        self.assertParseResultsEquals(r, expected_list=[[5, 7], [0, 1, 2, 3, 4, 5], [], [5, 4, 3]])

    def testCountedArrayTest3(self):
        int_chars = '_' + pp.alphas
        array_counter = pp.Word(int_chars).set_parse_action(lambda t: int_chars.index(t[0]))
        testString = 'B 5 7 F 0 1 2 3 4 5 _ C 5 4 3'
        integer = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        countedField = pp.counted_array(integer, int_expr=array_counter)
        r = pp.OneOrMore(pp.Group(countedField)).parse_string(testString, parse_all=True)
        print(testString)
        print(r)
        self.assertParseResultsEquals(r, expected_list=[[5, 7], [0, 1, 2, 3, 4, 5], [], [5, 4, 3]])

    def testCountedArrayTest4(self):
        ppc = pp.pyparsing_common
        counter_with_metadata = ppc.integer('count') + ppc.identifier('type') + ppc.identifier('source')
        countedField = pp.counted_array(pp.Word(pp.alphanums), int_expr=counter_with_metadata)
        testString = '5 string input item1 item2 item3 item4 item5 0 int user 2 int file 3 8'
        r = pp.Group(countedField('items'))[...].parse_string(testString, parse_all=True)
        print(testString)
        print(r.dump())
        print(f'type = {r.type!r}')
        print(f'source = {r.source!r}')
        self.assertParseResultsEquals(r, expected_list=[['item1', 'item2', 'item3', 'item4', 'item5'], [], ['3', '8']])
        self.assertParseResultsEquals(r[0], expected_dict={'count': 5, 'source': 'input', 'type': 'string', 'items': ['item1', 'item2', 'item3', 'item4', 'item5']})
        count_with_metadata = ppc.integer + pp.Word(pp.alphas)('type')
        typed_array = pp.counted_array(pp.Word(pp.alphanums), int_expr=count_with_metadata)('items')
        result = typed_array.parse_string('3 bool True True False', parse_all=True)
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=['True', 'True', 'False'], expected_dict={'type': 'bool', 'items': ['True', 'True', 'False']})

    def testLineStart(self):
        pass_tests = ['            AAA\n            BBB\n            ', '            AAA...\n            BBB\n            ']
        fail_tests = ['            AAA...\n            ...BBB\n            ', '            AAA  BBB\n            ']
        pass_tests = ['\n'.join((s.lstrip() for s in t.splitlines())).replace('.', ' ') for t in pass_tests]
        fail_tests = ['\n'.join((s.lstrip() for s in t.splitlines())).replace('.', ' ') for t in fail_tests]
        test_patt = pp.Word('A') - pp.LineStart() + pp.Word('B')
        print(test_patt)
        (success, _) = test_patt.run_tests(pass_tests)
        self.assertTrue(success, 'failed LineStart passing tests (1)')
        (success, _) = test_patt.run_tests(fail_tests, failure_tests=True)
        self.assertTrue(success, 'failed LineStart failure mode tests (1)')
        with ppt.reset_pyparsing_context():
            print('no \\n in default whitespace chars')
            pp.ParserElement.set_default_whitespace_chars(' ')
            test_patt = pp.Word('A') - pp.LineStart() + pp.Word('B')
            print(test_patt)
            (success, _) = test_patt.run_tests(pass_tests, failure_tests=True)
            self.assertTrue(success, 'failed LineStart passing tests (2)')
            (success, _) = test_patt.run_tests(fail_tests, failure_tests=True)
            self.assertTrue(success, 'failed LineStart failure mode tests (2)')
            test_patt = pp.Word('A') - pp.LineEnd().suppress() + pp.LineStart() + pp.Word('B') + pp.LineEnd().suppress()
            print(test_patt)
            (success, _) = test_patt.run_tests(pass_tests)
            self.assertTrue(success, 'failed LineStart passing tests (3)')
            (success, _) = test_patt.run_tests(fail_tests, failure_tests=True)
            self.assertTrue(success, 'failed LineStart failure mode tests (3)')

    def testLineStart2(self):
        test = '        AAA 1\n        AAA 2\n\n          AAA\n\n        B AAA\n\n        '
        test = dedent(test)
        print('normal parsing')
        for (t, s, e) in (pp.LineStart() + 'AAA').scan_string(test):
            print(s, e, pp.lineno(s, test), pp.line(s, test), repr(t))
            print()
            self.assertEqual('A', t[0][0], 'failed LineStart with insignificant newlines')
        print('parsing without \\n in whitespace chars')
        with ppt.reset_pyparsing_context():
            pp.ParserElement.set_default_whitespace_chars(' ')
            for (t, s, e) in (pp.LineStart() + 'AAA').scan_string(test):
                print(s, e, pp.lineno(s, test), pp.line(s, test), repr(test[s]))
                print()
                self.assertEqual('A', t[0][0], 'failed LineStart with insignificant newlines')

    def testLineStartWithLeadingSpaces(self):
        instring = dedent('\n            a\n             b\n              c\n            d\n            e\n             f\n              g\n            ')
        alpha_line = pp.LineStart().leave_whitespace() + pp.Word(pp.alphas) + pp.LineEnd().suppress()
        tests = [alpha_line, pp.Group(alpha_line), alpha_line | pp.Word('_'), alpha_line | alpha_line, pp.MatchFirst([alpha_line, alpha_line]), alpha_line ^ pp.Word('_'), alpha_line ^ alpha_line, pp.Or([alpha_line, pp.Word('_')]), pp.LineStart() + pp.Word(pp.alphas) + pp.LineEnd().suppress(), pp.And([pp.LineStart(), pp.Word(pp.alphas), pp.LineEnd().suppress()])]
        fails = []
        for test in tests:
            print(test.search_string(instring))
            if ['a', 'b', 'c', 'd', 'e', 'f', 'g'] != flatten(sum(test.search_string(instring)).as_list()):
                fails.append(test)
        if fails:
            self.fail('failed LineStart tests:\n{}'.format('\n'.join((str(expr) for expr in fails))))

    def testAtLineStart(self):
        test = dedent('        AAA this line\n        AAA and this line\n          AAA but not this one\n        B AAA and definitely not this one\n        ')
        expr = pp.AtLineStart('AAA') + pp.rest_of_line
        for t in expr.search_string(test):
            print(t)
        self.assertEqual(['AAA', ' this line', 'AAA', ' and this line'], sum(expr.search_string(test)).as_list())

    def testStringStart(self):
        self.assertParseAndCheckList(pp.StringStart() + pp.Word(pp.nums), '123', ['123'])
        self.assertParseAndCheckList(pp.StringStart() + pp.Word(pp.nums), '   123', ['123'])
        self.assertParseAndCheckList(pp.StringStart() + '123', '123', ['123'])
        self.assertParseAndCheckList(pp.StringStart() + '123', '   123', ['123'])
        self.assertParseAndCheckList(pp.AtStringStart(pp.Word(pp.nums)), '123', ['123'])
        self.assertParseAndCheckList(pp.AtStringStart('123'), '123', ['123'])
        with self.assertRaisesParseException():
            pp.AtStringStart(pp.Word(pp.nums)).parse_string('    123')
        with self.assertRaisesParseException():
            pp.AtStringStart('123').parse_string('    123')

    def testStringStartAndLineStartInsideAnd(self):
        P_MTARG = pp.StringStart() + pp.Word('abcde') + pp.StringEnd()
        P_MTARG2 = pp.LineStart() + pp.Word('abcde') + pp.StringEnd()
        P_MTARG3 = pp.AtLineStart(pp.Word('abcde')) + pp.StringEnd()

        def test(expr, string):
            print(expr, repr(string), end=' ')
            print(expr.parse_string(string))
        test(P_MTARG, 'aaa')
        test(P_MTARG2, 'aaa')
        test(P_MTARG2, '\naaa')
        test(P_MTARG2, '   aaa')
        test(P_MTARG2, '\n   aaa')
        with self.assertRaisesParseException():
            test(P_MTARG3, '   aaa')
        with self.assertRaisesParseException():
            test(P_MTARG3, '\n   aaa')

    def testLineAndStringEnd(self):
        NLs = pp.OneOrMore(pp.line_end)
        bnf1 = pp.DelimitedList(pp.Word(pp.alphanums).leave_whitespace(), NLs)
        bnf2 = pp.Word(pp.alphanums) + pp.string_end
        bnf3 = pp.Word(pp.alphanums) + pp.SkipTo(pp.string_end)
        tests = [('testA\ntestB\ntestC\n', ['testA', 'testB', 'testC']), ('testD\ntestE\ntestF', ['testD', 'testE', 'testF']), ('a', ['a'])]
        for (test, expected) in tests:
            res1 = bnf1.parse_string(test, parse_all=True)
            print(res1, '=?', expected)
            self.assertParseResultsEquals(res1, expected_list=expected, msg=f'Failed line_end/string_end test (1): {test!r} -> {res1}')
            res2 = bnf2.search_string(test)[0]
            print(res2, '=?', expected[-1:])
            self.assertParseResultsEquals(res2, expected_list=expected[-1:], msg=f'Failed line_end/string_end test (2): {test!r} -> {res2}')
            res3 = bnf3.parse_string(test, parse_all=True)
            first = res3[0]
            rest = res3[1]
            print(repr(rest), '=?', repr(test[len(first) + 1:]))
            self.assertEqual(rest, test[len(first) + 1:], msg=f'Failed line_end/string_end test (3): {test!r} -> {res3.as_list()}')
            print()
        k = pp.Regex('a+', flags=re.S + re.M)
        k = k.parse_with_tabs()
        k = k.leave_whitespace()
        tests = [('aaa', ['aaa']), ('\\naaa', None), ('a\\naa', None), ('aaa\\n', None)]
        for (i, (src, expected)) in enumerate(tests):
            with self.subTest('', src=src, expected=expected):
                print(i, repr(src).replace('\\\\', '\\'), end=' ')
                if expected is None:
                    with self.assertRaisesParseException():
                        k.parse_string(src, parse_all=True)
                else:
                    res = k.parse_string(src, parse_all=True)
                    self.assertParseResultsEquals(res, expected, msg=f'Failed on parse_all=True test {i}')

    def testSingleArgException(self):
        testMessage = 'just one arg'
        try:
            raise pp.ParseFatalException(testMessage)
        except pp.ParseBaseException as pbe:
            print('Received expected exception:', pbe)
            raisedMsg = pbe.msg
            self.assertEqual(testMessage, raisedMsg, 'Failed to get correct exception message')

    def testOriginalTextFor(self):

        def rfn(t):
            return f"{t.src}:{len(''.join(t))}"
        makeHTMLStartTag = lambda tag: pp.original_text_for(pp.make_html_tags(tag)[0], as_string=False)
        start = makeHTMLStartTag('IMG')
        start.add_parse_action(rfn)
        text = '_<img src="images/cal.png"\n            alt="cal image" width="16" height="15">_'
        s = start.transform_string(text)
        print(s)
        self.assertTrue(s.startswith('_images/cal.png:'), 'failed to preserve input s properly')
        self.assertTrue(s.endswith('77_'), 'failed to return full original text properly')
        tag_fields = makeHTMLStartTag('IMG').search_string(text)[0]
        print(sorted(tag_fields.keys()))
        self.assertEqual(['alt', 'empty', 'height', 'src', 'startImg', 'tag', 'width'], sorted(tag_fields.keys()), 'failed to preserve results names in original_text_for')

    def testParseResultsDel(self):
        grammar = pp.OneOrMore(pp.Word(pp.nums))('ints') + pp.OneOrMore(pp.Word(pp.alphas))('words')
        res = grammar.parse_string('123 456 ABC DEF', parse_all=True)
        print(res.dump())
        origInts = res.ints.as_list()
        origWords = res.words.as_list()
        del res[1]
        del res['words']
        print(res.dump())
        self.assertEqual('ABC', res[1], "failed to delete 0'th element correctly")
        self.assertEqual(origInts, res.ints.as_list(), 'updated named attributes, should have updated list only')
        self.assertEqual('', res.words, 'failed to update named attribute correctly')
        self.assertEqual('DEF', res[-1], 'updated list, should have updated named attributes only')

    def testWithAttributeParseAction(self):
        """
        This unit test checks with_attribute in these ways:

        * Argument forms as keywords and tuples
        * Selecting matching tags by attribute
        * Case-insensitive attribute matching
        * Correctly matching tags having the attribute, and rejecting tags not having the attribute

        (Unit test written by voigts as part of the Google Highly Open Participation Contest)
        """
        data = '\n        <a>1</a>\n        <a b="x">2</a>\n        <a B="x">3</a>\n        <a b="X">4</a>\n        <a b="y">5</a>\n        <a class="boo">8</ a>\n        '
        (tagStart, tagEnd) = pp.make_html_tags('a')
        expr = tagStart + pp.Word(pp.nums)('value') + tagEnd
        expected = ([['a', ['b', 'x'], False, '2', '</a>'], ['a', ['b', 'x'], False, '3', '</a>']], [['a', ['b', 'x'], False, '2', '</a>'], ['a', ['b', 'x'], False, '3', '</a>']], [['a', ['class', 'boo'], False, '8', '</a>']])
        for (attrib, exp) in zip([pp.with_attribute(b='x'), pp.with_attribute(('b', 'x')), pp.with_class('boo')], expected):
            tagStart.set_parse_action(attrib)
            result = expr.search_string(data)
            print(result.dump())
            self.assertParseResultsEquals(result, expected_list=exp, msg=f'Failed test, expected {expected}, got {result.as_list()}')

    def testNestedExpressions(self):
        """
        This unit test checks nested_expr in these ways:
        - use of default arguments
        - use of non-default arguments (such as a pyparsing-defined comment
          expression in place of quoted_string)
        - use of a custom content expression
        - use of a pyparsing expression for opener and closer is *OPTIONAL*
        - use of input data containing nesting delimiters
        - correct grouping of parsed tokens according to nesting of opening
          and closing delimiters in the input string

        (Unit test written by christoph... as part of the Google Highly Open Participation Contest)
        """
        print('Test defaults:')
        teststring = '((ax + by)*C) (Z | (E^F) & D)'
        expr = pp.nested_expr()
        expected = [[['ax', '+', 'by'], '*C']]
        result = expr.parse_string(teststring, parse_all=False)
        print(result.dump())
        self.assertParseResultsEquals(result, expected_list=expected, msg=f"Defaults didn't work. That's a bad sign. Expected: {expected}, got: {result}")
        print('\nNon-default opener')
        teststring = '[[ ax + by)*C)'
        expected = [[['ax', '+', 'by'], '*C']]
        expr = pp.nested_expr('[')
        self.assertParseAndCheckList(expr, teststring, expected, f"Non-default opener didn't work. Expected: {expected}, got: {result}", verbose=True)
        print('\nNon-default closer')
        teststring = '((ax + by]*C]'
        expected = [[['ax', '+', 'by'], '*C']]
        expr = pp.nested_expr(closer=']')
        self.assertParseAndCheckList(expr, teststring, expected, f"Non-default closer didn't work. Expected: {expected}, got: {result}", verbose=True)
        print('\nLiteral expressions for opener and closer')
        (opener, closer) = map(pp.Literal, 'bar baz'.split())
        expr = pp.nested_expr(opener, closer, content=pp.Regex('([^b ]|b(?!a)|ba(?![rz]))+'))
        teststring = 'barbar ax + bybaz*Cbaz'
        expected = [[['ax', '+', 'by'], '*C']]
        self.assertParseAndCheckList(expr, teststring, expected, f"Multicharacter opener and closer didn't work. Expected: {expected}, got: {result}", verbose=True)
        print('\nUse ignore expression (1)')
        comment = pp.Regex(';;.*')
        teststring = '\n        (let ((greeting "Hello, world!")) ;;(foo bar\n           (display greeting))\n        '
        expected = [['let', [['greeting', '"Hello,', 'world!"']], ';;(foo bar', ['display', 'greeting']]]
        expr = pp.nested_expr(ignore_expr=comment)
        self.assertParseAndCheckList(expr, teststring, expected, f"""Lisp-ish comments (";; <...> $") didn't work. Expected: {expected}, got: {result}""", verbose=True)
        print('\nUse ignore expression (2)')
        comment = ';;' + pp.rest_of_line
        teststring = '\n        (let ((greeting "Hello, )world!")) ;;(foo bar\n           (display greeting))\n        '
        expected = [['let', [['greeting', '"Hello, )world!"']], ';;', '(foo bar', ['display', 'greeting']]]
        expr = pp.nested_expr(ignore_expr=comment ^ pp.quoted_string)
        self.assertParseAndCheckList(expr, teststring, expected, f"""Lisp-ish comments (";; <...> $") and quoted strings didn't work. Expected: {expected}, got: {result}""", verbose=True)

    def testNestedExpressions2(self):
        """test nested_expr with conditions that explore other paths

        identical opener and closer
        opener and/or closer of type other than string or iterable
        multi-character opener and/or closer
        single character opener and closer with ignore_expr=None
        multi-character opener and/or closer with ignore_expr=None
        """
        name = pp.Word(pp.alphanums + '_')
        with self.assertRaises(ValueError, msg='matching opener and closer should raise error'):
            expr = name + pp.nested_expr(opener='{', closer='{')
        with self.assertRaises(ValueError, msg='opener and closer as ints should raise error'):
            expr = name + pp.nested_expr(opener=12, closer=18)
        tstMulti = "aName {{ outer {{ 'inner with opener {{ and closer }} in quoted string' }} }}"
        expr = name + pp.nested_expr(opener='{{', closer='}}')
        result = expr.parse_string(tstMulti, parse_all=True)
        expected = ['aName', ['outer', ["'inner with opener {{ and closer }} in quoted string'"]]]
        print(result.dump())
        self.assertParseResultsEquals(result, expected, msg='issue with multi-character opener and closer')
        tst = "aName { outer { 'inner with opener { and closer } in quoted string' }}"
        expr = name + pp.nested_expr(opener='{', closer='}', ignore_expr=None)
        singleCharResult = expr.parse_string(tst, parse_all=True)
        print(singleCharResult.dump())
        expr = name + pp.nested_expr(opener='{{', closer='}}', ignore_expr=None)
        multiCharResult = expr.parse_string(tstMulti, parse_all=True)
        print(multiCharResult.dump())
        self.assertParseResultsEquals(singleCharResult, multiCharResult.as_list(), msg="using different openers and closers shouldn't affect resulting ParseResults")

    def testNestedExpressions3(self):
        with ppt.reset_pyparsing_context():
            pp.ParserElement.set_default_whitespace_chars('')
            input_str = dedent('                selector\n                {\n                  a:b;\n                  c:d;\n                  selector\n                  {\n                    a:b;\n                    c:d;\n                  }\n                  y:z;\n                }')
            nested_result = pp.nested_expr('{', '}').parse_string('{' + input_str + '}').as_list()
            expected_result = [['selector\n', ['\n  a:b;\n  c:d;\n  selector\n  ', ['\n    a:b;\n    c:d;\n  '], '\n  y:z;\n']]]
            self.assertEqual(nested_result, expected_result)

    def testNestedExpressions4(self):
        allowed = pp.alphas
        plot_options_short = pp.nested_expr('[', ']', content=pp.OneOrMore(pp.Word(allowed) ^ pp.quoted_string)).set_results_name('plot_options')
        self.assertParseAndCheckList(plot_options_short, "[slkjdfl sldjf [lsdf'lsdf']]", [['slkjdfl', 'sldjf', ['lsdf', "'lsdf'"]]])

    def testNestedExpressionDoesNotOverwriteParseActions(self):
        content = pp.Word(pp.nums + ' ')
        content.add_parse_action(lambda t: None)
        orig_pa = content.parseAction[0]
        expr = pp.nested_expr(content=content)
        assert content.parseAction[0] is orig_pa

    def testNestedExpressionRandom(self):
        import random
        word_chars = pp.alphanums

        def get_random_character(_charset=word_chars + '               '):
            return random.choice(_charset)

        def create_random_quoted_string():
            quote_char = random.choice(('"', "'"))
            yield quote_char
            yield from (get_random_character() for _ in range(random.randint(0, 12)))
            yield quote_char

        def create_random_nested_expression():
            yield '['
            if random.random() < 0.25:
                yield from create_random_quoted_string()
            for _ in range(random.randint(0, 16)):
                rnd = random.random()
                if rnd < 0.25:
                    yield from create_random_quoted_string()
                elif rnd < 0.3:
                    yield from create_random_nested_expression()
                else:
                    yield from (get_random_character() for _ in range(random.randint(1, 4)))
            if random.random() < 0.25:
                yield from create_random_quoted_string()
            yield ']'
        num_reps = 150
        (LBRACK, RBRACK) = pp.Suppress.using_each('[]')
        wd = pp.Word(word_chars)
        qs = pp.quoted_string()
        ls = pp.Forward()
        ls <<= pp.Group(LBRACK + (qs | ls | wd)[...] + RBRACK)

        def crack_nested_string(s) -> list:
            return ls.parse_string(s, parse_all=True).as_list()
        expr = pp.nested_expr('[', ']')
        for _ in range(num_reps):
            nested_str = ''.join(create_random_nested_expression())
            cracked_result = crack_nested_string(nested_str)
            self.assertParseAndCheckList(expr, nested_str, cracked_result, f'Failed: {nested_str}, expected {cracked_result}', verbose=False)
        expr = pp.nested_expr('<<', '>>')
        for _ in range(num_reps):
            nested_str = ''.join(create_random_nested_expression())
            cracked_result = crack_nested_string(nested_str)
            nested_str = nested_str.replace('[', '<<').replace(']', '>>')
            self.assertParseAndCheckList(expr, nested_str, cracked_result, f'Failed: {nested_str}, expected {cracked_result}', verbose=False)
        expr = pp.nested_expr('[', ']', ignore_expr=None)
        for _ in range(num_reps):
            nested_str = ''.join(create_random_nested_expression())
            nested_str = nested_str.replace('"', '').replace("'", '')
            cracked_result = crack_nested_string(nested_str)
            self.assertParseAndCheckList(expr, nested_str, cracked_result, f'Failed: {nested_str}, expected {cracked_result}', verbose=False)
        expr = pp.nested_expr('<<', '>>', ignore_expr=None)
        for _ in range(num_reps):
            nested_str = ''.join(create_random_nested_expression())
            nested_str = nested_str.replace('"', '').replace("'", '')
            cracked_result = crack_nested_string(nested_str)
            nested_str = nested_str.replace('[', '<<').replace(']', '>>')
            self.assertParseAndCheckList(expr, nested_str, cracked_result, f'Failed: {nested_str}, expected {cracked_result}', verbose=False)

    def testWordMinMaxArgs(self):
        parsers = ['A' + pp.Word(pp.nums), 'A' + pp.Word(pp.nums, min=1), 'A' + pp.Word(pp.nums, max=6), 'A' + pp.Word(pp.nums, min=1, max=6), 'A' + pp.Word(pp.nums, min=1), 'A' + pp.Word(pp.nums, min=2), 'A' + pp.Word(pp.nums, min=2, max=6), pp.Word('A', pp.nums), pp.Word('A', pp.nums, min=1), pp.Word('A', pp.nums, max=6), pp.Word('A', pp.nums, min=1, max=6), pp.Word('A', pp.nums, min=1), pp.Word('A', pp.nums, min=2), pp.Word('A', pp.nums, min=2, max=6), pp.Word(pp.alphas, pp.nums), pp.Word(pp.alphas, pp.nums, min=1), pp.Word(pp.alphas, pp.nums, max=6), pp.Word(pp.alphas, pp.nums, min=1, max=6), pp.Word(pp.alphas, pp.nums, min=1), pp.Word(pp.alphas, pp.nums, min=2), pp.Word(pp.alphas, pp.nums, min=2, max=6)]
        fails = []
        for p in parsers:
            print(p, getattr(p, 'reString', '...'), end=' ', flush=True)
            try:
                p.parse_string('A123', parse_all=True)
            except Exception as e:
                print('      <<< FAIL')
                fails.append(p)
            else:
                print()
        if fails:
            self.fail(f"{','.join((str(f) for f in fails))} failed to match")

    def testWordMinMaxExactArgs(self):
        for minarg in range(1, 9):
            for maxarg in range(minarg, 10):
                with self.subTest(minarg=minarg, maxarg=maxarg):
                    expr = pp.Word('AB', pp.nums, min=minarg, max=maxarg)
                    self.assertParseAndCheckList(expr + pp.rest_of_line.suppress(), 'A1234567890', ['A1234567890'[:maxarg]])
                    if minarg > 1:
                        with self.assertRaisesParseException():
                            expr.parse_string('A1234567890'[:minarg - 1], parse_all=True)
        for exarg in range(1, 9):
            with self.subTest(exarg=exarg):
                expr = pp.Word('AB', pp.nums, exact=exarg)
                self.assertParseAndCheckList(expr + pp.rest_of_line.suppress(), 'A1234567890', ['A1234567890'[:exarg]])
                if exarg > 1:
                    with self.assertRaisesParseException():
                        expr.parse_string('A1234567890'[:exarg - 1], parse_all=True)

    def testWordMin(self):
        for min_val in range(3, 5):
            with self.subTest(min_val=min_val):
                wd = pp.Word('a', '1', min=min_val)
                with self.assertRaisesParseException():
                    wd.parse_string('a1')
        for min_val in range(2, 5):
            with self.subTest(min_val=min_val):
                wd = pp.Word('a', min=min_val)
                with self.assertRaisesParseException():
                    wd.parse_string('a')
        for min_val in range(3, 5):
            with self.subTest(min_val=min_val):
                wd = pp.Word('a', '1', min=min_val)
                with self.assertRaisesParseException():
                    wd.parse_string('a1')
        for min_val in range(2, 5):
            with self.subTest(min_val=min_val):
                wd = pp.Word('a', min=min_val)
                test_string = 'a' * min_val
                self.assertParseAndCheckList(wd, test_string, [test_string], msg=f'Word(min={min_val}) failed', verbose=True)
        for min_val in range(2, 5):
            with self.subTest(min_val=min_val):
                wd = pp.Word('a', '1', min=min_val)
                test_string = 'a' + '1' * (min_val - 1)
                self.assertParseAndCheckList(wd, test_string, [test_string], msg=f'Word(min={min_val}) failed', verbose=True)

    def testWordExact(self):
        for exact_val in range(2, 5):
            with self.subTest(exact_val=exact_val):
                wd = pp.Word('a', exact=exact_val)
                with self.assertRaisesParseException():
                    wd.parse_string('a')
        for exact_val in range(2, 5):
            with self.subTest(exact_val=exact_val):
                wd = pp.Word('a', exact=exact_val)
                test_string = 'a' * exact_val
                self.assertParseAndCheckList(wd, test_string, [test_string], msg=f'Word(exact={exact_val}) failed', verbose=True)

    def testInvalidMinMaxArgs(self):
        with self.assertRaises(ValueError):
            wd = pp.Word(min=2, max=1)

    def testWordExclude(self):
        allButPunc = pp.Word(pp.printables, exclude_chars='.,:;-_!?')
        test = "Hello, Mr. Ed, it's Wilbur!"
        result = allButPunc.search_string(test).as_list()
        print(result)
        self.assertEqual([['Hello'], ['Mr'], ['Ed'], ["it's"], ['Wilbur']], result, 'failed WordExcludeTest')

    def testWordExclude2(self):
        punc_chars = '.,:;-_!?'
        all_but_punc = pp.Word(pp.printables, exclude_chars=punc_chars)
        all_and_punc = pp.Word(pp.printables)
        expr = all_but_punc('no_punc*') | all_and_punc('with_punc*')
        self.assertParseAndCheckDict(expr[...], 'Mr. Ed,', {'no_punc': ['Mr', 'Ed'], 'with_punc': ['.', ',']}, 'failed matching with exclude_chars (1)')
        self.assertParseAndCheckDict(expr[...], ':Mr. Ed,', {'no_punc': ['Ed'], 'with_punc': [':Mr.', ',']}, 'failed matching with exclude_chars (2)')

    def testWordMinOfZero(self):
        """test a Word with min=0"""
        with self.assertRaises(ValueError, msg='expected min 0 to error'):
            expr = pp.Word(pp.nums, min=0, max=10)

    @staticmethod
    def setup_testWordMaxGreaterThanZeroAndAsKeyword():
        bool_operand = pp.Word(pp.alphas, max=1, as_keyword=True) | pp.one_of('True False')
        test_string = 'p q r False'
        return SimpleNamespace(**locals())

    def testWordMaxGreaterThanZeroAndAsKeyword1(self):
        """test a Word with max>0 and as_keyword=True"""
        setup = self.setup_testWordMaxGreaterThanZeroAndAsKeyword()
        result = setup.bool_operand[...].parse_string(setup.test_string, parse_all=True)
        self.assertParseAndCheckList(setup.bool_operand[...], setup.test_string, setup.test_string.split(), msg=f'{__()}Failed to parse Word(max=1, as_keyword=True)', verbose=True)

    def testWordMaxGreaterThanZeroAndAsKeyword2(self):
        """test a Word with max>0 and as_keyword=True"""
        setup = self.setup_testWordMaxGreaterThanZeroAndAsKeyword()
        with self.assertRaisesParseException(msg=f'{__()}Failed to detect Word with max > 0 and as_keyword=True'):
            setup.bool_operand.parse_string('abc', parse_all=True)

    def testCharAsKeyword(self):
        """test a Char with as_keyword=True"""
        grade = pp.OneOrMore(pp.Char('ABCDF', as_keyword=True))
        result = grade.parse_string('B B C A D', parse_all=True)
        print(result)
        expected = ['B', 'B', 'C', 'A', 'D']
        self.assertParseResultsEquals(result, expected, msg='issue with Char as_keyword=True')
        test2 = 'B BB C A D'
        result2 = grade.parse_string(test2, parse_all=False)
        print(result2)
        expected2 = ['B']
        self.assertParseResultsEquals(result2, expected2, msg='issue with Char as_keyword=True parsing 2 chars')

    def testCharRe(self):
        expr = pp.Char('ABCDEFG')
        self.assertEqual('[A-G]', expr.reString)

    def testCharsNotIn(self):
        """test CharsNotIn initialized with various arguments"""
        vowels = 'AEIOU'
        tst = 'bcdfghjklmnpqrstvwxyz'
        consonants = pp.CharsNotIn(vowels)
        result = consonants.parse_string(tst, parse_all=True)
        print(result)
        self.assertParseResultsEquals(result, [tst], msg='issue with CharsNotIn w/ default args')
        consonants = pp.CharsNotIn(vowels, max=5)
        result = consonants.parse_string(tst, parse_all=False)
        print(result)
        self.assertParseResultsEquals(result, [tst[:5]], msg='issue with CharsNotIn w max > 0')
        consonants = pp.CharsNotIn(vowels, exact=10)
        result = consonants.parse_string(tst[:10], parse_all=True)
        print(result)
        self.assertParseResultsEquals(result, [tst[:10]], msg='issue with CharsNotIn w/ exact > 0')
        consonants = pp.CharsNotIn(vowels, min=25)
        with self.assertRaisesParseException(msg='issue with CharsNotIn min > tokens'):
            result = consonants.parse_string(tst, parse_all=True)

    def testParseAll(self):
        testExpr = pp.Word('A')
        tests = [('AAAAA', False, True), ('AAAAA', True, True), ('AAABB', False, True), ('AAABB', True, False)]
        for (s, parse_allFlag, shouldSucceed) in tests:
            try:
                print(f"'{s}' parse_all={parse_allFlag} (shouldSucceed={shouldSucceed})")
                testExpr.parse_string(s, parse_all=parse_allFlag)
                self.assertTrue(shouldSucceed, 'successfully parsed when should have failed')
            except ParseException as pe:
                print(pe.explain())
                self.assertFalse(shouldSucceed, 'failed to parse when should have succeeded')
        testExpr.ignore(pp.cpp_style_comment)
        tests = [('AAAAA //blah', False, True), ('AAAAA //blah', True, True), ('AAABB //blah', False, True), ('AAABB //blah', True, False)]
        for (s, parse_allFlag, shouldSucceed) in tests:
            try:
                print(f"'{s}' parse_all={parse_allFlag} (shouldSucceed={shouldSucceed})")
                testExpr.parse_string(s, parse_all=parse_allFlag)
                self.assertTrue(shouldSucceed, 'successfully parsed when should have failed')
            except ParseException as pe:
                print(pe.explain())
                self.assertFalse(shouldSucceed, 'failed to parse when should have succeeded')
        anything_but_an_f = pp.OneOrMore(pp.MatchFirst([pp.Literal(c) for c in pp.printables if c != 'f']))
        testExpr = pp.Word('012') + anything_but_an_f
        tests = [('00aab', False, True), ('00aab', True, True), ('00aaf', False, True), ('00aaf', True, False)]
        for (s, parse_allFlag, shouldSucceed) in tests:
            try:
                print(f"'{s}' parse_all={parse_allFlag} (shouldSucceed={shouldSucceed})")
                testExpr.parse_string(s, parse_all=parse_allFlag)
                self.assertTrue(shouldSucceed, 'successfully parsed when should have failed')
            except ParseException as pe:
                print(pe.explain())
                self.assertFalse(shouldSucceed, 'failed to parse when should have succeeded')

    def testGreedyQuotedStrings(self):
        src = '           "string1", "strin""g2"\n           \'string1\', \'string2\'\n           ^string1^, ^string2^\n           <string1>, <string2>'
        testExprs = (pp.sgl_quoted_string, pp.dbl_quoted_string, pp.quoted_string, pp.QuotedString('"', esc_quote='""'), pp.QuotedString("'", esc_quote="''"), pp.QuotedString('^'), pp.QuotedString('<', end_quote_char='>'))
        for expr in testExprs:
            strs = pp.DelimitedList(expr).search_string(src)
            print(strs)
            self.assertTrue(bool(strs), f"no matches found for test expression '{expr}'")
            for lst in strs:
                self.assertEqual(2, len(lst), f"invalid match found for test expression '{expr}'")
        src = "'ms1',1,0,'2009-12-22','2009-12-22 10:41:22') ON DUPLICATE KEY UPDATE sent_count = sent_count + 1, mtime = '2009-12-22 10:41:22';"
        tok_sql_quoted_value = pp.QuotedString("'", '\\', "''", True, False) ^ pp.QuotedString('"', '\\', '""', True, False)
        tok_sql_computed_value = pp.Word(pp.nums)
        tok_sql_identifier = pp.Word(pp.alphas)
        val = tok_sql_quoted_value | tok_sql_computed_value | tok_sql_identifier
        vals = pp.DelimitedList(val)
        print(vals.parse_string(src, parse_all=False))
        self.assertEqual(5, len(vals.parse_string(src, parse_all=False)), 'error in greedy quote escaping')

    def testQuotedStringEscapedQuotes(self):
        quoted = pp.QuotedString('"', esc_quote='""')
        res = quoted.parse_string('"like ""SQL"""', parse_all=True)
        print(res.as_list())
        self.assertEqual(['like "SQL"'], res.as_list())
        quoted = pp.QuotedString('y', esc_char=None, esc_quote='xy')
        res = quoted.parse_string('yaaay', parse_all=True)
        self.assertEqual(['aaa'], res.as_list())
        res = quoted.parse_string('yaaaxyaaay', parse_all=True)
        print(res.as_list())
        self.assertEqual(['aaayaaa'], res.as_list())

    def testQuotedStringEscapedExtendedChars(self):
        quoted = pp.QuotedString("'")
        self.assertParseAndCheckList(quoted, "'null: \x00 octal: · hex: · unicode: ·'", ['null: \x00 octal: · hex: · unicode: ·'], 'failed to parse embedded numeric escapes')

    def testWordBoundaryExpressions(self):
        ws = pp.WordStart()
        we = pp.WordEnd()
        vowel = pp.one_of(list('AEIOUY'))
        consonant = pp.one_of(list('BCDFGHJKLMNPQRSTVWXZ'))
        leadingVowel = ws + vowel
        trailingVowel = vowel + we
        leadingConsonant = ws + consonant
        trailingConsonant = consonant + we
        internalVowel = ~ws + vowel + ~we
        bnf = leadingVowel | trailingVowel
        tests = '        ABC DEF GHI\n          JKL MNO PQR\n        STU VWX YZ  '.splitlines()
        tests.append('\n'.join(tests))
        expectedResult = [[['D', 'G'], ['A'], ['C', 'F'], ['I'], ['E'], ['A', 'I']], [['J', 'M', 'P'], [], ['L', 'R'], ['O'], [], ['O']], [['S', 'V'], ['Y'], ['X', 'Z'], ['U'], [], ['U', 'Y']], [['D', 'G', 'J', 'M', 'P', 'S', 'V'], ['A', 'Y'], ['C', 'F', 'L', 'R', 'X', 'Z'], ['I', 'O', 'U'], ['E'], ['A', 'I', 'O', 'U', 'Y']]]
        for (t, expected) in zip(tests, expectedResult):
            print(t)
            results = [flatten(e.search_string(t).as_list()) for e in [leadingConsonant, leadingVowel, trailingConsonant, trailingVowel, internalVowel, bnf]]
            print(results)
            print()
            self.assertEqual(expected, results, f'Failed WordBoundaryTest, expected {expected}, got {results}')

    def testWordBoundaryExpressions2(self):
        from itertools import product
        ws1 = pp.WordStart(pp.alphas)
        ws2 = pp.WordStart(word_chars=pp.alphas)
        ws3 = pp.WordStart(word_chars=pp.alphas)
        we1 = pp.WordEnd(pp.alphas)
        we2 = pp.WordEnd(word_chars=pp.alphas)
        we3 = pp.WordEnd(word_chars=pp.alphas)
        for (i, (ws, we)) in enumerate(product((ws1, ws2, ws3), (we1, we2, we3))):
            try:
                expr = '(' + ws + pp.Word(pp.alphas) + we + ')'
                expr.parse_string('(abc)', parse_all=True)
            except pp.ParseException as pe:
                self.fail(f'Test {i} failed: {pe}')
            else:
                pass

    def testRequiredEach(self):
        parser = pp.Keyword('bam') & pp.Keyword('boo')
        try:
            res1 = parser.parse_string('bam boo', parse_all=True)
            print(res1.as_list())
            res2 = parser.parse_string('boo bam', parse_all=True)
            print(res2.as_list())
        except ParseException:
            failed = True
        else:
            failed = False
            self.assertFalse(failed, 'invalid logic in Each')
            self.assertEqual(set(res1), set(res2), f'Failed RequiredEachTest, expected {res1.as_list()} and {res2.as_list} to contain the same words in any order')

    def testOptionalEachTest1(self):
        for the_input in ['Tal Weiss Major', 'Tal Major', 'Weiss Major', 'Major', 'Major Tal', 'Major Weiss', 'Major Tal Weiss']:
            print(the_input)
            parser1 = pp.Optional('Tal') + pp.Optional('Weiss') & pp.Keyword('Major')
            parser2 = pp.Optional(pp.Optional('Tal') + pp.Optional('Weiss')) & pp.Keyword('Major')
            parser3 = (pp.Keyword('Tal') | pp.Keyword('Weiss'))[...] & pp.Keyword('Major')
            p1res = parser1.parse_string(the_input, parse_all=True)
            p2res = parser2.parse_string(the_input, parse_all=True)
            self.assertEqual(p1res.as_list(), p2res.as_list(), f'Each failed to match with nested Optionals, {p1res.as_list()} should match {p2res.as_list()}')
            p3res = parser3.parse_string(the_input, parse_all=True)
            self.assertEqual(p1res.as_list(), p3res.as_list(), f'Each failed to match with repeated Optionals, {p1res.as_list()} should match {p3res.as_list()}')

    def testOptionalEachTest2(self):
        word = pp.Word(pp.alphanums + '_').set_name('word')
        with_stmt = 'with' + pp.OneOrMore(pp.Group(word('key') + '=' + word('value')))('overrides')
        using_stmt = 'using' + pp.Regex('id-[0-9a-f]{8}')('id')
        modifiers = pp.Optional(with_stmt('with_stmt')) & pp.Optional(using_stmt('using_stmt'))
        self.assertEqual('with foo=bar bing=baz using id-deadbeef', modifiers)
        self.assertNotEqual('with foo=bar bing=baz using id-deadbeef using id-feedfeed', modifiers)

    def testOptionalEachTest3(self):
        foo = pp.Literal('foo')
        bar = pp.Literal('bar')
        openBrace = pp.Suppress(pp.Literal('{'))
        closeBrace = pp.Suppress(pp.Literal('}'))
        exp = openBrace + (foo[1, ...]('foo') & bar[...]('bar')) + closeBrace
        tests = '            {foo}\n            {bar foo bar foo bar foo}\n            '.splitlines()
        for test in tests:
            test = test.strip()
            if not test:
                continue
            self.assertParseAndCheckList(exp, test, test.strip('{}').split(), f'failed to parse Each expression {test!r}', verbose=True)
        with self.assertRaisesParseException():
            exp.parse_string('{bar}', parse_all=True)

    def testOptionalEachTest4(self):
        expr = ~ppc.iso8601_date + ppc.integer('id') & pp.Group(ppc.iso8601_date)('date*')[...]
        (success, _) = expr.run_tests('\n            1999-12-31 100 2001-01-01\n            42\n            ')
        self.assertTrue(success)

    def testEachWithParseFatalException(self):
        option_expr = pp.Keyword('options') - '(' + ppc.integer + ')'
        step_expr1 = pp.Keyword('step') - '(' + ppc.integer + ')'
        step_expr2 = pp.Keyword('step') - '(' + ppc.integer + 'Z' + ')'
        step_expr = step_expr1 ^ step_expr2
        parser = option_expr & step_expr[...]
        tests = [('options(100) step(A)', "Expected integer, found 'A'  (at char 18), (line:1, col:19)"), ('step(A) options(100)', "Expected integer, found 'A'  (at char 5), (line:1, col:6)"), ('options(100) step(100A)', "Expected 'Z', found 'A'  (at char 21), (line:1, col:22)"), ('options(100) step(22) step(100ZA)', "Expected ')', found 'A'  (at char 31), (line:1, col:32)")]
        test_lookup = dict(tests)
        (success, output) = parser.run_tests((t[0] for t in tests), failure_tests=True)
        for (test_str, result) in output:
            self.assertEqual(test_lookup[test_str], str(result), f'incorrect exception raised for test string {test_str!r}')

    def testEachWithMultipleMatch(self):
        size = 'size' + pp.one_of('S M L XL')
        color = pp.Group('color' + pp.one_of('red orange yellow green blue purple white black brown'))
        size.set_name('size_spec')
        color.set_name('color_spec')
        spec0 = size('size') & color[...]('colors')
        spec1 = size('size') & color[1, ...]('colors')
        for spec in (spec0, spec1):
            for (test, expected_dict) in [('size M color red color yellow', {'colors': [['color', 'red'], ['color', 'yellow']], 'size': ['size', 'M']}), ('color green size M color red color yellow', {'colors': [['color', 'green'], ['color', 'red'], ['color', 'yellow']], 'size': ['size', 'M']})]:
                result = spec.parse_string(test, parse_all=True)
                self.assertParseResultsEquals(result, expected_dict=expected_dict)

    def testSumParseResults(self):
        samplestr1 = 'garbage;DOB 10-10-2010;more garbage\nID PARI12345678;more garbage'
        samplestr2 = 'garbage;ID PARI12345678;more garbage\nDOB 10-10-2010;more garbage'
        samplestr3 = 'garbage;DOB 10-10-2010'
        samplestr4 = 'garbage;ID PARI12345678;more garbage- I am cool'
        res1 = 'ID:PARI12345678 DOB:10-10-2010 INFO:'
        res2 = 'ID:PARI12345678 DOB:10-10-2010 INFO:'
        res3 = 'ID: DOB:10-10-2010 INFO:'
        res4 = 'ID:PARI12345678 DOB: INFO: I am cool'
        dob_ref = 'DOB' + pp.Regex('\\d{2}-\\d{2}-\\d{4}')('dob')
        id_ref = 'ID' + pp.Word(pp.alphanums, exact=12)('id')
        info_ref = '-' + pp.rest_of_line('info')
        person_data = dob_ref | id_ref | info_ref
        tests = (samplestr1, samplestr2, samplestr3, samplestr4)
        results = (res1, res2, res3, res4)
        for (test, expected) in zip(tests, results):
            person = sum(person_data.search_string(test))
            result = f'ID:{person.id} DOB:{person.dob} INFO:{person.info}'
            print(test)
            print(expected)
            print(result)
            for pd in person_data.search_string(test):
                print(pd.dump())
            print()
            self.assertEqual(expected, result, f"Failed to parse '{test}' correctly, \nexpected '{expected}', got '{result}'")

    def testMarkInputLine(self):
        samplestr1 = 'DOB 100-10-2010;more garbage\nID PARI12345678;more garbage'
        dob_ref = 'DOB' + pp.Regex('\\d{2}-\\d{2}-\\d{4}')('dob')
        try:
            res = dob_ref.parse_string(samplestr1, parse_all=True)
        except ParseException as pe:
            outstr = pe.mark_input_line()
            print(outstr)
            self.assertEqual('DOB >!<100-10-2010;more garbage', outstr, 'did not properly create marked input line')
        else:
            self.fail('test construction failed - should have raised an exception')

    def testLocatedExpr(self):
        samplestr1 = 'DOB 10-10-2010;more garbage;ID PARI12345678  ;more garbage'
        with self.assertWarns(PyparsingDeprecationWarning):
            id_ref = pp.locatedExpr('ID' + pp.Word(pp.alphanums, exact=12)('id'))
        res = id_ref.search_string(samplestr1)[0][0]
        print(res.dump())
        self.assertEqual('ID PARI12345678', samplestr1[res.locn_start:res.locn_end], 'incorrect location calculation')

    def testLocatedExprUsingLocated(self):
        samplestr1 = 'DOB 10-10-2010;more garbage;ID PARI12345678  ;more garbage'
        id_ref = pp.Located('ID' + pp.Word(pp.alphanums, exact=12)('id'))
        res = id_ref.search_string(samplestr1)[0]
        print(res.dump())
        self.assertEqual('ID PARI12345678', samplestr1[res.locn_start:res.locn_end], 'incorrect location calculation')
        self.assertParseResultsEquals(res, [28, ['ID', 'PARI12345678'], 43], {'locn_end': 43, 'locn_start': 28, 'value': {'id': 'PARI12345678'}})
        self.assertEqual('PARI12345678', res.value.id)
        id_ref = pp.Located('ID' + pp.Word(pp.alphanums, exact=12)('id'))('loc')
        res = id_ref.search_string(samplestr1)[0]
        print(res.dump())
        self.assertEqual('ID PARI12345678', samplestr1[res.loc.locn_start:res.loc.locn_end], 'incorrect location calculation')
        self.assertParseResultsEquals(res.loc, [28, ['ID', 'PARI12345678'], 43], {'locn_end': 43, 'locn_start': 28, 'value': {'id': 'PARI12345678'}})
        self.assertEqual('PARI12345678', res.loc.value.id)
        wd = pp.Word(pp.alphas)
        test_string = 'ljsdf123lksdjjf123lkkjj1222'
        pp_matches = pp.Located(wd).search_string(test_string)
        re_matches = find_all_re_matches('[a-z]+', test_string)
        for (pp_match, re_match) in zip(pp_matches, re_matches):
            self.assertParseResultsEquals(pp_match, [re_match.start(), [re_match.group(0)], re_match.end()])
            print(pp_match)
            print(re_match)
            print(pp_match.value)

    def testLocatedExprLeadingWhitespace(self):
        abc = pp.Keyword('abc')
        single = pp.Located(abc).parse_string('   abc')
        self.assertParseResultsEquals(single, [3, ['abc'], 6])
        match_first = pp.Located(abc | abc).parse_string('   abc')
        self.assertParseResultsEquals(match_first, [3, ['abc'], 6])
        self.assertEqual('abc', '   abc'[match_first.locn_start:match_first.locn_end], 'Located(MatchFirst) included leading whitespace in its location')
        sample = '   ID PARI12345678'
        seq = pp.Located(pp.Literal('ID') + pp.Word(pp.alphanums)).parse_string(sample)
        self.assertEqual('ID PARI12345678', sample[seq.locn_start:seq.locn_end], 'Located(And) included leading whitespace in its location')
        leave_ws = pp.Located(pp.Word(' abc').leave_whitespace()).parse_string('   abc')
        self.assertEqual(0, leave_ws.locn_start, 'Located should not skip whitespace for a leave_whitespace expression')

    def testPop(self):
        source = 'AAA 123 456 789 234'
        patt = pp.Word(pp.alphas)('name') + pp.Word(pp.nums) * (1,)
        result = patt.parse_string(source, parse_all=True)
        tests = [(0, 'AAA', ['123', '456', '789', '234']), (None, '234', ['123', '456', '789']), ('name', 'AAA', ['123', '456', '789']), (-1, '789', ['123', '456'])]
        for test in tests:
            (idx, val, remaining) = test
            if idx is not None:
                ret = result.pop(idx)
            else:
                ret = result.pop()
            print('EXP:', val, remaining)
            print('GOT:', ret, result.as_list())
            print(ret, result.as_list())
            self.assertEqual(val, ret, f'wrong value returned, got {ret!r}, expected {val!r}')
            self.assertEqual(remaining, result.as_list(), f'list is in wrong state after pop, got {result.as_list()!r}, expected {remaining!r}')
            print()
        prevlist = result.as_list()
        ret = result.pop('name', default='noname')
        print(ret)
        print(result.as_list())
        self.assertEqual('noname', ret, f"default value not successfully returned, got {ret!r}, expected {'noname'!r}")
        self.assertEqual(prevlist, result.as_list(), f'list is in wrong state after pop, got {result.as_list()!r}, expected {remaining!r}')

    def testPopKwargsErr(self):
        """raise a TypeError in pop by adding invalid named args"""
        source = 'AAA 123 456 789 234'
        patt = pp.Word(pp.alphas)('name') + pp.Word(pp.nums) * (1,)
        result = patt.parse_string(source, parse_all=True)
        print(result.dump())
        with self.assertRaises(TypeError):
            result.pop(notDefault='foo')

    def testAddCondition(self):
        numParser = pp.Word(pp.nums)
        numParser.add_parse_action(lambda s, l, t: int(t[0]))
        numParser.add_condition(lambda s, l, t: t[0] % 2)
        numParser.add_condition(lambda s, l, t: t[0] >= 7)
        result = numParser.search_string('1 2 3 4 5 6 7 8 9 10')
        print(result.as_list())
        self.assertEqual([[7], [9]], result.as_list(), 'failed to properly process conditions')
        numParser = pp.Word(pp.nums)
        numParser.add_parse_action(lambda s, l, t: int(t[0]))
        rangeParser = numParser('from_') + pp.Suppress('-') + numParser('to')
        result = rangeParser.search_string('1-4 2-4 4-3 5 6 7 8 9 10')
        print(result.as_list())
        self.assertEqual([[1, 4], [2, 4], [4, 3]], result.as_list(), 'failed to properly process conditions')
        rangeParser.add_condition(lambda t: t.to > t.from_, message='from must be <= to', fatal=False)
        result = rangeParser.search_string('1-4 2-4 4-3 5 6 7 8 9 10')
        print(result.as_list())
        self.assertEqual([[1, 4], [2, 4]], result.as_list(), 'failed to properly process conditions')
        rangeParser = numParser('from_') + pp.Suppress('-') + numParser('to')
        rangeParser.add_condition(lambda t: t.to > t.from_, message='from must be <= to', fatal=True)
        try:
            result = rangeParser.search_string('1-4 2-4 4-3 5 6 7 8 9 10')
            self.fail('failed to interrupt parsing on fatal condition failure')
        except ParseFatalException:
            print('detected fatal condition')

    def testPatientOr(self):

        def validate(token):
            if token[0] == 'def':
                raise pp.ParseException('signalling invalid token')
            return token
        a = pp.Word('de').set_name('Word')
        b = pp.Literal('def').set_name('Literal').set_parse_action(validate)
        c = pp.Literal('d').set_name('d')
        try:
            result = (a ^ b ^ c).parse_string('def', parse_all=False)
            print(result)
            self.assertEqual(['de'], result.as_list(), f'failed to select longest match, chose {result}')
        except ParseException:
            failed = True
        else:
            failed = False
        if failed:
            self.fail('invalid logic in Or, fails on longest match with exception in parse action')
        word = pp.Word(pp.alphas).set_name('word')
        word_1 = pp.Word(pp.alphas).set_name('word_1').add_condition(lambda t: len(t[0]) == 1)
        a = word + (word_1 + word ^ word)
        b = word * 3
        c = a ^ b
        print(c)
        test_string = 'foo bar temp'
        result = c.parse_string(test_string, parse_all=True)
        print(test_string, '->', result.as_list())
        self.assertEqual(test_string.split(), result.as_list(), 'failed to match longest choice')

    def testEachWithOptionalWithResultsName(self):
        result = (pp.Optional('foo')('one') & pp.Optional('bar')('two')).parse_string('bar foo', parse_all=True)
        print(result.dump())
        self.assertEqual(sorted(['one', 'two']), sorted(result.keys()))

    def testUnicodeExpression(self):
        z = 'a' | pp.Literal('ᄑ')
        try:
            z.parse_string('b', parse_all=True)
        except ParseException as pe:
            self.assertEqual("Expected {'a' | 'ᄑ'}", pe.msg, f'Invalid error message raised, got {pe.msg!r}')

    def testSetName(self):
        a = pp.one_of('a b c')
        b = pp.one_of('d e f')
        arith_expr = pp.infix_notation(pp.Word(pp.nums), [(pp.one_of('* /').set_name('* | /'), 2, pp.OpAssoc.LEFT), (pp.one_of('+ -').set_name('+ | -'), 2, pp.OpAssoc.LEFT)])
        arith_expr2 = pp.infix_notation(pp.Word(pp.nums), [(('?', ':'), 3, pp.OpAssoc.LEFT)])
        recursive = pp.Forward()
        recursive <<= a + (b + recursive)[...]
        tests = [a, b, a | b, arith_expr, arith_expr.expr, arith_expr2, arith_expr2.expr, recursive, pp.DelimitedList(pp.Word(pp.nums).set_name('int')), pp.counted_array(pp.Word(pp.nums).set_name('int')), pp.nested_expr(), pp.make_html_tags('Z'), (pp.any_open_tag, pp.any_close_tag), pp.common_html_entity, pp.common_html_entity.set_parse_action(pp.replace_html_entity).transform_string('lsdjkf &lt;lsdjkf&gt;&amp;&apos;&quot;&xyzzy;')]
        expected = map(str.strip, '            \'a\' | \'b\' | \'c\'\n            \'d\' | \'e\' | \'f\'\n            {\'a\' | \'b\' | \'c\' | \'d\' | \'e\' | \'f\'}\n            W:(0-9)_expression\n            + | - operations\n            W:(0-9)_expression\n            ?: operations\n            Forward: {\'a\' | \'b\' | \'c\' [{\'d\' | \'e\' | \'f\' : ...}]...}\n            int [, int]...\n            (len) int...\n            nested () expression\n            (<Z>, </Z>)\n            (<any tag>, </any tag>)\n            common HTML entity\n            lsdjkf <lsdjkf>&\'"&xyzzy;'.splitlines())
        for (t, e) in zip(tests, expected):
            with self.subTest('set_name', t=t, e=e):
                tname = str(t)
                print(tname)
                self.assertEqual(e, tname, f'expression name mismatch, expected {e} got {tname}')

    def testClearParseActions(self):
        realnum = ppc.real()
        self.assertEqual(3.14159, realnum.parse_string('3.14159', parse_all=True)[0], 'failed basic real number parsing')
        realnum.set_parse_action(None)
        self.assertEqual('3.14159', realnum.parse_string('3.14159', parse_all=True)[0], 'failed clearing parse action')
        realnum.add_parse_action(lambda t: '.' in t[0])
        self.assertEqual(True, realnum.parse_string('3.14159', parse_all=True)[0], 'failed setting new parse action after clearing parse action')

    def testOneOrMoreStop(self):
        test = 'BEGIN aaa bbb ccc END'
        (BEGIN, END) = map(pp.Keyword, 'BEGIN,END'.split(','))
        body_word = pp.Word(pp.alphas).set_name('word')
        for ender in (END, 'END', pp.CaselessKeyword('END')):
            repetitions = (
                pp.OneOrMore(body_word, stop_on=ender),
                pp.ZeroOrMore(body_word, stop_on=ender),
                body_word[...:ender],
            )
            for repetition in repetitions:
                expr = BEGIN + repetition + END
                self.assertParseAndCheckList(expr, test, test.split(), f'Did not successfully stop on ending expression {ender!r}')
        number = pp.Word(pp.nums + ',.()').set_name('number with optional commas')
        parser = pp.OneOrMore(pp.Word(pp.alphanums + '-/.'), stop_on=number)('id').set_parse_action(' '.join) + number('data')
        self.assertParseAndCheckList(parser, '        XXX Y/123          1,234.567890', ['XXX Y/123', '1,234.567890'], f'Did not successfully stop on ending expression {number!r}', verbose=True)

    def testZeroOrMoreStop(self):
        test = 'BEGIN END'
        (BEGIN, END) = map(pp.Keyword, 'BEGIN,END'.split(','))
        body_word = pp.Word(pp.alphas).set_name('word')
        for ender in (END, 'END', pp.CaselessKeyword('END')):
            expr = BEGIN + pp.ZeroOrMore(body_word, stop_on=ender) + END
            self.assertParseAndCheckList(expr, test, test.split(), f'Did not successfully stop on ending expression {ender!r}')
            expr = BEGIN + body_word[...].stopOn(ender) + END
            self.assertParseAndCheckList(expr, test, test.split(), f'Did not successfully stop on ending expression {ender!r}')
            expr = BEGIN + body_word[...:ender] + END
            self.assertParseAndCheckList(expr, test, test.split(), f'Did not successfully stop on ending expression {ender!r}')
            expr = BEGIN + body_word[:ender] + END
            self.assertParseAndCheckList(expr, test, test.split(), f'Did not successfully stop on ending expression {ender!r}')

    def testNestedAsDict(self):
        equals = pp.Literal('=').suppress()
        lbracket = pp.Literal('[').suppress()
        rbracket = pp.Literal(']').suppress()
        lbrace = pp.Literal('{').suppress()
        rbrace = pp.Literal('}').suppress()
        value_dict = pp.Forward()
        value_list = pp.Forward()
        value_string = pp.Word(pp.alphanums + '@. ')
        value = value_list ^ value_dict ^ value_string
        values = pp.Group(pp.DelimitedList(value, ','))
        value_list <<= lbracket + values + rbracket
        identifier = pp.Word(pp.alphanums + '_.')
        assignment = pp.Group(identifier + equals + pp.Optional(value))
        assignments = pp.Dict(pp.DelimitedList(assignment, ';'))
        value_dict <<= lbrace + assignments + rbrace
        response = assignments
        rsp = 'username=goat; errors={username=[already taken, too short]}; empty_field='
        result_dict = response.parse_string(rsp, parse_all=True).as_dict()
        print(result_dict)
        self.assertEqual('goat', result_dict['username'], 'failed to process string in ParseResults correctly')
        self.assertEqual(['already taken', 'too short'], result_dict['errors']['username'], 'failed to process nested ParseResults correctly')

    def testTraceParseActionDecorator(self):

        @pp.trace_parse_action
        def convert_to_int(t):
            return int(t[0])

        class Z:

            def __call__(self, other):
                return other[0] * 1000
        integer = pp.Word(pp.nums).add_parse_action(convert_to_int)
        integer.add_parse_action(pp.trace_parse_action(lambda t: t[0] * 10))
        integer.add_parse_action(pp.trace_parse_action(Z()))
        integer.parse_string('132', parse_all=True)

    def testTraceParseActionDecorator_with_exception(self):

        @pp.trace_parse_action
        def convert_to_int_raising_type_error(t):
            return int(t[0]) + '.000'

        @pp.trace_parse_action
        def convert_to_int_raising_index_error(t):
            return int(t[1])

        @pp.trace_parse_action
        def convert_to_int_raising_value_error(t):
            (a, b) = t[0]
            return int(t[1])

        @pp.trace_parse_action
        def convert_to_int_raising_parse_exception(t):
            pp.Word(pp.alphas).parse_string('123')
        for (pa, expected_message) in ((convert_to_int_raising_type_error, 'TypeError:'), (convert_to_int_raising_index_error, 'IndexError:'), (convert_to_int_raising_value_error, 'ValueError:'), (convert_to_int_raising_parse_exception, 'ParseException:')):
            print(f'Using parse action {pa.__name__!r}')
            integer = pp.Word(pp.nums).set_parse_action(pa)
            stderr_capture = StringIO()
            try:
                with contextlib.redirect_stderr(stderr_capture):
                    integer.parse_string('132', parse_all=True)
            except Exception as exc:
                print(f'Exception raised: {type(exc).__name__}: {exc}')
            else:
                print('No exception raised')
            stderr_text = stderr_capture.getvalue()
            print(stderr_text)
            self.assertTrue(expected_message in stderr_text, f'Expected exception type {expected_message!r} not found in trace_parse_action output')

    def testRunTests(self):
        integer = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        intrange = integer('start') + '-' + integer('end')
        intrange.add_condition(lambda t: t.end > t.start, message='invalid range, start must be <= end', fatal=True)
        intrange.add_parse_action(lambda t: list(range(t.start, t.end + 1)))
        indices = pp.DelimitedList(intrange | integer)
        indices.add_parse_action(lambda t: sorted(set(t)))
        tests = '            # normal data\n            1-3,2-4,6,8-10,16\n\n            # lone integer\n            11'
        results = indices.run_tests(tests, print_results=False)[1]
        expectedResults = [[1, 2, 3, 4, 6, 8, 9, 10, 16], [11]]
        for (res, expected) in zip(results, expectedResults):
            print(res[1].as_list())
            print(expected)
            self.assertEqual(expected, res[1].as_list(), 'failed test: ' + str(expected))
        tests = '            # invalid range\n            1-2, 3-1, 4-6, 7, 12\n            '
        (success, _) = indices.run_tests(tests, print_results=False, failure_tests=True)
        self.assertTrue(success, 'failed to raise exception on improper range test')

    def testRunTestsPostParse(self):
        integer = ppc.integer
        fraction = integer('numerator') + '/' + integer('denominator')
        accum = []

        def eval_fraction(test, result):
            accum.append((test, result.as_list()))
            return f'eval: {result.numerator / result.denominator}'
        (success, _) = fraction.run_tests('            1/2\n            1/0\n        ', post_parse=eval_fraction)
        self.assertTrue(success, 'failed to parse fractions in RunTestsPostParse')
        expected_accum = [('1/2', [1, '/', 2]), ('1/0', [1, '/', 0])]
        self.assertEqual(expected_accum, accum, 'failed to call post_parse method during run_tests')

    def testConvertToDateErr(self):
        """raise a ParseException in convert_to_date with incompatible date str"""
        expr = pp.Word(pp.alphanums + '-')
        expr.add_parse_action(ppc.convert_to_date())
        with self.assertRaisesParseException():
            expr.parse_string('1997-07-error', parse_all=True)

    def testConvertToDatetimeErr(self):
        """raise a ParseException in convert_to_datetime with incompatible datetime str"""
        expr = pp.Word(pp.alphanums + '-')
        expr.add_parse_action(ppc.convert_to_datetime())
        with self.assertRaisesParseException():
            expr.parse_string('1997-07-error', parse_all=True)

    def testCommonExpressions(self):
        import ast
        with self.subTest('MAC address success run_tests'):
            (success, _) = ppc.mac_address.run_tests('\n                AA:BB:CC:DD:EE:FF\n                AA.BB.CC.DD.EE.FF\n                AA-BB-CC-DD-EE-FF\n                ')
            self.assertTrue(success, 'error in parsing valid MAC address')
        with self.subTest('MAC address expected failure run_tests'):
            (success, _) = ppc.mac_address.run_tests('\n                # mixed delimiters\n                AA.BB:CC:DD:EE:FF\n                ', failure_tests=True)
            self.assertTrue(success, 'error in detecting invalid mac address')
        with self.subTest('IPv4 address success run_tests'):
            (success, _) = ppc.ipv4_address.run_tests('\n                0.0.0.0\n                1.1.1.1\n                127.0.0.1\n                1.10.100.199\n                255.255.255.255\n                ')
            self.assertTrue(success, 'error in parsing valid IPv4 address')
        with self.subTest('IPv4 address expected failure run_tests'):
            (success, _) = ppc.ipv4_address.run_tests('\n                # out of range value\n                256.255.255.255\n                ', failure_tests=True)
            self.assertTrue(success, 'error in detecting invalid IPv4 address')
        with self.subTest('IPv6 address success run_tests'):
            (success, _) = ppc.ipv6_address.run_tests('\n                2001:0db8:85a3:0000:0000:8a2e:0370:7334\n                2134::1234:4567:2468:1236:2444:2106\n                0:0:0:0:0:0:A00:1\n                1080::8:800:200C:417A\n                ::A00:1\n    \n                # loopback address\n                ::1\n    \n                # the null address\n                ::\n    \n                # ipv4 compatibility form\n                ::ffff:192.168.0.1\n                ')
            self.assertTrue(success, 'error in parsing valid IPv6 address')
        with self.subTest('IPv6 address expected failure run_tests'):
            (success, _) = ppc.ipv6_address.run_tests("\n                # too few values\n                1080:0:0:0:8:800:200C\n    \n                # too many ::'s, only 1 allowed\n                2134::1234:4567::2444:2106\n                ", failure_tests=True)
            self.assertTrue(success, 'error in detecting invalid IPv6 address')
        with self.subTest('ppc.number success run_tests'):
            (success, _) = ppc.number.run_tests('\n                100\n                -100\n                +100\n                3.14159\n                6.02e23\n                1e-12\n                ')
            self.assertTrue(success, 'error in parsing valid numerics')
        with self.subTest('ppc.sci_real success run_tests'):
            (success, _) = ppc.sci_real.run_tests('\n                1e12\n                -1e12\n                3.14159\n                6.02e23\n                ')
            self.assertTrue(success, 'error in parsing valid scientific notation reals')
        with self.subTest('ppc.fnumber success run_tests'):
            (success, _) = ppc.fnumber.run_tests('\n                100\n                -100\n                +100\n                3.14159\n                6.02e23\n                1e-12\n                ')
            self.assertTrue(success, 'error in parsing valid numerics')
        with self.subTest('ppc.ieee_float success run_tests'):
            (success, _) = ppc.ieee_float.run_tests('\n                100\n                3.14159\n                6.02e23\n                1E-12\n                0\n                -0\n                NaN\n                -nan\n                inf\n                -Infinity\n                ')
            self.assertTrue(success, 'error in parsing valid floating-point literals')
        with self.subTest('ppc.iso8601_date success run_tests'):
            (success, results) = ppc.iso8601_date.run_tests('\n                1997\n                1997-07\n                1997-07-16\n                ')
            self.assertTrue(success, 'error in parsing valid iso8601_date')
            expected = [('1997', None, None), ('1997', '07', None), ('1997', '07', '16')]
            for (r, exp) in zip(results, expected):
                self.assertEqual(exp, (r[1].year, r[1].month, r[1].day), 'failed to parse date into fields')
        with self.subTest('ppc.iso8601_date conversion success run_tests'):
            (success, results) = ppc.iso8601_date().add_parse_action(ppc.convert_to_date()).run_tests('\n                1997-07-16\n                ')
            self.assertTrue(success, 'error in parsing valid iso8601_date with parse action')
            self.assertEqual(datetime.date(1997, 7, 16), results[0][1][0], 'error in parsing valid iso8601_date with parse action - incorrect value')
        with self.subTest('ppc.iso8601_datetime success run_tests'):
            (success, results) = ppc.iso8601_datetime.run_tests('\n                1997-07-16T19:20+01:00\n                1997-07-16T19:20:30+01:00\n                1997-07-16T19:20:30.45Z\n                1997-07-16 19:20:30.45\n                ')
            self.assertTrue(success, 'error in parsing valid iso8601_datetime')
        with self.subTest('ppc.iso8601_datetime conversion success run_tests'):
            (success, results) = ppc.iso8601_datetime().add_parse_action(ppc.convert_to_datetime()).run_tests('\n                1997-07-16T19:20:30.45\n                ')
            self.assertTrue(success, 'error in parsing valid iso8601_datetime')
            self.assertEqual(datetime.datetime(1997, 7, 16, 19, 20, 30, 450000), results[0][1][0], 'error in parsing valid iso8601_datetime - incorrect value')
        with self.subTest('ppc.as_datetime fractional seconds run_tests'):
            (success, results) = ppc.iso8601_datetime().add_parse_action(ppc.as_datetime).run_tests('\n                1997-07-16T19:20:30.45\n                ')
            self.assertTrue(success, 'error in parsing valid iso8601_datetime')
            self.assertEqual(datetime.datetime(1997, 7, 16, 19, 20, 30, 450000), results[0][1][0], 'error in as_datetime fractional seconds - incorrect microseconds')
        with self.subTest('ppc.uuid success run_tests'):
            (success, _) = ppc.uuid.run_tests('\n                123e4567-e89b-12d3-a456-426655440000\n                ')
            self.assertTrue(success, 'failed to parse valid uuid')
        with self.subTest('ppc.fraction success run_tests'):
            (success, _) = ppc.fraction.run_tests('\n                1/2\n                -15/16\n                -3/-4\n                ')
            self.assertTrue(success, 'failed to parse valid fraction')
        with self.subTest('ppc.mixed_integer success run_tests'):
            (success, _) = ppc.mixed_integer.run_tests('\n                1/2\n                -15/16\n                -3/-4\n                1 1/2\n                2 -15/16\n                0 -3/-4\n                12\n                ')
            self.assertTrue(success, 'failed to parse valid mixed integer')
        with self.subTest('ppc.number success run_tests'):
            (success, results) = ppc.number.run_tests('\n                100\n                -3\n                1.732\n                -3.14159\n                6.02e23')
            self.assertTrue(success, 'failed to parse numerics')
            for (test, result) in results:
                expected = ast.literal_eval(test)
                self.assertEqual(expected, result[0], f'numeric parse failed (wrong value) ({result[0]} should be {expected})')
                self.assertEqual(type(expected), type(result[0]), f'numeric parse failed (wrong type) ({type(result[0])} should be {type(expected)})')

    def testDateTimeValidation(self):
        if sys.version_info[:2] < (3, 10):
            return
        ppc = pp.pyparsing_common
        date_expr = ppc.iso8601_date_validated
        datetime_expr = ppc.iso8601_datetime_validated
        valid_dates = ['2023-01-01', '2024-02-29', '2000-02-29', '1900-01-01', '9999-12-31', '2023-12', '2023']
        for d in valid_dates:
            with self.subTest(date=d):
                date_expr.parse_string(d, parse_all=True)
        invalid_dates = ['2023-02-29', '2023-04-31', '2023-13-01', '2023-00-01', '2023-01-32', '2023-01-00', '1900-02-29']
        for d in invalid_dates:
            with self.subTest(date=d):
                with self.assertRaises(pp.ParseException):
                    date_expr.parse_string(d, parse_all=True)
        valid_datetimes = ['2023-01-01T12:00:00', '2023-01-01 12:00:00', '2023-01-01T12:00:00Z', '2023-01-01T12:00:00+05:00', '2023-01-01T12:00:00-05:00', '2023-01-01T12:00:00.123', '2023-01-01T12:00:00.123Z', '2024-02-29T23:59:59']
        for dt in valid_datetimes:
            with self.subTest(datetime=dt):
                datetime_expr.parse_string(dt, parse_all=True)
        invalid_datetimes = ['2023-02-29T12:00:00', '2023-01-01T24:00:00', '2023-01-01T12:60:00', '2023-01-01T12:00:60']
        for dt in invalid_datetimes:
            with self.subTest(datetime=dt):
                with self.assertRaises(pp.ParseException):
                    datetime_expr.parse_string(dt, parse_all=True)

    def testCommonUrl(self):
        url_good_tests = '            http://foo.com/blah_blah\n            http://foo.com/blah_blah/\n            http://foo.com/blah_blah_(wikipedia)\n            http://foo.com/blah_blah_(wikipedia)_(again)\n            http://www.example.com/wpstyle/?p=364\n            https://www.example.com/foo/?bar=baz&inga=42&quux\n            http://✪df.ws/123\n            http://userid:password@example.com:8080\n            http://userid:password@example.com:8080/\n            http://userid@example.com\n            http://userid@example.com/\n            http://userid@example.com:8080\n            http://userid@example.com:8080/\n            http://userid:password@example.com\n            http://userid:password@example.com/\n            http://142.42.1.1/\n            http://142.42.1.1:8080/\n            http://➡.ws/䨹\n            http://⌘.ws\n            http://⌘.ws/\n            http://foo.com/blah_(wikipedia)#cite-1\n            http://foo.com/blah_(wikipedia)_blah#cite-1\n            http://foo.com/unicode_(✪)_in_parens\n            http://foo.com/(something)?after=parens\n            http://☺.damowmow.com/\n            http://code.google.com/events/#&product=browser\n            http://j.mp\n            ftp://foo.bar/baz\n            http://foo.bar/?q=Test%20URL-encoded%20stuff\n            http://مثال.إختبار\n            '
        (success, report) = ppc.url.run_tests(url_good_tests)
        self.assertTrue(success)
        url_bad_tests = '            http://\n            http://.\n            http://..\n            http://../\n            http://?\n            http://??\n            http://??/\n            http://#\n            http://##\n            http://##/\n            # skip: http://foo.bar?q=Spaces should be encoded\n            //\n            //a\n            ///a\n            ///\n            http:///a\n            foo.com\n            rdar://1234\n            h://test\n            http:// shouldfail.com\n\n            :// should fail\n            http://foo.bar/foo(bar)baz quux\n            ftps://foo.bar/\n            http://-error-.invalid/\n            # skip: http://a.b--c.de/\n            http://-a.b.co\n            http://a.b-.co\n            http://0.0.0.0\n            http://10.1.1.0\n            http://10.1.1.255\n            http://224.1.1.1\n            http://1.1.1.1.1\n            http://123.123.123\n            http://3628126748\n            http://.www.foo.bar/\n            # skip: http://www.foo.bar./\n            http://.www.foo.bar./\n            http://10.1.1.1\n            '
        (success, report) = ppc.url.run_tests(url_bad_tests, failure_tests=True)
        self.assertTrue(success)

    def testCommonUrlParts(self):
        from urllib.parse import urlparse
        sample_url = 'https://bob:secret@www.example.com:8080/path/to/resource?filter=int#book-mark'
        parts = urlparse(sample_url)
        expected = {'scheme': parts.scheme, 'auth': f'{parts.username}:{parts.password}', 'host': parts.hostname, 'port': str(parts.port), 'path': parts.path, 'query': parts.query, 'fragment': parts.fragment, 'url': sample_url}
        self.assertParseAndCheckDict(ppc.url, sample_url, expected, verbose=True)

    def testCommonUrlExprs(self):

        def extract_parts(s, split=' '):
            return [[_.strip(split)] for _ in s.strip(split).split(split)]
        test_string = 'http://example.com https://blah.org '
        self.assertParseAndCheckList(pp.Group(ppc.url)[...], test_string, extract_parts(test_string))
        test_string = test_string.replace(' ', ' , ')
        self.assertParseAndCheckList(pp.DelimitedList(pp.Group(ppc.url), allow_trailing_delim=True), test_string, extract_parts(test_string, ' , '))

    def testNumericExpressions(self):
        real = ppc.real().set_parse_action(None)
        sci_real = ppc.sci_real().set_parse_action(None)
        signed_integer = ppc.signed_integer().set_parse_action(None)
        from itertools import product

        def make_tests():
            leading_sign = ['+', '-', '']
            leading_digit = ['0', '']
            dot = ['.', '']
            decimal_digit = ['1', '']
            e = ['e', 'E', '']
            e_sign = ['+', '-', '']
            e_int = ['22', '']
            stray = ['9', '.', '']
            seen = set()
            seen.add('')
            for parts in product(leading_sign, stray, leading_digit, dot, decimal_digit, stray, e, e_sign, e_int, stray):
                parts_str = ''.join(parts).strip()
                if parts_str in seen:
                    continue
                seen.add(parts_str)
                yield parts_str
            print(len(seen) - 1, 'tests produced')
        valid_ints = set()
        valid_reals = set()
        valid_sci_reals = set()
        invalid_ints = set()
        invalid_reals = set()
        invalid_sci_reals = set()
        for test_str in make_tests():
            if '.' in test_str or 'e' in test_str.lower():
                try:
                    float(test_str)
                except ValueError:
                    invalid_sci_reals.add(test_str)
                    if 'e' not in test_str.lower():
                        invalid_reals.add(test_str)
                else:
                    valid_sci_reals.add(test_str)
                    if 'e' not in test_str.lower():
                        valid_reals.add(test_str)
            try:
                int(test_str)
            except ValueError:
                invalid_ints.add(test_str)
            else:
                valid_ints.add(test_str)
        all_pass = True
        suppress_results = {'print_results': False}
        for (expr, tests, is_fail, fn) in zip([real, sci_real, signed_integer] * 2, [valid_reals, valid_sci_reals, valid_ints, invalid_reals, invalid_sci_reals, invalid_ints], [False, False, False, True, True, True], [float, float, int] * 2):
            success = True
            for t in tests:
                if expr.matches(t, parse_all=True):
                    if is_fail:
                        print(t, 'should fail but did not')
                        success = False
                elif not is_fail:
                    print(t, 'should not fail but did')
                    success = False
            print(expr, ('FAIL', 'PASS')[success], f"{('in' if is_fail else '')}valid tests ({len(tests)})")
            all_pass = all_pass and success
        self.assertTrue(all_pass, 'failed one or more numeric tests')

    def testTokenMap(self):
        parser = pp.OneOrMore(pp.Word(pp.hexnums)).set_parse_action(pp.token_map(int, 16))
        (success, report) = parser.run_tests('\n            00 11 22 aa FF 0a 0d 1a\n            ')
        self.assertRunTestResults((success, report), [([0, 17, 34, 170, 255, 10, 13, 26], 'token_map parse action failed')], msg='failed to parse hex integers')

    def testParseFile(self):
        s = '\n        123 456 789\n        '
        from pathlib import Path
        integer = ppc.integer
        test_parser = integer[1, ...]
        input_file_as_stringio = StringIO(s)
        input_file_as_path = Path(__file__).with_name('parsefiletest_input_file.txt')
        input_file_as_str = str(input_file_as_path)
        expected_list = [int(i) for i in s.split()]
        for input_file in (input_file_as_stringio, input_file_as_str, input_file_as_path):
            with self.subTest(input_file=input_file):
                print(f'parse_file() called with {type(input_file).__name__}')
                results = test_parser.parse_file(input_file)
                print(results)
                self.assertEqual(expected_list, results.as_list())

    def testHTMLStripper(self):
        sample = '\n        <html>\n        Here is some sample <i>HTML</i> text.\n        </html>\n        '
        read_everything = pp.original_text_for(pp.OneOrMore(pp.Word(pp.printables)))
        read_everything.add_parse_action(ppc.strip_html_tags)
        result = read_everything.parse_string(sample, parse_all=True)
        self.assertEqual('Here is some sample HTML text.', result[0].strip())

    def testExprSplitter(self):
        expr = pp.Literal(';') + pp.Empty()
        expr.ignore(pp.quoted_string)
        expr.ignore(pp.python_style_comment)
        sample = '\n        def main():\n            this_semi_does_nothing();\n            neither_does_this_but_there_are_spaces_afterward();\n            a = "a;b"; return a # this is a comment; it has a semicolon!\n\n        def b():\n            if False:\n                z=1000;b("; in quotes");  c=200;return z\n            return \';\'\n\n        class Foo(object):\n            def bar(self):\n                \'\'\'a docstring; with a semicolon\'\'\'\n                a = 10; b = 11; c = 12\n\n                # this comment; has several; semicolons\n                if self.spam:\n                    x = 12; return x # so; does; this; one\n                    x = 15;;; y += x; return y\n\n            def baz(self):\n                return self.bar\n        '
        expected = [['            this_semi_does_nothing()', ''], ['            neither_does_this_but_there_are_spaces_afterward()', ''], ['            a = "a;b"', 'return a # this is a comment; it has a semicolon!'], ['                z=1000', 'b("; in quotes")', 'c=200', 'return z'], ["            return ';'"], ["                '''a docstring; with a semicolon'''"], ['                a = 10', 'b = 11', 'c = 12'], ['                # this comment; has several; semicolons'], ['                    x = 12', 'return x # so; does; this; one'], ['                    x = 15', '', '', 'y += x', 'return y']]
        exp_iter = iter(expected)
        for line in filter(lambda ll: ';' in ll, sample.splitlines()):
            print(str(list(expr.split(line))) + ',')
            self.assertEqual(next(exp_iter), list(expr.split(line)), 'invalid split on expression')
        print()
        expected = [['            this_semi_does_nothing()', ';', ''], ['            neither_does_this_but_there_are_spaces_afterward()', ';', ''], ['            a = "a;b"', ';', 'return a # this is a comment; it has a semicolon!'], ['                z=1000', ';', 'b("; in quotes")', ';', 'c=200', ';', 'return z'], ["            return ';'"], ["                '''a docstring; with a semicolon'''"], ['                a = 10', ';', 'b = 11', ';', 'c = 12'], ['                # this comment; has several; semicolons'], ['                    x = 12', ';', 'return x # so; does; this; one'], ['                    x = 15', ';', '', ';', '', ';', 'y += x', ';', 'return y']]
        exp_iter = iter(expected)
        for line in filter(lambda ll: ';' in ll, sample.splitlines()):
            print(str(list(expr.split(line, include_separators=True))) + ',')
            self.assertEqual(next(exp_iter), list(expr.split(line, include_separators=True)), 'invalid split on expression')
        print()
        expected = [['            this_semi_does_nothing()', ''], ['            neither_does_this_but_there_are_spaces_afterward()', ''], ['            a = "a;b"', 'return a # this is a comment; it has a semicolon!'], ['                z=1000', 'b("; in quotes");  c=200;return z'], ['                a = 10', 'b = 11; c = 12'], ['                    x = 12', 'return x # so; does; this; one'], ['                    x = 15', ';; y += x; return y']]
        exp_iter = iter(expected)
        for line in sample.splitlines():
            pieces = list(expr.split(line, maxsplit=1))
            print(str(pieces) + ',')
            if len(pieces) == 2:
                exp = next(exp_iter)
                self.assertEqual(exp, pieces, 'invalid split on expression with maxSplits=1')
            elif len(pieces) == 1:
                self.assertEqual(0, len(expr.search_string(line)), 'invalid split with maxSplits=1 when expr not present')
            else:
                print('\n>>> ' + line)
                self.fail('invalid split on expression with maxSplits=1, corner case')

    def testParseFatalException(self):
        with self.assertRaisesParseException(exc_type=ParseFatalException, msg='failed to raise ErrorStop exception'):
            expr = 'ZZZ' - pp.Word(pp.nums)
            expr.parse_string('ZZZ bad', parse_all=True)

    def testParseFatalException2(self):

        def raise_exception(tokens):
            raise pp.ParseSyntaxException('should raise here')
        test = pp.MatchFirst((pp.pyparsing_common.integer + pp.pyparsing_common.identifier).set_parse_action(raise_exception) | pp.pyparsing_common.number)
        with self.assertRaisesParseException(pp.ParseFatalException):
            test.parse_string('1s', parse_all=True)

    def testParseFatalException3(self):
        test = pp.MatchFirst(pp.pyparsing_common.integer - pp.pyparsing_common.identifier | pp.pyparsing_common.integer)
        with self.assertRaisesParseException(pp.ParseFatalException):
            test.parse_string('1', parse_all=True)

    def testInlineLiteralsUsing(self):
        wd = pp.Word(pp.alphas)
        pp.ParserElement.inline_literals_using(pp.Suppress)
        result = (wd + ',' + wd + pp.one_of('! . ?')).parse_string('Hello, World!', parse_all=True)
        self.assertEqual(3, len(result), 'inline_literals_using(Suppress) failed!')
        pp.ParserElement.inline_literals_using(pp.Literal)
        result = (wd + ',' + wd + pp.one_of('! . ?')).parse_string('Hello, World!', parse_all=True)
        self.assertEqual(4, len(result), 'inline_literals_using(Literal) failed!')
        pp.ParserElement.inline_literals_using(pp.CaselessKeyword)
        self.assertParseAndCheckList('SELECT' + wd + 'FROM' + wd, 'select color from colors', expected_list=['SELECT', 'color', 'FROM', 'colors'], msg='inline_literals_using(CaselessKeyword) failed!', verbose=True)
        pp.ParserElement.inline_literals_using(pp.CaselessLiteral)
        self.assertParseAndCheckList('SELECT' + wd + 'FROM' + wd, 'select color from colors', expected_list=['SELECT', 'color', 'FROM', 'colors'], msg='inline_literals_using(CaselessLiteral) failed!', verbose=True)
        integer = pp.Word(pp.nums)
        pp.ParserElement.inline_literals_using(pp.Literal)
        date_str = integer('year') + '/' + integer('month') + '/' + integer('day')
        self.assertParseAndCheckList(date_str, '1999/12/31', expected_list=['1999', '/', '12', '/', '31'], msg='inline_literals_using(example 1) failed!', verbose=True)
        pp.ParserElement.inline_literals_using(pp.Suppress)
        date_str = integer('year') + '/' + integer('month') + '/' + integer('day')
        self.assertParseAndCheckList(date_str, '1999/12/31', expected_list=['1999', '12', '31'], msg='inline_literals_using(example 2) failed!', verbose=True)

    def testCloseMatch(self):
        searchseq = pp.CloseMatch('ATCATCGAATGGA', 2)
        (_, results) = searchseq.run_tests('\n            ATCATCGAATGGA\n            XTCATCGAATGGX\n            ATCATCGAAXGGA\n            ATCAXXGAATGGA\n            ATCAXXGAATGXA\n            ATCAXXGAATGG\n            ')
        expected = ([], [0, 12], [9], [4, 5], None, None)
        for (r, exp) in zip(results, expected):
            if exp is not None:
                self.assertEqual(exp, r[1].mismatches, f'fail CloseMatch for {r[0]!r}')
            print(r[0], f'exc: {r[1]}' if exp is None and isinstance(r[1], Exception) else ('no match', 'match')[r[1].mismatches == exp])

    def testCloseMatchCaseless(self):
        searchseq = pp.CloseMatch('ATCATCGAATGGA', 2, caseless=True)
        (_, results) = searchseq.run_tests('\n            atcatcgaatgga\n            xtcatcgaatggx\n            atcatcgaaxgga\n            atcaxxgaatgga\n            atcaxxgaatgxa\n            atcaxxgaatgg\n            ')
        expected = ([], [0, 12], [9], [4, 5], None, None)
        for (r, exp) in zip(results, expected):
            if exp is not None:
                self.assertEqual(exp, r[1].mismatches, f'fail CaselessCloseMatch for {r[0]!r}')
            print(r[0], f'exc: {r[1]}' if exp is None and isinstance(r[1], Exception) else ('no match', 'match')[r[1].mismatches == exp])

    def testDefaultKeywordChars(self):
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            pp.Keyword('start').parse_string('start1000', parse_all=True)
        try:
            pp.Keyword('start', ident_chars=pp.alphas).parse_string('start1000', parse_all=False)
        except pp.ParseException:
            self.fail('failed to match keyword using updated keyword chars')
        with ppt.reset_pyparsing_context():
            pp.Keyword.set_default_keyword_chars(pp.alphas)
            try:
                pp.Keyword('start').parse_string('start1000', parse_all=False)
            except pp.ParseException:
                self.fail('failed to match keyword using updated keyword chars')
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            pp.CaselessKeyword('START').parse_string('start1000', parse_all=False)
        try:
            pp.CaselessKeyword('START', ident_chars=pp.alphas).parse_string('start1000', parse_all=False)
        except pp.ParseException:
            self.fail('failed to match keyword using updated keyword chars')
        with ppt.reset_pyparsing_context():
            pp.Keyword.set_default_keyword_chars(pp.alphas)
            try:
                pp.CaselessKeyword('START').parse_string('start1000', parse_all=False)
            except pp.ParseException:
                self.assertTrue(False, 'failed to match keyword using updated keyword chars')

    def testKeywordCopyIdentChars(self):
        a_keyword = pp.Keyword('start', ident_chars='_')
        b_keyword = a_keyword.copy()
        self.assertEqual(a_keyword.ident_chars, b_keyword.ident_chars)

    def testWordCopyWhenWordCharsIncludeSpace(self):
        word_with_space = pp.Word(pp.alphas + ' ')
        word_with_space.parse_string('ABC')
        word_with_space.copy().parse_string('ABC')

    def testWordCopyWhenWordCharsIncludeSpace2(self):
        element = pp.QuotedString('"') | pp.Combine(pp.Word(' abcdefghijklmnopqrstuvwxyz'))
        element.parse_string('abc')
        element_list = pp.DelimitedList(element)
        element_list.parse_string('abc')

    def testWordCopyWhenWordCharsIncludeSpace3(self):
        word_with_space = pp.Word(pp.alphas + ' ')
        word_with_space.parse_string('ABC')
        word_with_space('trouble').parse_string('ABC')

    def testLiteralVsKeyword(self):
        integer = ppc.integer
        literal_expr = integer + pp.Literal('start') + integer
        keyword_expr = integer + pp.Keyword('start') + integer
        caseless_keyword_expr = integer + pp.CaselessKeyword('START') + integer
        word_keyword_expr = integer + pp.Word(pp.alphas, as_keyword=True).set_name('word') + integer
        print()
        test_string = '1 start 2'
        print(test_string)
        print(literal_expr, literal_expr.parse_string(test_string, parse_all=True))
        print(keyword_expr, keyword_expr.parse_string(test_string, parse_all=True))
        print(caseless_keyword_expr, caseless_keyword_expr.parse_string(test_string, parse_all=True))
        print(word_keyword_expr, word_keyword_expr.parse_string(test_string, parse_all=True))
        print()
        test_string = '3 start4'
        print(test_string)
        print(literal_expr, literal_expr.parse_string(test_string, parse_all=True))
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            print(keyword_expr.parse_string(test_string, parse_all=True))
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            print(caseless_keyword_expr.parse_string(test_string, parse_all=True))
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            print(word_keyword_expr.parse_string(test_string, parse_all=True))
        print()
        test_string = '5start 6'
        print(test_string)
        print(literal_expr.parse_string(test_string, parse_all=True))
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            print(keyword_expr.parse_string(test_string, parse_all=True))
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            print(caseless_keyword_expr.parse_string(test_string, parse_all=True))
        with self.assertRaisesParseException(msg='failed to fail matching keyword using updated keyword chars'):
            print(word_keyword_expr.parse_string(test_string, parse_all=True))

    def testCol(self):
        test = '*\n* \n*   ALF\n*\n'
        initials = [c for (i, c) in enumerate(test) if pp.col(i, test) == 1]
        print(initials)
        self.assertTrue(len(initials) == 4 and all((c == '*' for c in initials)), 'fail col test')

    def testLiteralException(self):
        for cls in (pp.Literal, pp.CaselessLiteral, pp.Keyword, pp.CaselessKeyword, pp.Word, pp.Regex):
            expr = cls('xyz')
            try:
                expr.parse_string(' ', parse_all=True)
            except Exception as e:
                print(cls.__name__, str(e))
                self.assertTrue(isinstance(e, pp.ParseBaseException), f'class {cls.__name__} raised wrong exception type {type(e).__name__}')

    def testParseActionIndexErrorException(self):
        """
        Tests raising an IndexError in a parse action
        """
        import traceback
        number = pp.Word(pp.nums)

        def number_action():
            raise IndexError
        number.add_parse_action(number_action)
        symbol = pp.Word('abcd', max=1)
        expr = pp.Group(number) ^ symbol
        try:
            expr.parse_string('1 + 2', parse_all=True)
        except IndexError as ie:
            pass
        except Exception as e:
            traceback.print_exc()
            self.fail(f'Expected IndexError not raised, raised {type(e).__name__}: {e}')
        else:
            self.fail('Expected IndexError not raised')

    def testParseActionNesting(self):
        vals = pp.OneOrMore(ppc.integer)('int_values')

        def add_total(tokens):
            tokens['total'] = sum(tokens)
            return tokens
        vals.add_parse_action(add_total)
        results = vals.parse_string('244 23 13 2343', parse_all=True)
        print(results.dump())
        self.assertParseResultsEquals(results, expected_dict={'int_values': [244, 23, 13, 2343], 'total': 2623}, msg='noop parse action changed ParseResults structure')
        name = pp.Word(pp.alphas)('name')
        score = pp.Word(pp.nums + '.')('score')
        nameScore = pp.Group(name + score)
        line1 = nameScore('Rider')
        result1 = line1.parse_string('Mauney 46.5', parse_all=True)
        print('### before parse action is added ###')
        print('result1.dump():\n' + result1.dump() + '\n')
        before_pa_dict = result1.as_dict()
        line1.set_parse_action(lambda t: t)
        result1 = line1.parse_string('Mauney 46.5', parse_all=True)
        after_pa_dict = result1.as_dict()
        print('### after parse action was added ###')
        print('result1.dump():\n' + result1.dump() + '\n')
        self.assertEqual(before_pa_dict, after_pa_dict, 'noop parse action changed ParseResults structure')

    def testParseActionWithDelimitedList(self):

        class AnnotatedToken:

            def __init__(self, kind, elements):
                self.kind = kind
                self.elements = elements

            def __str__(self):
                return f'AnnotatedToken({self.kind!r}, {self.elements!r})'

            def __eq__(self, other):
                return type(self) == type(other) and self.kind == other.kind and (self.elements == other.elements)
            __repr__ = __str__

        def annotate(name):

            def _(t):
                return AnnotatedToken(name, t.as_list())
            return _
        identifier = pp.Word(pp.srange('[a-z0-9]'))
        numeral = pp.Word(pp.nums)
        named_number_value = pp.Suppress('(') + numeral + pp.Suppress(')')
        named_number = identifier + named_number_value
        named_number_list = pp.Suppress('{') + pp.Group(pp.Optional(pp.DelimitedList(named_number))) + pp.Suppress('}')
        named_number_value.set_parse_action(annotate('val'))
        test_string = '{ x1(1), x2(2) }'
        expected = [['x1', AnnotatedToken('val', ['1']), 'x2', AnnotatedToken('val', ['2'])]]
        self.assertParseAndCheckList(named_number_list, test_string, expected)

    def testParseActionRunsInNotAny(self):
        data = ' [gog1] [G1] [gog2] [gog3] [gog4] [G2] [gog5] [G3] [gog6] '
        poi_type = pp.Word(pp.alphas).set_results_name('type')
        poi = pp.Suppress('[') + poi_type + pp.Char(pp.nums) + pp.Suppress(']')

        def cnd_is_type(val):
            return lambda toks: toks.type == val
        poi_gog = poi('gog').add_condition(cnd_is_type('gog'))
        poi_g = poi('g').add_condition(cnd_is_type('G'))
        pattern = poi_gog + ~poi_g
        matches = pattern.search_string(data).as_list()
        self.assertEqual([['gog', '2'], ['gog', '3'], ['gog', '6']], matches, 'failed testing parse actions being run inside a NotAny')

    def testParseResultsNameBelowUngroupedName(self):
        rule_num = pp.Regex('[0-9]+')('LIT_NUM*')
        list_num = pp.Group(pp.Literal('[')('START_LIST') + pp.DelimitedList(rule_num)('LIST_VALUES') + pp.Literal(']')('END_LIST'))('LIST')
        test_string = '[ 1,2,3,4,5,6 ]'
        (success, _) = list_num.run_tests(test_string)
        self.assertTrue(success)
        U = list_num.parse_string(test_string, parse_all=True)
        self.assertTrue('LIT_NUM' not in U.LIST.LIST_VALUES, 'results name retained as sub in ungrouped named result')

    def testParseResultsNamesInGroupWithDict(self):
        key = ppc.identifier()
        value = ppc.integer()
        lat = ppc.real()
        long = ppc.real()
        EQ = pp.Suppress('=')
        data = lat('lat') + long('long') + pp.Dict(pp.OneOrMore(pp.Group(key + EQ + value)))
        site = pp.QuotedString('"')('name') + pp.Group(data)('data')
        test_string = '"Golden Gate Bridge" 37.819722 -122.478611 height=746 span=4200'
        (success, _) = site.run_tests(test_string)
        self.assertTrue(success)
        (a, aEnd) = pp.make_html_tags('a')
        attrs = a.parse_string("<a href='blah'>", parse_all=True)
        print(attrs.dump())
        self.assertParseResultsEquals(attrs, expected_dict={'startA': {'href': 'blah', 'tag': 'a', 'empty': False}, 'href': 'blah', 'tag': 'a', 'empty': False})

    def testMakeXMLTags(self):
        """test helper function make_xml_tags in simple use case"""
        (body, bodyEnd) = pp.make_xml_tags('body')
        tst = '<body>Hello</body>'
        expr = body + pp.Word(pp.alphas)('contents') + bodyEnd
        result = expr.parse_string(tst, parse_all=True)
        print(result.dump())
        self.assertParseResultsEquals(result, ['body', False, 'Hello', '</body>'], msg='issue using make_xml_tags')

    def testFollowedBy(self):
        expr = pp.Word(pp.alphas)('item') + pp.FollowedBy(ppc.integer('qty'))
        result = expr.parse_string('balloon 99', parse_all=False)
        print(result.dump())
        self.assertTrue('qty' in result, 'failed to capture results name in FollowedBy')
        self.assertEqual({'item': 'balloon', 'qty': 99}, result.as_dict(), 'invalid results name structure from FollowedBy')

    def testUnicodeTests(self):
        import unicodedata
        ppu = pp.pyparsing_unicode
        unicode_version = unicodedata.unidata_version
        print(f'Unicode version {unicode_version}')
        for (unicode_property, expected_length) in [('alphas', 48965), ('alphanums', 49430), ('identchars', 49013), ('identbodychars', 50729), ('printables', 65484)]:
            charset = getattr(ppu.BMP, unicode_property)
            charset_len = len(charset)
            if unicode_version == '14.0.0':
                with self.subTest(unicode_property=unicode_property, msg='verify len'):
                    print(f'ppu.BMP.{unicode_property:14}: {charset_len:6d}')
                    self.assertEqual(charset_len, expected_length, f'incorrect number of ppu.BMP.{unicode_property}, found {charset_len} expected {expected_length}')
            with self.subTest(unicode_property=unicode_property, msg='verify unique'):
                char_counts = collections.Counter(charset)
                self.assertTrue(all((count == 1 for count in char_counts.values())), f'duplicate items found in ppu.BMP.{unicode_property}: {[(ord(c), c) for (c, count) in char_counts.items() if count > 1]}')
        kanji_printables = ppu.Japanese.Kanji.printables
        katakana_printables = ppu.Japanese.Katakana.printables
        hiragana_printables = ppu.Japanese.Hiragana.printables
        japanese_printables = ppu.Japanese.printables
        with self.subTest(msg='verify constructing ranges by merging types'):
            self.assertEqual(set(kanji_printables + katakana_printables + hiragana_printables), set(japanese_printables), 'failed to construct ranges by merging Japanese types')
        cjk_printables = ppu.CJK.printables
        chinese_printables = ppu.Chinese.printables
        korean_printables = ppu.Korean.printables
        with self.subTest(msg='verify merging ranges by using multiple inheritance generates unique list of characters'):
            char_counts = collections.Counter(cjk_printables)
            self.assertTrue(all((count == 1 for count in char_counts.values())), f'duplicate items found in ppu.CJK.printables: {[(ord(c), c) for (c, count) in char_counts.items() if count > 1]}')
        with self.subTest(msg='verify merging ranges by using multiple inheritance generates sorted list of characters'):
            self.assertEqual(list(cjk_printables), sorted(cjk_printables), 'CJK printables are not sorted')
        with self.subTest(msg='verify summing chars is equivalent to merging ranges by using multiple inheritance (CJK)'):
            print(len(set(chinese_printables + korean_printables + japanese_printables)), len(cjk_printables))
            self.assertEqual(set(chinese_printables + korean_printables + japanese_printables), set(cjk_printables), 'failed to construct ranges by merging Chinese, Japanese and Korean')

    def testUnicodeTests2(self):
        ppu = pp.unicode
        alphas = ppu.Greek.alphas
        greet = pp.Word(alphas) + ',' + pp.Word(alphas) + '!'
        hello = 'Καλημέρα, κόσμε!'
        result = greet.parse_string(hello, parse_all=True)
        print(result)
        self.assertParseResultsEquals(result, expected_list=['Καλημέρα', ',', 'κόσμε', '!'], msg="Failed to parse Greek 'Hello, World!' using pyparsing_unicode.Greek.alphas")

        class Turkish_set(ppu.Latin1, ppu.LatinA):
            pass
        for attrname in 'printables alphas nums identchars identbodychars'.split():
            with self.subTest('verify unicode_set composed using MI', attrname=attrname):
                latin1_value = getattr(ppu.Latin1, attrname)
                latinA_value = getattr(ppu.LatinA, attrname)
                turkish_value = getattr(Turkish_set, attrname)
                self.assertEqual(set(latin1_value + latinA_value), set(turkish_value), f'failed to construct ranges by merging Latin1 and LatinA ({attrname})')
        with self.subTest('Test using new Turkish_set for parsing'):
            key = pp.Word(Turkish_set.alphas)
            value = ppc.integer | pp.Word(Turkish_set.alphas, Turkish_set.alphanums)
            EQ = pp.Suppress('=')
            key_value = key + EQ + value
            sample = '                şehir=İzmir\n                ülke=Türkiye\n                nüfus=4279677'
            result = pp.Dict(pp.OneOrMore(pp.Group(key_value))).parse_string(sample, parse_all=True)
            print(result.dump())
            self.assertParseResultsEquals(result, expected_dict={'şehir': 'İzmir', 'ülke': 'Türkiye', 'nüfus': 4279677}, msg='Failed to parse Turkish key-value pairs')

        def filter_16_bit(s):
            return ''.join((c for c in s if ord(c) < 2 ** 16))
        with self.subTest():
            bmp_printables = ppu.BMP.printables
            sample = ''.join((random.choice(filter_16_bit(unicode_set.printables)) for unicode_set in (ppu.Japanese, Turkish_set, ppu.Greek, ppu.Hebrew, ppu.Devanagari, ppu.Hangul, ppu.Latin1, ppu.Chinese, ppu.Cyrillic, ppu.Arabic, ppu.Thai) for _ in range(8))) + '�'
            print(sample)
            self.assertParseAndCheckList(pp.Word(bmp_printables), sample, [sample])

    def testUnicodeSetNameEquivalence(self):
        ppu = pp.unicode
        for (ascii_name, unicode_name) in [('Arabic', 'العربية'), ('Chinese', '中文'), ('Cyrillic', 'кириллица'), ('Greek', 'Ελληνικά'), ('Hebrew', 'עִברִית'), ('Japanese', '日本語'), ('Korean', '한국어'), ('Thai', 'ไทย'), ('Devanagari', 'देवनागरी')]:
            with self.subTest(ascii_name=ascii_name, unicode_name=unicode_name):
                self.assertTrue(eval(f'ppu.{ascii_name} is ppu.{unicode_name}', {}, locals()))

    def testIndentedBlock(self):
        EQ = pp.Suppress('=')
        stack = [1]
        key = ppc.identifier
        value = pp.Forward()
        key_value = pp.Group(key + EQ + value)
        compound_value = pp.Dict(pp.ungroup(pp.IndentedBlock(key_value, grouped=True)))
        value <<= ppc.integer | pp.QuotedString("'") | compound_value
        parser = pp.Dict(pp.OneOrMore(key_value))
        text = "\n            a = 100\n            b = 101\n            c =\n                c1 = 200\n                c2 =\n                    c21 = 999\n                c3 = 'A horse, a horse, my kingdom for a horse'\n            d = 505\n        "
        text = dedent(text)
        print(text)
        result = parser.parse_string(text, parse_all=True)
        print(result.dump())
        self.assertEqual(100, result.a, 'invalid indented block result')
        self.assertEqual(200, result.c.c1, 'invalid indented block result')
        self.assertEqual(999, result.c.c2.c21, 'invalid indented block result')

    def testIndentedBlockTest2(self):
        indent_stack = [1]
        key = pp.Word(pp.alphas, pp.alphanums) + pp.Suppress(':')
        stmt = pp.Forward()
        suite = pp.IndentedBlock(stmt, grouped=True)
        body = key + suite
        pattern = pp.Word(pp.alphas) + pp.Suppress('(') + pp.Word(pp.alphas) + pp.Suppress(')')
        stmt <<= pattern

        def key_parse_action(toks):
            print(f"Parsing '{toks[0]}'...")
        key.set_parse_action(key_parse_action)
        header = pp.Suppress('[') + pp.Literal('test') + pp.Suppress(']')
        content = header - pp.OneOrMore(pp.IndentedBlock(body))
        contents = pp.Forward()
        suites = pp.IndentedBlock(content)
        extra = pp.Literal('extra') + pp.Suppress(':') - suites
        contents <<= content | extra
        parser = pp.OneOrMore(contents)
        sample = dedent('\n        extra:\n            [test]\n            one0:\n                two (three)\n            four0:\n                five (seven)\n        extra:\n            [test]\n            one1:\n                two (three)\n            four1:\n                five (seven)\n        ')
        (success, _) = parser.run_tests([sample])
        self.assertTrue(success, 'Failed IndentedBlock test for issue #87')
        sample2 = dedent('\n        extra:\n            [test]\n            one:\n                two (three)\n            four:\n                five (seven)\n        extra:\n            [test]\n            one:\n                two (three)\n            four:\n                five (seven)\n\n            [test]\n            one:\n                two (three)\n            four:\n                five (seven)\n\n            [test]\n            eight:\n                nine (ten)\n            eleven:\n                twelve (thirteen)\n\n            fourteen:\n                fifteen (sixteen)\n            seventeen:\n                eighteen (nineteen)\n        ')
        del indent_stack[1:]
        (success, _) = parser.run_tests([sample2])
        self.assertTrue(success, 'Failed indented_block multi-block test for issue #87')

    def testIndentedBlockScan(self):

        def get_parser():
            """
            A valid statement is the word "block:", followed by an indent, followed by the letter A only, or another block
            """
            stack = [1]
            block = pp.Forward()
            body = pp.IndentedBlock(pp.Literal('A') ^ block)
            block <<= pp.Literal('block:') + body
            return block
        p1 = get_parser()
        r1 = list(p1.scan_string(dedent('        block:\n            A\n        ')))
        self.assertEqual(1, len(r1))
        p2 = get_parser()
        r2 = list(p2.scan_string(dedent('        block:\n            B\n        ')))
        self.assertEqual(0, len(r2))
        p3 = get_parser()
        r3 = list(p3.scan_string(dedent('        block:\n            A\n        block:\n            B\n        ')))
        self.assertEqual(1, len(r3))
        p4 = get_parser()
        r4 = list(p4.scan_string(dedent('        block:\n            B\n        block:\n            A\n        ')))
        self.assertEqual(1, len(r4))
        p5 = get_parser()
        r5 = list(p5.scan_string(dedent('        block:\n            block:\n                A\n        block:\n            block:\n                B\n        ')))
        self.assertEqual(1, len(r5))
        p6 = get_parser()
        r6 = list(p6.scan_string(dedent('        block:\n            block:\n                B\n        block:\n            block:\n                A\n        ')))
        self.assertEqual(1, len(r6))

    def testIndentedBlockClass(self):
        data = '            A\n                100\n                101\n\n                102\n            B\n                200\n                201\n\n            C\n                300\n\n        '
        integer = ppc.integer
        group = pp.Group(pp.Char(pp.alphas) + pp.IndentedBlock(integer))
        self.assertParseAndCheckList(group[...], data, [['A', [100, 101, 102]], ['B', [200, 201]], ['C', [300]]])

    def testIndentedBlockClass2(self):
        datas = ['             A\n                100\n             B\n                200\n             201\n            ', '             A\n                100\n             B\n                200\n               201\n            ', '             A\n                100\n             B\n                200\n                  201\n            ']
        integer = ppc.integer
        group = pp.Group(pp.Char(pp.alphas) + pp.IndentedBlock(integer, recursive=False))
        for data in datas:
            print()
            print(group[...].parse_string(data).as_list())
            self.assertParseAndCheckList(group[...] + integer.suppress(), data, [['A', [100]], ['B', [200]]], verbose=False)

    def testIndentedBlockClassWithRecursion(self):
        data = '\n            A\n                100\n                101\n\n                102\n            B\n                b\n                    200\n                    201\n\n            C\n                300\n\n        '
        integer = ppc.integer
        group = pp.Forward()
        group <<= pp.Group(pp.Char(pp.alphas) + pp.IndentedBlock(integer | group))
        print('using search_string')
        print(group.search_string(data))
        self.assertParseAndCheckList(group[...], data, [['A', [100, 101, 102]], ['B', [['b', [200, 201]]]], ['C', [300]]])
        print('using parse_string')
        print(group[...].parse_string(data, parse_all=True).dump())
        dotted_int = pp.DelimitedList(pp.Word(pp.nums), '.', allow_trailing_delim=True, combine=True)
        indented_expr = pp.IndentedBlock(dotted_int, recursive=True, grouped=True)
        good_data = '            1.\n                1.1\n                    1.1.1\n                    1.1.2\n            2.'
        bad_data1 = '            1.\n                1.1\n                    1.1.1\n                 1.2\n            2.'
        bad_data2 = '            1.\n                1.1\n                    1.1.1\n               1.2\n            2.'
        print('test good indentation')
        print(indented_expr.parse_string(good_data, parse_all=True).as_list())
        print()
        print('test bad indentation')
        with self.assertRaisesParseException(msg='Failed to raise exception with bad indentation 1'):
            indented_expr.parse_string(bad_data1, parse_all=True)
        with self.assertRaisesParseException(msg='Failed to raise exception with bad indentation 2'):
            indented_expr.parse_string(bad_data2, parse_all=True)

    def testParseResultsWithNameMatchFirst(self):
        expr_a = pp.Literal('not') + pp.Literal('the') + pp.Literal('bird')
        expr_b = pp.Literal('the') + pp.Literal('bird')
        expr = (expr_a | expr_b)('rexp')
        (success, report) = expr.run_tests('            not the bird\n            the bird\n        ')
        results = [rpt[1] for rpt in report]
        self.assertParseResultsEquals(results[0], ['not', 'the', 'bird'], {'rexp': ['not', 'the', 'bird']})
        self.assertParseResultsEquals(results[1], ['the', 'bird'], {'rexp': ['the', 'bird']})
        with ppt.reset_pyparsing_context():
            pp.__compat__.collect_all_And_tokens = False
            pp.enable_diag(pp.Diagnostics.warn_multiple_tokens_in_named_alternation)
            expr_a = pp.Literal('not') + pp.Literal('the') + pp.Literal('bird')
            expr_b = pp.Literal('the') + pp.Literal('bird')
            with self.assertWarns(UserWarning, msg='failed to warn of And within alternation'):
                expr = (expr_a | expr_b)('rexp')
            with self.assertDoesNotWarn(UserWarning, msg='warned when And within alternation warning was suppressed'):
                expr = (expr_a | expr_b).suppress_warning(pp.Diagnostics.warn_multiple_tokens_in_named_alternation)('rexp')
            (success, report) = expr.run_tests('\n                not the bird\n                the bird\n            ')
            results = [rpt[1] for rpt in report]
            self.assertParseResultsEquals(results[0], ['not', 'the', 'bird'], {'rexp': ['not', 'the', 'bird']})
            self.assertParseResultsEquals(results[1], ['the', 'bird'], {'rexp': ['the', 'bird']})

    def testParseResultsWithNameOr(self):
        expr_a = pp.Literal('not') + pp.Literal('the') + pp.Literal('bird')
        expr_b = pp.Literal('the') + pp.Literal('bird')
        expr = (expr_a ^ expr_b)('rexp')
        (success, _) = expr.run_tests('            not the bird\n            the bird\n        ')
        self.assertTrue(success)
        result = expr.parse_string('not the bird', parse_all=True)
        self.assertParseResultsEquals(result, ['not', 'the', 'bird'], {'rexp': ['not', 'the', 'bird']})
        result = expr.parse_string('the bird', parse_all=True)
        self.assertParseResultsEquals(result, ['the', 'bird'], {'rexp': ['the', 'bird']})
        expr = (expr_a | expr_b)('rexp')
        (success, _) = expr.run_tests('            not the bird\n            the bird\n        ')
        self.assertTrue(success)
        result = expr.parse_string('not the bird', parse_all=True)
        self.assertParseResultsEquals(result, ['not', 'the', 'bird'], {'rexp': ['not', 'the', 'bird']})
        result = expr.parse_string('the bird', parse_all=True)
        self.assertParseResultsEquals(result, ['the', 'bird'], {'rexp': ['the', 'bird']})
        with ppt.reset_pyparsing_context():
            pp.__compat__.collect_all_And_tokens = False
            pp.enable_diag(pp.Diagnostics.warn_multiple_tokens_in_named_alternation)
            expr_a = pp.Literal('not') + pp.Literal('the') + pp.Literal('bird')
            expr_b = pp.Literal('the') + pp.Literal('bird')
            with self.assertWarns(UserWarning, msg='failed to warn of And within alternation'):
                expr = (expr_a ^ expr_b)('rexp')
            with self.assertDoesNotWarn(UserWarning, msg='warned when And within alternation warning was suppressed'):
                expr = (expr_a ^ expr_b).suppress_warning(pp.Diagnostics.warn_multiple_tokens_in_named_alternation)('rexp')
            (success, _) = expr.run_tests('                not the bird\n                the bird\n            ')
            self.assertTrue(success)
            self.assertEqual('not the bird'.split(), list(expr.parse_string('not the bird', parse_all=True)['rexp']))
            self.assertEqual('the bird'.split(), list(expr.parse_string('the bird', parse_all=True)['rexp']))

    def testEmptyDictDoesNotRaiseException(self):
        key = pp.Word(pp.alphas)
        value = pp.Word(pp.nums)
        EQ = pp.Suppress('=')
        key_value_dict = pp.dict_of(key, EQ + value)
        print(key_value_dict.parse_string('            a = 10\n            b = 20\n            ', parse_all=True).dump())
        try:
            print(key_value_dict.parse_string('', parse_all=True).dump())
        except pp.ParseException as pe:
            print(pp.ParseException.explain(pe))
        else:
            self.fail('failed to raise exception when matching empty string')

    def testCaselessKeywordVsKeywordCaseless(self):
        frule = pp.Keyword('t', caseless=True) + pp.Keyword('yes', caseless=True)
        crule = pp.CaselessKeyword('t') + pp.CaselessKeyword('yes')
        flist = frule.search_string('not yes').as_list()
        print(flist)
        clist = crule.search_string('not yes').as_list()
        print(clist)
        self.assertEqual(flist, clist, 'CaselessKeyword not working the same as Keyword(caseless=True)')

    def testOneOf(self):
        expr = pp.one_of('a b abb')
        assert expr.pattern == 'abb|a|b'
        expr = pp.one_of('a abb b abb')
        assert expr.pattern == 'abb|a|b'
        expr = pp.one_of('a abb abbb b abb')
        assert expr.pattern == 'abbb|abb|a|b'
        expr = pp.one_of('a abbb abb b abb')
        assert expr.pattern == 'abbb|abb|a|b'
        expr = pp.one_of('a+ b* c? () +a *b ?c')
        assert expr.pattern == 'a\\+|b\\*|c\\?|\\(\\)|\\+a|\\*b|\\?c'

    def testOneOfKeywords(self):
        literal_expr = pp.one_of('a b c')
        (success, _) = literal_expr[...].run_tests('\n            # literal one_of tests\n            a b c\n            a a a\n            abc\n        ')
        self.assertTrue(success, 'failed literal one_of matching')
        keyword_expr = pp.one_of('a b c', as_keyword=True)
        (success, _) = keyword_expr[...].run_tests('\n            # keyword one_of tests\n            a b c\n            a a a\n        ')
        self.assertTrue(success, 'failed keyword one_of matching')
        (success, _) = keyword_expr[...].run_tests('\n            # keyword one_of failure tests\n            abc\n        ', failure_tests=True)
        self.assertTrue(success, 'failed keyword one_of failure tests')

    def testDelimitedListName(self):
        bool_constant = pp.Literal('True') | 'true' | 'False' | 'false'
        bool_list = pp.DelimitedList(bool_constant)
        print(bool_list)
        self.assertEqual("{'True' | 'true' | 'False' | 'false'} [, {'True' | 'true' | 'False' | 'false'}]...", str(bool_list))
        bool_constant.set_name('bool')
        print(bool_constant)
        print(bool_constant.streamline())
        bool_list2 = pp.DelimitedList(bool_constant)
        print(bool_constant)
        print(bool_constant.streamline())
        print(bool_list2)
        with self.subTest():
            self.assertEqual('bool [, bool]...', str(bool_list2))
        with self.subTest():
            street_address = pp.common.integer.set_name('integer') + pp.Word(pp.alphas)[1, ...].set_name('street_name')
            self.assertEqual('{integer street_name} [, {integer street_name}]...', str(pp.DelimitedList(street_address)))
        with self.subTest():
            operand = pp.Char(pp.alphas).set_name('var')
            math = pp.infix_notation(operand, [(pp.one_of('+ -'), 2, pp.OpAssoc.LEFT)])
            self.assertEqual('var_expression [, var_expression]...', str(pp.DelimitedList(math)))

    def testDelimitedListOfStrLiterals(self):
        expr = pp.DelimitedList('ABC')
        print(str(expr))
        source = 'ABC, ABC,ABC'
        self.assertParseAndCheckList(expr, source, [s.strip() for s in source.split(',')])

    def testDelimitedListMinMax(self):
        source = 'ABC, ABC,ABC'
        with self.assertRaises(ValueError, msg='min must be greater than 0'):
            pp.DelimitedList('ABC', min=0)
        with self.assertRaises(ValueError, msg='max must be greater than, or equal to min'):
            pp.DelimitedList('ABC', min=1, max=0)
        with self.assertRaises(pp.ParseException):
            pp.DelimitedList('ABC', min=4).parse_string(source)
        source_expr_pairs = [('ABC,  ABC', pp.DelimitedList('ABC', max=2)), (source, pp.DelimitedList('ABC', min=2, max=4))]
        for (source, expr) in source_expr_pairs:
            print(str(expr))
            self.assertParseAndCheckList(expr, source, [s.strip() for s in source.split(',')])

    def testDelimitedListParseActions1(self):
        keyword = pp.Keyword('foobar')
        untyped_identifier = ~keyword + pp.Word(pp.alphas)
        dotted_vars = pp.DelimitedList(untyped_identifier, delim='.')
        lvalue = pp.Opt(dotted_vars)
        stmt = pp.DelimitedList(pp.Opt(dotted_vars))

        seen = []

        def parse_identifier(toks):
            seen.append(toks.as_list())
        untyped_identifier.set_parse_action(parse_identifier)
        dotted_vars.parse_string('B.C')
        self.assertEqual([['B'], ['C']], seen)

    def testDelimitedListParseActions2(self):
        keyword = pp.Keyword('foobar')
        untyped_identifier = ~keyword + pp.Word(pp.alphas)
        dotted_vars = pp.DelimitedList(untyped_identifier, delim='.')
        lvalue = pp.Opt(dotted_vars)
        stmt = pp.DelimitedList(dotted_vars)

        seen = []

        def parse_identifier(toks):
            seen.append(toks.as_list())
        untyped_identifier.set_parse_action(parse_identifier)
        dotted_vars.parse_string('B.C')
        self.assertEqual([['B'], ['C']], seen)

    def testDelimitedListParseActions3(self):
        keyword = pp.Keyword('foobar')
        untyped_identifier = ~keyword + pp.Word(pp.alphas)
        dotted_vars = pp.DelimitedList(untyped_identifier, delim='.')
        lvalue = pp.Opt(dotted_vars)
        stmt = pp.Opt(dotted_vars)

        seen = []

        def parse_identifier(toks):
            seen.append(toks.as_list())
        untyped_identifier.set_parse_action(parse_identifier)
        dotted_vars.parse_string('B.C')
        self.assertEqual([['B'], ['C']], seen)

    def testTagElements(self):
        end_punc = '.' + pp.Tag('mood', 'normal') | '!' + pp.Tag('mood', 'excited') | '?' + pp.Tag('mood', 'curious')
        greeting = 'Hello' + pp.Word(pp.alphas) + end_punc[1, ...]
        for (ending, expected_mood) in [('.', 'normal'), ('!', 'excited'), ('?', 'curious'), ('!!', 'excited'), ('!?', 'curious')]:
            self.assertParseAndCheckDict(greeting, f'Hello World{ending}', {'mood': expected_mood})

    def testWordInternalReRangesKnownSet(self):
        tests = [('ABCDEMNXYZ', '[A-EMNX-Z]+'), (pp.printables, '[!-~]+'), (pp.alphas, '[A-Za-z]+'), (pp.alphanums, '[0-9A-Za-z]+'), (pp.pyparsing_unicode.Latin1.printables, '[!-~¡-ÿ]+'), (pp.pyparsing_unicode.Latin1.alphas, '[A-Za-zªµºÀ-ÖØ-öø-ÿ]+'), (pp.pyparsing_unicode.Latin1.alphanums, '[0-9A-Za-zª²³µ¹ºÀ-ÖØ-öø-ÿ]+'), (pp.alphas8bit, '[À-ÖØ-öø-ÿ]+')]
        failed = []
        for (word_string, expected_re) in tests:
            try:
                msg = f'failed to generate correct internal re for {word_string!r}'
                resultant_re = pp.Word(word_string).reString
                self.assertEqual(expected_re, resultant_re, msg + f'; expected {expected_re!r} got {resultant_re!r}')
            except AssertionError:
                failed.append(msg)
        if failed:
            print('Errors:\n{}'.format('\n'.join(failed)))
            self.fail("failed to generate correct internal re's")

    def testWordInternalReRanges(self):
        import random
        esc_chars = '\\^-]['
        esc_chars2 = '*+.?'

        def esc_re_set_char(c):
            return '\\' + c if c in esc_chars else c

        def esc_re_set2_char(c):
            return '\\' + c if c in esc_chars + esc_chars2 else c
        for esc_char in esc_chars + esc_chars2:
            next_char = chr(ord(esc_char) + 1)
            prev_char = chr(ord(esc_char) - 1)
            esc_word = pp.Word(esc_char + next_char)
            expected = f'[{esc_re_set_char(esc_char)}{esc_re_set_char(next_char)}]+'
            print(f"Testing escape char: {esc_char} -> {esc_word} re: '{esc_word.reString}')")
            self.assertEqual(expected, esc_word.reString, 'failed to generate correct internal re')
            test_string = ''.join((random.choice([esc_char, next_char]) for __ in range(16)))
            print(f"Match '{test_string}' -> {test_string == esc_word.parse_string(test_string, parse_all=True)[0]}")
            self.assertEqual(test_string, esc_word.parse_string(test_string, parse_all=True)[0], 'Word using escaped range char failed to parse')
            esc_word = pp.Word(prev_char + esc_char)
            expected = f'[{esc_re_set_char(prev_char)}{esc_re_set_char(esc_char)}]+'
            print(f"Testing escape char: {esc_char} -> {esc_word} re: '{esc_word.reString}')")
            self.assertEqual(expected, esc_word.reString, 'failed to generate correct internal re')
            test_string = ''.join((random.choice([esc_char, prev_char]) for __ in range(16)))
            print(f"Match '{test_string}' -> {test_string == esc_word.parse_string(test_string, parse_all=True)[0]}")
            self.assertEqual(test_string, esc_word.parse_string(test_string, parse_all=True)[0], 'Word using escaped range char failed to parse')
            next_char = chr(ord(esc_char) + 1)
            prev_char = chr(ord(esc_char) - 1)
            esc_word = pp.Word(esc_char + next_char)
            expected = f'[{esc_re_set_char(esc_char)}{esc_re_set_char(next_char)}]+'
            print(f"Testing escape char: {esc_char} -> {esc_word} re: '{esc_word.reString}')")
            self.assertEqual(expected, esc_word.reString, 'failed to generate correct internal re')
            test_string = ''.join((random.choice([esc_char, next_char]) for __ in range(16)))
            print(f"Match '{test_string}' -> {test_string == esc_word.parse_string(test_string, parse_all=True)[0]}")
            self.assertEqual(test_string, esc_word.parse_string(test_string, parse_all=True)[0], 'Word using escaped range char failed to parse')
            esc_word = pp.Word(esc_char, pp.alphas.upper())
            expected = f'{esc_re_set2_char(esc_char)}[A-Z]*'
            print(f"Testing escape char: {esc_char} -> {esc_word} re: '{esc_word.reString}')")
            self.assertEqual(expected, esc_word.reString, 'failed to generate correct internal re')
            test_string = esc_char + ''.join((random.choice(pp.alphas.upper()) for __ in range(16)))
            print(f"Match '{test_string}' -> {test_string == esc_word.parse_string(test_string, parse_all=True)[0]}")
            self.assertEqual(test_string, esc_word.parse_string(test_string, parse_all=True)[0], 'Word using escaped range char failed to parse')
            esc_word = pp.Word(esc_char, pp.alphas.upper())
            expected = f'{re.escape(esc_char)}[A-Z]*'
            print(f"Testing escape char: {esc_char} -> {esc_word} re: '{esc_word.reString}')")
            self.assertEqual(expected, esc_word.reString, 'failed to generate correct internal re')
            test_string = esc_char + ''.join((random.choice(pp.alphas.upper()) for __ in range(16)))
            print(f"Match '{test_string}' -> {test_string == esc_word.parse_string(test_string, parse_all=True)[0]}")
            self.assertEqual(test_string, esc_word.parse_string(test_string, parse_all=True)[0], 'Word using escaped range char failed to parse')
            print()

    def testWordWithIdentChars(self):
        ppu = pp.pyparsing_unicode
        latin_identifier = pp.Word(pp.identchars, pp.identbodychars)('latin*')
        japanese_identifier = ppu.Japanese.identifier('japanese*')
        cjk_identifier = ppu.CJK.identifier('cjk*')
        greek_identifier = ppu.Greek.identifier('greek*')
        cyrillic_identifier = ppu.Cyrillic.identifier('cyrillic*')
        thai_identifier = ppu.Thai.identifier('thai*')
        idents = latin_identifier | japanese_identifier | cjk_identifier | thai_identifier | greek_identifier | cyrillic_identifier
        result = idents[...].parse_string('abc_100 кириллицаx_10 日本語f_300 ไทยg_600 def_200 漢字y_300 한국어_中文c_400 Ελληνικάb_500', parse_all=True)
        self.assertParseResultsEquals(result, ['abc_100', 'кириллицаx_10', '日本語f_300', 'ไทยg_600', 'def_200', '漢字y_300', '한국어_中文c_400', 'Ελληνικάb_500'], {'cjk': ['한국어_中文c_400'], 'cyrillic': ['кириллицаx_10'], 'greek': ['Ελληνικάb_500'], 'japanese': ['日本語f_300', '漢字y_300'], 'latin': ['abc_100', 'def_200'], 'thai': ['ไทยg_600']})

    def testChainedTernaryOperator(self):
        TERNARY_INFIX = pp.infix_notation(ppc.integer, [(('?', ':'), 3, pp.OpAssoc.LEFT)])
        self.assertParseAndCheckList(TERNARY_INFIX, '1?1:0?1:0', [[1, '?', 1, ':', 0, '?', 1, ':', 0]])
        TERNARY_INFIX = pp.infix_notation(ppc.integer, [(('?', ':'), 3, pp.OpAssoc.RIGHT)])
        self.assertParseAndCheckList(TERNARY_INFIX, '1?1:0?1:0', [[1, '?', 1, ':', [0, '?', 1, ':', 0]]])

    def testOneOfWithDuplicateSymbols(self):
        print('verify one_of handles duplicate symbols')
        try:
            test1 = pp.one_of('a b c d a')
        except RuntimeError:
            self.fail('still have infinite loop in one_of with duplicate symbols (string input)')
        print('verify one_of handles duplicate symbols')
        try:
            test1 = pp.one_of('a a a b c d a')
        except RuntimeError:
            self.fail('still have infinite loop in one_of with duplicate symbols (string input)')
        assert test1.pattern == '[abcd]'
        print('verify one_of handles generator input')
        try:
            test1 = pp.one_of((c for c in 'a b c d a d d d' if not c.isspace()))
        except RuntimeError:
            self.fail('still have infinite loop in one_of with duplicate symbols (generator input)')
        assert test1.pattern == '[abcd]'
        print('verify one_of handles list input')
        try:
            test1 = pp.one_of('a b c d a'.split())
        except RuntimeError:
            self.fail('still have infinite loop in one_of with duplicate symbols (list input)')
        assert test1.pattern == '[abcd]'
        print('verify one_of handles set input')
        try:
            test1 = pp.one_of(set('a b c d a'.split()))
        except RuntimeError:
            self.fail('still have infinite loop in one_of with duplicate symbols (set input)')
        pattern_letters = test1.pattern[1:-1]
        assert sorted(pattern_letters) == sorted('abcd')

    def testOneOfWithEmptyList(self):
        """test one_of helper function with an empty list as input"""
        tst = []
        result = pp.one_of(tst)
        expected = True
        found = isinstance(result, pp.NoMatch)
        self.assertEqual(expected, found)

    def testOneOfWithUnexpectedInput(self):
        """test one_of with an input that isn't a string or iterable"""
        with self.assertRaises(TypeError, msg='failed to warn use of integer for one_of'):
            expr = pp.one_of(6)

    def testMatchFirstIteratesOverAllChoices(self):
        print('verify MatchFirst iterates properly')
        results = pp.quoted_string.parse_string("'this is a single quoted string'", parse_all=True)
        self.assertTrue(len(results) > 0, 'MatchFirst error - not iterating over all choices')

    def testOptionalWithResultsNameAndNoMatch(self):
        print("verify Optional's do not cause match failure if have results name")
        testGrammar = pp.Literal('A') + pp.Optional('B')('gotB') + pp.Literal('C')
        try:
            testGrammar.parse_string('ABC', parse_all=True)
            testGrammar.parse_string('AC', parse_all=True)
        except pp.ParseException as pe:
            print(pe.pstr, '->', pe)
            self.fail(f'error in Optional matching of string {pe.pstr}')

    def testOptionalBeyondEndOfString(self):
        print("verify handling of Optional's beyond the end of string")
        testGrammar = 'A' + pp.Optional('B') + pp.Optional('C') + pp.Optional('D')
        testGrammar.parse_string('A', parse_all=True)
        testGrammar.parse_string('AB', parse_all=True)

    def testLineMethodSpecialCaseAtStart(self):
        print('verify correct line() behavior when first line is empty string')
        self.assertEqual('', pp.line(0, '\nabc\ndef\n'), 'Error in line() with empty first line in text')
        txt = '\nabc\ndef\n'
        results = [pp.line(i, txt) for i in range(len(txt))]
        self.assertEqual(['', 'abc', 'abc', 'abc', 'abc', 'def', 'def', 'def', 'def'], results, 'Error in line() with empty first line in text')
        txt = 'abc\ndef\n'
        results = [pp.line(i, txt) for i in range(len(txt))]
        self.assertEqual(['abc', 'abc', 'abc', 'abc', 'def', 'def', 'def', 'def'], results, 'Error in line() with non-empty first line in text')

    def testSetResultsNameWithOneOrMoreAndZeroOrMore(self):
        print('verify behavior of set_results_name with OneOrMore and ZeroOrMore')
        stmt = pp.Keyword('test')
        print(stmt[...]('tests').parse_string('test test', parse_all=True).tests)
        print(stmt[1, ...]('tests').parse_string('test test', parse_all=True).tests)
        print(pp.Optional(stmt[1, ...]('tests')).parse_string('test test', parse_all=True).tests)
        print(pp.Optional(stmt[1, ...])('tests').parse_string('test test', parse_all=True).tests)
        print(pp.Optional(pp.DelimitedList(stmt))('tests').parse_string('test,test', parse_all=True).tests)
        self.assertEqual(2, len(stmt[...]('tests').parse_string('test test', parse_all=True).tests), 'ZeroOrMore failure with set_results_name')
        self.assertEqual(2, len(stmt[1, ...]('tests').parse_string('test test', parse_all=True).tests), 'OneOrMore failure with set_results_name')
        self.assertEqual(2, len(pp.Optional(stmt[1, ...]('tests')).parse_string('test test', parse_all=True).tests), 'OneOrMore failure with set_results_name')
        self.assertEqual(2, len(pp.Optional(pp.DelimitedList(stmt))('tests').parse_string('test,test', parse_all=True).tests), 'DelimitedList failure with set_results_name')
        self.assertEqual(2, len((stmt * 2)('tests').parse_string('test test', parse_all=True).tests), 'multiplied(1) failure with set_results_name')
        self.assertEqual(2, len(stmt[..., 2]('tests').parse_string('test test', parse_all=True).tests), 'multiplied(2) failure with set_results_name')
        self.assertEqual(2, len(stmt[1, ...]('tests').parse_string('test test', parse_all=True).tests), 'multiplied(3) failure with set_results_name')
        self.assertEqual(2, len(stmt[2, ...]('tests').parse_string('test test', parse_all=True).tests), 'multiplied(3) failure with set_results_name')

    def testParseExpressionsWithRegex(self):
        from itertools import product
        match_empty_regex = pp.Regex('[a-z]*')
        match_nonempty_regex = pp.Regex('[a-z]+')
        parser_classes = pp.ParseExpression.__subclasses__()
        test_string = 'abc def'
        expected = ['abc']
        for (expr, cls) in product((match_nonempty_regex, match_empty_regex), parser_classes):
            print(expr, cls)
            parser = cls([expr])
            parsed_result = parser.parse_string(test_string, parse_all=False)
            print(parsed_result.dump())
            self.assertParseResultsEquals(parsed_result, expected)
        for (expr, cls) in product((match_nonempty_regex, match_empty_regex), (pp.MatchFirst, pp.Or)):
            parser = cls([expr, expr])
            print(parser)
            parsed_result = parser.parse_string(test_string, parse_all=False)
            print(parsed_result.dump())
            self.assertParseResultsEquals(parsed_result, expected)

    def testOnlyOnce(self):
        """test class OnlyOnce and its reset method"""

        def append_sum(tokens):
            tokens.append(sum(map(int, tokens)))
        pa = pp.OnlyOnce(append_sum)
        expr = pp.OneOrMore(pp.Word(pp.nums)).add_parse_action(pa)
        result = expr.parse_string('0 123 321', parse_all=True)
        print(result.dump())
        expected = ['0', '123', '321', 444]
        self.assertParseResultsEquals(result, expected, msg='issue with OnlyOnce first call')
        with self.assertRaisesParseException(msg='failed to raise exception calling OnlyOnce more than once'):
            result2 = expr.parse_string('1 2 3 4 5', parse_all=True)
        pa.reset()
        result = expr.parse_string('100 200 300')
        print(result.dump())
        expected = ['100', '200', '300', 600]
        self.assertParseResultsEquals(result, expected, msg='issue with OnlyOnce after reset')

    def testGoToColumn(self):
        """tests for GoToColumn class"""
        dateExpr = pp.Regex('\\d\\d(\\.\\d\\d){2}')('date')
        numExpr = ppc.number('num')
        sample = '            date                Not Important                         value    NotImportant2\n            11.11.13       |    useless . useless,21 useless 2     |  14.21  | asmdakldm\n            21.12.12       |    fmpaosmfpoamsp 4                   |  41     | ajfa9si90'.splitlines()
        patt = dateExpr + pp.GoToColumn(70).ignore('|') + numExpr + pp.rest_of_line
        infile = iter(sample)
        next(infile)
        expecteds = [['11.11.13', 14.21], ['21.12.12', 41]]
        for (line, expected) in zip(infile, expecteds):
            result = patt.parse_string(line, parse_all=True)
            print(result)
            self.assertEqual(expected, [result.date, result.num], msg='issue with GoToColumn')
        patt = dateExpr('date') + pp.GoToColumn(30) + numExpr + pp.rest_of_line
        infile = iter(sample)
        next(infile)
        for line in infile:
            with self.assertRaisesParseException(msg='issue with GoToColumn not finding match'):
                result = patt.parse_string(line, parse_all=True)

    def testExpressionDefaultStrings(self):
        expr = pp.Word(pp.nums)
        print(expr)
        self.assertEqual('W:(0-9)', repr(expr))
        expr = pp.Word(pp.nums, exact=3)
        print(expr)
        self.assertEqual('W:(0-9){3}', repr(expr))
        expr = pp.Word(pp.nums, min=2)
        print(expr)
        self.assertEqual('W:(0-9){2,...}', repr(expr))
        expr = pp.Word(pp.nums, max=3)
        print(expr)
        self.assertEqual('W:(0-9){1,3}', repr(expr))
        expr = pp.Word(pp.nums, min=2, max=3)
        print(expr)
        self.assertEqual('W:(0-9){2,3}', repr(expr))
        expr = pp.Char(pp.nums)
        print(expr)
        self.assertEqual('(0-9)', repr(expr))

    def testEmptyExpressionsAreHandledProperly(self):
        try:
            from pyparsing.diagram import to_railroad
        except ModuleNotFoundError as mnfe:
            print(f"Failed 'from pyparsing.diagram import to_railroad'\n  {type(mnfe).__name__}: {mnfe}")
            if mnfe.__cause__:
                print(f'\n {type(mnfe.__cause__).__name__}: {mnfe.__cause__}')
            self.skipTest("Failed 'from pyparsing.diagram import to_railroad'")
        for cls in (pp.And, pp.Or, pp.MatchFirst, pp.Each):
            print('testing empty', cls.__name__)
            expr = cls([])
            to_railroad(expr)

    def testDiagramToRailroadPreservesNamedGrammarAndResultsName(self):
        from pyparsing.diagram import railroad_to_html, to_railroad

        expr = (pp.Keyword('select') + pp.Word(pp.alphas)('field')).set_name('query')
        rendered = railroad_to_html(to_railroad(expr, show_results_names=True))
        self.assertIn('query', rendered)
        self.assertIn('field', rendered)

    def testDiagramRailroadToHtmlSupportsDocumentAndEmbedModes(self):
        from pyparsing.diagram import railroad_to_html, to_railroad

        expr = (pp.Keyword('select') + pp.Word(pp.alphas)('field')).set_name('query')
        diagrams = to_railroad(expr, show_results_names=True)
        document = railroad_to_html(diagrams)
        embedded = railroad_to_html(diagrams, embed=True)

        self.assertIn('query', document)
        self.assertIn('query', embedded)
        self.assertNotEqual(document, embedded)

    def testCreateDiagramWritesCompleteOrEmbeddedHtml(self):
        expr = (pp.Keyword('select') + pp.Word(pp.alphas)('field')).set_name('query')
        with tempfile.TemporaryDirectory() as temp_dir:
            document_path = f'{temp_dir}/document.html'
            embedded_path = f'{temp_dir}/embedded.html'
            expr.create_diagram(document_path, embed=False, show_results_names=True)
            expr.create_diagram(embedded_path, embed=True, show_results_names=True)
            document = open(document_path, encoding='utf-8').read()
            embedded = open(embedded_path, encoding='utf-8').read()

        self.assertIn('query', document)
        self.assertIn('query', embedded)
        self.assertNotEqual(document, embedded)
    test_exception_messages_tests = ((pp.Word(pp.alphas), '123', "Expected W:(A-Za-z), found '123'"), (pp.Word(pp.alphas).set_name('word'), '123', "Expected word, found '123'"), (pp.Group(pp.Word(pp.alphas).set_name('word')), '123', "Expected word, found '123'"), (pp.OneOrMore(pp.Word(pp.alphas).set_name('word')), '123', "Expected word, found '123'"), (pp.DelimitedList(pp.Word(pp.alphas).set_name('word')), '123', "Expected word, found '123'"), (pp.Suppress(pp.Word(pp.alphas).set_name('word')), '123', "Expected word, found '123'"), (pp.Forward() << pp.Word(pp.alphas).set_name('word'), '123', "Expected word, found '123'"), (pp.Forward() << pp.Word(pp.alphas), '123', "Expected W:(A-Za-z), found '123'"), (pp.Group(pp.Word(pp.alphas)), '123', "Expected W:(A-Za-z), found '123'"), ('prefix' + (pp.Regex('a').set_name('a') | pp.Regex('b').set_name('b')), 'prefixc', "Expected {a | b}, found 'c'"), ('prefix' + (pp.Regex('a').set_name('a') | pp.Regex('b').set_name('b')), 'prefix c', "Expected {a | b}, found 'c'"), ('prefix' + (pp.Regex('a').set_name('a') ^ pp.Regex('b').set_name('b')), 'prefixc', "Expected {a ^ b}, found 'c'"), ('prefix' + (pp.Regex('a').set_name('a') ^ pp.Regex('b').set_name('b')), 'prefix c', "Expected {a ^ b}, found 'c'"))

    def test_pep8_synonyms(self):
        """
        Test that staticmethods wrapped by replaced_by_pep8 wrapper are properly
        callable as staticmethods.
        """

        def run_subtest(fn_name, expr=None, args=''):
            bool_expr = pp.one_of('true false', as_keyword=True)
            if expr is None:
                expr = 'bool_expr'
            with self.subTest(fn_name=fn_name):
                exec(f'{expr}.{fn_name}({args})', globals(), locals())
        parser_element_staticmethod_names = '\n            enable_packrat disable_memoization enable_left_recursion reset_cache\n        '.split()
        for name in parser_element_staticmethod_names:
            run_subtest(name)
        pp.ParserElement.disable_memoization()
        run_subtest('set_default_whitespace_chars', args="' '")
        run_subtest('inline_literals_using', args='pp.Suppress')
        run_subtest('set_default_keyword_chars', expr="pp.Keyword('START')", args="'abcde'")
        pass

class Test11_LR1_Recursion(TestCase, ppt.TestParseResultsAsserts):
    """
    Tests for recursive parsing
    """
    suite_context = None
    save_suite_context = None

    def setUp(self):
        recursion_suite_context.restore()

    def tearDown(self):
        default_suite_context.restore()

    def test_repeat_as_recurse(self):
        """repetition rules formulated with recursion"""
        one_or_more = pp.Forward().set_name('one_or_more')
        one_or_more <<= one_or_more + 'a' | 'a'
        self.assertParseResultsEquals(one_or_more.parse_string('a', parse_all=True), expected_list=['a'])
        self.assertParseResultsEquals(one_or_more.parse_string('aaa aa', parse_all=True), expected_list=['a', 'a', 'a', 'a', 'a'])
        DelimitedList = pp.Forward().set_name('DelimitedList')
        DelimitedList <<= DelimitedList + pp.Suppress(',') + 'b' | 'b'
        self.assertParseResultsEquals(DelimitedList.parse_string('b', parse_all=True), expected_list=['b'])
        self.assertParseResultsEquals(DelimitedList.parse_string('b,b', parse_all=True), expected_list=['b', 'b'])
        self.assertParseResultsEquals(DelimitedList.parse_string('b,b , b, b,b', parse_all=True), expected_list=['b', 'b', 'b', 'b', 'b'])

    def test_binary_recursive(self):
        """parsing of single left-recursive binary operator"""
        expr = pp.Forward().set_name('expr')
        num = pp.Word(pp.nums)
        expr <<= expr + '+' - num | num
        self.assertParseResultsEquals(expr.parse_string('1+2', parse_all=True), expected_list=['1', '+', '2'])
        self.assertParseResultsEquals(expr.parse_string('1+2+3+4', parse_all=True), expected_list=['1', '+', '2', '+', '3', '+', '4'])

    def test_binary_associative(self):
        """associative is preserved for single left-recursive binary operator"""
        expr = pp.Forward().set_name('expr')
        num = pp.Word(pp.nums)
        expr <<= pp.Group(expr) + '+' - num | num
        self.assertParseResultsEquals(expr.parse_string('1+2', parse_all=True), expected_list=[['1'], '+', '2'])
        self.assertParseResultsEquals(expr.parse_string('1+2+3+4', parse_all=True), expected_list=[[[['1'], '+', '2'], '+', '3'], '+', '4'])

    def test_add_sub(self):
        """indirectly left-recursive/associative add/sub calculator"""
        expr = pp.Forward().set_name('expr')
        num = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        expr <<= (expr + '+' - num).set_parse_action(lambda t: t[0] + t[2]) | (expr + '-' - num).set_parse_action(lambda t: t[0] - t[2]) | num
        self.assertEqual(expr.parse_string('1+2', parse_all=True)[0], 3)
        self.assertEqual(expr.parse_string('1+2+3', parse_all=True)[0], 6)
        self.assertEqual(expr.parse_string('1+2-3', parse_all=True)[0], 0)
        self.assertEqual(expr.parse_string('1-2+3', parse_all=True)[0], 2)
        self.assertEqual(expr.parse_string('1-2-3', parse_all=True)[0], -4)

    def test_math(self):
        """precedence climbing parser for math"""
        expr = pp.Forward().set_name('expr')
        add_sub = pp.Forward().set_name('add_sub')
        mul_div = pp.Forward().set_name('mul_div')
        power = pp.Forward().set_name('power')
        terminal = pp.Forward().set_name('terminal')
        number = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        signed = '+' - expr | ('-' - expr).set_parse_action(lambda t: -t[1])
        group = pp.Suppress('(') - expr - pp.Suppress(')')
        add_sub <<= (add_sub + '+' - mul_div).set_parse_action(lambda t: t[0] + t[2]) | (add_sub + '-' - mul_div).set_parse_action(lambda t: t[0] - t[2]) | mul_div
        mul_div <<= (mul_div + '*' - power).set_parse_action(lambda t: t[0] * t[2]) | (mul_div + '/' - power).set_parse_action(lambda t: t[0] / t[2]) | power
        power <<= (terminal + '^' - power).set_parse_action(lambda t: t[0] ** t[2]) | terminal
        terminal <<= number | signed | group
        expr <<= add_sub
        self.assertEqual(expr.parse_string('1+2', parse_all=True)[0], 3)
        self.assertEqual(expr.parse_string('1+2+3', parse_all=True)[0], 6)
        self.assertEqual(expr.parse_string('1+2-3', parse_all=True)[0], 0)
        self.assertEqual(expr.parse_string('1-2+3', parse_all=True)[0], 2)
        self.assertEqual(expr.parse_string('1-2-3', parse_all=True)[0], -4)
        self.assertEqual(expr.parse_string('1+(2+3)', parse_all=True)[0], 6)
        self.assertEqual(expr.parse_string('1+(2-3)', parse_all=True)[0], 0)
        self.assertEqual(expr.parse_string('1-(2+3)', parse_all=True)[0], -4)
        self.assertEqual(expr.parse_string('1-(2-3)', parse_all=True)[0], 2)
        self.assertEqual(expr.parse_string('1----3', parse_all=True)[0], 1 - ---3)
        self.assertEqual(expr.parse_string('1+2*3', parse_all=True)[0], 1 + 2 * 3)
        self.assertEqual(expr.parse_string('1*2+3', parse_all=True)[0], 1 * 2 + 3)
        self.assertEqual(expr.parse_string('1*2^3', parse_all=True)[0], 1 * 2 ** 3)
        self.assertEqual(expr.parse_string('4^3^2^1', parse_all=True)[0], 4 ** 3 ** 2 ** 1)

    def test_terminate_empty(self):
        """Recursion with ``Empty`` terminates"""
        empty = pp.Forward().set_name('e')
        empty <<= empty + pp.Empty() | pp.Empty()
        self.assertParseResultsEquals(empty.parse_string('', parse_all=True), expected_list=[])

    def test_non_peg(self):
        """Recursion works for non-PEG operators"""
        expr = pp.Forward().set_name('expr')
        expr <<= expr + 'a' ^ expr + 'ab' ^ expr + 'abc' ^ '.'
        self.assertParseResultsEquals(expr.parse_string('.abcabaabc', parse_all=True), expected_list=['.', 'abc', 'ab', 'a', 'abc'])

class TestShowBestPractices(unittest.TestCase):

    def test_loads_markdown_file(self):
        result = pp.show_best_practices(file=None)
        self.assertIsInstance(result, str)
        self.assertTrue(result.strip())

    def test_fallback_when_file_missing(self):
        expected = pp.show_best_practices(file=None)
        output = StringIO()
        pp.show_best_practices(file=output)
        self.assertEqual(expected.strip(), output.getvalue().strip())

    def test_cli_invocation_with_module_flag(self):
        cmd = [sys.executable, '-m', 'pyparsing.ai.show_best_practices']
        subproc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(subproc.returncode, 0, msg=f'stderr: {subproc.stderr}')
        expected = pp.show_best_practices(file=None)
        self.assertEqual(expected.strip(), subproc.stdout.strip())
pp.ParserElement.disable_memoization()
Test02_WithoutPackrat.suite_context = ppt.reset_pyparsing_context().save()
Test02_WithoutPackrat.save_suite_context = ppt.reset_pyparsing_context().save()
default_suite_context = ppt.reset_pyparsing_context().save()
pp.ParserElement.enable_left_recursion()
recursion_suite_context = ppt.reset_pyparsing_context().save()
default_suite_context.restore()
