# Spec2Repo oracle - atomic tests for peewee-fullrepro-001
import json
import os
import subprocess
import sys
import datetime

import pytest
from peewee import *
from playhouse.db_url import connect as url_connect, parse as url_parse
from playhouse.migrate import SchemaMigrator, migrate
from playhouse.reflection import Introspector, generate_models
from playhouse.shortcuts import dict_to_model, model_to_dict, update_model_from_dict


def memory_db(**kwargs):
    kwargs.setdefault('pragmas', {'foreign_keys': 1})
    return SqliteDatabase(':memory:', **kwargs)


def create_bound(db, models):
    db.bind(models, bind_refs=False, bind_backrefs=False)
    db.connect()
    db.create_tables(models)


def close_db(db):
    if not db.is_closed():
        db.close()


def test_atomic_auto_field_added_to_model_without_primary_key():
    """Verifies: PEEWEE-MODEL-002, PEEWEE-MODEL-005"""
    class Widget(Model):
        name = TextField()
        class Meta:
            legacy_table_names = False
    assert isinstance(Widget._meta.primary_key, AutoField)
    assert Widget._meta.primary_key.name == 'id'
    assert 'id' in Widget._meta.fields


def test_atomic_field_descriptor_stores_declared_values_on_instance():
    """Verifies: PEEWEE-MODEL-001, PEEWEE-MODEL-010"""
    class Widget(Model):
        name = TextField(help_text='visible label', verbose_name='Name')
        class Meta:
            legacy_table_names = False
    item = Widget(name='alpha')
    assert item.name == 'alpha'
    assert Widget._meta.fields['name'].help_text == 'visible label'
    assert Widget._meta.fields['name'].verbose_name == 'Name'


def test_atomic_callable_default_runs_for_each_instance():
    """Verifies: PEEWEE-MODEL-011"""
    calls = []
    def next_value():
        calls.append(len(calls) + 1)
        return calls[-1]
    class Counter(Model):
        value = IntegerField(default=next_value)
        class Meta:
            legacy_table_names = False
    first = Counter(); second = Counter()
    assert (first.value, second.value, calls) == (1, 2, [1, 2])


def test_atomic_literal_default_is_assigned_to_new_instance():
    """Verifies: PEEWEE-MODEL-011"""
    class Flag(Model):
        enabled = BooleanField(default=True)
        class Meta:
            legacy_table_names = False
    assert Flag().enabled is True


def test_atomic_choices_are_metadata_and_do_not_validate_assignment():
    """Verifies: PEEWEE-MODEL-012"""
    choices = (('draft', 'Draft'), ('published', 'Published'))
    class Article(Model):
        status = TextField(choices=choices)
        class Meta:
            legacy_table_names = False
    row = Article(status='other')
    assert row.status == 'other'
    assert Article._meta.fields['status'].choices == choices


def test_atomic_column_name_is_kept_in_field_metadata():
    """Verifies: PEEWEE-MODEL-010"""
    class Article(Model):
        title = TextField(column_name='article_title')
        class Meta:
            legacy_table_names = False
    field = Article._meta.fields['title']
    assert field.column_name == 'article_title'


def test_atomic_explicit_table_name_overrides_default():
    """Verifies: PEEWEE-MODEL-006"""
    class UserAccount(Model):
        username = TextField()
        class Meta:
            table_name = 'app_user'
    assert UserAccount._meta.table_name == 'app_user'


def test_atomic_table_function_derives_table_name():
    """Verifies: PEEWEE-MODEL-007"""
    class LineItem(Model):
        sku = TextField()
        class Meta:
            table_function = lambda cls: 'tbl_' + cls.__name__.lower()
    assert LineItem._meta.table_name == 'tbl_lineitem'


def test_atomic_legacy_and_modern_table_name_rules_differ():
    """Verifies: PEEWEE-MODEL-008"""
    class APIResponseLegacy(Model):
        class Meta:
            legacy_table_names = True
    class APIResponseModern(Model):
        class Meta:
            legacy_table_names = False
    assert APIResponseLegacy._meta.table_name == 'apiresponselegacy'
    assert APIResponseModern._meta.table_name == 'api_response_modern'


def test_atomic_inherited_model_fields_and_meta_options_are_available():
    """Verifies: PEEWEE-MODEL-003"""
    db = memory_db()
    class Base(Model):
        base_name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Child(Base):
        child_name = TextField()
    assert set(Child._meta.fields) >= {'id', 'base_name', 'child_name'}
    assert Child._meta.database is db
    assert Child._meta.table_name == 'child'


def test_atomic_composite_key_records_primary_key_fields():
    """Verifies: PEEWEE-MODEL-024"""
    class Enrollment(Model):
        student = IntegerField()
        course = IntegerField()
        class Meta:
            primary_key = CompositeKey('student', 'course')
    assert Enrollment._meta.primary_key.field_names == ('student', 'course')


def test_atomic_foreign_key_default_column_name_appends_id():
    """Verifies: PEEWEE-MODEL-018"""
    class User(Model):
        username = TextField()
        class Meta:
            legacy_table_names = False
    class Tweet(Model):
        user = ForeignKeyField(User)
        class Meta:
            legacy_table_names = False
    assert Tweet._meta.fields['user'].column_name == 'user_id'


def test_atomic_self_referential_foreign_key_resolves_model_class():
    """Verifies: PEEWEE-MODEL-023"""
    class Category(Model):
        parent = ForeignKeyField('self', null=True, backref='children')
        name = TextField()
        class Meta:
            legacy_table_names = False
    assert Category._meta.fields['parent'].rel_model is Category


