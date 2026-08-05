from __future__ import annotations

import pypika
import pytest


def test_public_import_surface_exposes_query_table_field_and_dialects():
    assert pypika.__version__ == "0.51.1"
    assert callable(pypika.Query.from_)
    assert callable(pypika.Table)
    assert callable(pypika.Field)
    assert callable(pypika.MySQLQuery.into)
    assert callable(pypika.PostgreSQLQuery.into)


def test_query_select_from_strings_builds_quoted_select(sql):
    query = pypika.Query.from_("customers").select("id", "name")
    assert sql(query.get_sql()) == 'SELECT "id","name" FROM "customers"'


def test_table_fields_project_namespaced_columns(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.id, users.name)
    assert sql(query.get_sql()) == 'SELECT "id","name" FROM "users"'


def test_table_alias_changes_from_projection_namespace(sql):
    customers = pypika.Table("customer_view").as_("customers")
    query = pypika.Query.from_(customers).select(customers.id)
    assert sql(query.get_sql()) == 'SELECT "customers"."id" FROM "customer_view" "customers"'


def test_field_alias_is_rendered_after_an_expression(sql):
    products = pypika.Table("products")
    query = pypika.Query.from_(products).select((products.price - products.cost).as_("margin"))
    assert sql(query.get_sql()) == 'SELECT "price"-"cost" "margin" FROM "products"'


def test_schema_and_database_namespace_tables(sql):
    schema_query = pypika.Query.from_(pypika.Schema("reporting").sales).select("*")
    database_query = pypika.Query.from_(pypika.Database("warehouse").reporting.sales).select("*")
    assert sql(schema_query.get_sql()) == 'SELECT * FROM "reporting"."sales"'
    assert sql(database_query.get_sql()) == 'SELECT * FROM "warehouse"."reporting"."sales"'


def test_string_conversion_and_get_sql_share_stable_semantics(sql):
    query = pypika.Query.from_("users").select("id").where(pypika.Field("active") == True)
    assert sql(str(query)) == sql(query.get_sql())


def test_arithmetic_expression_preserves_operator_precedence(sql):
    products = pypika.Table("products")
    expression = ((products.price + products.tax) * products.quantity).as_("gross")
    query = pypika.Query.from_(products).select(expression)
    assert sql(query.get_sql()) == 'SELECT ("price"+"tax")*"quantity" "gross" FROM "products"'


def test_comparison_criteria_render_documented_comparators(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.id).where(
        (users.age >= 18) & (users.status != "blocked") & (users.score < 10)
    )
    assert sql(query.get_sql()) == (
        'SELECT "id" FROM "users" WHERE "age">=18 AND "status"<>\'blocked\' AND "score"<10'
    )


def test_boolean_criteria_support_and_or_xor_and_not(sql):
    users = pypika.Table("users")
    criterion = ((users.active == True) & (users.age >= 18)) | ~(users.role == "guest")
    query = pypika.Query.from_(users).select(users.id).where(criterion)
    assert sql(query.get_sql()) == (
        'SELECT "id" FROM "users" WHERE ("active"=true AND "age">=18) OR NOT "role"=\'guest\''
    )
    xor_query = pypika.Query.from_(users).select(users.id).where((users.active == True) ^ (users.admin == True))
    assert " XOR " in sql(xor_query.get_sql())


def test_membership_and_between_criteria_render_sql(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.id).where(
        users.id.isin([1, 2, 3]) & users.age[18:65]
    )
    assert sql(query.get_sql()) == (
        'SELECT "id" FROM "users" WHERE "id" IN (1,2,3) AND "age" BETWEEN 18 AND 65'
    )


def test_null_and_negated_null_criteria_render_sql(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.id).where(users.deleted_at.isnull() | users.name.notnull())
    assert sql(query.get_sql()) == (
        'SELECT "id" FROM "users" WHERE "deleted_at" IS NULL OR NOT "name" IS NULL'
    )


def test_string_criteria_render_like_ilike_and_regex(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.name).where(
        users.name.like("A%") & users.email.ilike("%@EXAMPLE.COM") & users.code.regex("^[A-Z]+$")
    )
    assert sql(query.get_sql()) == (
        'SELECT "name" FROM "users" WHERE "name" LIKE \'A%\' AND "email" ILIKE \'%@EXAMPLE.COM\' '
        "AND \"code\" REGEX '^[A-Z]+$'"
    )


def test_bitwise_criteria_use_documented_operators(sql):
    flags = pypika.Table("flags")
    query = pypika.Query.from_(flags).select(flags.name).where(
        (flags.permissions.bitwiseand(4) == 4) | (flags.mask.bitwiseor(2) == 3)
    )
    assert sql(query.get_sql()) == (
        'SELECT "name" FROM "flags" WHERE ("permissions" & 4)=4 OR ("mask" | 2)=3'
    )


