from google.cloud import storage


def upload_bytes_to_gcs(
    data_bytes: bytes,
    bucket_name: str,
    destination_blob_name: str,
    project_id: str | None = None
) -> None:
    """Streams raw in-memory bytes directly to a GCS bucket blob."""
    
    # Instantiate client (uses GCP service account key or ADC environment variables)
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    print(f"Uploading in-memory stream to gs://{bucket_name}/{destination_blob_name}...")
    
    # Upload directly from bytes string
    blob.upload_from_string(data_bytes, content_type="application/octet-stream")
    
    print(f"Successfully uploaded to gs://{bucket_name}/{destination_blob_name}")
    