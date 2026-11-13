# DES-006: Static files (stop tracking build output, serve from the container)

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-12
- **Updated:** 2026-11-12
- **Depends on:** None
- **Related:** DES-002 (app contract: "static files collected at build time and served by the app"), DES-003 (where the new package is declared), DES-004 (stage settings inherit what this sets), DES-007 (shares the storage setting), DES-008 (runs the collect step in the image), DES-012 (the parser files that move out of `static/`)

## Summary

The output of `collectstatic` (`static_files/`, 376 files, 33 MB) is
committed to git and is the only copy of some files the site uses. This
design makes the source directories the single source of truth, stops
tracking the collected output, and has the app serve its own static files
with WhiteNoise, so the container image on Cloud Run needs no web server or
bucket for them.

## Motivation / Problem

Today's setup:

| Setting / path | Today |
|---|---|
| `STATIC_URL` | `static/` |
| `STATICFILES_DIRS` | the repo's `static/` directory |
| `STATIC_ROOT` | `static_files/`, **tracked in git** |
| Storage | Django's default (no hashed names, no compression) |
| Who serves `/static/` | PythonAnywhere's static file mapping, pointing at `static_files/` |
| Deploy on PythonAnywhere | `git pull`; `collectstatic` is not needed because its output is in the pull |

Problems this causes:

1. **The collected output is not reproducible.** Comparing `static_files/`
   with every source directory, 41 files have no source at all:
   - `images/` (favicons, `site.webmanifest`, logos, the resume page's
     background images). `templates/base.html` loads the favicons and
     manifest from `images/…` and `resume/index.html` loads
     `images/central_park.png`. The sources exist, but under
     `static/localtools/images/` and `resume/static/resume/images/`, which
     collect to `localtools/images/…` and `resume/images/…`. The pages only
     work because an old copy sits at the top level of `static_files/`.
   - `bootstrap/`, `styles/` and `rates/scripts/`: leftovers of earlier
     layouts, no longer referenced.

   Running `collectstatic` into an empty directory, which is what a
   container build does, would lose the favicons.
2. **Build output in git.** Every `collectstatic` run creates a large,
   noisy diff, and Django's admin files are stored twice more:
   once in `static_files/admin/` and once as a stale copy in
   `static/localtools/admin/` (130 files, 1.9 MB, from an older Django).
3. **Nothing serves static files on Cloud Run.** There is no PythonAnywhere
   mapping there, and Django does not serve static files with debug off.
   Pages would load without styles or images.
4. **No cache busting.** File names never change, so browsers cannot cache
   static files for long without risking stale CSS after a deploy.
5. **Private files are published.** `resume_parser/static/` is an app
   static directory, so `collectstatic` copies the parser's source code and
   its pickled models (`scripts/resume_parser/…`) to a public URL. The
   parser also writes uploads and output under that directory at run time.

## Goals and Non-goals

**Goals**

- `collectstatic` into an empty directory produces everything the site uses.
- `static_files/` is no longer tracked; it is created at build or deploy time.
- The app serves `/static/` itself, with long-lived caching and compressed
  responses, on Cloud Run and anywhere else it runs.
- Templates reference static files through the `static` tag so that file
  names carry a content hash.
- Nothing that is not meant to be public ends up under `/static/`.
- PythonAnywhere keeps working until cutover, with one added deploy step.

**Non-goals**

- Writing the Dockerfile or the Tailwind build (DES-008). This design only
  says what the image must run and when.
- User uploads and the media bucket (DES-007). Upload fields that point
  into `static/` directories are noted below and left to DES-007.
- A CDN or serving static files from a bucket (see Alternatives).
- Untracking the Tailwind stylesheet `theme/static/css/dist/styles.css`.
  PythonAnywhere has no Node build, so it stays committed until the live
  site moves to Cloud Run (DES-011). DES-008 rebuilds it in the image, so
  the committed copy is not what stage serves.
- Fixing the informedvoter representative images, which reference
  `images/<code>.png` paths that are not in `static_files/` today either.
  That is an existing bug, logged separately.
- How the resume parser is served (DES-012).

## Proposed Design

### Serving: WhiteNoise

WhiteNoise is added as a main dependency (in whichever dependency file is
current when this is built: the Pipfile, or `pyproject.toml` once DES-003
lands). Its middleware goes into the base settings directly after Django's
security middleware, as WhiteNoise requires. It serves everything under
`STATIC_ROOT` at `STATIC_URL`, from the same gunicorn process as the app.

Static storage, set through the `staticfiles` entry of Django's `STORAGES`
setting:

