import os
import pyarrow.parquet as pq
from huggingface_hub import list_repo_files, hf_hub_download

os.makedirs("data/raw", exist_ok=True)

def download_dataset():
    repo_id = "McAuley-Lab/Amazon-Reviews-2023"
    
    print("1. Looking up exact Parquet files in Hugging Face repository...")
    all_files = list_repo_files(repo_id=repo_id, repo_type="dataset")
    
    # Filter for any Electronics metadata Parquet file across folders (full/raw)
    parquet_files = [
        f for f in all_files 
        if "meta" in f.lower() and "electronics" in f.lower() and f.endswith(".parquet")
    ]
    
    if not parquet_files:
        # Fallback: print available directories to help debug pathing
        meta_files = [f for f in all_files if "meta" in f.lower() and f.endswith(".parquet")]
        print(f"Available metadata files sample: {meta_files[:3]}")
        raise FileNotFoundError("Could not locate Electronics metadata Parquet file.")
        
    target_file = parquet_files[0]
    print(f"   Found target file: {target_file}")
    
    print("2. Downloading Parquet file...")
    cached_path = hf_hub_download(
        repo_id=repo_id,
        filename=target_file,
        repo_type="dataset"
    )
    
    print("3. Slicing first 50,000 records...")
    table = pq.read_table(cached_path)
    table_subset = table.slice(0, 50000)
    
    local_meta_path = "data/raw/amazon_electronics_meta.parquet"
    pq.write_table(table_subset, local_meta_path)
    
    print(f"✅ Success! Saved {len(table_subset):,} records to: {local_meta_path}")

if __name__ == "__main__":
    download_dataset()