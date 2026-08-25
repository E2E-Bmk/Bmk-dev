# Spec2Repo oracle - integration tests for peewee-fullrepro-001
import os
import subprocess
import sys
import tempfile
import textwrap

import pytest
from peewee import *
from playhouse.db_url import connect as url_connect
from playhouse.migrate import SchemaMigrator, migrate
from playhouse.reflection import Introspector, generate_models
from playhouse.shortcuts import dict_to_model, model_to_dict, update_model_from_dict


def memory_db(**kwargs):
    kwargs.setdefault('pragmas', {'foreign_keys': 1})
    return SqliteDatabase(':memory:', **kwargs)


def bind_create(db, models):
    db.bind(models, bind_refs=False, bind_backrefs=False)
    db.connect()
    db.create_tables(models)


def close_db(db):
    if not db.is_closed():
        db.close()


@pytest.mark.depends_on(
    'test_atomic_foreign_key_default_column_name_appends_id',
    'test_atomic_connection_lifecycle_return_values')
def test_integration_create_tables_orders_foreign_keys_and_backref_reads_rows():
    """Verifies: PEEWEE-SCHEMA-001, PEEWEE-MODEL-020, PEEWEE-INV-002"""
    db = memory_db()
    class User(Model):
        username = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Tweet(Model):
        user = ForeignKeyField(User, backref='tweets')
        content = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        db.connect()
        db.create_tables([Tweet, User])
        user = User.create(username='charlie')
        Tweet.create(user=user, content='hello')
        assert set(db.get_tables()) == {'user', 'tweet'}
        assert [tweet.content for tweet in user.tweets] == ['hello']
    finally:
        close_db(db)


@pytest.mark.depends_on(
    'test_atomic_foreign_key_default_column_name_appends_id',
    'test_atomic_field_descriptor_stores_declared_values_on_instance')
def test_integration_join_reconstructs_selected_related_model_graph():
    """Verifies: PEEWEE-QUERY-021, PEEWEE-QUERY-022, PEEWEE-INV-002"""
    db = memory_db()
    class User(Model):
        username = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Tweet(Model):
        user = ForeignKeyField(User, backref='tweets')
        content = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [User, Tweet])
        user = User.create(username='huey')
        Tweet.create(user=user, content='join works')
        row = (Tweet
               .select(Tweet, User)
               .join(User)
               .where(Tweet.content == 'join works')
               .get())
        assert row.user.username == 'huey'
        assert row.user.id == user.id
    finally:
        close_db(db)


@pytest.mark.depends_on(
    'test_atomic_foreign_key_default_column_name_appends_id',
    'test_atomic_connection_lifecycle_return_values')
def test_integration_prefetch_associates_children_with_parent_instances():
    """Verifies: PEEWEE-QUERY-023, PEEWEE-MODEL-020, PEEWEE-INV-002"""
    db = memory_db()
    class User(Model):
        username = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Tweet(Model):
        user = ForeignKeyField(User, backref='tweets')
        content = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [User, Tweet])
        user = User.create(username='mickey')
        Tweet.insert_many([
            {'user': user.id, 'content': 'one'},
            {'user': user.id, 'content': 'two'},
        ]).execute()
        loaded = list(prefetch(User.select(), Tweet.select()))
        assert [(u.username, [t.content for t in u.tweets]) for u in loaded] == [
            ('mickey', ['one', 'two'])
        ]
    finally:
        close_db(db)


@pytest.mark.depends_on(
    'test_atomic_field_descriptor_stores_declared_values_on_instance',
    'test_atomic_connection_lifecycle_return_values')
def test_integration_row_adapters_return_consistent_inserted_values():
    """Verifies: PEEWEE-QUERY-004, PEEWEE-QUERY-005, PEEWEE-INV-001"""
    db = memory_db()
    class Note(Model):
        text = TextField()
        priority = IntegerField(default=1)
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Note])
        Note.insert_many([
            {'text': 'alpha', 'priority': 2},
            {'text': 'beta', 'priority': 5},
        ]).execute()
        query = Note.select().order_by(Note.priority)
        assert [note.text for note in query] == ['alpha', 'beta']
        assert list(query.dicts()) == [
            {'id': 1, 'text': 'alpha', 'priority': 2},
            {'id': 2, 'text': 'beta', 'priority': 5},
        ]
        assert list(query.tuples()) == [(1, 'alpha', 2), (2, 'beta', 5)]
        assert [row.text for row in query.namedtuples()] == ['alpha', 'beta']
    finally:
        close_db(db)


