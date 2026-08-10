variable "project_id" {
  description = "My GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for resources"
  type        = string
  default     = "europe-west1"
}

variable "bucket_name" {
  description = "GCS Bucket Name for raw data"
  type        = string
}
