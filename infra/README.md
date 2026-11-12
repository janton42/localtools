# infra/

Where the Google Cloud infrastructure for localtools will live. The design is
[DES-002](../docs/active/DES-002-gcp-infrastructure.md).

**Nothing is provisioned yet.** This directory is a skeleton: the Terraform
and Cloud Build files are added when DES-002 is implemented, and the runbook
below is filled in then.

| Path | What it will hold |
|---|---|
| `BOOTSTRAP.md` | One-time setup, done by hand before the first apply |
| `terraform/shared` | Project-wide APIs and the Artifact Registry image repository |
| `terraform/modules/home-env` | One environment: service accounts, database, secret, media bucket, Cloud Run web service and jobs, deploy trigger |
| `terraform/envs/stage` | The stage root, in project `home-stage-514419` |
| `cloudbuild/` | The deploy pipeline: build, push, migrate, deploy. A push to `staging` runs it |

**Conventions**

- The project belongs to the personal Google account. Nothing here uses or
  refers to any HiredLabs project, network, bucket, database or secret.
- Resources are named `home-<env>-<thing>`, e.g. `home-stage-web`.
- No service account keys anywhere. Cloud Run and Cloud Build use their
  service accounts directly.
- Cloud Build owns container images. Terraform owns everything else.
- Secrets and the database password never go through Terraform, so they stay
  out of state. Terraform creates only the empty secret.
- Terraform state lives in a bucket inside the project, one prefix per root.
- Terraform `plan` and `apply` are run by hand. CI only checks formatting and validity.

## Runbook

To be written when stage exists: standing up stage, promoting `develop` to
`staging`, running a management command, and editing and rotating secrets.