@pytest.mark.depends_on(
    'test_atomic_field_descriptor_stores_declared_values_on_instance',
    'test_atomic_query_without_bound_database_raises_interface_error')
def test_integration_single_row_retrieval_variants_share_primary_key_lookup():
    """Verifies: PEEWEE-QUERY-007, PEEWEE-QUERY-008, PEEWEE-QUERY-009, PEEWEE-QUERY-010"""
    db = memory_db()
    class User(Model):
        username = TextField(unique=True)
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [User])
        user = User.create(username='nugget')
        assert User.get(User.username == 'nugget').id == user.id
        assert User.get_by_id(user.id).username == 'nugget'
        assert User[user.id].username == 'nugget'
        assert User.get_or_none(User.username == 'missing') is None
        assert User.select().where(User.username == 'missing').first() is None
        with pytest.raises(DoesNotExist):
            User.get(User.username == 'missing')
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_chunked_splits_iterable_into_fixed_size_batches')
def test_integration_filtering_sorting_paginating_and_counting_rows():
    """Verifies: PEEWEE-QUERY-011, PEEWEE-QUERY-012, PEEWEE-QUERY-015, PEEWEE-QUERY-016, PEEWEE-QUERY-017"""
    db = memory_db()
    class Item(Model):
        name = TextField()
        qty = IntegerField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Item])
        Item.insert_many([
            {'name': 'alpha', 'qty': 2},
            {'name': 'beta', 'qty': 5},
            {'name': 'gamma', 'qty': 8},
            {'name': 'delta', 'qty': 3},
        ]).execute()
        query = (Item
                 .select()
                 .where((Item.qty.between(3, 8)) & (Item.name.contains('a')))
                 .order_by(Item.qty.desc()))
        assert [item.name for item in query] == ['gamma', 'beta', 'delta']
        assert query.count() == 3
        assert [item.name for item in query.paginate(2, 2)] == ['delta']
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_aggregate_group_having_and_scalar_results():
    """Verifies: PEEWEE-QUERY-018, PEEWEE-QUERY-019"""
    db = memory_db()
    class Sale(Model):
        region = TextField()
        amount = IntegerField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Sale])
        Sale.insert_many([
            {'region': 'east', 'amount': 4},
            {'region': 'east', 'amount': 7},
            {'region': 'west', 'amount': 2},
        ]).execute()
        total = fn.SUM(Sale.amount).alias('total')
        rows = (Sale
                .select(Sale.region, total)
                .group_by(Sale.region)
                .having(fn.SUM(Sale.amount) > 5)
                .order_by(Sale.region)
                .dicts())
        assert list(rows) == [{'region': 'east', 'total': 11}]
        assert Sale.select(fn.COUNT(Sale.id), fn.MAX(Sale.amount)).scalar(as_tuple=True) == (3, 7)
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_insert_many_update_delete_return_affected_counts():
    """Verifies: PEEWEE-QUERY-027, PEEWEE-QUERY-028"""
    db = memory_db()
    class Task(Model):
        title = TextField()
        done = BooleanField(default=False)
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Task])
        Task.insert_many([{'title': 'a'}, {'title': 'b'}, {'title': 'c'}]).execute()
        assert Task.update(done=True).where(Task.title << ['a', 'b']).execute() == 2
        assert Task.select().where(Task.done == True).count() == 2
        assert Task.delete().where(Task.done == False).execute() == 1
        assert [task.title for task in Task.select().order_by(Task.title)] == ['a', 'b']
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_sqlite_conflict_update_uses_excluded_values():
    """Verifies: PEEWEE-QUERY-029, PEEWEE-QUERY-030, PEEWEE-INV-008"""
    db = memory_db()
    class Account(Model):
        username = TextField(unique=True)
        login_count = IntegerField(default=0)
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Account])
        Account.create(username='huey', login_count=1)
        (Account
         .insert(username='huey', login_count=3)
         .on_conflict(
             conflict_target=[Account.username],
             update={Account.login_count: Account.login_count + EXCLUDED.login_count})
         .execute())
        assert Account.get(Account.username == 'huey').login_count == 4
        with pytest.raises(IntegrityError):
            Account.create(username='huey', login_count=0)
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_table_query_builder_writes_reads_and_deletes_rows():
    """Verifies: PEEWEE-QUERY-031, PEEWEE-QUERY-032"""
    db = memory_db()
    people = Table('people')
    try:
        db.connect()
        db.execute_sql('CREATE TABLE people (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)')
        people.insert(name='alice', age=30).execute(db)
        people.insert(name='bob', age=41).execute(db)
        people.update(age=42).where(people.c.name == 'bob').execute(db)
        rows = list(people.select(people.c.name, people.c.age).order_by(people.c.name).tuples().execute(db))
        assert rows == [('alice', 30), ('bob', 42)]
        assert people.delete().where(people.c.age < 40).execute(db) == 1
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_case_cast_sql_and_value_expressions_execute_together():
    """Verifies: PEEWEE-QUERY-031, PEEWEE-QUERY-034"""
    db = memory_db()
    class Score(Model):
        name = TextField()
        points = IntegerField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Score])
        Score.insert_many([
            {'name': 'low', 'points': 3},
            {'name': 'high', 'points': 9},
        ]).execute()
        label = Case(None, ((Score.points >= 5, Value('pass')),), Value('retry')).alias('label')
        rows = (Score
                .select(Score.name, Cast(Score.points, 'TEXT').alias('points_text'), label)
                .order_by(SQL('points_text').desc())
                .dicts())
        assert list(rows) == [
            {'name': 'high', 'points_text': '9', 'label': 'pass'},
            {'name': 'low', 'points_text': '3', 'label': 'retry'},
        ]
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_database_context_manager_closes_after_success')
def test_integration_database_context_rolls_back_exception_and_closes():
    """Verifies: PEEWEE-DB-012, PEEWEE-INV-003"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SqliteDatabase(os.path.join(tmpdir, 'context.db'))
        class Entry(Model):
            title = TextField()
            class Meta:
                database = db
                legacy_table_names = False
        db.connect()
        db.create_tables([Entry])
        db.close()
        with pytest.raises(RuntimeError):
            with db:
                Entry.create(title='rolled back')
                raise RuntimeError('boom')
        assert db.is_closed() is True
        with db.connection_context():
            assert Entry.select().count() == 0


@pytest.mark.depends_on('test_atomic_connection_context_does_not_start_transaction')
def test_integration_nested_atomic_uses_savepoint_for_inner_rollback():
    """Verifies: PEEWEE-DB-014, PEEWEE-DB-015, PEEWEE-INV-003"""
    db = memory_db()
    class Event(Model):
        name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Event])
        with db.atomic():
            Event.create(name='outer')
            with pytest.raises(ValueError):
                with db.atomic():
                    Event.create(name='inner')
                    raise ValueError('rollback inner')
            Event.create(name='after')
        assert [event.name for event in Event.select().order_by(Event.id)] == ['outer', 'after']
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_context_does_not_start_transaction')
def test_integration_manual_atomic_commit_starts_new_transaction_segment():
    """Verifies: PEEWEE-DB-014, PEEWEE-DB-016"""
    db = memory_db()
    class Item(Model):
        name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Item])
        with pytest.raises(RuntimeError):
            with db.atomic() as txn:
                Item.create(name='kept')
                txn.commit()
                Item.create(name='rolled back')
                raise RuntimeError('rollback remaining segment')
        assert [item.name for item in Item.select()] == ['kept']
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_pragmas_and_shortcut_properties_share_sqlite_state():
    """Verifies: PEEWEE-DB-022, PEEWEE-DB-023"""
    db = memory_db()
    try:
        db.connect()
        assert db.pragma('foreign_keys') == 1
        db.foreign_keys = 0
        assert db.pragma('foreign_keys') == 0
        db.pragma('cache_size', -2000)
        assert db.cache_size == -2000
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_sqlite_registered_function_and_collation_affect_queries():
    """Verifies: PEEWEE-DB-024"""
    db = memory_db()
    class Word(Model):
        value = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    db.register_function(lambda value: value[::-1], 'reverse_text', 1)
    db.register_collation(lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()), 'casefold')
    try:
        bind_create(db, [Word])
        Word.insert_many([{'value': 'Banana'}, {'value': 'apple'}]).execute()
        values = [row.value for row in Word.select().order_by(Word.value.collate('casefold'))]
        assert values == ['apple', 'Banana']
        assert Word.select(fn.reverse_text(Word.value)).where(Word.value == 'apple').scalar() == 'elppa'
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_explicit_table_name_overrides_default')
def test_integration_schema_safe_create_and_drop_semantics_are_observable():
    """Verifies: PEEWEE-SCHEMA-002, PEEWEE-SCHEMA-003, PEEWEE-SCHEMA-004"""
    db = memory_db()
    class Widget(Model):
        name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        db.connect()
        Widget.create_table()
        Widget.create_table()
        assert Widget.table_exists() is True
        with pytest.raises(OperationalError):
            Widget.create_table(safe=False)
        Widget.drop_table()
        assert Widget.table_exists() is False
        Widget.drop_table()
        with pytest.raises(OperationalError):
            Widget.drop_table(safe=False)
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_foreign_key_default_column_name_appends_id')
def test_integration_introspection_reports_columns_indexes_and_foreign_keys():
    """Verifies: PEEWEE-SCHEMA-006, PEEWEE-SCHEMA-008, PEEWEE-SCHEMA-009, PEEWEE-SCHEMA-010, PEEWEE-INV-001"""
    db = memory_db()
    class User(Model):
        username = TextField(unique=True)
        class Meta:
            database = db
            legacy_table_names = False
    class Tweet(Model):
        user = ForeignKeyField(User, backref='tweets')
        content = TextField(index=True)
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [User, Tweet])
        assert set(db.get_tables()) == {'user', 'tweet'}
        column_names = {column.name for column in db.get_columns('tweet')}
        index_columns = {tuple(index.columns) for index in db.get_indexes('tweet')}
        fk_rows = db.get_foreign_keys('tweet')
        assert {'id', 'user_id', 'content'} <= column_names
        assert ('content',) in index_columns
        assert [(fk.column, fk.dest_table, fk.dest_column) for fk in fk_rows] == [('user_id', 'user', 'id')]
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_foreign_key_default_column_name_appends_id')
def test_integration_reflection_generates_model_classes_for_selected_tables():
    """Verifies: PEEWEE-SCHEMA-012, PEEWEE-SCHEMA-013, PEEWEE-SCHEMA-014, PEEWEE-SCHEMA-015"""
    db = memory_db()
    class Category(Model):
        name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Product(Model):
        category = ForeignKeyField(Category, backref='products')
        sku = TextField(unique=True)
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Category, Product])
        Category.create(name='tools')
        models = generate_models(db, table_names=['category'])
        RefCategory = models['category']
        assert set(models) == {'category'}
        assert RefCategory._meta.table_name == 'category'
        assert [row.name for row in RefCategory.select()] == ['tools']
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_reflection_can_include_sqlite_views():
    """Verifies: PEEWEE-SCHEMA-007, PEEWEE-SCHEMA-016"""
    db = memory_db()
    try:
        db.connect()
        db.execute_sql('CREATE TABLE sale (id INTEGER PRIMARY KEY, amount INTEGER)')
        db.execute_sql('INSERT INTO sale (amount) VALUES (3), (8)')
        db.execute_sql('CREATE VIEW large_sale AS SELECT id, amount FROM sale WHERE amount > 5')
        view_names = [view.name for view in db.get_views()]
        models = Introspector.from_database(db).generate_models(include_views=True)
        assert view_names == ['large_sale']
        assert 'large_sale' in models
        assert [row.amount for row in models['large_sale'].select()] == [8]
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_migration_add_column_is_visible_to_introspection_reflection_and_queries():
    """Verifies: PEEWEE-SCHEMA-019, PEEWEE-SCHEMA-020, PEEWEE-SCHEMA-021, PEEWEE-SCHEMA-022, PEEWEE-INV-004"""
    db = memory_db()
    class Product(Model):
        sku = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Product])
        Product.create(sku='hammer')
        migrator = SchemaMigrator.from_database(db)
        migrate(migrator.add_column('product', 'active', BooleanField(default=True)))
        columns = {column.name for column in db.get_columns('product')}
        RefProduct = generate_models(db)['product']
        assert 'active' in columns
        assert [row.active for row in RefProduct.select()] == [True]
        assert db.execute_sql('SELECT active FROM product WHERE sku = ?', ('hammer',)).fetchone() == (1,)
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_migration_rename_column_updates_schema_and_sql_access():
    """Verifies: PEEWEE-SCHEMA-020, PEEWEE-SCHEMA-021, PEEWEE-INV-004"""
    db = memory_db()
    class Product(Model):
        sku = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Product])
        Product.create(sku='saw')
        migrator = SchemaMigrator.from_database(db)
        migrate(migrator.rename_column('product', 'sku', 'code'))
        columns = {column.name for column in db.get_columns('product')}
        assert 'code' in columns
        assert db.execute_sql('SELECT code FROM product').fetchall() == [('saw',)]
        assert 'code' in generate_models(db)['product']._meta.fields
    finally:
        close_db(db)


@pytest.mark.depends_on(
    'test_atomic_connection_lifecycle_return_values',
    'test_atomic_explicit_table_name_overrides_default')
def test_integration_bind_ctx_switches_schema_queries_reflection_and_restores_binding():
    """Verifies: PEEWEE-DB-005, PEEWEE-INV-007"""
    first = memory_db()
    second = memory_db()
    class Entry(Model):
        label = TextField()
        class Meta:
            database = first
            legacy_table_names = False
    try:
        bind_create(first, [Entry])
        Entry.create(label='first')
        with second.bind_ctx([Entry], bind_refs=False, bind_backrefs=False):
            second.connect()
            second.create_tables([Entry])
            Entry.create(label='second')
            assert [row.label for row in Entry.select()] == ['second']
            assert 'entry' in generate_models(second)
        assert [row.label for row in Entry.select()] == ['first']
    finally:
        close_db(first)
        close_db(second)


@pytest.mark.depends_on('test_atomic_db_url_connect_merges_explicit_parameters')
def test_system_db_url_file_reflection_and_migration_share_database_state():
    """Verifies: PEEWEE-SCHEMA-025, PEEWEE-SCHEMA-013, PEEWEE-SCHEMA-020, PEEWEE-INV-004"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'inventory.db')
        db = url_connect('sqlite:///%s' % path)
        try:
            db.connect()
            db.execute_sql('CREATE TABLE product (id INTEGER PRIMARY KEY, sku TEXT)')
            db.execute_sql("INSERT INTO product (sku) VALUES ('sprocket')")
            migrate(SchemaMigrator.from_database(db).add_column('product', 'active', BooleanField(default=True)))
            Product = generate_models(db)['product']
            assert [(row.sku, row.active) for row in Product.select()] == [('sprocket', True)]
        finally:
            close_db(db)


