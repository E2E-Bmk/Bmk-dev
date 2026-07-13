import sys
sys.path.insert(0, r"G\:research\01_agents\swe-e2e\Bmk-dev\runs\minitemplate-realrepo-submit\solution-openhands-deepseek-v4-pro-v2-001")
from minitemplate import Environment, Template, TemplateSyntaxError, TemplateNotFound

# Test 1: Basic PRD example
print("=== Test 1: PRD Example ===")
env = Environment(
    {
        "base.html": "Hello {% block body %}{{ name }}{% endblock %}",
        "page.html": '{% extends "base.html" %}{% block body %}{{ name|upper }}{% endblock %}',
    },
    globals={"site_name": "Docs"},
)
result1 = env.get_template("page.html").render(name="Ada")
print("Result:", repr(result1))
assert result1 == "Hello ADA", "Expected 'Hello ADA', got " + repr(result1)

result1b = Template("Hi {{ name }}").render(name="Bob")
print("Standalone:", repr(result1b))
assert result1b == "Hi Bob", "Expected 'Hi Bob', got " + repr(result1b)

# Test 2: Variables and filters
print()
print("=== Test 2: Variables and Filters ===")
t = Template("{{ name }} {{ name|upper }} {{ name|lower }} {{ name|title }}")
print(t.render(name="Ada Lovelace"))

t2 = Template('{{ missing|default("guest") }}')
print("Default:", repr(t2.render()))
assert t2.render() == "guest", "Expected 'guest', got " + repr(t2.render())

t3 = Template("{{ items|length }}")
print("Length:", repr(t3.render(items=[1,2,3])))
assert t3.render(items=[1,2,3]) == "3"

# Test 3: Conditionals
print()
print("=== Test 3: Conditionals ===")
t4 = Template("{% if x %}yes{% else %}no{% endif %}")
print("if True:", repr(t4.render(x=True)))
print("if False:", repr(t4.render(x=False)))

t5 = Template("{% if user is defined %}Hello {{ user }}{% else %}Guest{% endif %}")
print("defined:", repr(t5.render(user="Ada")))
print("undefined:", repr(t5.render()))

# Test 4: Loops
print()
print("=== Test 4: Loops ===")
t6 = Template("{% for item in items %}{{ item }},{% else %}empty{% endfor %}")
print("loop:", repr(t6.render(items=[1,2,3])))
print("empty:", repr(t6.render(items=[])))

# Test 5: With
print()
print("=== Test 5: With ===")
t7 = Template('{% with label = "draft" %}{{ label }}{% endwith %}')
print("with:", repr(t7.render()))

# Test 6: Inheritance
print()
print("=== Test 6: Inheritance ===")
env2 = Environment({
    "base.html": "<title>{% block title %}Default{% endblock %}</title>",
    "child.html": '{% extends "base.html" %}{% block title %}My Title{% endblock %}',
})
print("child:", repr(env2.get_template("child.html").render()))

# Test 7: Include
print()
print("=== Test 7: Include ===")
env3 = Environment({
    "page.html": 'Before {% include "nav.html" %} After',
    "nav.html": "[NAV: {{ section }}]",
})
print("include:", repr(env3.get_template("page.html").render(section="home")))

# Test 8: Macros
print()
print("=== Test 8: Macros ===")
t8 = Template('{% macro input(value) %}<input value="{{ value }}">{% endmacro %}{{ input("test") }}')
print("macro:", repr(t8.render()))

# Test 9: Import
print()
print("=== Test 9: Import ===")
env4 = Environment({
    "page.html": '{% import "forms.html" as forms %}{{ forms.input("test") }}',
    "forms.html": '{% macro input(value) %}<input value="{{ value }}">{% endmacro %}',
})
print("import:", repr(env4.get_template("page.html").render()))

print()
print("=== All tests passed! ===")
