import pytest

from backend.dataset_registry import get_active_dataset
from backend.main import validate_sql


def test_bank_marketing_is_selectable(monkeypatch):
    monkeypatch.setenv("DATAMIND_DATASET", "bank_marketing")

    dataset = get_active_dataset()

    assert dataset.database == "DATAMIND"
    assert dataset.schema == "BANK_MARKETING"
    assert "BANK_MARKETING" in dataset.tables
    validate_sql(
        "SELECT Y, COUNT(*) FROM DATAMIND.BANK_MARKETING.BANK_MARKETING GROUP BY Y"
    )


def test_tpch_is_selectable_without_code_changes(monkeypatch):
    monkeypatch.setenv("DATAMIND_DATASET", "tpch")

    dataset = get_active_dataset()

    assert dataset.database == "SNOWFLAKE_SAMPLE_DATA"
    assert dataset.schema == "TPCH_SF1"
    validate_sql(
        "SELECT C_NAME FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER LIMIT 5"
    )


def test_active_dataset_rejects_a_table_from_another_dataset(monkeypatch):
    monkeypatch.setenv("DATAMIND_DATASET", "bank_marketing")

    with pytest.raises(ValueError, match="Table is not allowed"):
        validate_sql(
            "SELECT C_NAME FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER"
        )


def test_unknown_dataset_requires_explicit_fix(monkeypatch):
    monkeypatch.setenv("DATAMIND_DATASET", "unknown")

    with pytest.raises(ValueError, match="Unsupported DATAMIND_DATASET"):
        get_active_dataset()
