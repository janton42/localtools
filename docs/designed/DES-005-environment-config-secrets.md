# DES-005: Environment config and secrets

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-12
- **Updated:** 2026-11-12
- **Depends on:** DES-003 (see Dependencies)
- **Related:** DES-002 (app contract, the `home-stage-app-env` secret, the runbook step), DES-004 (stage settings read the keys listed here), DES-010 and DES-011 (PythonAnywhere keeps its `.env` until cutover)

## Summary

The app gets one way to load its environment: on Cloud Run it reads the
Secret Manager secret named in `GCP_SECRETS_NAME` and loads it as if it were
a `.env` file; everywhere else it keeps reading `localtools/.env`. This
design also fixes the list of keys the secret must hold, so the first secret
version for stage can be created.

## Motivation / Problem

DES-002 created an empty secret, `home-stage-app-env`, and gave the web
service and both jobs five plain environment variables. Everything else is
supposed to come from that secret, but nothing in the app reads it.

Today `localtools/settings/base.py` creates a django-environ reader and
loads `localtools/.env`, then reads `DJANGO_SECRET_KEY`; the dev and prod
settings read `DB_USER` and `DB_PASSWORD` the same way. That has three
problems for stage:

- There is no `.env` file in the container, and there must not be one: the
  file holds passwords and would end up in the image.
- The path is relative to the working directory, so it only works when the
  process starts in the repo root. Cloud Run jobs, gunicorn and tests started
  from elsewhere would silently find no file.
- Nobody has written down which keys the app needs. The local file has four
  lines, one of which (`DJANGO_SETTINGS_MODULE`) has no effect, because the
  file is read after the settings module has already been chosen.

Without this design the first secret version can't be written (DES-002's
gated step) and stage can't start.

## Goals and Non-goals

**Goals**

- On Cloud Run, settings come from the secret, read once when each process
  starts.
- Locally and on PythonAnywhere, nothing changes for whoever runs the site:
  the same `.env` file, found no matter which directory the process starts in.
- Plain environment variables always win over the secret or the file, so
  Terraform's five variables can't be overridden by mistake, and a one-off
  override on a job execution works.
- A missing key or an unreadable secret stops startup with a message that
  names the key or the secret, never a value.
- One written list of every key, what it is for and where it is needed,
  with a committed example file to match.
- A written procedure for editing and rotating the secret.

**Non-goals**

- The stage settings module, `DATABASES` for PostgreSQL, `DEBUG`, and how
  hosts and CSRF origins are turned into settings. Those are DES-004; this
  design only names the keys DES-004 reads.
- Media storage settings (DES-007). The bucket name is already a plain
  variable set by Terraform.
- Configuring email. The password reset pages send mail, but no email
  backend is configured anywhere today. See Open Questions.
- Moving PythonAnywhere off its `.env` file. It keeps the file until
  cutover (DES-011).
- Splitting the secret into one Secret Manager secret per key.

## Dependencies

| Design | What this design needs from it | Blocks |
|---|---|---|
| DES-003 | `pyproject.toml` and `uv.lock`, so the Secret Manager client library can be added to the main group | The implementation step that adds the cloud path |

Before starting a gated step, check the backlog: every design listed above
must be **Done**. If any is not, stop and do not start the step.

The local `.env` fixes do not need DES-003 and can go first.

## Proposed Design

### Where values come from

```
                 process starts, settings/base.py is imported
                                   │
                    is GCP_SECRETS_NAME set in the environment?
                         │                          │
                        yes                         no
                         │                          │
      read versions/latest of that secret     read localtools/.env
      in GCP_PROJECT_ID, as the runtime       (path built from BASE_DIR;
      service account                          a missing file is allowed)
                         │                          │
                         └────────────┬─────────────┘
                                      │
                 load each line into the process environment,
                 skipping any key that is already set
                                      │
                 settings read keys with django-environ as today;
                 a missing required key fails with its name
```

Choosing on `GCP_SECRETS_NAME` rather than on the settings module keeps the
loader independent of DES-004: whichever settings module runs, the secret is
read only where Terraform has said there is one. Locally and on
PythonAnywhere that variable is never set, so the cloud path never runs and
the client library is never imported there.

