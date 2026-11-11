# DES-002: GCP infrastructure (stage on Cloud Run)

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-11
- **Updated:** 2026-11-11
- **Related:** DES-003 to DES-011 (follow-ups, still ideas). Layout modeled on the hl_vae project's `infra/`; no resources are shared with it.

## Summary

localtools gets one hosted environment, **stage**, on Google Cloud, in the
personal project `home-stage-514419`. It runs on Cloud Run with a Cloud SQL
database, Secret Manager, a storage bucket for uploads, keyless service
accounts and Cloud Build deploys, all provisioned by Terraform in `infra/`.

## Motivation / Problem

The site is deployed by hand on PythonAnywhere with a MySQL database. Nothing
about that environment is written down or reproducible: there is no
infrastructure code, no deploy pipeline and no staging copy to test against.
The settings for it are committed, but the environment itself can only be
changed by logging in and editing it.

Moving to Google Cloud gives an environment that is defined in git, reviewed
in pull requests and deployed by pushing a branch. Stage comes first so the
move can be proven without touching the live site. Prod and the jeffstock.us
cutover are a later design (DES-011).

## Goals and Non-goals

**Goals**

- A reproducible stage environment, defined in Terraform and reviewed in git.
- A push to a `staging` branch builds, migrates and deploys.
- No service account keys anywhere, and no secrets or passwords in Terraform state.
- Low idle cost: the web service scales to zero.
- Everything lives in `home-stage-514419`, owned by the personal Google account.
- Define what the app has to provide (the app contract below) so DES-003 to
  DES-008 can be designed against it.

**Non-goals**

- A prod environment, a custom domain, a load balancer or a CDN (DES-011).
- Any HiredLabs resource. No Shared VPC, no organization policy, no shared
  state bucket, no shared database or secrets. Only the directory layout and
  conventions are borrowed.
- Moving the live data (DES-010).
- Background workers or task queues. django-q is commented out today and stays out.
- A cloud dev environment. Dev stays local.

## Proposed Design

### Naming and placement

Resources are named `home-<env>-<thing>`, so on stage that is `home-stage-*`.
The project `home-stage-514419` stands alone: it belongs to a personal
account and has no organization or folder above it. The proposed region is
us-west1 (see Open Questions).

### Resources

| Piece | Stage | Notes |
|---|---|---|
| Project | `home-stage-514419` | Already created. Billing must be linked (bootstrap) |
| Cloud Run web | `home-stage-web` | Public. Scales from zero to a small maximum. Starts on a placeholder image; Terraform ignores later image changes because Cloud Build owns the image |
| Cloud Run jobs | `home-stage-migrate`, `home-stage-manage` | The first runs database migrations on every deploy. The second runs any management command, with the command given at execution time |
| Database | `home-stage-sql` | Cloud SQL, smallest shared-core tier, small disk, single zone, one retained backup, no deletion protection. Engine is an open question. Terraform creates the instance and the database; the user and password are created by hand so they stay out of state |
| Secret | `home-stage-app-env` | One Secret Manager secret holding the app's environment as a single block of key-value lines. Terraform creates only the empty secret; values are added by hand |
| Media bucket | `home-stage-media` (globally unique name to be settled) | Holds user uploads, which today go to the local `media/` directory and would be lost on Cloud Run. How the app uses it is DES-007 |
| Service accounts | `home-stage-app`, `home-stage-deploy` | The first is the runtime identity for the web service and jobs: it can connect to the database, read the secret, read and write the media bucket and write logs. The second is the Cloud Build deployer: it can push images, update the service and jobs, and act as the runtime identity. Neither has keys. The default compute service account is not used |
| Images | Artifact Registry repository in the same project | Each build is tagged with the short commit hash and with the environment name. A cleanup policy keeps recent images and removes old ones |
| Deploy trigger | `home-stage-deploy` | Cloud Build trigger on `janton42/localtools`, branch `staging`, reading the pipeline file from `infra/cloudbuild/`. Changes that touch only Terraform or Markdown do not trigger a deploy |
| Terraform state | A versioned bucket inside `home-stage-514419` | Created by hand in the bootstrap. One prefix per Terraform root |

### How this differs from hl_vae

| hl_vae | Here | Why |
|---|---|---|
| Service project attached to a Shared VPC | No VPC at all | The project stands alone, and the connection below needs no network |
| Database on a private address inside the shared network | Cloud Run's built-in Cloud SQL connection | Cloud Run mounts a local socket to the instance and authenticates with the runtime service account. The instance has a public address but no authorised networks, so only identities with the database-client role can reach it. No connector, no subnet, nothing to pay for |
| Organization policy override to allow a public service | None | A project with no organization has no such policy; the service is made public directly |
| State in a shared, pre-existing bucket | Own bucket, created in the bootstrap | Nothing is shared |
| `shared/` root attaches the VPC, overrides policy, creates the image repo | `shared/` enables project-wide APIs and creates the image repo | Kept as its own root so a later prod project can read images from one place |
| No media bucket | Media bucket | This app accepts uploads |

### Repo layout

