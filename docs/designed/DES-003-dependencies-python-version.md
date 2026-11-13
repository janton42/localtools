# DES-003: Dependency management and Python version (Pipfile → pyproject)

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-11
- **Updated:** 2026-11-11
- **Depends on:** None
- **Related:** DES-002 (app contract), DES-008 (container image), DES-012 (serving the resume parser), DES-011 (the end of MySQL)

## Summary

Replace the Pipfile with a `pyproject.toml` and a `uv.lock`, pin Python to
3.12, and add what stage needs: gunicorn and the PostgreSQL driver. The
resume parser's machine-learning stack moves into an optional group that the
web image does not install, so it can't hold up the first deploy.

## Motivation / Problem

DES-002 needs pinned dependencies that install in a container, a production
WSGI server and a PostgreSQL driver. The current setup has none of these:

- The Pipfile lists every package as `*`. Only the lock pins versions, and
  pipenv is a tool nothing else here uses.
- It asks for Python 3.10, which reached end of life in October 2026. The
  local virtualenv is 3.12, and the machine's own Python is now 3.14.
- There is no WSGI server and no PostgreSQL driver. `mysqlclient` is the
  only database driver.
- The Pipfile is wrong about what the code uses. `pdfminer` is imported by
  the resume parser but is not listed. `requests` is listed but nothing
  imports it. `asgiref` and `sqlparse` come in with Django anyway. The
  tailwind extra is misspelled (`cookieutter`).
- The resume parser can't work with the locked versions anyway. Its three
  models were pickled with scikit-learn 1.1.1, and the locked 1.7.2 fails
  to load them (`No module named 'sklearn.ensemble._gb_losses'`). Getting
  versions old enough to load them means old NumPy and old Python too.
  Together with NLTK and its data, this is most of the image's size and
  memory, all for one feature that is already broken.

## Goals and Non-goals

**Goals**

- One standard project file (`pyproject.toml`) and one lock file that pins
  every package, including the indirect ones.
- Python 3.12 everywhere: locally, in the image, and in the lock.
- The web install has Django, gunicorn, the PostgreSQL driver and nothing
  heavy.
- The site starts and passes its tests without the resume parser's packages.

**Non-goals**

- Making the resume parser work again, or choosing how to serve it. That is
  DES-012.
- Settings changes such as `DATABASES` for PostgreSQL (DES-004).
- The Dockerfile (DES-008). This design only says what the image installs.
- The broken `localtools/asgi.py`, which imports `channels` and a `chat` app
  that don't exist. gunicorn uses the WSGI entry point and never loads it.
  It is left alone and noted in the backlog.

## Proposed Design

### Tooling

uv manages the project. `pyproject.toml` lists only the packages the code
uses directly, with lower bounds. `uv.lock` pins everything. The image
installs with a frozen sync that leaves out the dev group and every optional
group, so a build can never pick up a version that differs from the lock.
`Pipfile` and `Pipfile.lock` are deleted in the same change.

The project is an application, not a library. The file declares no build
backend, and uv does not install the project itself into the environment.

### Python version

`requires-python` is set to 3.12 and above but below 3.13, and a
`.python-version` file holds `3.12`. `.python-version` is ignored in
`.gitignore` today, so that line is removed. uv downloads 3.12 when the
machine doesn't have it, which covers the system Python now being 3.14.
3.12 is supported by Django 5.2 and all the packages below until 2028, and
it matches the virtualenv already in use.

### Dependency groups

| Group | Installed where | Packages | Why |
|---|---|---|---|
| Main | Everywhere, including the image | Django 5.2 (LTS), django-environ, django-tailwind, Pillow, gunicorn, psycopg 3 with its binary build | The site itself, the production WSGI server, the stage database driver. Pillow is needed for image fields |
| `mysql` (optional) | Only where the site still runs on MySQL: local dev and PythonAnywhere | mysqlclient | Removed when the live site moves off MySQL (DES-010, DES-011). Kept out of the image so it doesn't need MySQL's C headers |
| `parser` (optional) | Nowhere by default | scikit-learn, joblib, nltk, pandas, pdfminer.six, striprtf | The resume parser only. Versions stay unpinned beyond the lock until DES-012 decides how it runs |
| `dev` | Local only | django-browser-reload | `localtools.settings.dev` adds it to installed apps and middleware |