@pytest.mark.depends_on('test_atomic_db_url_connect_merges_explicit_parameters')
def test_system_pwiz_generates_models_for_selected_sqlite_tables():
    """Verifies: PEEWEE-SCHEMA-027, PEEWEE-SCHEMA-028, PEEWEE-INV-002"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'app.db')
        db = SqliteDatabase(path, pragmas={'foreign_keys': 1})
        try:
            db.connect()
            db.execute_sql('CREATE TABLE user (id INTEGER PRIMARY KEY, username TEXT NOT NULL)')
            db.execute_sql('CREATE TABLE tweet (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES user(id), content TEXT NOT NULL)')
        finally:
            close_db(db)
        result = subprocess.run(
            [sys.executable, '-m', 'pwiz', '-e', 'sqlite', '-i', '-t', 'user,tweet', path],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False)
        assert result.returncode == 0
        assert 'database = SqliteDatabase' in result.stdout
        assert 'class User(BaseModel):' in result.stdout
        assert 'class Tweet(BaseModel):' in result.stdout
        assert 'user = ForeignKeyField' in result.stdout


@pytest.mark.depends_on('test_atomic_db_url_connect_merges_explicit_parameters')
def test_system_pwiz_include_views_emits_model_for_sqlite_view():
    """Verifies: PEEWEE-SCHEMA-007, PEEWEE-SCHEMA-016, PEEWEE-SCHEMA-027"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'report.db')
        db = SqliteDatabase(path)
        try:
            db.connect()
            db.execute_sql('CREATE TABLE sale (id INTEGER PRIMARY KEY, amount INTEGER)')
            db.execute_sql('CREATE VIEW sale_report AS SELECT id, amount FROM sale')
        finally:
            close_db(db)
        result = subprocess.run(
            [sys.executable, '-m', 'pwiz', '-e', 'sqlite', '--views', path],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False)
        assert result.returncode == 0
        assert 'class SaleReport(BaseModel):' in result.stdout
        assert "table_name = 'sale_report'" in result.stdout


