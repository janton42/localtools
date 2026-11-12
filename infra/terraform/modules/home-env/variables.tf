variable "env" {
  description = "Environment name, e.g. stage. Used as the home-<env>-* resource prefix."
  type        = string
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-west1"
}

# --- Cloud Run --------------------------------------------------------------

variable "image_repo" {
  description = "Artifact Registry image path without a tag (output image_repo of shared/)."
  type        = string
}

variable "artifact_repo" {
  description = "Artifact Registry repository the image lives in (output artifact_repo of shared/)."
  type = object({
    project  = string
    location = string
    name     = string
  })
}

variable "web_min_instances" {
  type    = number
  default = 0
}

variable "web_max_instances" {
  type    = number
  default = 3
}

variable "memory" {
  description = "Memory for the web service and the jobs. The resume parser loads scikit-learn models and NLTK data; revisit once DES-008 shows what the image needs."
  type        = string
  default     = "1Gi"
}

# --- Cloud SQL --------------------------------------------------------------

variable "sql_tier" {
  type    = string
  default = "db-f1-micro"
}

variable "sql_disk_type" {
  description = "PD_SSD or PD_HDD. Can't be changed after creation."
  type        = string
}

variable "sql_always_on" {
  description = "false: deploys start the instance (so the deploy SA may); combine with sql_nightly_stop to keep it off when idle."
  type        = bool
}

variable "sql_nightly_stop" {
  description = "Cloud Scheduler job that stops the instance every night."
  type        = bool
  default     = false
}

variable "sql_retained_backups" {
  type = number
}

variable "sql_point_in_time_recovery" {
  type = bool
}

variable "deletion_protection" {
  description = "Protects the database instance, the web service and the media bucket's contents from terraform destroy."
  type        = bool
}

# --- Media ------------------------------------------------------------------

variable "media_bucket" {
  description = "Globally unique name of the bucket that holds user uploads (DES-007)."
  type        = string
}

# --- CI/CD ------------------------------------------------------------------

variable "github_owner" {
  type    = string
  default = "janton42"
}

variable "github_repo" {
  type    = string
  default = "localtools"
}

variable "deploy_branch" {
  description = "Pushes to this branch build and deploy this environment."
  type        = string
}
