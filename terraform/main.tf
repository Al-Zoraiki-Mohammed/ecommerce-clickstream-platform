resource "google_storage_bucket" "sentiment_bucket" {
  name                        = var.bucket_name
  location                    = var.region
  force_destroy               = false
  public_access_prevention    = "enforced"
  uniform_bucket_level_access = true
}

resource "google_bigquery_dataset" "raw_data" {
  dataset_id                  = "raw_data"
  location                    = var.region
  default_table_expiration_ms = null
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "analytics"
  location                    = var.region
  default_table_expiration_ms = null
}
