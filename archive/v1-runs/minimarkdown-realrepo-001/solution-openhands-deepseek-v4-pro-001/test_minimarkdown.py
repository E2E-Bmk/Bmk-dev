"""Quick validation tests for minimarkdown.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minimarkdown import Markdown, HTMLRenderer, ASTRenderer, escape_html

passed = 0
failed = 0

def check(name, actual, expected):
    global passed, failed
    if actual == expected:
        passed += 1
        print(f'  PASS: {name}')
    else:
        failed += 1
        print(f'  FAIL: {name}')
        print(f'    expected: {repr(expected)}')
        print(f'    actual:   {repr(actual)}')

def check_contains(name, actual, expected_substr):
    global passed, failed
    if expected_substr in actual:
        passed += 1
        print(f'  PASS: {name}')
    else:
        failed += 1
        print(f'  FAIL: {name}')
        print(f'    expected to contain: {repr(expected_substr)}')
        print(f'    actual: {repr(actual)}')

def check_not_contains(name, actual, bad_substr):
    global passed, failed
    if bad_substr not in actual:
        passed += 1
        print(f'  PASS: {name}')
    else:
        failed += 1
        print(f'  FAIL: {name}')
        print(f'    should NOT contain: {repr(bad_substr)}')
        print(f'    actual: {repr(actual)}')

# ---- escape_html ----
print('\n=== escape_html ===')
check('escapes &', escape_html('a & b'), 'a &amp; b')
check('escapes <', escape_html('<tag>'), '&lt;tag&gt;')
check('escapes >', escape_html('<tag>'), '&lt;tag&gt;')
check('escapes "', escape_html('"hi"'), '&quot;hi&quot;')

# ---- headings ----
print('\n=== Headings ===')
md = Markdown()
check('h1', md('# Hello'), '<h1>Hello</h1>')
check('h2', md('## Hello'), '<h2>Hello</h2>')
check('h6', md('###### Hello'), '<h6>Hello</h6>')
check('h1 trailing #', md('# Hello #'), '<h1>Hello</h1>')
check_contains('h1 with escape', md('# A & B'), 'A &amp; B')

# ---- paragraphs ----
print('\n=== Paragraphs ===')
check('simple para', md('Hello world'), '<p>Hello world</p>')
check('multi-line para', md('Hello\nworld'), '<p>Hello\nworld</p>')

# ---- emphasis ----
print('\n=== Emphasis ===')
check('em *', md('*hello*'), '<p><em>hello</em></p>')
check('em _', md('_hello_'), '<p><em>hello</em></p>')
check('strong **', md('**hello**'), '<p><strong>hello</strong></p>')
check('strong __', md('__hello__'), '<p><strong>hello</strong></p>')
check_contains('nested em+strong', md('*em **strong** em*'), '<em>em <strong>strong</strong> em</em>')

# ---- code spans ----
print('\n=== Code spans ===')
check_contains('code span', md('`code`'), '<code>code</code>')
check_contains('code span escaped', md('`a < b`'), 'a &lt; b')

# ---- code blocks ----
print('\n=== Code blocks ===')
check_contains('fenced code', md('```\ncode\n```'), '<pre><code>code</code></pre>')
check_contains('fenced with lang', md('```python\nx=1\n```'), 'class="language-python"')
check_contains('indented code', md('    code'), '<pre><code>code</code></pre>')

# ---- links and images ----
print('\n=== Links and Images ===')
check_contains('link', md('[text](url)'), '<a href="url">text</a>')
check_contains('link with title', md('[text](url "title")'), 'title="title"')
check_contains('image', md('![alt](img.png)'), '<img src="img.png" alt="alt">')

# ---- autolinks ----
print('\n=== Autolinks ===')
check_contains('http autolink', md('<https://example.com>'), 'href="https://example.com"')

# ---- block quotes ----
print('\n=== Block quotes ===')
check_contains('blockquote', md('> quote'), '<blockquote>')
check_contains('blockquote inner', md('> quote'), 'quote')

# ---- horizontal rules ----
print('\n=== Horizontal rules ===')
check('hr ---', md('---'), '<hr>')
check('hr ___', md('___'), '<hr>')
check('hr ***', md('***'), '<hr>')

# ---- lists ----
print('\n=== Lists ===')
check_contains('unordered', md('- a\n- b'), '<ul>')
check_contains('ordered', md('1. a\n2. b'), '<ol>')
check_contains('list item', md('- a'), '<li>')

# ---- escapes ----
print('\n=== Escapes ===')
check_contains('escape star', md(r'\*not em\*'), '*not em*')

# ---- hard line break ----
print('\n=== Line breaks ===')
# Two trailing spaces
check('hard break', md('line1  \nline2'), '<p>line1<br>\nline2</p>')

# ---- AST renderer ----
print('\n=== AST Renderer ===')
md_ast = Markdown(renderer='ast')
result = md_ast('# Hello')
check('ast is list', isinstance(result, list), True)
check('ast heading type', result[0]['type'], 'heading')
check('ast heading level', result[0]['level'], 1)

# ---- Strikethrough plugin ----
print('\n=== Strikethrough plugin ===')
md_s = Markdown(plugins=['strikethrough'])
check_contains('strikethrough', md_s('~~deleted~~'), '<del>deleted</del>')

# ---- Table plugin ----
print('\n=== Table plugin ===')
md_t = Markdown(plugins=['table'])
table_input = '| a | b |\n| - | - |\n| 1 | 2 |'
check_contains('table', md_t(table_input), '<table>')
check_contains('table th', md_t(table_input), '<th>a</th>')

# ---- Task list plugin ----
print('\n=== Task list plugin ===')
md_tl = Markdown(plugins=['task_list'])
check_contains('task list', md_tl('- [ ] todo'), '<input type="checkbox"')
check_contains('task list checked', md_tl('- [x] done'), 'checked')

# ---- Unknown plugin ----
print('\n=== Unknown plugin ===')
try:
    Markdown(plugins=['nonexistent'])
    print('  FAIL: should have raised ValueError')
    failed += 1
except ValueError:
    print('  PASS: raises ValueError for unknown plugin')
    passed += 1

# ---- Malformed recovery ----
print('\n=== Malformed recovery ===')
check_contains('unclosed em literal', md('*unclosed'), '*unclosed')
check_contains('unclosed strong literal', md('**unclosed'), '**unclosed')
check_contains('unclosed code span', md('`unclosed'), '`unclosed')

# ---- Parse isolation ----
print('\n=== Parse isolation ===')
md_iso = Markdown()
md_iso('*unclosed')
result2 = md_iso('**hello**')
check_contains('parse isolation', result2, '<strong>hello</strong>')

# ---- Complex documents ----
print('\n=== Complex ===')
complex_doc = """# Title

This is a **bold** and *italic* paragraph with `code`.

## Section

- Item 1
- Item 2 with `code`

> A blockquote with **bold**

```
code block
```

---

End."""
html = md(complex_doc)
check_contains('complex h1', html, '<h1>Title</h1>')
check_contains('complex strong', html, '<strong>bold</strong>')
check_contains('complex em', html, '<em>italic</em>')
check_contains('complex hr', html, '<hr>')
check_contains('complex blockquote', html, '<blockquote>')

# ---- Empty input ----
print('\n=== Edge cases ===')
check('empty string', md(''), '')
check('only blanks', md('  \n  \n'), '')

print(f'\n{"="*50}')
print(f'Results: {passed} passed, {failed} failed ({passed+failed} total)')
if failed:
    sys.exit(1)