### The loader

A small module, `localtools/appenv.py`, holds one function that the top of
`settings/base.py` calls in place of the current `read_env` line. It:

1. Looks for `GCP_SECRETS_NAME` in the environment.
2. If it is set, requires `GCP_PROJECT_ID` too, then asks Secret Manager for
   the latest version of that secret. The client library is imported inside
   the function, only on this path.
3. If it is not set, reads `localtools/.env`, using a path built from
   `BASE_DIR`, not from the working directory.
4. Hands the text to django-environ's own `.env` parser, which only sets
   keys that are not already in the environment.

When the secret can't be read (it doesn't exist, it has no enabled version,
or the service account lacks access), startup fails with Django's
"improperly configured" error naming the secret's full path and the kind of
failure. The secret's contents are never logged, printed or put in an error.

Each process reads the secret once. gunicorn workers each import the
settings, so a web instance makes one read per worker at start. Secret
Manager charges three cents per ten thousand reads, so this costs nothing
worth counting. A new version only takes effect in processes that start
after it is added (see Editing and rotating).

This is the same pattern hl_vae uses, so both projects behave the same way;
no code is shared with it.

### Format of the secret

The secret's value is the same format as the local file: one `KEY=value`
per line, `#` for comments, blank lines ignored. That means a stage secret
can be written and checked as an ordinary file before it is uploaded.

Two rules follow from django-environ's parser, and the example file states
both:

- A value that starts with `$` is read as a reference to another variable.
  Generated passwords and keys must not start with `$`, or must be escaped.
- Values with spaces or `#` are quoted.

### The keys

Plain variables (set by Terraform on Cloud Run, never in the secret or file):
`DJANGO_SETTINGS_MODULE`, `GCP_PROJECT_ID`, `GCP_SECRETS_NAME`,
`GCP_CLOUDSQL_CONNECTION_NAME`, `GCP_MEDIA_BUCKET`. They are in DES-002.

Keys in the secret or the `.env` file:

| Key | Local dev | PythonAnywhere | Stage secret | Used for |
|---|---|---|---|---|
| `DJANGO_SECRET_KEY` | Required | Required | Required | `SECRET_KEY`. Stage gets its own key, never a copy of the local or live one |
| `DJANGO_SECRET_KEY_FALLBACKS` | — | — | Optional, empty | Comma-separated old keys, read into `SECRET_KEY_FALLBACKS` so sessions and reset links survive a rotation. Only `base.py` reads it, and an empty value means none |
| `DB_USER` | Required | Required | Required (`localtools`) | Database user. The names are kept as they are, so dev, prod and stage read the same keys |
| `DB_PASSWORD` | Required | Required | Required | Database password; on stage, the one set by hand when the user was created (DES-002) |
| `ALLOWED_HOSTS` | — | — | Required | Comma-separated hostnames: the stage Cloud Run URL's host. DES-004 turns it into the setting |
| `CSRF_TRUSTED_ORIGINS` | — | — | Required | Comma-separated origins with scheme, for the same URL. DES-004 turns it into the setting |

`DJANGO_SETTINGS_MODULE` is removed from the local file's example: it has
never had an effect there. How the default settings module resolves is
DES-004.

The secret never holds anything that would turn a safety setting off. Stage
settings hard-code `DEBUG` off and the secure cookie settings on (DES-004),
and no key in the secret can change them.

If DES-004 settles on different names for the host and origin keys, this
table is changed in the same pull request so there is only ever one list.

### Example file

A committed `localtools/.env.example` lists every key in the table above
with a placeholder value and a one-line comment, marks which are needed
where, and states the two format rules. It contains no real value. The
README's setup section says to copy it to `localtools/.env`. The existing
`.env` line in `.gitignore` matches only that exact name, so the example file
is tracked and the real one stays ignored.

### Editing and rotating

This design supplies the procedure; DES-002's runbook step writes it into
`infra/README.md`. All of it is done by hand.

