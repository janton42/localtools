output "app_service_account" {
  value = google_service_account.app.email
}

output "deploy_service_account" {
  value = google_service_account.deploy.email
}

output "web_service_name" {
  value = google_cloud_run_v2_service.web.name
}

output "web_url" {
  value = google_cloud_run_v2_service.web.uri
}

output "sql_instance" {
  value = google_sql_database_instance.db.name
}

# The database socket is /cloudsql/<this>/.s.PGSQL.5432.
output "sql_connection_name" {
  value = google_sql_database_instance.db.connection_name
}

output "sql_database" {
  value = google_sql_database.app.name
}

output "secret_name" {
  value = google_secret_manager_secret.app_env.secret_id
}

output "media_bucket" {
  value = google_storage_bucket.media.name
}

output "deploy_trigger" {
  value = google_cloudbuild_trigger.deploy.name
}
