# DES-007: Media storage for user uploads

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-12
- **Updated:** 2026-11-12
- **Depends on:** DES-003, DES-004 (see Dependencies)
- **Related:** DES-002 (media bucket, app contract), DES-006 (static files), DES-010 (copying existing files), DES-011 (cutover), DES-012 (the resume parser reads uploads)

## Summary

On Cloud Run, uploaded files go to Cloud Storage instead of the local
`media/` directory, which disappears with each instance. Public images (the
portfolio) go to a public bucket and are served by plain URLs; private
uploads (resumes, informedvoter files) go to a private bucket and are served
by short-lived signed URLs. Local dev keeps the filesystem.

## Motivation / Problem

Django writes uploads to `MEDIA_ROOT`, the `media/` directory next to the
code. A Cloud Run instance's disk is in memory and is thrown away when the
instance stops or a new revision deploys, so on stage every upload would be
lost within hours. DES-002 created a bucket for uploads and lists "uploads
stored in the media bucket" in its app contract; this design says how the app
uses it.

Three model fields hold files today:

| Field | Who sees the file | How it is shown today |
|---|---|---|
| `portfolio.Project.image` | Anyone: it is on the public home page and project pages | `image.url` in the portfolio templates |
| `resume_parser.ResumeUpload.resume` | Only the user who uploaded it (views are login-only and filter by user) | A link built by hand from `MEDIA_URL` and the stored name in `resume_parser/templates/resume_parser/index.html` |
| `informedvoter.FileUpload.file` | Users with the add-file permission; only listed in the admin | Not shown outside the admin |

Resumes hold personal details, so they must not be readable by anyone who
can guess a URL. Portfolio images are public and appear on the busiest page,
so they should be plain, cacheable URLs. A single bucket can't do both: the
DES-002 bucket uses uniform bucket-level access, which means one access rule
for every object in it.

A few smaller problems sit in the same code:

- The resume list builds its link from `MEDIA_URL` instead of asking the
  storage for a URL, so it would point at the web service, which has no
  files.
- `upload_to` for resumes is `./resume_parser/static/uploads/` and for
  informedvoter is `informedvoter/static/uploads/`. Uploads have nothing to
  do with static files, and the leading `./` ends up in stored names.
- Portfolio images are committed to git under `media/portfolio/images/`
  (13 files). That is how they reach PythonAnywhere today, but a container
  image should not carry uploads.

## Goals and Non-goals

**Goals**

- On stage, every upload is stored in Cloud Storage and survives restarts and deploys.
- Portfolio images are served from a public bucket by plain URLs that browsers can cache.
- Resumes and informedvoter files are in a private bucket; their links are signed and expire.
- No service account keys: signing uses the runtime service account through the IAM API.
- Templates get every file URL from the storage, never by joining `MEDIA_URL` to a name.
- Local dev and the test suite need no cloud access.

**Non-goals**

- Copying the existing files into the buckets. Stage starts with an empty
  database, so there are no rows to point at them; the copy goes with the
  data in DES-010.
- Making the resume parser read from storage. It opens the upload by joining
  `BASE_DIR` to the stored name and writes its output to a local directory.
  Both are DES-012's to change; this design only notes that the parser must
  open uploads through the storage.
- Static files (DES-006). This design adds named storages next to
  `staticfiles` but does not choose its backend.
- A CDN or custom domain for media (DES-011, if ever).
- Deleting files when their rows are deleted. Django never does this, and it
  stays that way; orphaned files cost fractions of a cent.
- Image resizing or thumbnails.

## Dependencies

| Design | What this design needs from it | Blocks |
|---|---|---|
| DES-003 | `pyproject.toml` and `uv.lock`, so the storage library can be added to the main group | Adding the storage library |
| DES-004 | `localtools.settings.stage`, where the cloud storages are configured | Configuring stage storages |

Before starting a gated step, check the backlog: every design listed above
must be **Done**. If any is not, stop and do not start the step.

## Proposed Design

### Two buckets

| Bucket | Access | Holds | Plain env var |
|---|---|---|---|
| `home-stage-media-4269` (exists) | Private. Public access prevention enforced, so no object can ever be made public | Resumes, informedvoter files, and any future private upload | `GCP_MEDIA_BUCKET` (exists) |
| `home-stage-media-public-4269` (new) | Public read: everyone can view objects, not list them | Portfolio images | `GCP_PUBLIC_MEDIA_BUCKET` (new) |

