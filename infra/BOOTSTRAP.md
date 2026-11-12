# Bootstrap (one time, by hand)

Done once, before the first `terraform apply`. Everything after this is in
Terraform or in the [README](README.md). The design is
[DES-002](../docs/active/DES-002-gcp-infrastructure.md).

## Who can do it

The owner of `home-stage-514419`, signed in with the personal Google account.
The local gcloud configuration for this project is `home-stage`. Every command
below names the project or the configuration explicitly, so a different active
configuration can't send it to the wrong place, but check anyway:

```bash
gcloud config configurations describe home-stage
```

It should show the personal account and `home-stage-514419`.

## Steps

1. **Base APIs.** Terraform needs these before it can enable anything else,
   and Cloud Build has to be on before the repository can be connected:

   ```bash
   gcloud services enable \
     serviceusage.googleapis.com \
     cloudresourcemanager.googleapis.com \
     iam.googleapis.com \
     cloudbuild.googleapis.com \
     --project=home-stage-514419 --configuration=home-stage
   ```

2. **State bucket.** A private, versioned bucket for Terraform state:

   ```bash
   gcloud storage buckets create gs://home-stage-514419-tfstate \
     --project=home-stage-514419 --configuration=home-stage \
     --location=us-west1 --uniform-bucket-level-access --public-access-prevention
   gcloud storage buckets update gs://home-stage-514419-tfstate \
     --versioning --configuration=home-stage
   ```

3. **GitHub connection.** In `home-stage-514419`: Console → Cloud Build →
   Triggers → **Connect repository** → GitHub (Cloud Build GitHub App,
   **1st gen**) → `janton42/localtools`. Don't create a trigger there;
   Terraform creates `home-stage-deploy`. This has to be done before applying
   `envs/stage`, or creating the trigger fails.

4. **`staging` branch.** Create it on GitHub from GitHub's `develop`:

   ```bash
   git fetch origin && git push origin origin/develop:refs/heads/staging
   ```

   Nothing deploys yet: the trigger doesn't exist until `envs/stage` is applied.

5. **Credentials for Terraform.** Terraform acts as the project owner. Give it
   a short-lived token from the `home-stage` configuration, in the shell that
   will run Terraform:

   ```bash
   export GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token --configuration=home-stage)"
   ```

   The token lasts an hour; run the line again when it expires. This is used
   instead of `gcloud auth application-default login` on purpose: application
   default credentials are one file for the whole machine, so signing in with
   the personal account would replace any work credentials stored there, and
   a leftover work sign-in could be picked up by Terraform here. The token
   can only ever belong to the personal account.

Then continue with the runbook in the [README](README.md).