def test_atomic_deferred_foreign_key_resolves_after_target_defined():
    """Verifies: PEEWEE-MODEL-025"""
    class Booking(Model):
        event = DeferredForeignKey('Event', backref='bookings')
        class Meta:
            legacy_table_names = False
    class Event(Model):
        name = TextField()
        class Meta:
            legacy_table_names = False
    assert Booking._meta.fields['event'].rel_model is Event


def test_atomic_db_url_parse_converts_query_parameter_types():
    """Verifies: PEEWEE-SCHEMA-024"""
    parsed = url_parse('sqlite:///data.db?timeout=2&flag=true&pi=3.5&empty=null')
    assert parsed == {'database': 'data.db', 'timeout': 2, 'flag': True, 'pi': 3.5, 'empty': None}


def test_atomic_db_url_connect_merges_explicit_parameters():
    """Verifies: PEEWEE-SCHEMA-025"""
    db = url_connect('sqlite:///:memory:?timeout=1', timeout=7)
    try:
        assert isinstance(db, SqliteDatabase)
        db.connect()
        assert db.execute_sql('pragma busy_timeout').fetchone() == (7000,)
    finally:
        close_db(db)


def test_atomic_db_url_unknown_scheme_raises_runtime_error():
    """Verifies: PEEWEE-SCHEMA-026"""
    with pytest.raises(RuntimeError):
        url_connect('unknown:///database')


def test_atomic_deferred_database_requires_init_before_use():
    """Verifies: PEEWEE-DB-002, PEEWEE-DB-004"""
    db = SqliteDatabase(None)
    with pytest.raises(InterfaceError):
        db.connect()
    db.init(':memory:')
    assert db.connect() is True
    close_db(db)


def test_atomic_database_proxy_rejects_use_before_initialize():
    """Verifies: PEEWEE-DB-003, PEEWEE-DB-004"""
    proxy = DatabaseProxy()
    with pytest.raises(AttributeError):
        proxy.connect()
    db = memory_db()
    proxy.initialize(db)
    assert proxy.obj is db


def test_atomic_connection_lifecycle_return_values():
    """Verifies: PEEWEE-DB-006, PEEWEE-DB-008, PEEWEE-DB-009"""
    db = memory_db()
    assert db.is_closed() is True
    assert db.connect() is True
    assert db.is_closed() is False
    assert db.close() is True
    assert db.close() is False


def test_atomic_connect_reuse_reports_existing_connection():
    """Verifies: PEEWEE-DB-007"""
    db = memory_db()
    try:
        assert db.connect() is True
        assert db.connect(reuse_if_open=True) is False
        with pytest.raises(OperationalError):
            db.connect()
    finally:
        close_db(db)


def test_atomic_database_context_manager_closes_after_success():
    """Verifies: PEEWEE-DB-012"""
    db = memory_db()
    with db:
        assert db.is_closed() is False
    assert db.is_closed() is True


def test_atomic_connection_context_does_not_start_transaction():
    """Verifies: PEEWEE-DB-013"""
    db = memory_db()
    with db.connection_context():
        assert db.is_closed() is False
        assert db.transaction_depth() == 0
    assert db.is_closed() is True


def test_atomic_many_to_many_rejects_unsaved_source_mutation():
    """Verifies: PEEWEE-MODEL-026, PEEWEE-MODEL-027"""
    db = memory_db()
    class Tag(Model):
        name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Post(Model):
        title = TextField()
        tags = ManyToManyField(Tag, backref='posts')
        class Meta:
            database = db
            legacy_table_names = False
    Through = Post.tags.get_through_model()
    try:
        create_bound(db, [Tag, Post, Through])
        with pytest.raises(ValueError):
            Post(title='draft').tags.add(Tag.create(name='x'))
    finally:
        close_db(db)


def test_atomic_model_to_dict_serializes_plain_fields():
    """Verifies: PEEWEE-JSON-012"""
    class User(Model):
        username = TextField()
        active = BooleanField(default=True)
        class Meta:
            legacy_table_names = False
    assert model_to_dict(User(username='huey')) == {'id': None, 'username': 'huey', 'active': True}


def test_atomic_dict_to_model_constructs_unsaved_instance():
    """Verifies: PEEWEE-JSON-013"""
    class User(Model):
        username = TextField()
        class Meta:
            legacy_table_names = False
    user = dict_to_model(User, {'username': 'mickey'})
    assert isinstance(user, User)
    assert user.username == 'mickey'
    assert user.get_id() is None


def test_atomic_update_model_from_dict_changes_existing_instance():
    """Verifies: PEEWEE-JSON-014"""
    class User(Model):
        username = TextField()
        active = BooleanField(default=False)
        class Meta:
            legacy_table_names = False
    user = User(username='old')
    update_model_from_dict(user, {'username': 'new', 'active': True})
    assert (user.username, user.active) == ('new', True)


def test_atomic_unknown_shortcut_key_raises_when_not_ignored():
    """Verifies: PEEWEE-JSON-015"""
    class User(Model):
        username = TextField()
        class Meta:
            legacy_table_names = False
    with pytest.raises((AttributeError, KeyError)):
        dict_to_model(User, {'missing': 'value'}, ignore_unknown=False)


def test_atomic_chunked_splits_iterable_into_fixed_size_batches():
    """Verifies: PEEWEE-QUERY-031"""
    assert list(chunked(range(5), 2)) == [[0, 1], [2, 3], [4]]


def test_atomic_query_without_bound_database_raises_interface_error():
    """Verifies: PEEWEE-MODEL-009, PEEWEE-QUERY-020"""
    class Detached(Model):
        name = TextField()
        class Meta:
            database = None
            legacy_table_names = False
    with pytest.raises(InterfaceError):
        list(Detached.select())

# Track A stopped after atomic public-surface recovery; integration/system
# floors are intentionally routed to Track B.
