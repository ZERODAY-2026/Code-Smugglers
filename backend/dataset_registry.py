"""Configuration for datasets available to the DataMind query pipeline."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DatasetConfig:
    """Snowflake objects and metadata for one selectable dataset."""

    key: str
    database: str
    schema: str
    tables: frozenset[str]
    description: str

    @property
    def objects(self) -> dict[tuple[str, str], frozenset[str]]:
        return {(self.database.upper(), self.schema.upper()): self.tables}


DATASETS = {
    "bank_marketing": DatasetConfig(
        key="bank_marketing",
        database="DATAMIND",
        schema="BANK_MARKETING",
        tables=frozenset({"BANK_MARKETING"}),
        description="UCI Bank Marketing campaign data",
    ),
    "tpch": DatasetConfig(
        key="tpch",
        database="SNOWFLAKE_SAMPLE_DATA",
        schema="TPCH_SF1",
        tables=frozenset(
            {
                "CUSTOMER",
                "ORDERS",
                "LINEITEM",
                "PART",
                "PARTSUPP",
                "SUPPLIER",
                "NATION",
                "REGION",
            }
        ),
        description="Snowflake TPC-H sample data",
    ),
}


def get_active_dataset() -> DatasetConfig:
    """Return the configured dataset, or infer it from database and schema."""

    requested_key = os.getenv("DATAMIND_DATASET", "").strip().lower()
    if requested_key:
        try:
            return DATASETS[requested_key]
        except KeyError as exc:
            supported = ", ".join(sorted(DATASETS))
            raise ValueError(
                f"Unsupported DATAMIND_DATASET '{requested_key}'. "
                f"Choose one of: {supported}."
            ) from exc

    database = os.getenv("SNOWFLAKE_DATABASE", "").strip().upper()
    schema = os.getenv("SNOWFLAKE_SCHEMA", "").strip().upper()
    for dataset in DATASETS.values():
        if dataset.database == database and dataset.schema == schema:
            return dataset

    raise ValueError(
        "No active dataset matches SNOWFLAKE_DATABASE and SNOWFLAKE_SCHEMA. "
        "Set DATAMIND_DATASET explicitly."
    )
