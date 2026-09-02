import os
from dotenv import load_dotenv
import pandas as pd
from scripts.sentiment import SentimentAnalyzer

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

# 15,000 reviews per category = ~45k total rows
REVIEWS_PER_CATEGORY = 15000

def process_reviews_sentiment(df: pd.DataFrame, analyzer: SentimentAnalyzer) -> pd.DataFrame:
    """
    Extracts text from reviews, runs batch sentiment analysis using Hugging Face DistilBERT,
    and attaches sentiment_label and sentiment_score columns.
    """
    # Detect the correct text column name in your dataset
    text_col = "text" if "text" in df.columns else ("review_text" if "review_text" in df.columns else None)
    
    if text_col:
        reviews_list = df[text_col].fillna("").tolist()
    else:
        print("Warning: No valid text column found for sentiment analysis.")
        reviews_list = [""] * len(df)

    print(f"Running sentiment analysis on {len(reviews_list)} reviews...")
    sentiment_results = analyzer.analyze_batch(reviews_list)

    # Attach sentiment predictions to the DataFrame
    df["sentiment_label"] = [res["sentiment_label"] for res in sentiment_results]
    df["sentiment_score"] = [res["sentiment_score"] for res in sentiment_results]

    return df

def main():
    print("==================================================")
    print(" Starting Phase 1: Historical Data Ingestion      ")
    print("==================================================")

    # Instantiate the Sentiment Analyzer once to avoid re-loading the model per category
    analyzer = SentimentAnalyzer()

    for category in TARGET_CATEGORIES:
        print(f"\n--- Processing Category: {category} ---")

        # 1. Extract reviews DataFrame
        reviews_df = extract_reviews_dataframe(category=category, limit=REVIEWS_PER_CATEGORY)

        # 2. Enrich reviews DataFrame with NLP sentiment scores
        reviews_df = process_reviews_sentiment(df=reviews_df, analyzer=analyzer)

        # 3. Extract unique ASIN keys from reviews
        unique_asins = reviews_df["parent_asin"].unique().tolist()

        # 4. Extract matching metadata DataFrame
        metadata_df = extract_matching_metadata_dataframe(category=category, target_asins=unique_asins)

        # 5. Stream enriched Reviews Parquet to GCS
        reviews_bytes = dataframe_to_parquet_bytes(reviews_df)
        upload_bytes_to_gcs(
            data_bytes=reviews_bytes,
            bucket_name=GCS_BUCKET_NAME,
            destination_blob_name=f"raw/reviews/{category.lower()}_reviews.parquet",
            project_id=GCP_PROJECT_ID
        )

        # 6. Stream Metadata Parquet to GCS
        metadata_bytes = dataframe_to_parquet_bytes(metadata_df)
        upload_bytes_to_gcs(
            data_bytes=metadata_bytes,
            bucket_name=GCS_BUCKET_NAME,
            destination_blob_name=f"raw/metadata/{category.lower()}_metadata.parquet",
            project_id=GCP_PROJECT_ID
        )

    print("\n==================================================")
    print(" Phase 1 Ingestion & Sentiment Enrichment Completed!")
    print("==================================================")

if __name__ == "__main__":
    main()