The runtime service account (`home-stage-app`) gets object admin on both.
The new bucket uses uniform bucket-level access like the first one. Both
live in the `home-env` module next to the existing bucket, so a prod
environment later gets the same pair.

### Storage library

`django-storages` with its Google Cloud extra is added to the main dependency
group. It provides a Django storage backend for Cloud Storage and finds
credentials the standard Google way, which on Cloud Run is the runtime
service account from the metadata server. Locally nothing calls it.

### Named storages

Django 5.2 configures storages in one `STORAGES` setting. This design uses
three names:

| Name | Used by | Dev and tests | Stage |
|---|---|---|---|
| `default` | Every file field that doesn't name a storage: resumes, informedvoter files | Filesystem, under `MEDIA_ROOT` (as today) | Private bucket, signed URLs |
| `public` | `portfolio.Project.image` | Filesystem, under the same `MEDIA_ROOT` and `MEDIA_URL` | Public bucket, plain URLs, a long browser cache header |
| `staticfiles` | Static files | Owned by DES-006 | Owned by DES-006 |

`base.py` defines `default` and `public` as the filesystem, so dev and
PythonAnywhere behave exactly as now. Setting `STORAGES` replaces Django's
whole default, so `base.py` also keeps `staticfiles` at Django's standard
backend until DES-006 changes it. `localtools.settings.stage` (DES-004)
replaces both with the Cloud Storage backend, taking each bucket name from
its plain env var. If either variable is missing, stage fails at startup
instead of quietly writing to the instance's disk.

`Project.image` names its storage through a small function that returns
`storages["public"]`, so the field's migration does not record which backend
is in use and doesn't change between dev and stage. This adds a migration
with no database change.

### Signed URLs without keys

The private bucket's URLs are V4 signed URLs that expire after one hour,
long enough to open a link from a page that has been sitting in a tab, short
enough that a copied link stops working. A signed URL normally needs a
private key. Cloud Run has none, so the backend is told to sign through the
IAM Credentials API instead: it sends the bytes to be signed to Google, which
signs them as the runtime service account. For that, the runtime service
account gets the Token Creator role **on itself only**. The IAM Credentials
API is already enabled by the `home-env` module.

Signing makes one network call per URL. Only the resume list shows private
files, and it shows one user's handful of uploads, so the cost is a few
calls on a page few people see. Public images are never signed, which is why
the portfolio has its own bucket.

The backend needs the service account's email to sign. It is taken from the
credentials Cloud Run provides; if the library cannot read it from there,
Terraform sets it as one more plain env var, `GCP_SERVICE_ACCOUNT_EMAIL`, and
DES-002's env var table is updated to match.

### File names and upload paths

| Field | `upload_to` today | `upload_to` after |
|---|---|---|
| `Project.image` | `portfolio/images/` | unchanged |
| `ResumeUpload.resume` | `./resume_parser/static/uploads/` | `resume_parser/uploads/` |
| `FileUpload.file` | `informedvoter/static/uploads/` | `informedvoter/uploads/` |

Only new uploads use the new paths. Existing rows keep the names they were
stored with, and DES-010 copies files under exactly those names, so old and
new rows both resolve. Files are never overwritten: if a name is taken, the
storage adds a suffix, as Django does today.

### Code changes in the apps

| Where | Change |
|---|---|
| `resume_parser/views.py`, `index` | Passes model instances to the template, not `.values()` dictionaries, so each upload has a file object that can produce a URL |
| `resume_parser/templates/resume_parser/index.html` | Links to the upload's `url` instead of `MEDIA_URL` joined to the name |
| `resume_parser/models.py`, `informedvoter/models.py` | New `upload_to` paths, with migrations |
| `portfolio/models.py` | `image` uses the `public` storage, with a migration |
| `localtools/urls.py` | Unchanged. The `static()` helper that serves `MEDIA_ROOT` only does anything when `DEBUG` is on, so it keeps working for dev and is inert on stage |

Nothing else reads files by path. The resume parser does, and stays as it
is until DES-012 (see Non-goals).

### Upload size

Cloud Run rejects requests over 32 MiB, and Django spools uploads larger
than 2.5 MB to a temporary file, which on Cloud Run is held in memory. The
resume and informedvoter forms reject files over 10 MB with a form error, so
a large upload fails with a message instead of a bare 413 or memory pressure.

