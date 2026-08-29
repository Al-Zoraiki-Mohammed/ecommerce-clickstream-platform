import os
from dotenv import load_dotenv
from scripts.extract_data import (
    extract_reviews_dataframe,
    extract_matching_metadata_dataframe,
    dataframe_to_parquet_bytes
)
from scripts.load_data import upload_bytes_to_gcs

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ecommerce-sentiment-platform")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "ecommerce-raw-data-mohammed")

# Target categories for cross-category benchmarking
TARGET_CATEGORIES = [
    "All_Beauty",
    "Toys_and_Games",
    "Gift_Cards"
]

# 15,000 reviews per category = ~45k total rows (~20 MB GCS footprint)
REVIEWS_PER_CATEGORY = 15000

def main():
    print("==================================================")
    print(" Starting Phase 1: Historical Data Ingestion      ")
    print("==================================================")
    
    for category in TARGET_CATEGORIES:
        print(f"\n--- Processing Category: {category} ---")
        
        # 1. Extract reviews DataFrame
        reviews_df = extract_reviews_dataframe(category=category, limit=REVIEWS_PER_CATEGORY)
        
        # 2. Extract unique ASIN keys from reviews
        unique_asins = reviews_df["parent_asin"].unique().tolist()
        
        # 3. Extract matching metadata DataFrame
        metadata_df = extract_matching_metadata_dataframe(category=category, target_asins=unique_asins)
        
        # 4. Stream Reviews Parquet to GCS
        reviews_bytes = dataframe_to_parquet_bytes(reviews_df)
        upload_bytes_to_gcs(
            data_bytes=reviews_bytes,
            bucket_name=GCS_BUCKET_NAME,
            destination_blob_name=f"raw/reviews/{category.lower()}_reviews.parquet",
            project_id=GCP_PROJECT_ID
        )
        
        # 5. Stream Metadata Parquet to GCS
        metadata_bytes = dataframe_to_parquet_bytes(metadata_df)
        upload_bytes_to_gcs(
            data_bytes=metadata_bytes,
            bucket_name=GCS_BUCKET_NAME,
            destination_blob_name=f"raw/metadata/{category.lower()}_metadata.parquet",
            project_id=GCP_PROJECT_ID
        )

    print("\n==================================================")
    print(" Phase 1 Ingestion Completed Successfully!        ")
    print("==================================================")

if __name__ == "__main__":
    main()
    