# DES-004: Settings package for cloud (stage settings, default settings module)

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-12
- **Updated:** 2026-11-12
- **Depends on:** DES-003 (see Dependencies)
- **Related:** DES-002 (app contract, environment variables), DES-005 (loads the secret these settings read), DES-006 (static files), DES-007 (media), DES-011 (prod settings on Cloud Run), DES-013 (outgoing email)

## Summary

Add `localtools.settings.stage` for Cloud Run: debug off, hosts and CSRF
origins from the environment, PostgreSQL over the Cloud SQL socket, HTTPS
behind Cloud Run's proxy, and logs on the console. Fix the default settings
module, which today points at a package that holds no settings, and stop the
URL configuration from importing a dev-only package.

## Motivation / Problem

DES-002 sets `DJANGO_SETTINGS_MODULE` to `localtools.settings.stage` on the
web service and both jobs, and that module does not exist. The app contract
asks for it, with debug off and hosts and CSRF origins taken from the
environment, and for a default settings module that resolves.

The settings package has other problems that would stop stage or confuse
anyone running the project:

- **The default doesn't resolve.** `manage.py` and `asgi.py` default to
  `localtools.settings`, which is the package directory itself. It has no
  `__init__.py` and no settings, so a command run without the variable set
  fails with an error about an empty `SECRET_KEY`, which hides the real cause.
  `wsgi.py` has its default commented out.
- **The `.env` line does nothing.** `localtools/.env` holds a
  `DJANGO_SETTINGS_MODULE` line, but the file is read by `base.py`, which only
  runs after the settings module has already been chosen. It works today only
  because the variable is also set in the shell or in PythonAnywhere's own
  WSGI file.
- **The URL configuration imports a dev package.** `localtools/urls.py`
  includes `django_browser_reload.urls` for every environment. DES-003 moves
  that package into the dev group, which the image does not install, so every
  request on stage would fail when the URL configuration loads.
- **Errors go nowhere.** With debug off, Django sends 500 tracebacks to the
  site admins by email. No admins and no email are configured, so on stage a
  failing page would leave no trace in the logs.
- **Email is not configured.** The password reset page sends email, and no
  email backend is set, so Django tries an SMTP server on localhost. That is
  broken on the live site today and would be broken on stage too.

## Goals and Non-goals

**Goals**

- A stage settings module that works on Cloud Run with only the five
  variables Terraform sets plus the values DES-005 loads from the secret.
- A default settings module that always resolves, and that never picks a
  development configuration for a server by accident.
- The site starts without the dev group installed.
- Errors on stage show up in Cloud Logging with their tracebacks.
- Django's deployment check passes with the stage settings.
- The live site on PythonAnywhere keeps working with no change on its side.

**Non-goals**

- How values get into the environment on Cloud Run, or fixing how `.env` is
  found (it is read relative to the working directory today). That is DES-005.
- Static file serving (DES-006) and the media bucket (DES-007). Stage inherits
  the static and media settings from `base.py` unchanged; those designs change
  them.
- Settings for a prod environment on Cloud Run (DES-011). `prod.py` stays the
  PythonAnywhere configuration until the cutover.
- Sending real email (DES-013). Stage writes outgoing email to the log.
- Moving local development off MySQL. Dev keeps its current database settings.
- The broken `asgi.py`, which imports packages and an app that don't exist.
  DES-003 adds it to the backlog. Nothing here touches it.

## Dependencies

| Design | What this design needs from it | Blocks |
|---|---|---|
| DES-003 | The PostgreSQL driver in the main group, and `django-browser-reload` moved to the dev group | The PostgreSQL check and the check without the dev group, in Testing / Verification |

The settings files can be written before DES-003 is done, since nothing in
them imports the driver. Proving them against a real PostgreSQL database, and
proving the site starts without the dev group, needs DES-003.

Before starting a gated step, check the backlog: every design listed above
must be **Done**. If any is not, stop and do not start the step.

## Proposed Design

### Package layout