| Settings module | Storage | Why |
|---|---|---|
| `base` (so prod, and stage from DES-004) | WhiteNoise's compressed, manifest storage | File names get a content hash; a gzip copy is written next to each file at collect time; WhiteNoise sends hashed files with a one-year, immutable cache header |
| `dev` | Django's plain static storage | `runserver` serves from the source directories; tests run with debug off and must not need a collected manifest |

DES-007 adds the `default` entry of the same `STORAGES` setting for uploads.
Whichever design is built second keeps the other's entry.

Brotli files are not generated; gzip is enough for a site this size and
avoids another dependency.

The manifest storage turns a reference to a missing file into a server
error instead of a silent 404. That is what we want on stage, and it is why
every reference is checked before this ships (see Templates below).

### Source layout

The source directories stay as they are, except for removals. The project
directory keeps its `localtools/` namespace, so collected paths are
`localtools/images/…`, not `images/…`.

```
static/
└── localtools/
    ├── images/                         # kept: favicons, manifest, logos
    ├── DetectingAngrySocialMediaPosts.html   # kept (see Open Questions)
    ├── admin/                          # deleted: Django ships its own
    ├── bootstrap/                      # deleted: base.html loads Bootstrap 3.4.1 from a CDN
    └── styles/                         # deleted: not referenced
informedvoter/static/informedvoter/     # kept
resume/static/resume/                   # kept
theme/static/css/dist/styles.css        # kept, still tracked (see Non-goals)
resume_parser/static/                   # emptied and removed (see below)
static_files/                           # untracked and added to .gitignore
```

The repo-root copies of the favicons and `site.webmanifest` are duplicates
of `static/localtools/images/` and are deleted, unless the PythonAnywhere
check in Open Questions shows something uses them.

### Templates

Every hand-built static path is replaced with the `static` tag pointing at
the real collected path. Hand-built paths (the `STATIC_PREFIX` variable or a
literal `/static/…`) bypass the hashed names and are the reason the
orphaned files were needed.

| Template | Today | After |
|---|---|---|
| `templates/base.html` | favicons, touch icon and manifest via `STATIC_PREFIX` + `images/…` | `static` tag with `localtools/images/…` |
| `templates/home.html` | `static` tag with `/images/…_logo.svg`, which resolves to `/static/images/…`; those logos are not there, so they are broken today | `static` tag with `localtools/images/…_logo.svg` |
| `resume/templates/resume/index.html` | `STATIC_PREFIX` + `images/central_park.png`; a literal `/static/images/section_heading_2.jpg` in an inline style | `static` tag with `resume/images/central_park.png`. `section_heading_2.jpg` exists nowhere, so the background is removed or replaced with an image that does exist (Jeff's choice in review) |
| informedvoter templates | `STATIC_PREFIX` + `images/<code>.png` | Unchanged (existing bug, see Non-goals). They still render, because the prefix does not go through the manifest |

`site.webmanifest` lists its icons by path; those paths are updated to
`/static/localtools/images/…`. They are not hashed, which is fine: the
manifest storage keeps an unhashed copy of every file.

### The resume parser's files leave `static/`

Anything in an app's `static/` directory is published. The parser's code
and models are not meant to be public, so they move out:

| Today | After |
|---|---|
| `resume_parser/static/scripts/resume_parser/` (code, `final_models/`, `entities/`) | `resume_parser/ml/` |
| `ML_MODELS_PATH`, `ENTITIES_PATH` in base settings | point at the new directory |
| `RESUME_OUT_PATH` = `resume_parser/static/output/` | unchanged here; the parser's output location is DES-007's and DES-012's |
| Upload fields writing to `resume_parser/static/uploads/` and `informedvoter/static/uploads/` | unchanged here; DES-007 moves uploads to the media storage |

Until DES-007 is built, those upload and output directories are still under
`static/` paths, but they are only written at run time and are never in the
image at collect time, so nothing from them is published by this design.
DES-008's ignore file must keep local copies of them (for example the PDF in
`resume_parser/static/uploads/`) out of the build context.

DES-003 refers to the parser's files by their current path. If DES-003 is
built after this design, its import checks use the new path; the change is
a rename only, and the parser's imports are updated in the same commit.

### When collection runs

| Environment | When | What runs |
|---|---|---|
| Container image (DES-008) | During the image build, after the Tailwind stylesheet is built | `collectstatic`, non-interactive, into `STATIC_ROOT` inside the image. The image then contains the hashed files, their gzip copies and the manifest; nothing is collected at container start |
| PythonAnywhere | After every `git pull` | `collectstatic`, then reload the web app. This is new: until now the pull brought the collected files with it. The PythonAnywhere static mapping stays and keeps serving `/static/` from `static_files/` before Django sees the request |
| Local dev | Not needed | `runserver` serves from the sources |

