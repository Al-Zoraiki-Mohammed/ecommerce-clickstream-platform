import io
import pandas as pd
import pyarrow.parquet as pq
from datasets import load_dataset
from huggingface_hub import hf_hub_download
from huggingface_hub import hf_hub_download, list_repo_files


def extract_reviews_to_parquet(category: str = "All_Beauty", limit: int = 50000) -> bytes:
    """Fetches review data from Hugging Face and returns in-memory Parquet bytes."""
    print(f"Fetching top {limit} reviews for category: {category}...")
    
    dataset = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_review_{category}",
        split="full",
        streaming=True,
        trust_remote_code=True
    )
    
    records = []
    for item in dataset.take(limit):
        records.append(item)
        
    df = pd.DataFrame(records)
    print(f"Extracted {len(df)} review records successfully.")

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    
    return buffer.getvalue()


def extract_metadata_to_parquet(category: str = "All_Beauty", limit: int = 50000) -> bytes:
    """Infers exact Hugging Face metadata path dynamically, downloads file, and slices in memory."""
    repo_id = "McAuley-Lab/Amazon-Reviews-2023"
    print(f"Fetching top {limit} metadata items for category: {category}...")
    
    # 1. Dynamically list repository files to discover target path
    all_files = list_repo_files(repo_id=repo_id, repo_type="dataset")
    
    category_lower = category.lower()
    parquet_files = [
        f for f in all_files 
        if "meta" in f.lower() and category_lower in f.lower() and f.endswith(".parquet")
    ]
    
    if not parquet_files:
        raise FileNotFoundError(f"Could not locate metadata Parquet file for category: {category}")
        
    target_file = parquet_files[0]
    print(f"  Found target metadata file: {target_file}")
    
    # 2. Download file to HF cache
    cached_path = hf_hub_download(
        repo_id=repo_id,
        filename=target_file,
        repo_type="dataset"
    )
    
    # 3. Read and slice via PyArrow (bypasses datasets schema errors)
    table = pq.read_table(cached_path)
    if limit and len(table) > limit:
        table = table.slice(0, limit)
        
    df = table.to_pandas()
    
    # Convert object/complex columns to string format for GCS/Bronze layer schema stability
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)
            
    print(f"Extracted {len(df)} metadata records successfully.")

    # 4. Return as in-memory bytes for cloud upload
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    
    return buffer.getvalue()
