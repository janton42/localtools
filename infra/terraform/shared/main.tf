# Resources outside the environment module (DES-002): the project-wide APIs
# and the Artifact Registry repository that holds the app's images. Kept as
# its own root so a later prod project can read images from one place.
# Apply this before envs/stage.

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
    prefix = "shared"
  }
}

locals {
  region  = "us-west1"
  project = "home-stage-514419"
}

provider "google" {
  project = local.project
  region  = local.region
}

# The first four are also enabled by hand in the bootstrap, because Terraform
# can't enable anything without them. Listing them here keeps them on record.
resource "google_project_service" "apis" {
  for_each = toset([
    "serviceusage.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ])
  project            = local.project
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "images" {
  project       = local.project
  location      = local.region
  repository_id = "home-images"
  format        = "DOCKER"
  description   = "localtools images, built by Cloud Build"

  # Keep the 10 newest and anything tagged with an environment name; delete
  # the rest after 30 days.
  cleanup_policy_dry_run = false
  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
  cleanup_policies {
    id     = "keep-env-tags"
    action = "KEEP"
    condition {
      tag_state    = "TAGGED"
      tag_prefixes = ["stage", "prod"]
    }
  }
  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "2592000s" # 30 days
    }
  }

  depends_on = [google_project_service.apis]
}

# Inputs of the environment module (envs/stage/main.tf).
output "image_repo" {
  value = "${local.region}-docker.pkg.dev/${local.project}/${google_artifact_registry_repository.images.repository_id}/localtools"
}

output "artifact_repo" {
  value = {
    project  = local.project
    location = local.region
    name     = google_artifact_registry_repository.images.repository_id
  }
}
