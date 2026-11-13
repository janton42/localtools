# DES-008: Container image (Dockerfile, Tailwind build)

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-12
- **Updated:** 2026-11-12
- **Depends on:** DES-003
- **Related:** DES-002 (the pipeline that builds this image, the app contract), DES-004 (settings module), DES-006 (static files), DES-012 (resume parser), DES-009 (CI)

## Summary

A multi-stage Dockerfile at the repo root that builds the Tailwind
stylesheet with Node, installs the locked Python dependencies with uv, and
produces a small runtime image that serves the site with gunicorn on the
port Cloud Run gives it. The same image runs the web service and both Cloud
Run jobs. The ML stack is not in it: DES-003 moved it to an optional group,
and how the parser is served is DES-012.

## Motivation / Problem

DES-002's pipeline builds "the repo's Dockerfile", and there isn't one. Until
there is, nothing can be deployed to stage. Three things make the image more
than a one-line base image plus `pip install`:

- **The stylesheet is built by Node.** The theme app uses Tailwind 4 through
  PostCSS (`theme/static_src/`). The built file, `theme/static/css/dist/styles.css`,
  is committed today, so it can be stale or missing classes. The image must
  build it from source on every build and never rely on the committed copy.
- **Tailwind scans the whole repo.** The theme's source stylesheet tells
  Tailwind to look for class names in every `.html`, `.py` and `.js` file
  from the repo root down. Whatever is copied into the build decides which
  classes end up in the CSS, so the build context has to be curated.
- **The repo carries a lot that must not ship.** `static_files/` (33 MB of
  collected output), `media/` (user uploads, 11 MB), two `node_modules`
  trees, a local `venv/`, `.env` files and the docs and Terraform.

The backlog title also promised "ML dependencies". DES-003 settled that:
the web image installs only the main dependency group, and the parser's
packages, its pickled models and NLTK data are DES-012's problem.

## Goals and Non-goals

**Goals**

- One Dockerfile that builds on Cloud Build with no arguments and no secrets.
- The stylesheet is built from source inside the build.
- Python dependencies come only from `uv.lock`, main group only, and the
  build fails if the lock and `pyproject.toml` disagree.
- A small runtime image: Python 3.12 slim, no Node, no compilers, no build
  tools, running as a non-root user.
- One image for every environment and every entry point: the web service
  uses its default command, and the migrate and manage jobs override it.
- The image is environment-neutral. Which settings module to load, and every
  other environment value, comes from Cloud Run at run time.
- A measured memory figure, so DES-002's 1 GiB placeholder can be replaced.

**Non-goals**

- Collecting static files and serving them. DES-006 adds the collect step
  to this Dockerfile and chooses how files are served.
- The stage settings module (DES-004) and loading the secret (DES-005).
- Serving the resume parser or installing its packages (DES-012).
- Local development in containers. Dev stays on uv and `manage.py tailwind dev`.
- Image scanning (off until prod, decided in DES-011), signing, or
  multi-architecture builds. Cloud Run is amd64.
- The unused root `package.json` (it lists only jQuery, which the templates
  load from a CDN). The image ignores it; removing it is DES-013.

## Dependencies

| Design | What this design needs from it | Blocks |
|---|---|---|
| DES-003 | `pyproject.toml`, `uv.lock`, `.python-version` and a main group with gunicorn and the PostgreSQL driver; the site starting without the parser's packages | Every step except the `.dockerignore` |

Before starting a gated step, check the backlog: every design listed above
must be **Done**. If any is not, stop and do not start the step.

DES-004 is not a dependency. The image does not choose a settings module, and
the verification below boots the site with a temporary settings override, as
DES-003's does. DES-006 builds on this design, not the other way round.

## Proposed Design

### Stages

```
            build context (filtered by .dockerignore)
                 │
     ┌───────────┴───────────┐
     ▼                       ▼
┌──────────┐           ┌──────────┐
│  css     │           │  deps    │
│ Node LTS │           │ Py 3.12  │
│ npm ci   │           │ + uv     │
│ build    │           │ frozen   │
│ Tailwind │           │ sync     │
└────┬─────┘           └────┬─────┘
     │ styles.css           │ /app/.venv
     └──────────┬───────────┘
                ▼
          ┌───────────┐
          │ runtime   │
          │ Py 3.12   │
          │ slim,     │
          │ non-root, │
          │ gunicorn  │
          └───────────┘
```