```
infra/
├── README.md            # what lives where, conventions, day-2 runbook
├── BOOTSTRAP.md         # one-time setup, done by hand
├── cloudbuild/          # the deploy pipeline definition
└── terraform/
    ├── .gitignore       # local Terraform working files, state and plans
    ├── shared/          # project-wide APIs, the image repository
    ├── modules/
    │   └── home-env/    # one environment: everything in the resource table except the image repo
    └── envs/
        └── stage/       # calls the module with stage values
```

The module takes the environment name and project as inputs, so a prod
environment later is a new directory under `envs/` and not a redesign.

### Deploy pipeline

A push to `staging` starts the Cloud Build trigger, which runs these steps in
order and stops at the first failure:

1. Pull the previous image for the environment, to use as a build cache. A
   missing image is not an error.
2. Build the container image from the repo's Dockerfile and tag it with the
   commit hash and the environment name.
3. Push both tags to the image repository.
4. If the database is configured to be stopped when idle, start it and wait
   until it is ready.
5. Point both jobs at the new image and run the migrate job, waiting for it
   to finish.
6. Deploy the new image to the web service.

No step reads the app secret; only the runtime service account can. `develop`
is promoted by fast-forwarding `staging` to the commit on `origin/develop`,
never to a local branch.

### App contract

What the app has to provide before the first deploy can work. Each item is
designed in its own doc.

| Need | Doc |
|---|---|
| Pinned dependencies that install in a container, a production WSGI server, and the database driver for the chosen engine | DES-003 |
| A stage settings module with debug off, hosts and CSRF origins taken from the environment, and a default settings module that resolves | DES-004 |
| At startup on Cloud Run, the app reads the secret named in its environment and loads it as settings; locally it keeps reading a `.env` file | DES-005 |
| Static files collected at build time and served by the app, with the build output no longer tracked in git | DES-006 |
| Uploads stored in the media bucket | DES-007 |
| A Dockerfile that builds the Tailwind stylesheet and installs the ML dependencies and their data files, and listens on the port Cloud Run provides | DES-008 |
| Tests, lint and Terraform format and validate checks on every pull request | DES-009 |

The resume parser loads scikit-learn models and NLTK data, so the web
service's memory setting is chosen once DES-008 shows what the image needs.

### Cost

Rough expectation for an idle stage, to be confirmed after the first month's
bill: the web service, image repository, secret and buckets cost cents. The
database is the only real cost: about ten dollars a month if it runs all the
time, or a dollar or two for storage alone if it is stopped when nobody is
testing (see Open Questions).

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Stay on PythonAnywhere | Nothing to build | Manual deploys, no stage, no infrastructure in git | The reason for this work |
| Private-address database on a dedicated VPC | Database has no public address at all | Needs a network, a subnet and a private services range; more to manage for a personal site | The built-in connection already restricts access by identity. Can be revisited for prod |
| SQLite on a mounted volume or bucket | Cheapest | Unsafe with more than one instance; not what production will use | Stage should match prod |
| A VM running the app and database | Full control, fixed cost | Patching, no scale to zero, manual deploys again | Cloud Run removes the server |
| App Engine | Simple deploys | Less control over the container; the ML dependencies fit a custom image better | Cloud Run fits the container build |

## Implementation Plan

Each step is its own branch and pull request unless marked as done by hand.

- [ ] Settle the open questions below and update this doc.
- [ ] Design and build the app contract items (DES-003 to DES-008) and CI (DES-009).
- [ ] Bootstrap by hand, following `infra/BOOTSTRAP.md`: billing, state bucket, GitHub connection, `staging` branch, local credentials.
- [ ] Write `terraform/shared`: project-wide APIs and the image repository.
- [ ] Write `terraform/modules/home-env` and `terraform/envs/stage`.
- [ ] Write the Cloud Build pipeline in `infra/cloudbuild/`.
- [ ] Apply `shared`, then `envs/stage` (by hand).
- [ ] Create the database user and the first secret version (by hand).
- [ ] First deploy: promote `develop` to `staging`.
- [ ] Fill in the runbook in `infra/README.md`: promote, run a management command, edit and rotate secrets.

## Testing / Verification

- Terraform format and validate pass on every root; a plan after apply shows no changes.
- A push to `staging` completes every pipeline step.
- The stage URL serves the home page with styles, the admin login works with
  no host or CSRF error, and an uploaded image is still there after a new deploy.
- Django's deployment check passes when run through the manage job.
- No service account keys exist in the project, and the Terraform state
  contains no password or secret value.

## Open Questions

- **Database engine.** Postgres or MySQL. MySQL is what the site runs today,
  so the data moves with an ordinary dump and restore and the app needs no
  driver change. Postgres matches the patterns and runbooks already in use on
  hl_vae, and is the more common pairing with Django, but the data has to be
  moved through Django's own export and import, and any MySQL-specific
  behaviour in the apps has to be found and fixed. Both run on the same
  smallest Cloud SQL tier at a similar price.
- **Region.** us-west1 is proposed. Any reason to prefer another?
- **Stopping the database when idle.** hl_vae stops its stage database every
  night and lets deploys start it, which saves most of the cost but makes the
  first request after a stop fail until someone starts it. Worth it here?
- **GitHub connection.** Use the Cloud Build GitHub App (first generation, as
  on hl_vae) or a second-generation repository connection?
- **Media bucket name.** Bucket names are global; `home-stage-media` may be taken.

## Changelog

- 2026-11-11 — Created.
