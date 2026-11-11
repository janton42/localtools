# One localtools environment (DES-002) in a standalone project: no VPC, no
# organization. Cloud Build owns the container image; Terraform owns
# everything else. Modeled on hl_vae's vae-env module; nothing is shared with it.

locals {
  name = "home-${var.env}"
  apis = [
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
  ]
  # Deployed until the first Cloud Build run replaces it.
  placeholder_image = "us-docker.pkg.dev/cloudrun/container/hello"

  secret_name  = "${local.name}-app-env"
  sql_instance = "${local.name}-sql"

  # The only plain env vars. Everything else comes from the secret (DES-005).
  container_env = {
    DJANGO_SETTINGS_MODULE       = "localtools.settings.${var.env}"
    GCP_PROJECT_ID               = var.project_id
    GCP_SECRETS_NAME             = local.secret_name
    GCP_CLOUDSQL_CONNECTION_NAME = google_sql_database_instance.db.connection_name
    GCP_MEDIA_BUCKET             = google_storage_bucket.media.name
  }
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# --- Service accounts (no keys) ---------------------------------------------

resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "${local.name}-app"
  display_name = "localtools ${var.env} runtime (web and jobs)"
  depends_on   = [google_project_service.apis]
}

resource "google_service_account" "deploy" {
  project      = var.project_id
  account_id   = "${local.name}-deploy"
  display_name = "localtools ${var.env} Cloud Build deployer"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "app" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/logging.logWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = google_service_account.app.member
}

resource "google_project_iam_member" "deploy" {
  for_each = toset(concat(
    ["roles/run.developer", "roles/logging.logWriter"],
    # Deploys start the stopped-by-default database before migrating.
    var.sql_always_on ? [] : ["roles/cloudsql.editor"],
  ))
  project = var.project_id
  role    = each.value
  member  = google_service_account.deploy.member
}

resource "google_service_account_iam_member" "deploy_acts_as_app" {
  service_account_id = google_service_account.app.name
  role               = "roles/iam.serviceAccountUser"
  member             = google_service_account.deploy.member
}

# Cloud Run pulls the image as its own service agent, which can already read
# repositories in its own project. An environment in a different project from
# the repository would also need a reader grant for that agent here.
resource "google_artifact_registry_repository_iam_member" "deploy_writer" {
  project    = var.artifact_repo.project
  location   = var.artifact_repo.location
  repository = var.artifact_repo.name
  role       = "roles/artifactregistry.writer"
  member     = google_service_account.deploy.member
}

# --- Secret -----------------------------------------------------------------

# Container only. The value is a block of KEY=value lines, added by hand so no
# secret ends up in Terraform state (infra/README.md).
resource "google_secret_manager_secret" "app_env" {
  project   = var.project_id
  secret_id = local.secret_name
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

# Only the runtime reads it. The deployer and Cloud Build don't.
resource "google_secret_manager_secret_iam_member" "app_env" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.app_env.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.app.member
}

# --- Cloud SQL --------------------------------------------------------------

resource "google_sql_database_instance" "db" {
  project             = var.project_id
  name                = local.sql_instance
  region              = var.region
  database_version    = "POSTGRES_17"
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.sql_tier
    edition           = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_type         = var.sql_disk_type
    disk_size         = 10
    disk_autoresize   = true
    # Always created running (the database and user can't be created on a
    # stopped instance). With sql_always_on = false it's then stopped by the
    # nightly scheduler job and started by deploys.
    activation_policy           = "ALWAYS"
    deletion_protection_enabled = var.deletion_protection

    # No VPC. The instance has a public address but no authorised networks,
    # so nothing can connect to it directly. Cloud Run reaches it through its
    # built-in Cloud SQL connection (the cloudsql volume below), which
    # authenticates as the runtime service account and encrypts the link.
    ip_configuration {
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "08:00"
      point_in_time_recovery_enabled = var.sql_point_in_time_recovery
      transaction_log_retention_days = var.sql_point_in_time_recovery ? 7 : 1
      backup_retention_settings {
        retained_backups = var.sql_retained_backups
      }
    }

    # Sunday 03:00 Pacific
    maintenance_window {
      day  = 7
      hour = 10
    }
  }

  lifecycle {
    # Started and stopped outside Terraform (deploys, scheduler, by hand).
    ignore_changes = [settings[0].activation_policy]
  }

  depends_on = [google_project_service.apis]
}

# The DB user is created by hand so its password stays out of state
# (infra/README.md).
resource "google_sql_database" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.db.name
  name     = "localtools"
}

