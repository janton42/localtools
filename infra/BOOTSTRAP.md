# Bootstrap (one time, by hand)

**Draft.** This is the outline of what has to be done once, by hand, before
the first Terraform apply. The exact commands are added when
[DES-002](../docs/designed/DES-002-gcp-infrastructure.md) is implemented.

## Who can do it

The owner of `home-stage-514419`, signed in with the personal Google account.
The local gcloud configuration for this project is `home-stage`; check it is
the active one before running anything.

## Steps

1. **Billing.** Confirm the project is linked to the personal billing account.
2. **State bucket.** Create a versioned storage bucket in the project for
   Terraform state.
3. **GitHub connection.** Connect the `janton42/localtools` repository to
   Cloud Build in the project, without creating a trigger. Terraform creates
   the trigger, and that fails if the repository isn't connected first.
4. **`staging` branch.** Create `staging` on GitHub from `develop`.
5. **Local credentials.** Sign in for application default credentials with
   the personal account, so Terraform can act as the project owner.

Then continue with the runbook in the [README](README.md).
