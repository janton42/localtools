# DES-002: GCP infrastructure (stage on Cloud Run)

- **Status:** In Progress
- **Area:** Infrastructure
- **Created:** 2026-11-11
- **Updated:** 2026-11-11
- **Depends on:** DES-003, DES-004, DES-005, DES-006, DES-007, DES-008 (see Dependencies)
- **Related:** DES-009 to DES-011 (follow-ups, still ideas). Layout modeled on the hl_vae project's `infra/`; no resources are shared with it.

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
- Designing or building the app contract items. Each is its own design
  (DES-003 to DES-008) and its own stream of work; this design depends on
  them but does not contain them.

## Dependencies

The infrastructure can be written and applied without the app changes, but
stage cannot be deployed until the app meets the app contract below. Each
item is a separate design with its own doc, branch and pull requests.

| Design | What DES-002 needs from it | Blocks |
|---|---|---|
| DES-003 | Pinned dependencies, a production WSGI server, the PostgreSQL driver | First deploy |
| DES-004 | `localtools.settings.stage` and a default settings module that resolves | First deploy |
| DES-005 | The app loads the secret at startup, and the list of keys the secret must hold | First secret version, first deploy |
| DES-006 | Static files collected at build time and served by the app | First deploy |
| DES-007 | Uploads stored in the media bucket | First deploy |
| DES-008 | The Dockerfile the pipeline builds; the memory the image needs | First deploy |

Before starting a step marked as gated in the Implementation Plan, check the
backlog: every design listed above must be **Done**. If any is not, stop and
do not start the step.

## Proposed Design

### Naming and placement

Resources are named `home-<env>-<thing>`, so on stage that is `home-stage-*`.
The project `home-stage-514419` stands alone: it belongs to a personal
account and has no organization or folder above it. Everything is in
us-west1.

### Resources

