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


def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    ensure_dataset_exists(client, DATASET_ID)

    # 1. Historical Static Baseline Table
    baseline_table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.raw_reviews_baseline"
    client.delete_table(baseline_table_id, not_found_ok=True)
    
    baseline_table = bigquery.Table(baseline_table_id)
    config_baseline = bigquery.ExternalConfig("PARQUET")
    config_baseline.source_uris = [f"gs://{GCS_BUCKET_NAME}/raw/reviews/*.parquet"]
    config_baseline.autodetect = True
    baseline_table.external_data_configuration = config_baseline
    client.create_table(baseline_table)
    print(f"Created external table: {baseline_table_id}")

    # 2. Daily Hive-Partitioned Delta Table
    delta_table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.raw_reviews_delta"
    client.delete_table(delta_table_id, not_found_ok=True)
    
    delta_table = bigquery.Table(delta_table_id)
    config_delta = bigquery.ExternalConfig("PARQUET")
    config_delta.source_uris = [f"gs://{GCS_BUCKET_NAME}/raw/reviews_delta/*"]
    config_delta.autodetect = True

    hive_options = bigquery.HivePartitioningOptions()
    hive_options.mode = "AUTO"
    hive_options.source_uri_prefix = f"gs://{GCS_BUCKET_NAME}/raw/reviews_delta/"
    config_delta.hive_partitioning = hive_options

    delta_table.external_data_configuration = config_delta
    client.create_table(delta_table)
    print(f"Created external table: {delta_table_id}")

    # 3. Static Metadata External Table
    metadata_table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.raw_metadata"
    client.delete_table(metadata_table_id, not_found_ok=True)

    metadata_table = bigquery.Table(metadata_table_id)
    config_metadata = bigquery.ExternalConfig("PARQUET")
    config_metadata.source_uris = [f"gs://{GCS_BUCKET_NAME}/raw/metadata/*.parquet"]
    config_metadata.autodetect = True
    metadata_table.external_data_configuration = config_metadata
    client.create_table(metadata_table)
    print(f"Created external table: {metadata_table_id}")

    print("\nAll external tables created successfully!")


if __name__ == "__main__":
    main()
    