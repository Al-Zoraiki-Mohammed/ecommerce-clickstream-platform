import io
import pandas as pd
import pyarrow.parquet as pq
from datasets import load_dataset
from huggingface_hub import hf_hub_download, list_repo_files


def extract_reviews_dataframe(category: str = "All_Beauty", limit: int = 50000) -> pd.DataFrame:
    """Fetches review records and returns a Pandas DataFrame."""
    print(f"Fetching top {limit} reviews for category: {category}...")
    
    dataset = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_review_{category}",
        split="full",
        streaming=True,
        trust_remote_code=True
    )
    
    records = [item for item in dataset.take(limit)]
    df = pd.DataFrame(records)
    
    # Standardize types
    df["parent_asin"] = df["parent_asin"].astype(str)
    df["user_id"] = df["user_id"].astype(str)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    
    print(f"Successfully extracted {len(df)} review records.")
    return df


def extract_matching_metadata_dataframe(category: str, target_asins: list[str]) -> pd.DataFrame:
    """Downloads all metadata parquet chunks for a category and filters by target ASINs."""
    repo_id = "McAuley-Lab/Amazon-Reviews-2023"
    print(f"Fetching metadata for category: {category} matching {len(target_asins)} ASINs...")
    
    # 1. Fetch all repo file paths
    all_files = list_repo_files(repo_id=repo_id, repo_type="dataset")
    
    # 2. Target the exact metadata directory for this category
    target_prefix = f"raw_meta_{category}/"
    category_parquet_files = [
        f for f in all_files 
        if f.startswith(target_prefix) and f.endswith(".parquet")
    ]
    
    if not category_parquet_files:
        raise FileNotFoundError(f"No metadata files found matching prefix: {target_prefix}")
        
    print(f"  Found {len(category_parquet_files)} metadata file chunk(s) for {category}.")
    
    # 3. Read all chunks and combine
    dfs = []
    asin_set = set(target_asins)
    
    for file_path in category_parquet_files:
        cached_path = hf_hub_download(repo_id=repo_id, filename=file_path, repo_type="dataset")
        table = pq.read_table(cached_path)
        chunk_df = table.to_pandas()
        chunk_df["parent_asin"] = chunk_df["parent_asin"].astype(str)
        
        # Filter chunk immediately to save memory
        matched_chunk = chunk_df[chunk_df["parent_asin"].isin(asin_set)]
        if not matched_chunk.empty:
            dfs.append(matched_chunk)
            
    if not dfs:
        print(f"  Warning: No matching ASIN metadata found across files.")
        matched_df = pd.DataFrame(columns=["parent_asin"])
    else:
        matched_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["parent_asin"])
    
    # Fill object/complex columns as strings for schema stability in GCS/BigQuery
    for col in matched_df.columns:
        if matched_df[col].dtype == "object":
            matched_df[col] = matched_df[col].astype(str)
            
    print(f"Extracted {len(matched_df)} matching metadata records out of {len(asin_set)} target ASINs.")
    return matched_df

def dataframe_to_parquet_bytes(df: pd.DataFrame) -> bytes:
    """Converts a pandas DataFrame into in-memory Parquet bytes stream."""
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    return buffer.getvalue()