| Stage | Base | What it does | What leaves it |
|---|---|---|---|
| `css` | Official Node image, slim variant, on the LTS line current when it is written (Tailwind 4 needs Node 20 or later) | Installs the theme's Node packages from its lock file with a clean install, copies the source tree, runs the theme's production build script | The minified `theme/static/css/dist/styles.css` |
| `deps` | The same Python 3.12 slim image as `runtime`, with the uv binary copied in from uv's official image at a pinned version | Installs dependencies with a frozen sync: main group only, no dev group, no optional groups, without installing the project itself. Only `pyproject.toml`, `uv.lock` and `.python-version` are copied in first, so this layer is reused until the lock changes | The virtual environment at `/app/.venv` |
| `runtime` | Official Python 3.12 slim image on the current Debian stable, pinned to an exact patch tag | Creates an unprivileged user, copies the virtual environment, then the source, then the built stylesheet on top of the committed one | The image Cloud Run runs |

All base images are pinned to exact tags in the Dockerfile; bumping one is a
reviewed change. The runtime stage needs no system packages: psycopg's binary
build bundles libpq, and Pillow ships wheels with its image libraries. If a
package later needs a system library, it is installed in `runtime` alone.

### What the Tailwind build sees

Tailwind builds its CSS from the class names it finds in the files it scans,
so the `css` stage receives the same filtered context as everything else:
templates, app code and app JavaScript, but no `static_files/`, `node_modules`,
`venv/`, docs or media. That keeps old copies of templates and scripts in the
collected output from adding classes, and keeps the scan fast. The theme's
`@source` line is left as it is.

### Runtime image

| Setting | Value | Why |
|---|---|---|
| Working directory | `/app`, the repo root | `manage.py` and the WSGI module are found from there; the jobs run `python manage.py …` with no path |
| `PATH` | The virtual environment's `bin` first | The jobs call plain `python`; it must be the one with Django installed |
| User | An unprivileged user created in the image; files owned by root and readable by it | Nothing at run time needs to write into `/app`. Uploads go to the bucket (DES-007) |
| Python output | Unbuffered, no bytecode files written at run time | Logs reach Cloud Logging immediately |
| `DJANGO_SETTINGS_MODULE` | Not set in the image | Cloud Run sets it (DES-002). An image that defaults to one environment's settings could start with the wrong ones |
| Port | Read from `PORT`, which Cloud Run sets; 8080 if unset | Cloud Run's contract |
| Default command | gunicorn serving `localtools.wsgi` | Used by the web service. The jobs replace it with their own command, which DES-002's Terraform already sets |

### gunicorn

gunicorn reads its options from a `gunicorn.conf.py` at the repo root, which
it picks up automatically from the working directory, so the command stays
short and the options are reviewed as code:

| Option | Value | Why |
|---|---|---|
| Bind | All interfaces, on `PORT` | Cloud Run sends traffic to that port |
| Worker type | Threaded workers | Django views here are short and mostly wait on the database |
| Workers × threads | 2 × 4 by default, overridable with gunicorn's standard `WEB_CONCURRENCY` variable for workers | Two processes survive one crashing; eight requests in flight fits one CPU |
| Timeout | Disabled | Cloud Run already ends requests after DES-002's 300 seconds; a second, shorter limit only kills workers mid-request |
| Logs | Access and error logs to standard output | Cloud Logging collects standard output |
| Forwarded headers | Trust the proxy's forwarded-protocol header | Cloud Run terminates TLS. The settings that act on it are DES-004's |

DES-002 sets the web service to accept 80 concurrent requests per instance.
With eight in flight per instance, the other 72 would queue inside gunicorn
and Cloud Run would never start a second instance. The service's concurrency
is lowered to 8 to match, a one-line Terraform change applied by hand.

### `.dockerignore`

A new `.dockerignore` at the repo root keeps out everything that must not
reach the build or the image:

| Excluded | Why |
|---|---|
| `.git`, `.claude`, `docs/`, `infra/`, `README.md`, `LICENSE` | Not needed to run the site |
| `venv/`, `.venv/`, every `node_modules/`, `__pycache__` | Rebuilt inside the image for Linux |
| `static_files/` | Collected output. DES-006 regenerates it at build time |
| `media/` | User uploads belong in the bucket, never in an image |
| `.env` and any `.env.*`, `db.sqlite3`, `*.db`, `*.log` | Local secrets and data |
| The ignored local folders listed in `.gitignore` (`investotron/`, `output/`, `uploads/`, `db/`) | Never part of the site |

The tracked `static/` directory stays in: it is listed in `STATICFILES_DIRS`,
and DES-006 decides what happens to it.

### Build caching

DES-002's pipeline pulls the environment's previous image and passes it to
the build as a cache. Docker builds with BuildKit by default since version
23, and BuildKit only reuses layers from an image that was built with inline
cache metadata, and only for the final stage. The implementation checks
which builder Cloud Build's Docker image uses; if it is BuildKit, there are
two consequences:

- The pipeline's build step passes the build argument that turns on inline
  cache metadata, so the `runtime` layers (the virtual environment copy above
  all) are reused on the next build.
