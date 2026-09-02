import os
import random
import pandas as pd
from datetime import datetime, timezone
from google.cloud import bigquery
from dotenv import load_dotenv

from sentiment import SentimentAnalyzer
from extract_data import dataframe_to_parquet_bytes
from load_data import upload_bytes_to_gcs

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ecommerce-sentiment-platform")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "ecommerce-raw-data-mohammed")

NEGATIVE_TEXTS = [
    ("Severe Defect", "Product stopped working immediately after unboxing. Terrible quality."),
    ("Waste of money", "Arrived broken and completely useless. Zero support from seller!"),
    ("Quality dropped", "The recent batch feels cheap compared to my previous order."),
    ("Poor craftsmanship", "Broke within two days of normal use. Highly disappointed."),
]

POSITIVE_TEXTS = [
    ("Works great!", "Exceeded my expectations. Fast shipping and high quality."),
    ("Highly recommend", "Solid build and does exactly what it promises."),
    ("Great value", "Fantastic product for the price point. Will buy again."),
    ("Five stars", "Super happy with this purchase. Outstanding performance."),
]


def fetch_active_asins_from_bigquery(limit: int = 100) -> list[str]:
    """Dynamically queries BigQuery to fetch active ASINs from existing data."""
    client = bigquery.Client(project=GCP_PROJECT_ID)
    
    # Check baseline external table first
    query = f"""
        SELECT DISTINCT parent_asin 
        FROM `{GCP_PROJECT_ID}.raw_data.raw_reviews_baseline` 
        LIMIT {limit}
    """
    print("Fetching active ASINs from BigQuery raw_reviews_baseline...")
    try:
        query_job = client.query(query)
        asins = [row.parent_asin for row in query_job.result() if row.parent_asin]
        if asins:
            print(f"Retrieved {len(asins)} active catalog ASINs.")
            return asins
    except Exception as e:
        print(f"Notice: Could not fetch from BigQuery ({e}). Falling back to default target ASIN.")

    return ["B08CVTH56M"]


def generate_realistic_daily_deltas(catalog_asins: list[str], num_reviews: int = 100) -> pd.DataFrame:
    """Generates daily deltas scattered across 24h with 1 targeted anomaly surge."""
    now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    data = []

    target_anomaly_asin = random.choice(catalog_asins) if catalog_asins else "B08CVTH56M"
    print(f"Injecting simulated negative sentiment surge for target ASIN: {target_anomaly_asin}")

    for _ in range(num_reviews):
        asin = random.choice(catalog_asins)
        user_id = f"USER_DELTA_{random.randint(10000, 99999)}"

        # Scatter timestamps across the past 24 hours
        random_offset_ms = random.randint(0, 86400 * 1000)
        review_timestamp = now_ts - random_offset_ms

        if asin == target_anomaly_asin and random.random() < 0.80:
            title, text = random.choice(NEGATIVE_TEXTS)
            rating = float(random.choice([1.0, 2.0]))
        else:
            if random.random() < 0.85:
                title, text = random.choice(POSITIVE_TEXTS)
                rating = float(random.choice([4.0, 5.0]))
            else:
                title, text = random.choice(NEGATIVE_TEXTS)
                rating = float(random.choice([1.0, 2.0, 3.0]))

        data.append({
            "user_id": user_id,
            "parent_asin": asin,
            "rating": rating,
            "title": title,
            "text": text,
            "timestamp": review_timestamp,
            "helpful_vote": random.randint(0, 15),
            "verified_purchase": True,
        })

    return pd.DataFrame(data)


def main():
    catalog_asins = fetch_active_asins_from_bigquery()
    df = generate_realistic_daily_deltas(catalog_asins, num_reviews=100)

    print(f"Running DistilBERT sentiment inference on {len(df)} daily delta reviews...")
    analyzer = SentimentAnalyzer()
    sentiment_results = analyzer.analyze_batch(df["text"].tolist())

    df["sentiment_label"] = [res["sentiment_label"] for res in sentiment_results]
    df["sentiment_score"] = [res["sentiment_score"] for res in sentiment_results]

    now = datetime.now(timezone.utc)
    
    # Destination blob set to raw/reviews_delta/ with Hive partitioning
    hive_partition_path = (
        f"raw/reviews_delta/"
        f"year={now.strftime('%Y')}/"
        f"month={now.strftime('%m')}/"
        f"day={now.strftime('%d')}/"
        f"delta_reviews_{int(now.timestamp())}.parquet"
    )

    parquet_bytes = dataframe_to_parquet_bytes(df)

    upload_bytes_to_gcs(
        data_bytes=parquet_bytes,
        bucket_name=GCS_BUCKET_NAME,
        destination_blob_name=hive_partition_path,
        project_id=GCP_PROJECT_ID,
    )
    print(f"Uploaded delta partition: gs://{GCS_BUCKET_NAME}/{hive_partition_path}")


if __name__ == "__main__":
    main()
    