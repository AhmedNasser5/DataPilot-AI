from core.sql.query_validator import QueryValidator


def test_select_query_is_valid():
    v = QueryValidator()
    result = v.validate("SELECT * FROM orders")
    assert result.is_valid is True


def test_drop_is_blocked():
    v = QueryValidator()
    result = v.validate("DROP TABLE orders")
    assert result.is_valid is False


def test_delete_is_blocked():
    v = QueryValidator()
    result = v.validate("DELETE FROM orders WHERE id = 1")
    assert result.is_valid is False


def test_update_is_blocked():
    v = QueryValidator()
    result = v.validate("UPDATE orders SET amount = 0")
    assert result.is_valid is False


def test_multi_statement_blocked():
    v = QueryValidator()
    result = v.validate("SELECT * FROM orders; DROP TABLE orders;")
    assert result.is_valid is False


def test_limit_auto_injected():
    v = QueryValidator(max_result_rows=100)
    result = v.validate("SELECT * FROM orders")
    assert "LIMIT 100" in result.sanitized_sql


def test_existing_limit_preserved():
    v = QueryValidator(max_result_rows=100)
    result = v.validate("SELECT * FROM orders LIMIT 5")
    assert result.sanitized_sql.count("LIMIT") == 1