| Piece | Stage | Notes |
|---|---|---|
| Project | `home-stage-514419` | Already created with billing attached. |
| Cloud Run web | `home-stage-web` | Public. Scales from zero to a small maximum. Starts on a placeholder image; Terraform ignores later image changes because Cloud Build owns the image |
| Cloud Run jobs | `home-stage-migrate`, `home-stage-manage` | The first runs on every deploy: it applies database migrations and then creates the database cache table if it is missing (the app's cache backend is a database table). The second runs any management command, with the command given at execution time |
| Database | `home-stage-sql` | Cloud SQL for PostgreSQL 17, Enterprise edition, smallest shared-core tier, 10 GB hard-disk storage, single zone, one retained backup, no point-in-time recovery, no deletion protection. Terraform creates the instance and a database named `localtools`; the user (also `localtools`) and its password are created by hand so they stay out of state |
| Nightly database stop | `home-stage-sql-nightly-stop` | A Cloud Scheduler job that stops the database every night at 02:00 Pacific, so it only runs while someone is testing. Deploys start it again. While it is stopped, pages that need the database fail; it can also be started and stopped by hand. Terraform ignores whether the instance is running |
| Secret | `home-stage-app-env` | One Secret Manager secret holding the app's environment as a single block of key-value lines. Terraform creates only the empty secret; values are added by hand |
| Media bucket | `home-stage-media-4269` | Holds user uploads, which today go to the local `media/` directory and would be lost on Cloud Run. How the app uses it is DES-007 |
| Service accounts | `home-stage-app`, `home-stage-deploy`, `home-stage-sql-scheduler` | The first is the runtime identity for the web service and jobs: it can connect to the database, read the secret, read and write the media bucket and write logs. The second is the Cloud Build deployer: it can push images, update the service and jobs, start the database and act as the runtime identity. The third is used only by the nightly stop and can only administer Cloud SQL instances. None has keys. The default compute service account is not used |
| Images | Artifact Registry repository in the same project | Each build is tagged with the short commit hash and with the environment name. A cleanup policy keeps recent images and removes old ones |
| Deploy trigger | `home-stage-deploy` | Cloud Build trigger on `janton42/localtools`, connected through the first-generation Cloud Build GitHub App, branch `staging`, reading the pipeline file from `infra/cloudbuild/`. Changes that touch only Terraform or Markdown do not trigger a deploy |
| Terraform state | `home-stage-514419-tfstate` | A versioned bucket inside the project, created by hand in the bootstrap. One prefix per Terraform root: `shared` and `stage` |

### Environment variables set by Terraform

The web service and both jobs get the same five plain environment variables.
Everything else the app needs comes from the secret. DES-004, DES-005 and
DES-007 are designed against these names.

| Variable | Value on stage | Used for |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `localtools.settings.stage` | Which settings module to load (DES-004) |
| `GCP_PROJECT_ID` | `home-stage-514419` | Where to find the secret (DES-005) |
| `GCP_SECRETS_NAME` | `home-stage-app-env` | Which secret to read at startup (DES-005) |
| `GCP_CLOUDSQL_CONNECTION_NAME` | The instance's connection name | The database socket lives under `/cloudsql/` in a directory with this name (DES-004) |
| `GCP_MEDIA_BUCKET` | `home-stage-media-4269` | Where uploads are stored (DES-007) |

### How this differs from hl_vae

| hl_vae | Here | Why |
|---|---|---|
| Service project attached to a Shared VPC | No VPC at all | The project stands alone, and the connection below needs no network |
| Database on a private address inside the shared network | Cloud Run's built-in Cloud SQL connection | Cloud Run mounts a local socket to the instance and authenticates with the runtime service account. The instance has a public address but no authorised networks, so only identities with the database-client role can reach it. No connector, no subnet, nothing to pay for |
| Organization policy override to allow a public service | None | A project with no organization has no such policy; the service is made public directly |
| State in a shared, pre-existing bucket | Own bucket, created in the bootstrap | Nothing is shared |
| `shared/` root attaches the VPC, overrides policy, creates the image repo | `shared/` enables project-wide APIs and creates the image repo | Kept as its own root so a later prod project can read images from one place |
| No media bucket | Media bucket | This app accepts uploads |
| Public service by turning off the invoker check | Public service by granting the invoker role to everyone | With no organization there is no sharing restriction to work around, so the plain grant is enough |
| Migrate job only migrates | Migrate job also creates the cache table | This app caches in a database table |

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
4. Start the database and wait until it is ready. It is stopped every
   night, and starting it can take around fifteen minutes. (An environment
   whose database always runs skips this step.)
5. Point both jobs at the new image and run the migrate job (migrations, then
   the cache table), waiting for it to finish.
6. Deploy the new image to the web service.

No step reads the app secret; only the runtime service account can. `develop`
is promoted by fast-forwarding `staging` to the commit on `origin/develop`,
never to a local branch.

### App contract

What the app has to provide before the first deploy can work. Each item is
designed in its own doc, and each is a dependency of this design (see
Dependencies).

| Need | Doc |
|---|---|
| Pinned dependencies that install in a container, a production WSGI server, and the database driver for the chosen engine | DES-003 |
| A stage settings module with debug off, hosts and CSRF origins taken from the environment, and a default settings module that resolves | DES-004 |
| At startup on Cloud Run, the app reads the secret named in its environment and loads it as settings; locally it keeps reading a `.env` file | DES-005 |
| Static files collected at build time and served by the app, with the build output no longer tracked in git | DES-006 |
| Uploads stored in the media bucket | DES-007 |
| A Dockerfile that builds the Tailwind stylesheet and installs the ML dependencies and their data files, and listens on the port Cloud Run provides | DES-008 |

CI (DES-009) is not part of the contract. A deploy does not need it, and its
Terraform checks run against the Terraform written here, so it follows this
design, not the other way round.

The resume parser loads scikit-learn models and NLTK data, so the web
service and the jobs start at 1 GiB of memory, and the figure is revisited
once DES-008 shows what the image needs.

### Cost

Rough expectation for an idle stage, to be confirmed after the first month's
bill: the web service, image repository, secret and buckets cost cents. The
database is the only real cost: about ten dollars a month if it ran all the
time, or a dollar or two for storage alone when it is stopped. Because it is
stopped every night, the bill depends on how often stage is deployed or
started by hand.

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
Steps marked **gated** need every design in Dependencies to be Done first;
check the backlog before starting one, and stop if any is not.

- [x] Settle the open questions below and update this doc.
- [x] Bootstrap by hand, following `infra/BOOTSTRAP.md`: base APIs, state bucket, GitHub connection, `staging` branch, credentials for Terraform.
- [x] Write `terraform/shared`: project-wide APIs and the image repository (#7).
- [x] Write `terraform/modules/home-env` and `terraform/envs/stage` (#8).
- [ ] Write the Cloud Build pipeline in `infra/cloudbuild/`.
- [ ] Apply `shared`, then `envs/stage` (by hand).
- [ ] Create the database user (by hand).
- [ ] **Gated.** Create the first secret version (by hand), holding the keys DES-005 lists.
- [ ] **Gated.** First deploy: promote `develop` to `staging`.
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

None. Settled on 2026-11-11:

- **Database engine.** PostgreSQL. Version 17 was picked when the answers
  were folded in.
- **Region.** us-west1.
- **Stopping the database when idle.** Yes, as on hl_vae: a nightly stop, and
  deploys start it.
- **GitHub connection.** The first-generation Cloud Build GitHub App, as on hl_vae.
- **Media bucket name.** `home-stage-media-4269`.

## Changelog

- 2026-11-11 — Created.
- 2026-11-11 — Open questions settled: PostgreSQL, us-west1, nightly database
  stop, first-generation GitHub App, media bucket name. Added the scheduler
  job and its service account, the state bucket name, the environment
  variables Terraform sets, and the cache table step in the migrate job.
  Moved to In Progress.
- 2026-11-11 — DES-003 to DES-008 listed as dependencies instead of being an
  implementation step; the steps that need them are marked as gated. CI
  (DES-009) taken out of the app contract, since it depends on this design.
