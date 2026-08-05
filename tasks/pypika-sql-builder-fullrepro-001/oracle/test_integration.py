from __future__ import annotations

import pypika
import pytest


@pytest.mark.depends_on("test_query_select_from_strings_builds_quoted_select", "test_comparison_criteria_render_documented_comparators")
def test_select_where_order_workflow(sql):
    users = pypika.Table("users")
    query = (
        pypika.Query.from_(users)
        .select(users.id, users.name)
        .where(users.active == True)
        .orderby(users.name, order=pypika.Order.asc)
        .limit(20)
    )
    assert sql(query.get_sql()) == (
        'SELECT "id","name" FROM "users" WHERE "active"=true ORDER BY "name" ASC LIMIT 20'
    )


@pytest.mark.depends_on("test_table_alias_changes_from_projection_namespace", "test_arithmetic_expression_preserves_operator_precedence")
def test_alias_arithmetic_filter_workflow(sql):
    products = pypika.Table("products").as_("p")
    query = pypika.Query.from_(products).select(
        (products.price * products.quantity).as_("gross")
    ).where(products.quantity > 0)
    assert sql(query.get_sql()) == (
        'SELECT "p"."price"*"p"."quantity" "gross" FROM "products" "p" WHERE "p"."quantity">0'
    )


@pytest.mark.depends_on("test_boolean_criteria_support_and_or_xor_and_not", "test_membership_and_between_criteria_render_sql")
def test_composed_criteria_workflow(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select("*").where(
        ((users.active == True) & users.age[18:65]) | users.id.isin([7, 9])
    )
    assert sql(query.get_sql()) == (
        'SELECT * FROM "users" WHERE ("active"=true AND "age" BETWEEN 18 AND 65) OR "id" IN (7,9)'
    )


@pytest.mark.depends_on("test_join_on_adds_join_type_and_criterion", "test_string_criteria_render_like_ilike_and_regex")
def test_join_on_filter_projection_workflow(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    query = (
        pypika.Query.from_(users)
        .select(users.id, orders.total)
        .join(orders)
        .on(users.id == orders.user_id)
        .where(orders.status.like("paid%"))
    )
    assert sql(query.get_sql()) == (
        'SELECT "users"."id","orders"."total" FROM "users" JOIN "orders" '
        'ON "users"."id"="orders"."user_id" WHERE "orders"."status" LIKE \'paid%\''
    )


@pytest.mark.depends_on("test_join_using_projects_shared_field", "test_group_by_and_having_filter_aggregates")
def test_join_using_aggregate_workflow(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    from pypika import functions as fn

    query = (
        pypika.Query.from_(users)
        .join(orders)
        .using("user_id")
        .select(users.user_id, fn.Sum(orders.total).as_("total"))
        .groupby(users.user_id)
    )
    assert sql(query.get_sql()) == (
        'SELECT "users"."user_id",SUM("orders"."total") "total" FROM "users" JOIN "orders" '
        'USING ("user_id") GROUP BY "users"."user_id"'
    )


@pytest.mark.depends_on("test_join_helpers_render_left_and_cross_joins", "test_null_and_negated_null_criteria_render_sql")
def test_left_join_null_preservation_workflow(sql):
    users = pypika.Table("users")
    profiles = pypika.Table("profiles")
    query = (
        pypika.Query.from_(users)
        .select(users.id, profiles.city)
        .left_join(profiles)
        .on(users.id == profiles.user_id)
        .where(profiles.id.isnull())
    )
    assert sql(query.get_sql()) == (
        'SELECT "users"."id","profiles"."city" FROM "users" LEFT JOIN "profiles" '
        'ON "users"."id"="profiles"."user_id" WHERE "profiles"."id" IS NULL'
    )


@pytest.mark.depends_on("test_group_by_and_having_filter_aggregates", "test_order_limit_and_offset_are_composed_in_order")
def test_group_having_order_limit_workflow(sql):
    orders = pypika.Table("orders")
    from pypika import functions as fn

    total = fn.Sum(orders.total).as_("total")
    query = (
        pypika.Query.from_(orders)
        .select(orders.user_id, total)
        .groupby(orders.user_id)
        .having(fn.Sum(orders.total) > 100)
        .orderby(total, order=pypika.Order.desc)
        .limit(5)
        .offset(2)
    )
    assert sql(query.get_sql()) == (
        'SELECT "user_id",SUM("total") "total" FROM "orders" GROUP BY "user_id" '
        'HAVING SUM("total")>100 ORDER BY "total" DESC LIMIT 5 OFFSET 2'
    )


@pytest.mark.depends_on("test_distinct_removes_duplicate_projection_semantics", "test_order_limit_and_offset_are_composed_in_order")
def test_distinct_offset_workflow(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).select(users.email).distinct().orderby(users.email).offset(10).limit(4)
    assert sql(query.get_sql()) == 'SELECT DISTINCT "email" FROM "users" ORDER BY "email" LIMIT 4 OFFSET 10'


@pytest.mark.depends_on("test_builtin_functions_render_arguments_and_aliases", "test_case_expression_renders_ordered_branches_and_else")
def test_function_case_workflow(sql):
    users = pypika.Table("users")
    from pypika import functions as fn

    segment = pypika.Case().when(users.active == True, "live").else_("inactive").as_("segment")
    query = pypika.Query.from_(users).select(fn.Lower(users.name).as_("normalized"), segment)
    assert sql(query.get_sql()) == (
        'SELECT LOWER("name") "normalized",CASE WHEN "active"=true THEN \'live\' ELSE \'inactive\' END "segment" '
        'FROM "users"'
    )


@pytest.mark.depends_on("test_custom_function_uses_declared_parameters", "test_cte_and_aliased_query_render_a_named_subquery")
def test_custom_function_cte_workflow(sql):
    users = pypika.Table("users")
    date_diff = pypika.CustomFunction("DATE_DIFF", ["unit", "start", "end"])
    active = pypika.Query.from_(users).select(
        users.id, date_diff("day", users.created, users.updated).as_("age_days")
    ).where(users.active == True)
    query = pypika.Query.with_(active, "active_users").from_(pypika.AliasedQuery("active_users")).select("*")
    assert sql(query.get_sql()) == (
        'WITH active_users AS (SELECT "id",DATE_DIFF(\'day\',"created","updated") "age_days" '
        'FROM "users" WHERE "active"=true) SELECT * FROM active_users'
    )


@pytest.mark.depends_on("test_analytic_function_renders_partition_and_order", "test_boolean_criteria_support_and_or_xor_and_not")
def test_analytic_qualify_workflow(sql):
    events = pypika.Table("events")
    from pypika import analytics as an

    rank = an.Rank().over(events.account_id).orderby(events.created_at)
    query = pypika.Query.from_(events).select("*").qualify(rank == 1).orderby(events.created_at)
    assert sql(query.get_sql()) == (
        'SELECT * FROM "events" QUALIFY RANK() OVER(PARTITION BY "account_id" ORDER BY "created_at")=1 '
        'ORDER BY "created_at"'
    )


@pytest.mark.depends_on("test_tuple_criteria_render_pairwise_comparisons", "test_membership_and_between_criteria_render_sql")
def test_tuple_membership_filter_workflow(sql):
    products = pypika.Table("products")
    query = pypika.Query.from_(products).select(products.sku, products.region).where(
        pypika.Tuple(products.sku, products.region).isin([("A", "east"), ("B", "west")])
    ).where(products.price[1:100])
    assert sql(query.get_sql()) == (
        'SELECT "sku","region" FROM "products" WHERE ("sku","region") IN '
        "((\'A\',\'east\'),(\'B\',\'west\')) AND \"price\" BETWEEN 1 AND 100"
    )


@pytest.mark.depends_on("test_cte_and_aliased_query_render_a_named_subquery", "test_join_on_adds_join_type_and_criterion")
def test_cte_join_workflow(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    active = pypika.Query.from_(users).select(users.id).where(users.active == True)
    active_alias = pypika.AliasedQuery("active_users", active)
    query = pypika.Query.from_(active_alias).join(orders).on(active_alias.id == orders.user_id).select(
        active_alias.id, orders.total
    )
    assert sql(query.get_sql()) == (
        'SELECT "active_users"."id","orders"."total" FROM (SELECT "id" FROM "users" WHERE "active"=true) '
        'JOIN "orders" ON "active_users"."id"="orders"."user_id"'
    )


@pytest.mark.depends_on("test_set_operations_render_union_all_intersect_and_except", "test_order_limit_and_offset_are_composed_in_order")
def test_union_all_order_limit_workflow(sql):
    users = pypika.Table("users")
    archived = pypika.Table("archived_users")
    query = (
        pypika.Query.from_(users).select(users.id)
        .union_all(pypika.Query.from_(archived).select(archived.id))
        .orderby("id", order=pypika.Order.asc)
        .limit(10)
    )
    assert sql(query.get_sql()) == (
        '(SELECT "id" FROM "users") UNION ALL (SELECT "id" FROM "archived_users") ORDER BY "id" ASC LIMIT 10'
    )


@pytest.mark.depends_on("test_set_operations_render_union_all_intersect_and_except", "test_query_select_from_strings_builds_quoted_select")
def test_intersect_and_except_composition_workflow(sql):
    current = pypika.Query.from_("current_users").select("id")
    archived = pypika.Query.from_("archived_users").select("id")
    assert " INTERSECT " in sql(current.intersect(archived).get_sql())
    assert " EXCEPT " in sql(current.except_of(archived).get_sql())


@pytest.mark.depends_on("test_insert_values_and_multiple_rows_render_sql", "test_field_alias_is_rendered_after_an_expression")
def test_multirow_insert_workflow(sql):
    users = pypika.Table("users")
    query = pypika.Query.into(users).columns("id", "name").insert((1, "Ada"), (2, "Bob")).insert((3, "Cy"))
    assert sql(query.get_sql()) == (
        'INSERT INTO "users" ("id","name") VALUES (1,\'Ada\'),(2,\'Bob\'),(3,\'Cy\')'
    )


@pytest.mark.depends_on("test_insert_from_select_preserves_target_columns", "test_join_on_adds_join_type_and_criterion")
def test_insert_select_join_workflow(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    archive = pypika.Table("order_archive")
    query = (
        pypika.Query.into(archive)
        .columns("id", "user_name")
        .from_(users)
        .join(orders)
        .on(orders.user_id == users.id)
        .select(orders.id, users.name)
    )
    assert sql(query.get_sql()) == (
        'INSERT INTO "order_archive" ("id","user_name") SELECT "orders"."id","users"."name" FROM "users" '
        'JOIN "orders" ON "orders"."user_id"="users"."id"'
    )


@pytest.mark.depends_on("test_update_query_renders_assignments_filter_and_limit", "test_join_on_adds_join_type_and_criterion")
def test_update_join_filter_limit_workflow(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    query = (
        pypika.Query.update(users)
        .join(orders)
        .on(orders.user_id == users.id)
        .set(users.last_order, orders.created_at)
        .where(orders.status == "paid")
        .limit(2)
    )
    assert sql(query.get_sql()) == (
        'UPDATE "users" JOIN "orders" ON "orders"."user_id"="users"."id" SET "last_order"="orders"."created_at" '
        'WHERE "orders"."status"=\'paid\' LIMIT 2'
    )


@pytest.mark.depends_on("test_delete_query_renders_filter_and_limit", "test_null_and_negated_null_criteria_render_sql")
def test_delete_filter_limit_workflow(sql):
    users = pypika.Table("users")
    query = pypika.Query.from_(users).delete().where(users.deleted_at.notnull()).limit(3)
    assert sql(query.get_sql()) == 'DELETE FROM "users" WHERE NOT "deleted_at" IS NULL LIMIT 3'


@pytest.mark.depends_on("test_parameter_object_collects_values_with_qmark_placeholders", "test_boolean_criteria_support_and_or_xor_and_not")
def test_parameterized_composed_filter_workflow(sql):
    users = pypika.Table("users")
    parameter = pypika.QmarkParameter()
    query = pypika.Query.from_(users).select(users.id).where(
        (users.status == "active") & (users.score >= 10) & (users.name.like("A%"))
    )
    assert sql(query.get_sql(parameter=parameter)) == (
        'SELECT "id" FROM "users" WHERE "status"=? AND "score">=? AND "name" LIKE ?'
    )
    assert parameter.get_parameters() == ["active", 10, "A%"]


@pytest.mark.depends_on("test_mysql_dialect_uses_backticks_and_duplicate_handlers", "test_insert_values_and_multiple_rows_render_sql")
def test_mysql_duplicate_update_workflow(sql):
    users = pypika.Table("users")
    from pypika.terms import Values

    query = pypika.MySQLQuery.into(users).insert(1, "Ada").on_duplicate_key_update(users.name, Values(users.name))
    assert sql(query.get_sql()) == (
        'INSERT INTO `users` VALUES (1,\'Ada\') ON DUPLICATE KEY UPDATE `name`=VALUES(`name`)'
    )


@pytest.mark.depends_on("test_postgresql_dialect_supports_conflict_and_returning", "test_update_query_renders_assignments_filter_and_limit")
def test_postgresql_conflict_update_returning_workflow(sql):
    users = pypika.Table("users")
    query = (
        pypika.PostgreSQLQuery.into(users)
        .insert(1, "Ada")
        .on_conflict(users.id)
        .do_update(users.name, "Ann")
        .returning(users.id, users.name)
    )
    assert sql(query.get_sql()) == (
        'INSERT INTO "users" VALUES (1,\'Ada\') ON CONFLICT ("id") DO UPDATE SET "name"=\'Ann\' '
        'RETURNING "id","name"'
    )


@pytest.mark.depends_on("test_oracle_and_mssql_dialects_render_fetch_pagination", "test_order_limit_and_offset_are_composed_in_order")
def test_oracle_and_mssql_pagination_workflow(sql):
    users = pypika.Table("users")
    oracle = pypika.OracleQuery.from_(users).select(users.id).orderby(users.id).offset(2).limit(3)
    mssql = pypika.MSSQLQuery.from_(users).select(users.id).orderby(users.id).offset(2).limit(3)
    assert sql(oracle.get_sql()) == 'SELECT id FROM users ORDER BY id OFFSET 2 ROWS FETCH NEXT 3 ROWS ONLY'
    assert sql(mssql.get_sql()) == (
        'SELECT "id" FROM "users" ORDER BY "id" OFFSET 2 ROWS FETCH NEXT 3 ROWS ONLY'
    )


@pytest.mark.depends_on("test_clickhouse_dialect_supports_final_sample_and_limit_by", "test_builtin_functions_render_arguments_and_aliases")
def test_clickhouse_sampling_and_projection_workflow(sql):
    events = pypika.Table("events")
    from pypika import functions as fn

    query = (
        pypika.ClickHouseQuery.from_(events)
        .select(fn.Count("*").as_("n"))
        .final()
        .sample(5)
        .limit_by(2, events.account_id)
    )
    assert sql(query.get_sql()) == 'SELECT COUNT(*) AS "n" FROM "events" FINAL SAMPLE 5 LIMIT 2 BY ("account_id")'


@pytest.mark.depends_on("test_schema_and_database_namespace_tables", "test_table_fields_project_namespaced_columns")
def test_namespace_table_filter_workflow(sql):
    table = pypika.Database("warehouse").reporting.orders
    query = pypika.Query.from_(table).select(table.id, table.total).where(table.total > 0)
    assert sql(query.get_sql()) == (
        'SELECT "id","total" FROM "warehouse"."reporting"."orders" WHERE "total">0'
    )


@pytest.mark.depends_on("test_string_conversion_and_get_sql_share_stable_semantics", "test_repeated_where_calls_accumulate_with_and")
def test_immutable_builder_branching_workflow(sql):
    users = pypika.Table("users")
    base = pypika.Query.from_(users).select(users.id)
    active = base.where(users.active == True)
    adults = base.where(users.age >= 18)
    assert sql(base.get_sql()) == 'SELECT "id" FROM "users"'
    assert sql(active.get_sql()) == 'SELECT "id" FROM "users" WHERE "active"=true'
    assert sql(adults.get_sql()) == 'SELECT "id" FROM "users" WHERE "age">=18'


@pytest.mark.depends_on("test_cte_and_aliased_query_render_a_named_subquery", "test_arithmetic_expression_preserves_operator_precedence")
def test_correlated_subquery_expression_workflow(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    latest = (
        pypika.Query.from_(orders)
        .select(orders.created_at)
        .where(orders.user_id == users.id)
        .orderby(orders.created_at, order=pypika.Order.desc)
        .limit(1)
    )
    query = pypika.Query.from_(users).select(users.id, latest.as_("latest_order"))
    assert sql(query.get_sql()) == (
        'SELECT "id",(SELECT "orders"."created_at" FROM "orders" WHERE "orders"."user_id"="users"."id" '
        'ORDER BY "orders"."created_at" DESC LIMIT 1) "latest_order" FROM "users"'
    )


@pytest.mark.depends_on("test_builtin_functions_render_arguments_and_aliases", "test_group_by_and_having_filter_aggregates")
def test_composed_summary_workflow(sql):
    orders = pypika.Table("orders")
    from pypika import functions as fn

    net = (orders.total - orders.discount).as_("net")
    query = (
        pypika.Query.from_(orders)
        .select(orders.user_id, fn.Count("*").as_("rows"), fn.Sum(net).as_("net_total"))
        .where(orders.status == "paid")
        .groupby(orders.user_id)
        .having(fn.Sum(net) > 0)
        .orderby(orders.user_id)
    )
    assert sql(query.get_sql()) == (
        'SELECT "user_id",COUNT(*) "rows",SUM("total"-"discount") "net_total" FROM "orders" '
        'WHERE "status"=\'paid\' GROUP BY "user_id" HAVING SUM("total"-"discount")>0 ORDER BY "user_id"'
    )


@pytest.mark.depends_on("test_join_helpers_render_left_and_cross_joins", "test_analytic_function_renders_partition_and_order")
def test_join_window_and_order_workflow(sql):
    users = pypika.Table("users")
    events = pypika.Table("events")
    from pypika import analytics as an

    rank = an.RowNumber().over(users.id).orderby(events.created_at, order=pypika.Order.desc)
    query = (
        pypika.Query.from_(users)
        .left_join(events)
        .on(users.id == events.user_id)
        .select(users.id, rank.as_("position"))
        .orderby(users.id)
    )
    assert sql(query.get_sql()) == (
        'SELECT "users"."id",ROW_NUMBER() OVER(PARTITION BY "users"."id" ORDER BY "events"."created_at" DESC) '
        '"position" FROM "users" LEFT JOIN "events" ON "users"."id"="events"."user_id" ORDER BY "users"."id"'
    )


@pytest.mark.depends_on("test_cte_and_aliased_query_render_a_named_subquery", "test_group_by_and_having_filter_aggregates")
def test_cte_aggregate_and_order_workflow(sql):
    orders = pypika.Table("orders")
    from pypika import functions as fn

    summary = pypika.Query.from_(orders).select(
        orders.user_id, fn.Sum(orders.total).as_("total")
    ).groupby(orders.user_id)
    query = pypika.Query.with_(summary, "totals").from_(pypika.AliasedQuery("totals")).select("*").orderby("total")
    assert sql(query.get_sql()) == (
        'WITH totals AS (SELECT "user_id",SUM("total") "total" FROM "orders" GROUP BY "user_id") '
        'SELECT * FROM totals ORDER BY "totals"."total"'
    )


@pytest.mark.depends_on("test_insert_from_select_preserves_target_columns", "test_parameter_object_collects_values_with_qmark_placeholders")
def test_insert_parameter_workflow(sql):
    users = pypika.Table("users")
    parameter = pypika.QmarkParameter()
    query = pypika.Query.into(users).columns("id", "name").insert(1, "Ada")
    assert sql(query.get_sql(parameter=parameter)) == 'INSERT INTO "users" ("id","name") VALUES (?,?)'
    assert parameter.get_parameters() == [1, "Ada"]


@pytest.mark.depends_on("test_postgresql_dialect_supports_conflict_and_returning", "test_analytic_function_renders_partition_and_order")
def test_postgresql_distinct_on_and_returning_workflow(sql):
    users = pypika.Table("users")
    query = (
        pypika.PostgreSQLQuery.from_(users)
        .select(users.id, users.email)
        .distinct_on(users.email)
        .orderby(users.email, users.id)
    )
    assert sql(query.get_sql()) == (
        'SELECT DISTINCT ON("email") "id","email" FROM "users" ORDER BY "email","id"'
    )


@pytest.mark.depends_on("test_set_operations_render_union_all_intersect_and_except", "test_cte_and_aliased_query_render_a_named_subquery")
def test_cte_union_workflow(sql):
    users = pypika.Table("users")
    archived = pypika.Table("archived_users")
    current = pypika.Query.from_(users).select(users.id)
    old = pypika.Query.from_(archived).select(archived.id)
    combined = current.union(old)
    query = pypika.Query.with_(combined, "all_users").from_(pypika.AliasedQuery("all_users")).select("*")
    assert sql(query.get_sql()) == (
        'WITH all_users AS ((SELECT "id" FROM "users") UNION (SELECT "id" FROM "archived_users")) '
        'SELECT * FROM all_users'
    )


@pytest.mark.depends_on("test_delete_query_renders_filter_and_limit", "test_parameter_object_collects_values_with_qmark_placeholders")
def test_delete_parameter_workflow(sql):
    users = pypika.Table("users")
    parameter = pypika.QmarkParameter()
    query = pypika.Query.from_(users).delete().where(users.status == "inactive").limit(2)
    assert sql(query.get_sql(parameter=parameter)) == 'DELETE FROM "users" WHERE "status"=? LIMIT 2'
    assert parameter.get_parameters() == ["inactive"]


@pytest.mark.depends_on("test_arithmetic_expression_preserves_operator_precedence", "test_builtin_functions_render_arguments_and_aliases")
def test_date_interval_function_workflow(sql):
    products = pypika.Table("products")
    from pypika import functions as fn

    query = pypika.Query.from_(products).select(
        fn.Date(products.created_at).as_("day"),
        products.created_at + pypika.Interval(days=1),
    ).where(products.created_at < fn.Now())
    assert sql(query.get_sql()) == (
        'SELECT DATE("created_at") "day","created_at"+INTERVAL \'1 DAY\' FROM "products" '
        'WHERE "created_at"<NOW()'
    )


@pytest.mark.depends_on("test_join_on_adds_join_type_and_criterion", "test_repeated_where_calls_accumulate_with_and")
def test_multi_join_filter_workflow(sql):
    users = pypika.Table("users")
    orders = pypika.Table("orders")
    profiles = pypika.Table("profiles")
    query = (
        pypika.Query.from_(users)
        .join(profiles)
        .on(profiles.user_id == users.id)
        .left_join(orders)
        .on(orders.user_id == users.id)
        .select(users.id, profiles.city, orders.total)
        .where(users.active == True)
        .where(orders.total > 0)
    )
    assert sql(query.get_sql()) == (
        'SELECT "users"."id","profiles"."city","orders"."total" FROM "users" JOIN "profiles" '
        'ON "profiles"."user_id"="users"."id" LEFT JOIN "orders" ON "orders"."user_id"="users"."id" '
        'WHERE "users"."active"=true AND "orders"."total">0'
    )