The tailwind extras `honcho` and `reload` move to the dev group, since they
are only used locally (`manage.py tailwind dev` runs `Procfile.tailwind`
through honcho). The `cookiecutter` extra is dropped: it is only used to
create a theme app, and `theme/` already exists. Django stays on the 5.2 LTS line until 2028,
not the newest release.

### The resume parser without its packages

The parser module and the `rates` scripts that use pandas must not be
imported when the site starts. The implementation checks every import of
pandas, nltk, joblib, sklearn, pdfminer and striprtf outside
`resume_parser/static/scripts/` and moves each one inside the view or
function that uses it. When the packages are missing, the resume parser's
upload and parse pages render a short "temporarily unavailable" message, and
every other page works. If `rates` really needs pandas to serve a page, that
page is the one exception: pandas moves into the main group and the reason
is written into this doc.

### What changes for each consumer

| Consumer | Before | After |
|---|---|---|
| Local dev | `pipenv install` | `uv sync --extra mysql` for the full local site; add `--extra parser` to work on the parser |
| PythonAnywhere (live) | Installed by hand from the Pipfile | Installed by hand from a requirements file that uv exports from the lock, with the `mysql` and `parser` groups, so the live site keeps its parser until cutover |
| Container image (DES-008) | Not built yet | Frozen sync, main group only. The Tailwind build is still DES-008's job. Without ML packages or NLTK data, the image is much smaller, and the DES-002 memory figure of 1 GiB can be revisited |
| CI (DES-009) | None | Will run the same frozen sync with the dev group |

### Files

```
pyproject.toml      # new: project metadata, Python range, groups
uv.lock             # new: full pin set, committed
.python-version     # new: 3.12 (and removed from .gitignore)
Pipfile             # deleted
Pipfile.lock        # deleted
README.md           # install steps rewritten for uv
```

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Keep pipenv and pin the Pipfile | Smallest change | Slow, a niche tool, no standard project file | The backlog item exists to move to `pyproject` |
| `requirements.txt` compiled with pip-tools | Universal, simple | Separate files per group, no single lock across groups | uv gives one lock and can still export requirements for PythonAnywhere |
| Poetry | Mature, groups and lock | Heavier, its own project format | uv is faster and already installed |
| Keep the ML stack in the main install, pinned to versions that load the 1.1.1 models | The parser works on stage | Python 3.10 or 3.11 and NumPy 1.x for the whole site, a large image, and more memory on every instance for one feature | The parser should not set the Python version or the size of the site |
| Python 3.13 or 3.14 | Newer | Older scientific packages that DES-012 may need have no wheels for them | 3.12 is the safe common ground and is supported until 2028 |

## Implementation Plan

One branch and pull request.

- [ ] Write `pyproject.toml` with the groups above, add `.python-version`, take it out of `.gitignore`, and generate `uv.lock`.
- [ ] Move the heavy imports inside the views that use them, and add the "temporarily unavailable" message to the resume parser pages.
- [ ] Delete `Pipfile` and `Pipfile.lock`, and rewrite the install section of `README.md`.
- [ ] Add a row to the backlog for the broken `asgi.py`.

## Testing / Verification

- With a fresh environment that has only the main and dev groups, the Django
  system check passes and the test suite runs.
- With the main group alone, `gunicorn localtools.wsgi` starts and serves
  the home page (with SQLite or a local PostgreSQL through a temporary
  settings override; the real stage settings are DES-004).
- The resume parser pages show the unavailable message instead of an error
  when the `parser` group is missing.
- A frozen sync fails if `pyproject.toml` and `uv.lock` disagree.
- The exported requirements file installs on Python 3.12 with the `mysql`
  and `parser` groups.

## Open Questions

- **PythonAnywhere's Python.** The live site's Python version is unknown
  here. If it is older than 3.12, the exported requirements are still
  usable, but it needs a 3.12 virtualenv there. Jeff to check.
- **Answer** Python 3.10.5. If you mean that PythonAnywhere needs a 3.12 virtualenv,
  explain why. Nothing should need to change on that side.

## Changelog

- 2026-11-11 — Created. The resume parser's packages moved into an optional
  group; how it is served is split out as DES-012.