Collecting at build time means the build has no secret and no database.
`collectstatic` touches neither, but the base settings require
`DJANGO_SECRET_KEY` to load. The image's collect step therefore sets a
throwaway placeholder value for that single command only; it is not kept in
the image's environment. DES-005, which changes how settings load the
secret, must keep `collectstatic` runnable this way. It also needs the
resume parser's heavy imports to be out of app loading (DES-003), since the
web image has no ML packages.

### Request path on Cloud Run

```
browser ──► Cloud Run (home-stage-web)
              └─ gunicorn
                   └─ WhiteNoise middleware
                        ├─ /static/…  → file from the image (gzip if accepted,
                        │               one-year cache for hashed names)
                        └─ anything else → Django
```

No bucket, load balancer or extra Terraform is needed. DES-002's resources
are unchanged.

### Size

| | Before | After |
|---|---|---|
| Tracked under `static/` and `static_files/` | 39 MB | about 4 MB (`static/localtools/images/` and the HTML page) |
| Collected output in the image | — | Django admin, app images, the stylesheet, plus gzip copies: a few MB |

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Keep `static_files/` in git and copy it into the image | No build step | Output already out of sync with sources; noisy diffs; no hashing | The problem this design fixes |
| Serve static files from a Cloud Storage bucket (django-storages) | Offloads requests from Cloud Run | A second bucket, upload credentials at build time, a deploy step that must finish before the new revision serves | Traffic is tiny; Cloud Run instances serve files cheaply. Can be revisited with a CDN in DES-011 |
| A CDN or load balancer in front | Edge caching | Fixed monthly cost for the load balancer | Not worth it for stage; DES-011's call for prod |
| nginx in the container | Fast static serving | Two processes in one container and a process manager | WhiteNoise does the job inside gunicorn |
| Collect at container start | Image build stays simpler | Slower cold starts on a service that scales to zero; collect runs on every instance | Build time is the right place |
| Flatten `static/localtools/` to `static/` so the old `images/…` paths resolve | Templates' paths stay as they are | Every URL of the files under it changes, including any links stored in the database (portfolio entries) | Fixing the templates is smaller and keeps existing URLs |
| Exclude the parser's files with collect ignore patterns instead of moving them | No file moves | Easy to miss when files are added; code stays in a directory whose name says "public" | Moving them is clearer |

## Implementation Plan

One branch and pull request.

- [ ] Add WhiteNoise, its middleware, and the storage settings (compressed manifest in base, plain in dev).
- [ ] Update the templates and `site.webmanifest` to use the `static` tag and the real collected paths.
- [ ] Move the parser's code and models from `resume_parser/static/scripts/resume_parser/` to `resume_parser/ml/`; update the settings paths and imports.
- [ ] Delete `static/localtools/admin/`, `static/localtools/bootstrap/`, `static/localtools/styles/` and (after the PythonAnywhere check) the repo-root icon copies.
- [ ] Remove `static_files/` from git and add it to `.gitignore`.
- [ ] Add the collect step to the PythonAnywhere deploy steps in `README.md`.
- [ ] Add a row to the buglog for the informedvoter representative images.

The collect step in the image is written as part of DES-008, which this
design does not depend on.

## Testing / Verification

- `collectstatic` into an empty directory, with base settings and debug off,
  finishes with no errors and writes a manifest.
- With that output and debug off, under gunicorn, the home page, the resume
  page and the admin login render with styles, favicons and logos, and the
  server log shows no missing-manifest errors. Static responses carry a
  long cache header and a gzip encoding when the client accepts it.
- No path under `scripts/`, `uploads/` or `output/` exists in the collected
  output, and no `.py` or `.pkl` file does.
- The test suite passes with dev settings and no collected files.
- `git ls-files static_files` is empty.
- After merging to `develop` and pulling on PythonAnywhere, running
  `collectstatic` and reloading keeps the live site's styles and images.

## Open Questions

- **PythonAnywhere's static mappings.** Which URL paths are mapped to which
  directories on the live site? Expected: `/static/` to `static_files/`
  and `/media/` to `media/`. If `/favicon.ico` or another root path is mapped
  to the repo-root icons, those copies stay. Jeff to check the Web tab.
- **`DetectingAngrySocialMediaPosts.html`.** Nothing in the code links to it
  (2.6 MB). Is it linked from a portfolio entry in the database? If not, it
  can be deleted too; if so, it stays at its current URL.
- **Resume page background.** `section_heading_2.jpg` does not exist
  anywhere. Remove the background or pick an existing image?

## Changelog

- 2026-11-12 — Created.
