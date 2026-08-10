terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "raw_data_bucket" {
  name                     = var.bucket_name
  location                 = var.region
  force_destroy            = false
  public_access_prevention = "enforced"
}

resource "google_bigquery_dataset" "bronze" {
  dataset_id  = "ecommerce_bronze"
  description = "Raw ingested data from GCS and streaming sources"
  location    = var.region
}

resource "google_bigquery_dataset" "silver" {
  dataset_id  = "ecommerce_silver"
  description = "Cleaned and deduplicated source-of-truth tables"
  location    = var.region
}

resource "google_bigquery_dataset" "gold" {
  dataset_id  = "ecommerce_gold"
  description = "Business metrics and aggregated analytical tables"
  location    = var.region
}
