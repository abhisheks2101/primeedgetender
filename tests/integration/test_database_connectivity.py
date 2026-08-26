"""Database connectivity integration tests."""

import pytest
from sqlalchemy import text

from app.core.database import check_database_connection


@pytest.mark.integration
def test_database_connection(db_engine, database_is_available):
    if not database_is_available:
        pytest.skip("PostgreSQL is not available for integration tests")

    connected, latency_ms, error = check_database_connection(db_engine)

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.integration
def test_database_can_execute_simple_query(db_engine, database_is_available):
    if not database_is_available:
        pytest.skip("PostgreSQL is not available for integration tests")

    with db_engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    assert result == 1
