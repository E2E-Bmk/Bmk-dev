from __future__ import annotations

import textwrap

import pytest
from click.testing import CliRunner

from lektor.builder import Builder
from lektor.environment import Environment
from lektor.project import Project


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


def write_text(root, relative_path, content):
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


@pytest.fixture
def project_data(tmp_path):
    root = tmp_path / "site"
    write_text(
        root,
        "Demo.lektorproject",
        """
        [project]
        name = Demo Site
        output_path = build-output
        url = https://example.test/docs/
        excluded_assets = *.tmp
        included_assets = _included.txt

        [alternatives.en]
        name = English
        primary = yes
        locale = en_US

        [alternatives.fr]
        name = French
        url_prefix = /fr/
        locale = fr
        """,
    )
    write_text(
        root,
        "models/page.ini",
        """
        [model]
        name = Page
        label = {{ this.title }}

        [fields.title]
        type = string

        [fields.body]
        type = markdown

        [fields.count]
        type = integer

        [fields.featured]
        type = boolean

        [fields.tags]
        type = strings

        [fields.published]
        type = date

        [fields.when]
        type = datetime
        """,
    )
    write_text(
        root,
        "models/blog.ini",
        """
        [model]
        name = Blog
        label = {{ this.title }}

        [children]
        model = blog-post
        order_by = -pub_date, title

        [pagination]
        enabled = yes
        per_page = 1

        [fields.title]
        type = string
        """,
    )
    write_text(
        root,
        "models/blog-post.ini",
        """
        [model]
        name = Blog Post
        label = {{ this.title }}

        [fields.title]
        type = string

        [fields.pub_date]
        type = date

        [fields.summary]
        type = text

        [fields.body]
        type = markdown

        [fields.tags]
        type = strings
        """,
    )
    write_text(
        root,
        "content/contents.lr",
        """
        _model: page
        ---
        title: Home
        ---
        body: Welcome to **Lektor**.
        ---
        count: 7
        ---
        featured: yes
        ---
        tags:
        alpha
        beta
        ---
        published: 2024-01-02
        ---
        when: 2024-01-02 03:04:05
        """,
    )
    write_text(
        root,
        "content/contents+fr.lr",
        """
        _model: page
        ---
        title: Accueil
        ---
        body: Bonjour.
        """,
    )
    write_text(
        root,
        "content/about/contents.lr",
        """
        _model: page
        ---
        title: About
        ---
        body: About this site.
        """,
    )
    write_text(
        root,
        "content/about/contents+fr.lr",
        """
        _model: page
        ---
        title: A propos
        ---
        body: A propos de ce site.
        """,
    )
    write_text(
        root,
        "content/blog/contents.lr",
        """
        _model: blog
        ---
        title: Blog
        """,
    )
    write_text(
        root,
        "content/blog/first/contents.lr",
        """
        _model: blog-post
        ---
        title: First Post
        ---
        pub_date: 2024-01-02
        ---
        summary: The first summary.
        ---
        body: First **post**.
        ---
        tags:
        python
        lektor
        """,
    )
    write_text(
        root,
        "content/blog/second/contents.lr",
        """
        _model: blog-post
        ---
        title: Second Post
        ---
        pub_date: 2024-01-03
        ---
        summary: The second summary.
        ---
        body: Second post.
        ---
        tags:
        python
        static
        """,
    )
    write_text(
        root,
        "content/hidden/contents.lr",
        """
        _model: page
        ---
        _hidden: yes
        ---
        title: Hidden Page
        """,
    )
    write_text(
        root,
        "content/undiscoverable/contents.lr",
        """
        _model: page
        ---
        _discoverable: no
        ---
        title: Secret Page
        """,
    )
    write_text(root, "content/notes.txt", "plain attachment\n")
    write_text(root, "content/about/guide.txt", "about attachment\n")
    write_text(
        root,
        "templates/page.html",
        """
        <title>{{ this.title }}</title>
        <h1>{{ this.title }}</h1>
        <div class="body">{{ this.body }}</div>
        <p class="count">{{ this.count }}</p>
        <a class="about" href="{{ this.url_to('/about') }}">About</a>
        """,
    )
    write_text(
        root,
        "templates/blog.html",
        """
        <h1>{{ this.title }}</h1>
        <ul>
        {% for post in this.pagination.items %}
          <li>{{ post.title }}|{{ post.url_path }}</li>
        {% endfor %}
        </ul>
        {% if this.pagination.has_next %}NEXT{% endif %}
        """,
    )
    write_text(
        root,
        "templates/blog-post.html",
        """
        <h1>{{ this.title }}</h1>
        <p>{{ this.pub_date }}</p>
        <div class="body">{{ this.body }}</div>
        """,
    )
    write_text(root, "assets/static/site.css", "body { color: red; }\n")
    write_text(root, "assets/keep.txt", "kept asset\n")
    write_text(root, "assets/_included.txt", "included asset\n")
    write_text(root, "assets/ignored.tmp", "ignored asset\n")
    write_text(root, "assets/.hidden", "hidden asset\n")
    return root


@pytest.fixture
def project(project_data):
    return Project.from_path(project_data)


@pytest.fixture
def env(project):
    return Environment(project, load_plugins=False)


@pytest.fixture
def pad(env):
    return env.new_pad()


@pytest.fixture
def builder(pad, tmp_path):
    output_path = tmp_path / "direct-output"
    output_path.mkdir()
    return Builder(pad, output_path)


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def cli_project_file(project_data):
    return project_data / "Demo.lektorproject"