```
localtools/
├── settings/
│   ├── __init__.py   # new, empty: makes settings a regular package
│   ├── base.py       # shared by every environment; gains console logging
│   ├── dev.py        # local development; unchanged
│   ├── stage.py      # new: Cloud Run stage
│   └── prod.py       # PythonAnywhere; unchanged until DES-011
├── urls.py           # browser-reload route only when the app is installed
├── wsgi.py           # default settings module restored
└── asgi.py           # unchanged (see Non-goals)
manage.py             # default settings module fixed
```

Each environment module starts from everything in `base.py` and sets only
what differs. `stage.py` builds on `base.py`, not on `prod.py`, because
`prod.py` hard-codes the PythonAnywhere database and hostnames.

### Default settings module

An explicitly set `DJANGO_SETTINGS_MODULE` always wins: the defaults below
apply only when the variable is missing.

| Entry point | Default | Why |
|---|---|---|
| `manage.py` | `localtools.settings.dev` | It is run by hand on a developer's machine far more than anywhere else. On Cloud Run the jobs always set the variable |
| `wsgi.py` | `localtools.settings.prod` | It is what a server loads. If the variable were ever missing on a server, it should start with debug off and fail to reach a database it can't see, not start in debug mode with every host allowed |

The PythonAnywhere WSGI file already sets the variable (the site works today
with no default in `wsgi.py`), so the live site is unaffected. The
`DJANGO_SETTINGS_MODULE` line in `localtools/.env` is removed, since it has
never had any effect, and the README says to set the variable in the shell
when not using dev.

### Stage settings

| Setting | Value on stage | Notes |
|---|---|---|
| Debug | Off | |
| Allowed hosts | The comma-separated list in `DJANGO_ALLOWED_HOSTS` | Required: startup fails if it is missing. On stage it holds both URLs Cloud Run gives the service (the one built from the project number and the older hashed one) |
| CSRF trusted origins | Each allowed host with `https://` in front | Derived, so there is one list to keep up to date |
| Proxy SSL header | Trust `X-Forwarded-Proto` | Cloud Run ends TLS in front of the container and sets this header. Without it Django thinks every request is plain HTTP, and the redirect below would loop |
| SSL redirect, secure session and CSRF cookies | On | |
| HSTS | One hour, without subdomains or preload | Enough for the deployment check. The `run.app` hostname is temporary and shared, so it gets no long-lived or preloaded policy; DES-011 sets the full policy for jeffstock.us |
| Database | PostgreSQL, database `localtools`, user from `DB_USER`, password from `DB_PASSWORD` | Host is the Cloud SQL socket directory, `/cloudsql/` followed by `GCP_CLOUDSQL_CONNECTION_NAME`, which Cloud Run mounts. No port |
| Database host override | `DB_HOST`, if set, replaces the socket directory | Not set on Cloud Run. Lets the stage settings run locally against a local PostgreSQL or the Cloud SQL Auth Proxy |
| Persistent connections | Kept for 60 seconds, checked before reuse | Saves a connection per request. The smallest shared-core instance allows about 25 connections, so instances times workers must stay under that; DES-008 sets the worker count |
| Email backend | Console | Outgoing email, such as password resets, is written to the log instead of failing. DES-013 replaces this |
| Cache | Inherited database cache table | The migrate job creates the table (DES-002) |
| Static files, media | Inherited from `base.py` | Changed by DES-006 and DES-007 |

`DJANGO_SECRET_KEY` is already required by `base.py` and stays there.

### Logging

`base.py` gains a logging configuration that sends Django's log, including
request errors with their tracebacks, to the console at info level. Cloud Run
collects anything a container writes to standard output and standard error,
so this is all stage needs; locally it is what `runserver` already shows. No
admins are added, and email is not used for errors.

### URL configuration

The `__reload__/` route is added only when `django_browser_reload` is in the
installed apps, which is true only in dev. Dev keeps the live reload, and the
other environments never import the package. The media route from
`django.conf.urls.static` is left alone: it already does nothing with debug
off, and DES-007 decides how media is served.

### Environment the stage settings read