# Nightly stop, so the database only runs while someone is testing.
resource "google_service_account" "sql_scheduler" {
  count        = var.sql_nightly_stop ? 1 : 0
  project      = var.project_id
  account_id   = "${local.name}-sql-scheduler"
  display_name = "Stops ${local.sql_instance} nightly"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "sql_scheduler" {
  count   = var.sql_nightly_stop ? 1 : 0
  project = var.project_id
  role    = "roles/cloudsql.editor"
  member  = google_service_account.sql_scheduler[0].member
}

resource "google_cloud_scheduler_job" "sql_nightly_stop" {
  count     = var.sql_nightly_stop ? 1 : 0
  project   = var.project_id
  region    = var.region
  name      = "${local.sql_instance}-nightly-stop"
  schedule  = "0 2 * * *"
  time_zone = "America/Los_Angeles"

  http_target {
    http_method = "PATCH"
    uri         = "https://sqladmin.googleapis.com/v1/projects/${var.project_id}/instances/${local.sql_instance}"
    body        = base64encode(jsonencode({ settings = { activationPolicy = "NEVER" } }))
    headers     = { "Content-Type" = "application/json" }
    oauth_token {
      service_account_email = google_service_account.sql_scheduler[0].email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [google_project_service.apis]
}

# --- Media bucket -----------------------------------------------------------

# User uploads. How the app stores and serves them is DES-007; this only
# gives the runtime read and write access.
resource "google_storage_bucket" "media" {
  project                     = var.project_id
  name                        = var.media_bucket
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = !var.deletion_protection
  depends_on                  = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "app_media" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.app.member
}

# --- Cloud Run --------------------------------------------------------------

resource "google_cloud_run_v2_service" "web" {
  project             = var.project_id
  name                = "${local.name}-web"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL" # served on its run.app URL
  deletion_protection = var.deletion_protection

  template {
    service_account                  = google_service_account.app.email
    timeout                          = "300s"
    max_instance_request_concurrency = 80

    scaling {
      min_instance_count = var.web_min_instances
      max_instance_count = var.web_max_instances
    }

    # Mounts the database socket at /cloudsql/<connection name>/.
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.db.connection_name]
      }
    }

    containers {
      image = local.placeholder_image
      resources {
        limits            = { cpu = "1", memory = var.memory }
        cpu_idle          = true
        startup_cpu_boost = true
      }
      dynamic "env" {
        for_each = local.container_env
        content {
          name  = env.key
          value = env.value
        }
      }
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }

  lifecycle {
    # scaling: service-level block the API echoes back empty (scaling lives in template).
    ignore_changes = [template[0].containers[0].image, client, client_version, scaling]
  }

  depends_on = [google_project_service.apis, google_project_iam_member.app]
}

# Public. The project has no organization, so there is no sharing restriction
# and a plain grant to everyone is enough.
resource "google_cloud_run_v2_service_iam_member" "web_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# home-<env>-migrate runs on every deploy: migrations, then the cache table
# (the app's cache backend is a database table; createcachetable does nothing
# if it already exists). home-<env>-manage runs any management command on
# demand, with args given at execution (infra/README.md).
resource "google_cloud_run_v2_job" "jobs" {
  for_each = {
    migrate = ["sh", "-c", "python manage.py migrate --no-input && python manage.py createcachetable"]
    manage  = ["python", "manage.py", "showmigrations"]
  }
  project             = var.project_id
  name                = "${local.name}-${each.key}"
  location            = var.region
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.app.email
      max_retries     = 0
      timeout         = "1200s"

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.db.connection_name]
        }
      }

      containers {
        image   = local.placeholder_image
        command = [each.value[0]]
        args    = slice(each.value, 1, length(each.value))
        resources {
          limits = { cpu = "1", memory = var.memory }
        }
        dynamic "env" {
          for_each = local.container_env
          content {
            name  = env.key
            value = env.value
          }
        }
        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }

  depends_on = [google_project_service.apis, google_project_iam_member.app]
}

# --- CI/CD ------------------------------------------------------------------

# Needs the Cloud Build GitHub App (1st gen) installed on the repo and the
# repo connected to this project (one-time, by hand; infra/BOOTSTRAP.md).
resource "google_cloudbuild_trigger" "deploy" {
  project         = var.project_id
  location        = "global"
  name            = "${local.name}-deploy"
  description     = "Push to ${var.deploy_branch}: build, migrate and deploy ${var.env}"
  filename        = "infra/cloudbuild/deploy.yaml"
  service_account = google_service_account.deploy.id
  ignored_files   = ["infra/terraform/**", "**/*.md"]

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^${var.deploy_branch}$"
    }
  }

  substitutions = {
    _ENV       = var.env
    _REGION    = var.region
    _IMAGE     = var.image_repo
    _START_SQL = var.sql_always_on ? "false" : "true"
  }

  depends_on = [google_project_service.apis]
}