@pytest.mark.depends_on('test_atomic_db_url_unknown_scheme_raises_runtime_error')
def test_system_pwiz_invalid_engine_exits_nonzero():
    """Verifies: PEEWEE-SCHEMA-029"""
    result = subprocess.run(
        [sys.executable, '-m', 'pwiz', '-e', 'unknown', 'database-name'],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False)
    assert result.returncode != 0
    assert result.stdout or result.stderr


@pytest.mark.depends_on('test_atomic_model_to_dict_serializes_plain_fields')
def test_integration_jsonfield_round_trips_rows_paths_and_selected_aliases():
    """Verifies: PEEWEE-JSON-001, PEEWEE-JSON-002, PEEWEE-JSON-003, PEEWEE-JSON-006, PEEWEE-INV-006"""
    db = memory_db()
    class Document(Model):
        data = JSONField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Document])
        Document.create(data={'name': 'alpha', 'count': 3, 'tags': ['red', 'blue']})
        doc = Document.get(Document.data['name'] == 'alpha')
        assert doc.data == {'name': 'alpha', 'count': 3, 'tags': ['red', 'blue']}
        row = (Document
               .select(Document.data['count'].as_int().alias('count_value'))
               .dicts()
               .get())
        assert row == {'count_value': 3}
        assert Document.select().where(Document.data['tags'][1] == 'blue').count() == 1
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_model_to_dict_serializes_plain_fields')
def test_integration_jsonfield_mutation_expressions_update_visible_document_state():
    """Verifies: PEEWEE-JSON-008, PEEWEE-JSON-009, PEEWEE-JSON-010, PEEWEE-INV-006"""
    db = memory_db()
    class Document(Model):
        data = JSONField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Document])
        doc = Document.create(data={'items': ['a'], 'status': 'draft'})
        (Document
         .update(data=Document.data['items'].append('b'))
         .where(Document.id == doc.id)
         .execute())
        (Document
         .update(data=Document.data.update({'status': 'published'}))
         .where(Document.id == doc.id)
         .execute())
        refreshed = Document.get_by_id(doc.id)
        assert refreshed.data == {'items': ['a', 'b'], 'status': 'published'}
        assert Document.select(Document.data['items'].length()).scalar() == 2
    finally:
        close_db(db)


