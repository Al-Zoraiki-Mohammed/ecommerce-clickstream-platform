import os
from scripts.extract_data import extract_reviews_to_parquet, extract_metadata_to_parquet
from scripts.load_to_gcs import upload_bytes_to_gcs
from dotenv import load_dotenv
from scripts.extract_data import  extract_metadata_to_parquet
from scripts.load_to_gcs import upload_bytes_to_gcs


category_name = "All_Beauty" # Change this to the desired category for extraction

load_dotenv()  # Auto-loads variables from .env on script execution


GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ecommerce-sentiment-platform")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "ecommerce-raw-data-mohammed")

def main():
    print("--- Starting Extraction & Cloud Ingestion ---")
    
    # 1. Extract and Stream Reviews Data
    reviews_bytes = extract_reviews_to_parquet(category=category_name, limit=50)
    upload_bytes_to_gcs(
        data_bytes=reviews_bytes,
        bucket_name=GCS_BUCKET_NAME,
        destination_blob_name=f"raw/reviews/{category_name.lower()}_reviews.parquet",
        project_id=GCP_PROJECT_ID
    )

    # 2. Extract and Stream Metadata
    metadata_bytes = extract_metadata_to_parquet(category=category_name, limit=50)
    upload_bytes_to_gcs(
        data_bytes=metadata_bytes,
        bucket_name=GCS_BUCKET_NAME,
        destination_blob_name=f"raw/metadata/{category_name.lower()}_metadata.parquet",
        project_id=GCP_PROJECT_ID
    )

    print("--- Ingestion Complete ---")

if __name__ == "__main__":
    main()
    