| Variable | Comes from | Required |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Terraform (DES-002) | Yes |
| `GCP_CLOUDSQL_CONNECTION_NAME` | Terraform (DES-002) | Yes, unless `DB_HOST` is set |
| `DJANGO_SECRET_KEY` | The secret (DES-005) | Yes |
| `DB_USER` | The secret (DES-005) | Yes |
| `DB_PASSWORD` | The secret (DES-005) | Yes |
| `DJANGO_ALLOWED_HOSTS` | The secret (DES-005) | Yes |
| `DB_HOST` | Local shell only | No |

These are the keys DES-005 must load on stage. `DJANGO_SECRET_KEY`,
`DB_USER` and `DB_PASSWORD` keep the names the dev and prod settings already
use. The allowed hosts live in the secret rather than in Terraform because
the service's URLs are only known once the service exists, and Terraform
can't feed a service its own URL.

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| One settings file driven entirely by environment variables | One file, twelve-factor style | A large rewrite of working dev and prod settings; every difference becomes a variable to set in three places | Separate modules already exist and DES-002 names `settings.stage` |
| `stage.py` built on `prod.py` | Inherits the security settings | Inherits the PythonAnywhere database, hostnames and a two-year preloaded HSTS policy that must all be undone | Less to override starting from `base.py` |
| A shared module with the security settings used by stage and prod | No repetition | Only two users, one of which (`prod.py`) is replaced at the cutover | Can be done in DES-011 when prod moves to Cloud Run |
| Default to dev everywhere | Simplest | A server with the variable missing starts in debug mode with every host allowed | The server entry point should fail safe |
| No default at all; require the variable | Never guesses | Every local command needs the variable set first | `manage.py` defaulting to dev is the common convenience, and servers already set it |
| Allowed hosts as a sixth Terraform variable | Visible in Terraform, not secret | Terraform can't give a service its own URL without a second apply or a hard-coded hostname | The secret is edited by hand already and holds it simply |
| Allow every host on stage | Nothing to configure | Turns off Django's host header protection | Stage should behave like prod |

## Implementation Plan

One branch and pull request.

- [ ] Add the empty `__init__.py`, and fix the defaults in `manage.py` and `wsgi.py`.
- [ ] Remove the `DJANGO_SETTINGS_MODULE` line from the local `localtools/.env` (not tracked in git) and say in the README when to set it.
- [ ] Add console logging to `base.py`.
- [ ] Write `stage.py` as described above.
- [ ] Include the `__reload__/` route only when `django_browser_reload` is installed.
- [ ] Add tests for the stage settings (see below).
- [ ] **Gated.** Run the PostgreSQL check and the check without the dev group, below.

## Testing / Verification

- With no `DJANGO_SETTINGS_MODULE` set, `manage.py check` loads the dev
  settings.
- With the stage settings and placeholder values for the variables above,
  Django's system check and its deployment check pass with no warnings.
- A test loads the stage settings with dummy values and asserts debug is off,
  the CSRF origins are the hosts with `https://` in front, the database host
  is the socket directory built from the connection name, and `DB_HOST`
  replaces it when set.
- Loading the stage settings without `DJANGO_ALLOWED_HOSTS` fails at startup
  with a message naming the variable.
- **Gated on DES-003.** With only the main group installed, gunicorn serves
  the home page with the stage settings (no import error from the browser
  reload package).
- **Gated on DES-003.** With `DB_HOST` pointing at a local PostgreSQL,
  migrations run and a page that reads the database renders.
- On stage, after the first deploy (DES-002): a request to a missing page
  returns 404 with no debug page, a forced error shows its traceback in Cloud
  Logging, plain HTTP redirects to HTTPS without a loop, and logging in to the
  admin raises no host or CSRF error.

## Open Questions

- **Dev database.** Should local development move from MySQL to PostgreSQL
  so it matches stage? Proposed: not in this design. It makes the most sense
  once the live data has moved off MySQL (DES-010), and the `DB_HOST`
  override already lets anyone run the stage settings against a local
  PostgreSQL in the meantime.
- **Answer** Leave it on MySQL until DES-010

## Changelog

- 2026-11-12 — Created. Outgoing email split out as DES-013.