@pytest.mark.depends_on(
    'test_atomic_model_to_dict_serializes_plain_fields',
    'test_atomic_dict_to_model_constructs_unsaved_instance')
def test_integration_serialization_helpers_recurse_foreign_keys_and_backrefs():
    """Verifies: PEEWEE-JSON-012, PEEWEE-JSON-013, PEEWEE-JSON-014"""
    db = memory_db()
    class User(Model):
        username = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Tweet(Model):
        user = ForeignKeyField(User, backref='tweets')
        content = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [User, Tweet])
        user = User.create(username='charlie')
        Tweet.create(user=user, content='hello')
        data = model_to_dict(user, backrefs=True)
        assert data == {'id': user.id, 'username': 'charlie', 'tweets': [{'id': 1, 'content': 'hello'}]}
        clone = dict_to_model(User, {'username': 'mickey', 'tweets': [{'content': 'hi'}]})
        assert clone.username == 'mickey'
        assert [tweet.content for tweet in clone.tweets] == ['hi']
        update_model_from_dict(clone, {'username': 'minnie'})
        assert clone.username == 'minnie'
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_many_to_many_rejects_unsaved_source_mutation')
def test_integration_many_to_many_descriptor_adds_removes_clears_and_queries_related_rows():
    """Verifies: PEEWEE-MODEL-026"""
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
        bind_create(db, [Tag, Post, Through])
        post = Post.create(title='one')
        first = Tag.create(name='python')
        second = Tag.create(name='sqlite')
        post.tags.add([first, second])
        assert [tag.name for tag in post.tags.order_by(Tag.name)] == ['python', 'sqlite']
        post.tags.remove(first)
        assert [tag.name for tag in post.tags] == ['sqlite']
        post.tags.clear()
        assert post.tags.count() == 0
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_legacy_and_modern_table_name_rules_differ')
def test_integration_table_name_projection_matches_sql_introspection_and_reflection():
    """Verifies: PEEWEE-MODEL-006, PEEWEE-MODEL-008, PEEWEE-INV-005"""
    db = memory_db()
    class APIResponse(Model):
        code = IntegerField()
        class Meta:
            database = db
            legacy_table_names = False
    class Explicit(Model):
        value = TextField()
        class Meta:
            database = db
            table_name = 'explicit_table'
    try:
        bind_create(db, [APIResponse, Explicit])
        APIResponse.create(code=200)
        Explicit.create(value='named')
        assert set(db.get_tables()) == {'api_response', 'explicit_table'}
        models = generate_models(db)
        assert set(models) == {'api_response', 'explicit_table'}
        assert models['api_response'].select().scalar() == 1
        assert models['explicit_table'].select().dicts().get()['value'] == 'named'
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_replace_query_overwrites_existing_unique_row_state():
    """Verifies: PEEWEE-QUERY-029, PEEWEE-INV-008"""
    db = memory_db()
    class Counter(Model):
        name = TextField(unique=True)
        value = IntegerField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Counter])
        Counter.insert_many([
            {'name': 'a', 'value': 1},
            {'name': 'b', 'value': 2},
        ]).execute()
        Counter.replace(id=1, name='a', value=9).execute()
        Counter.insert(name='b', value=20).on_conflict_ignore().execute()
        assert [(row.name, row.value) for row in Counter.select().order_by(Counter.name)] == [('a', 9), ('b', 2)]
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_query_without_bound_database_raises_interface_error')
def test_integration_join_without_foreign_key_or_on_expression_raises_error():
    """Verifies: PEEWEE-QUERY-024"""
    db = memory_db()
    class Person(Model):
        name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    class Pet(Model):
        name = TextField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Person, Pet])
        with pytest.raises(ValueError):
            Person.select().join(Pet)
    finally:
        close_db(db)


@pytest.mark.depends_on('test_atomic_connection_lifecycle_return_values')
def test_integration_window_function_partitions_rows_by_group():
    """Verifies: PEEWEE-QUERY-031, PEEWEE-QUERY-033"""
    db = memory_db()
    class Score(Model):
        team = TextField()
        points = IntegerField()
        class Meta:
            database = db
            legacy_table_names = False
    try:
        bind_create(db, [Score])
        Score.insert_many([
            {'team': 'red', 'points': 3},
            {'team': 'red', 'points': 5},
            {'team': 'blue', 'points': 7},
        ]).execute()
        total = fn.SUM(Score.points).over(partition_by=[Score.team]).alias('team_total')
        rows = (Score
                .select(Score.team, Score.points, total)
                .order_by(Score.team, Score.points)
                .dicts())
        assert list(rows) == [
            {'team': 'blue', 'points': 7, 'team_total': 7},
            {'team': 'red', 'points': 3, 'team_total': 8},
            {'team': 'red', 'points': 5, 'team_total': 8},
        ]
    finally:
        close_db(db)
