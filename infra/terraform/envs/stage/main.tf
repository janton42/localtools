# localtools stage (DES-002): home-stage-514419, a standalone personal project.
# Apply infra/terraform/shared first.

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.20"
    }
  }
  # Created by hand (infra/BOOTSTRAP.md).
  backend "gcs" {
    bucket = "home-stage-514419-tfstate"
    prefix = "stage"
  }
}

provider "google" {
  project = "home-stage-514419"
  region  = "us-west1"
}

module "env" {
  source = "../../modules/home-env"

  env        = "stage"
  project_id = "home-stage-514419"

  # From shared/ (outputs image_repo and artifact_repo).
  image_repo    = "us-west1-docker.pkg.dev/home-stage-514419/home-images/localtools"
  artifact_repo = { project = "home-stage-514419", location = "us-west1", name = "home-images" }

  web_min_instances = 0
  web_max_instances = 3
  memory            = "1Gi"

  # Stopped unless someone is testing: about $1/mo stopped.
  sql_disk_type              = "PD_HDD"
  sql_always_on              = false
  sql_nightly_stop           = true
  sql_retained_backups       = 1
  sql_point_in_time_recovery = false
  deletion_protection        = false

  media_bucket = "home-stage-media-4269"

  deploy_branch = "staging"
}

output "env" {
  value = module.env
}