- The `css` and `deps` stages are rebuilt on every build. Without the ML
  stack each takes well under a minute, so a separate registry cache is not
  worth its cost and complexity yet.

### Size and memory

Without scikit-learn, pandas, NLTK and their data, the image should be in
the low hundreds of megabytes, most of it the Python base. Memory is
measured, not guessed: the image is run locally with a memory limit, the
home page and admin are loaded, and the resident memory of both workers is
recorded here. DES-002's `memory` variable is then lowered from 1 GiB to the
smallest Cloud Run size that leaves at least half again as much headroom,
expected to be 512 MiB.

### Found while designing, handed to other designs

- The parser's pickled models live in `resume_parser/static/`. Anything in
  an app's `static/` directory is collected and served publicly, so once
  DES-006 runs the collect step the models would be downloadable from the
  site. DES-006 or DES-012 should move them out of `static/`.
- `theme/static/css/dist/styles.css` is build output tracked in git. The
  image overwrites it, so it no longer matters for deploys; DES-006 stops
  tracking it.

### Files

```
Dockerfile          # new: css, deps and runtime stages
.dockerignore       # new
gunicorn.conf.py    # new: the options above
infra/cloudbuild/deploy.yaml               # build step: inline cache argument
infra/terraform/modules/home-env/main.tf   # web concurrency 8
infra/terraform/modules/home-env/variables.tf   # memory default, from the measurement
```

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Build the CSS with django-tailwind's own management command inside the Python image | One toolchain in the Dockerfile | Node and npm end up in the Python stage, or the command fails | A separate Node stage keeps Node out of the runtime image |
| Use Tailwind's standalone binary instead of Node | No Node at all | The theme's build uses PostCSS plugins (nested rules, variables) the binary doesn't include | Would change the theme's build, which works today |
| Keep using the committed `styles.css` | No Node stage | Stale whenever a template changes without a local rebuild | The reason for the Node stage |
| Single-stage image | Simplest Dockerfile | Node, uv and npm caches in the final image | Larger, slower cold starts, more to patch |
| Google Cloud Buildpacks | No Dockerfile | Little control over the Tailwind step and dependency groups; DES-002's pipeline already expects a Dockerfile | Less control for no gain |
| Alpine base | Smaller base | musl breaks or slows many Python wheels | Debian slim is the safe default |
| uWSGI or an ASGI server | — | `asgi.py` is broken (DES-003 notes it), and uWSGI is in maintenance mode | gunicorn is DES-003's choice |
| BuildKit registry cache for every stage | All stages cached | A cache image to store and clean up, buildx setup in the pipeline | Cold builds are already fast without the ML stack |

## Implementation Plan

One branch and pull request for the files, then the by-hand apply.

- [ ] Add `.dockerignore`.
- [ ] **Gated.** Add the `Dockerfile` with the three stages above and `gunicorn.conf.py`.
- [ ] **Gated.** Turn on inline cache metadata in the pipeline's build step.
- [ ] **Gated.** Build and run the image locally, take the measurements below, and record the size and memory in this doc.
- [ ] **Gated.** Lower the web service's concurrency to 8 and the `memory` default to the measured size in the `home-env` module, and update DES-002's app contract row and memory note to match (Terraform changes only; no commands run).
- [ ] Apply `envs/stage` (by hand).

## Testing / Verification

- The image builds from a clean checkout with no build arguments and no
  network access to anything but the package registries.
- The built stylesheet in the image contains a class that appears only in a
  template, and the image does not contain `static_files/`, `media/`,
  `node_modules`, `venv/`, `.env` or the `.git` directory.
- Changing only a template rebuilds the `css` stage and the source layers
  but reuses the virtual environment layer.
- A frozen sync in the `deps` stage fails the build when `pyproject.toml`
  is edited without updating `uv.lock`.
- The image contains no scikit-learn, pandas or NLTK, and its user is not root.
- Run locally with `PORT` set and a temporary settings override pointing at
  SQLite: gunicorn starts two workers, the home page loads with styles, and
  the admin login page renders.
- With the default command replaced by `python manage.py check`, as the jobs
  replace it, the check runs.
- A second build on Cloud Build with no Python changes reuses the cached
  virtual environment layer.

## Open Questions

- **Vulnerability scanning.** Settled 2026-11-12: off for stage. Artifact
  Registry's scanning is billed per image; whether to turn it on for prod is
  decided in DES-011.
- **The root `package.json`.** Settled 2026-11-12: it installs only jQuery,
  which nothing uses (the templates load it from a CDN). Removing it and the
  root `node_modules` is DES-013.

## Changelog

- 2026-11-12 — Created. The ML part of the backlog title was already settled
  by DES-003, so the title now names the Dockerfile and the Tailwind build.
- 2026-11-12 — Removing the root `package.json` split out as DES-013.
- 2026-11-12 — Vulnerability scanning left off until prod.