def test_repeated_where_calls_accumulate_with_and(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.id).where(users.active == True).where(users.age >= 21)
    assert sql(query.get_sql()) == 'SELECT "id" FROM "users" WHERE "active"=true AND "age">=21'


def test_join_on_adds_join_type_and_criterion(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    query = pypika.Query.from_(users).select(users.id, orders.total).join(orders).on(users.id == orders.user_id)
    assert sql(query.get_sql()) == (
        'SELECT "users"."id","orders"."total" FROM "users" JOIN "orders" '
        'ON "users"."id"="orders"."user_id"'
    )


def test_join_using_projects_shared_field(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    query = pypika.Query.from_(users).select("*").join(orders).using("user_id")
    assert sql(query.get_sql()) == 'SELECT * FROM "users" JOIN "orders" USING ("user_id")'


def test_join_helpers_render_left_and_cross_joins(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    products = pypika.Table("products")
    left = pypika.Query.from_(users).select("*").left_join(orders).on(users.id == orders.user_id)
    cross = pypika.Query.from_(users).select("*").cross_join(products).cross()
    assert "LEFT JOIN" in sql(left.get_sql())
    assert sql(cross.get_sql()) == 'SELECT * FROM "users" CROSS JOIN "products"'


def test_group_by_and_having_filter_aggregates(sql):
    orders = pypika.Table("orders")
    from pypika import functions as fn

    query = (
        pypika.Query.from_(orders)
        .select(orders.user_id, fn.Sum(orders.total).as_("total"))
        .groupby(orders.user_id)
        .having(fn.Sum(orders.total) > 100)
    )
    assert sql(query.get_sql()) == (
        'SELECT "user_id",SUM("total") "total" FROM "orders" GROUP BY "user_id" HAVING SUM("total")>100'
    )


def test_order_limit_and_offset_are_composed_in_order(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select("*").orderby(users.id, order=pypika.Order.desc).limit(10).offset(5)
    assert sql(query.get_sql()) == 'SELECT * FROM "users" ORDER BY "id" DESC LIMIT 10 OFFSET 5'


def test_distinct_removes_duplicate_projection_semantics(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.email).distinct()
    assert sql(query.get_sql()) == 'SELECT DISTINCT "email" FROM "users"'


def test_builtin_functions_render_arguments_and_aliases(sql):
    users = pypika.Table("users")
    from pypika import functions as fn

    query = pypika.Query.from_(users).select(
        fn.Concat(users.first_name, " ", users.last_name).as_("full_name"),
        fn.Upper(users.status),
        fn.Length(users.email),
    )
    assert sql(query.get_sql()) == (
        'SELECT CONCAT("first_name",\' \',"last_name") "full_name",UPPER("status"),LENGTH("email") FROM "users"'
    )


def test_aggregate_distinct_and_filter_render_sql(sql):
    orders = pypika.Table("orders")
    from pypika import functions as fn

    query = pypika.Query.from_(orders).select(
        fn.Count("*").distinct().as_("unique_orders"),
        fn.Sum(orders.total).filter(orders.status == "paid"),
    )
    assert sql(query.get_sql()) == (
        'SELECT COUNT(DISTINCT *) "unique_orders",SUM("total") FILTER(WHERE "status"=\'paid\') FROM "orders"'
    )


def test_case_expression_renders_ordered_branches_and_else(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(
        pypika.Case().when(users.age < 18, "minor").when(users.age >= 65, "senior").else_("adult").as_("segment")
    )
    assert sql(query.get_sql()) == (
        'SELECT CASE WHEN "age"<18 THEN \'minor\' WHEN "age">=65 THEN \'senior\' ELSE \'adult\' END "segment" '
        'FROM "users"'
    )


def test_custom_function_uses_declared_parameters(sql):
    users = pypika.Table("users")
    date_diff = pypika.CustomFunction("DATE_DIFF", ["unit", "start", "end"])
    query = pypika.Query.from_(users).select(date_diff("day", users.created, users.updated))
    assert sql(query.get_sql()) == 'SELECT DATE_DIFF(\'day\',"created","updated") FROM "users"'


def test_analytic_function_renders_partition_and_order(sql):
    events = pypika.Table("events")
    from pypika import analytics as an

    query = pypika.Query.from_(events).select(an.Rank().over(events.user_id).orderby(events.created_at))
    assert sql(query.get_sql()) == (
        'SELECT RANK() OVER(PARTITION BY "user_id" ORDER BY "created_at") FROM "events"'
    )


def test_tuple_criteria_render_pairwise_comparisons(sql):
    products = pypika.Table("products")
    query = pypika.Query.from_(products).select(products.sku).where(
        pypika.Tuple(products.sku, products.region).isin([("A", "east"), ("B", "west")])
    )
    assert sql(query.get_sql()) == (
        'SELECT "sku" FROM "products" WHERE ("sku","region") IN ((\'A\',\'east\'),(\'B\',\'west\'))'
    )


def test_cte_and_aliased_query_render_a_named_subquery(sql):
    users = pypika.Table("users")
    active = pypika.Query.from_(users).select("*").where(users.active == True)
    query = pypika.Query.with_(active, "active_users").from_(pypika.AliasedQuery("active_users")).select("*")
    assert sql(query.get_sql()) == (
        'WITH active_users AS (SELECT * FROM "users" WHERE "active"=true) SELECT * FROM active_users'
    )


def test_set_operations_render_union_all_intersect_and_except(sql):
    left = pypika.Query.from_("left_table").select("id")
    right = pypika.Query.from_("right_table").select("id")
    assert sql(left.union_all(right).get_sql()) == (
        '(SELECT "id" FROM "left_table") UNION ALL (SELECT "id" FROM "right_table")'
    )
    assert " INTERSECT " in sql(left.intersect(right).get_sql())
    assert " EXCEPT " in sql(left.except_of(right).get_sql())


def test_insert_values_and_multiple_rows_render_sql(sql):
    users = pypika.Table("users")
    query = pypika.Query.into(users).columns("id", "name").insert((1, "Ada"), (2, "Bob"))
    assert sql(query.get_sql()) == 'INSERT INTO "users" ("id","name") VALUES (1,\'Ada\'),(2,\'Bob\')'


def test_insert_from_select_preserves_target_columns(sql):
    users = pypika.Table("users")
    archive = pypika.Table("user_archive")
    query = pypika.Query.into(archive).columns("id", "name").from_(users).select(users.id, users.name)
    assert sql(query.get_sql()) == (
        'INSERT INTO "user_archive" ("id","name") SELECT "id","name" FROM "users"'
    )


def test_update_query_renders_assignments_filter_and_limit(sql):
    users = pypika.Table("users")
    query = pypika.Query.update(users).set(users.name, "Ada").where(users.id == 1).limit(2)
    assert sql(query.get_sql()) == 'UPDATE "users" SET "name"=\'Ada\' WHERE "id"=1 LIMIT 2'


def test_delete_query_renders_filter_and_limit(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).delete().where(users.active == False).limit(5)
    assert sql(query.get_sql()) == 'DELETE FROM "users" WHERE "active"=false LIMIT 5'


def test_parameter_object_collects_values_with_qmark_placeholders(sql):
    users = pypika.Table("users")
    parameter = pypika.QmarkParameter()
    query = pypika.Query.from_(users).select("*").where((users.name == "Ada") & (users.id >= 2))
    rendered = query.get_sql(parameter=parameter)
    assert sql(rendered) == 'SELECT * FROM "users" WHERE "name"=? AND "id">=?'
    assert parameter.get_parameters() == ["Ada", 2]


def test_mysql_dialect_uses_backticks_and_duplicate_handlers(sql):
    users = pypika.Table("users")
    query = pypika.MySQLQuery.into(users).insert(1, "Ada").on_duplicate_key_ignore()
    assert sql(query.get_sql()) == "INSERT INTO `users` VALUES (1,'Ada') ON DUPLICATE KEY IGNORE"


def test_postgresql_dialect_supports_conflict_and_returning(sql):
    users = pypika.Table("users")
    query = (
        pypika.PostgreSQLQuery.into(users)
        .insert(1, "Ada")
        .on_conflict(users.id)
        .do_nothing()
    )
    assert sql(query.get_sql()) == 'INSERT INTO "users" VALUES (1,\'Ada\') ON CONFLICT ("id") DO NOTHING'
    update = pypika.PostgreSQLQuery.update(users).set(users.name, "Ada").where(users.id == 1).returning(users.id)
    assert sql(update.get_sql()) == 'UPDATE "users" SET "name"=\'Ada\' WHERE "id"=1 RETURNING "users"."id"'


def test_oracle_and_mssql_dialects_render_fetch_pagination(sql):
    users = pypika.Table("users")
    oracle = pypika.OracleQuery.from_(users).select("*").orderby(users.id).limit(3).offset(2)
    mssql = pypika.MSSQLQuery.from_(users).select("*").orderby(users.id).limit(3).offset(2)
    expected = "SELECT * FROM users ORDER BY id OFFSET 2 ROWS FETCH NEXT 3 ROWS ONLY"
    assert sql(oracle.get_sql()) == expected
    assert sql(mssql.get_sql()) == 'SELECT * FROM "users" ORDER BY "id" OFFSET 2 ROWS FETCH NEXT 3 ROWS ONLY'


def test_clickhouse_dialect_supports_final_sample_and_limit_by(sql):
    events = pypika.Table("events")
    query = (
        pypika.ClickHouseQuery.from_(events)
        .select("*")
        .final()
        .sample(10, offset=2)
        .limit_offset_by(3, 1, events.user_id)
    )
    assert sql(query.get_sql()) == 'SELECT * FROM "events" FINAL SAMPLE 10 OFFSET 2 LIMIT 3 OFFSET 1 BY ("user_id")'
