import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ecommerce-sentiment-platform")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "ecommerce-raw-data-mohammed")
DATASET_ID = "raw_data"


def ensure_dataset_exists(client: bigquery.Client, dataset_id: str):
    """Creates the BigQuery dataset if it does not already exist."""
    dataset_ref = f"{GCP_PROJECT_ID}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "europe-west1"
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset '{dataset_ref}' is ready.")


def create_external_table(client: bigquery.Client, table_id: str, gcs_uri: str):
    """Creates or replaces a BigQuery External Table pointing to GCS Parquet files."""
    full_table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_id}"

    table = bigquery.Table(full_table_id)
    external_config = bigquery.ExternalConfig("PARQUET")
    external_config.source_uris = [gcs_uri]
    
    # Auto-detect schema directly from Parquet file footers
    external_config.autodetect = True
    table.external_data_configuration = external_config

    table = client.create_table(table, exists_ok=True)
    print(f"External table '{full_table_id}' configured -> {gcs_uri}")


def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)

    # 1. Ensure target raw dataset exists
    ensure_dataset_exists(client, DATASET_ID)

    # 2. External Table: Raw Reviews (scans all category reviews Parquet files)
    create_external_table(
        client=client,
        table_id="raw_reviews",
        gcs_uri=f"gs://{GCS_BUCKET_NAME}/raw/reviews/*.parquet"
    )

    # 3. External Table: Raw Metadata (scans all category metadata Parquet files)
    create_external_table(
        client=client,
        table_id="raw_metadata",
        gcs_uri=f"gs://{GCS_BUCKET_NAME}/raw/metadata/*.parquet"
    )

    print("\nExternal table setup completed successfully!")


if __name__ == "__main__":
    main()