### What stays in git

The 13 portfolio images in `media/portfolio/images/` stay tracked until the
cutover, because PythonAnywhere gets them from git. They are kept out of the
container image by DES-008's ignore file, since the image never reads
`media/`. At cutover (DES-011) `media/` is removed from git and added to
`.gitignore`.

### Infrastructure changes

The Terraform for the items above is written in this design's
implementation and applied by hand. All of it is in
`infra/terraform/modules/home-env/` and `infra/terraform/envs/stage/`:

- The public bucket, its public-read grant and the runtime account's object admin grant.
- Public access prevention enforced on the private bucket.
- Token Creator for the runtime account on itself.
- `GCP_PUBLIC_MEDIA_BUCKET` (and, only if needed, `GCP_SERVICE_ACCOUNT_EMAIL`) added to the plain env vars of the web service and both jobs.
- A new input for the public bucket's name and a matching output.

DES-002's resource and env var tables are updated in the same pull request.

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| One private bucket, everything signed | One bucket, no public grant | The home page makes one IAM call per portfolio image on every view; image URLs change on every render, so browsers never cache them | The public, busiest page pays for privacy it doesn't need |
| One public bucket for everything | Simplest, no signing | Anyone with a resume's URL can read it, and names are predictable (the uploaded file name) | Resumes are personal data |
| Private files streamed through a Django view that checks ownership | Exact access control, no Token Creator grant | New views and URLs per model, every download runs through a web instance and its memory | Signed URLs need no new views, and an hour's lifetime is acceptable for these files |
| Mount the bucket as a volume on Cloud Run | Django keeps writing to a directory | No locking or atomic renames, slower, the app still can't produce public or signed URLs | A mounted bucket is a filesystem in name only |
| A service account key for signing | Signing works offline | A key to store, rotate and leak | DES-002 rules out keys |
| Keep `upload_to` as is | No migrations | `static` and `./` stay in every stored name | Cheap to fix now, before stage has data |

## Implementation Plan

Each step is its own branch and pull request unless marked as done by hand.

- [ ] Terraform: the public bucket and its grants, public access prevention on the private bucket, Token Creator on itself for the runtime account, the new env var, input and output. Update DES-002's tables.
- [ ] Apply `envs/stage` (by hand).
- [ ] App code that needs no dependency: `base.py` defines the `default` and `public` storages as the filesystem; the portfolio image uses `public`; new `upload_to` paths; the resume list view and template use the file's URL; the 10 MB limit on the two upload forms. Migrations for all three models.
- [ ] **Gated.** Add `django-storages` with its Google Cloud extra to the main group and relock.
- [ ] **Gated.** In `localtools.settings.stage`, configure `default` (private bucket, signed URLs signed through IAM, one-hour expiry) and `public` (public bucket, plain URLs, long cache header), failing at startup if either bucket variable is missing.
- [ ] Add a note to DES-012's backlog row: the parser must open uploads through the storage.

## Testing / Verification

- Tests that upload files run against Django's in-memory storage, set per
  test with a settings override, so the suite writes nothing to disk and
  needs no cloud access. The upload test checks that the stored name starts
  with `resume_parser/uploads/` instead of checking a file path, since cloud
  storages have no paths.
- A test renders the resume list and checks the link comes from the
  storage's URL, not `MEDIA_URL`.
- A test checks that a file over 10 MB is rejected by each upload form.
- Locally, `runserver` with dev settings: upload a portfolio image and a
  resume, and both still show and download.
- On stage after the first deploy:
  - Upload a portfolio image in the admin; its URL is on the public bucket's
    host, opens without signing, and is still there after a redeploy.
  - Upload a resume; its link is signed, opens, and fails after an hour.
  - Fetching the same resume object without a signature returns access denied.
  - An attempt to make an object in the private bucket public is refused.
- Django's deployment check passes when run through the manage job.

## Open Questions

- **Public bucket name.** `home-stage-media-public-4269` follows the
  existing bucket's suffix. Bucket names are global; confirm it, or pick
  another.
- **`media/` in git until cutover.** Keeping the portfolio images tracked
  until DES-011 assumes PythonAnywhere gets them by `git pull`. If they are
  uploaded there through the admin instead, they can leave git now.

## Changelog

- 2026-11-12 — Created.