- **Editing.** Write the full set of lines to a file outside the repo, add
  it as a new version of `home-stage-app-env`, then delete the local file.
  Start a new revision of the web service so new instances read it; jobs
  read it on their next execution. Disable the previous version once the new
  revision is healthy, which also allows rolling back by re-enabling it.
- **Rotating `DJANGO_SECRET_KEY`.** Move the current key into
  `DJANGO_SECRET_KEY_FALLBACKS`, put a newly generated key (Django can
  generate one) in `DJANGO_SECRET_KEY`, and edit as above. Remove the old key
  from the fallbacks after the session lifetime (two weeks by default).
- **Rotating the database password.** Change it on the database user, then
  edit the secret straight away. Requests fail between the two steps, which
  is acceptable on stage.

### Files

```
localtools/
├── appenv.py            # new: decides between the secret and .env, loads it
├── .env.example         # new: every key, placeholders only
└── settings/
    └── base.py          # calls the loader; reads SECRET_KEY_FALLBACKS
localtools/tests/        # new: loader tests (or the closest existing test location)
pyproject.toml           # google-cloud-secret-manager added to the main group
uv.lock                  # regenerated
README.md                # setup: copy the example file
```

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Cloud Run mounts the secret as a file, and the app reads that file like `.env` | No client library, no network call in the app | Changes the Terraform module and the DES-002 contract; manage commands can't be pointed at stage from a laptop; a missing mount looks like an empty file | The contract already says the app reads the secret named in its environment, and it matches hl_vae. Worth revisiting if the library's size matters |
| Cloud Run exposes each key as its own environment variable from its own secret | No app code at all | One secret per key, each wired into Terraform; adding a key means a Terraform change and an apply | Too much ceremony for six keys |
| Bake a `.env` into the image at build time | Simple | Secrets in the image and its layers, readable by anyone with registry access | Unsafe |
| Load the secret in the stage settings module instead of `base.py` | Only stage knows about the cloud | Ties this design to DES-004, and every future cloud settings module has to repeat it | Choosing on `GCP_SECRETS_NAME` gives the same result with no coupling |
| Rename the database keys to `GCP_CLOUDSQL_USER` and friends, as hl_vae does | Matches hl_vae | Dev and prod would need different names for the same thing, or a change on PythonAnywhere | The live site should not have to change for stage |

## Implementation Plan

- [ ] Build the `.env` path from `BASE_DIR`, add `localtools/.env.example`, update the README. Not gated.
- [ ] **Gated.** Add the Secret Manager client library to the main group, write `localtools/appenv.py`, call it from `base.py`, read `DJANGO_SECRET_KEY_FALLBACKS`, and add the tests below.
- [ ] Update DES-002's resource notes if a key name changed during DES-004 review.

The first secret version itself is DES-002's step, done by hand from the key
table above once this design is Done.

## Testing / Verification

Tests replace the Secret Manager client with a fake, so they never call
Google:

- With `GCP_SECRETS_NAME` unset, the `.env` file is read even when the
  process starts outside the repo root, and the client library is never
  imported.
- With it set, the fake secret's lines become settings.
- A value already in the environment is not overwritten by the secret or the file.
- A missing secret, a disabled version and a permission error each fail
  startup with the secret's path in the message and none of its contents.
- `GCP_SECRETS_NAME` without `GCP_PROJECT_ID` fails with a message naming
  the missing variable.
- A missing required key fails with that key's name.
- An empty `DJANGO_SECRET_KEY_FALLBACKS` gives an empty list.

Manual checks:

- Local `runserver` and the test suite work from the repo root and from
  another directory.
- On stage, after the first deploy, the manage job runs Django's deployment
  check, and the Cloud Run logs contain no secret values.

## Open Questions

- **Email.** The password reset pages send mail, but no email backend is
  configured anywhere, so on stage they would fail. Recommend leaving it out
  of this design and adding a backlog idea for it; its credentials would go
  into the secret as new keys. Jeff to confirm.
- **Secret as a mounted file instead of a library call.** Recommend the
  library call, as above. Jeff to confirm, since the other choice changes
  the Terraform module.

## Changelog

- 2026-11-12 — Created.
