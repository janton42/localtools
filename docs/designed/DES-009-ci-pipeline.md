# DES-009: CI pipeline (tests, lint, Terraform checks)

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-19
- **Updated:** 2026-11-19
- **Depends on:** DES-002 (the Terraform roots, for the Terraform check), DES-003 (`pyproject.toml`, `uv.lock` and the dev group, for the Python checks)
- **Related:** DES-002 (the deploy pipeline, which CI is not part of), DES-003 (frozen sync; this design adds the `mysql` extra to its CI row), DES-004 (the dev settings the tests run with), DES-005 (CI sets its variables directly, so it does not depend on the secret loader), DES-006 (tests need no collected static files), DES-007 (tests need no cloud access), DES-008 (the image is built on deploy, not here), DES-012 (the parser's tests)

## Summary

Every pull request into `develop`, `staging` or `main` runs the same checks
before anyone reviews it: the Django test suite against MySQL, Django's
system and migration checks, a lint pass over the Python code, and Terraform
formatting and validation for every root. The checks run on GitHub Actions
in this public repository. They need no Google Cloud access and no secrets,
and they never deploy anything.

## Motivation / Problem

Nothing runs on a pull request today. Tests are run by hand, if at all. Of
the eight test files, only `tasktron/tests.py` and `resume_parser/tests.py`
hold tests; the rest are the three-line stubs Django generates. A change can
therefore break a migration, a template or an import and be merged without
anyone seeing it, and the first failure shows up on the stage deploy.

The Terraform code has no check either. `infra/README.md` already says that
CI "only checks formatting and validity", so that is the job this design
gives it.

The local virtualenv in this clone does not have Django installed, so the
suite's current pass or fail state has not been measured. The first CI run
measures it (see Open Questions).

## Goals and Non-goals

**Goals**

- Each pull request shows a pass or fail for every check before it is
  reviewed.
- CI needs no Google Cloud access, no service account key and no secret.
- Tests run against the same database engine as local development, and
  install the same locked dependencies as the image.
- A failing migration check, a failing test or a badly formatted Terraform
  file blocks the merge once the checks are required (see Required checks).
- Each job finishes in under fifteen minutes.

**Non-goals**

- `terraform plan` and `terraform apply`. Both are run by hand (`infra/README.md`).
  CI would need Google credentials to plan, and the design keeps those out
  of GitHub.
- Building or pushing the container image. The deploy pipeline builds it on
  a push to `staging` (DES-002), and a build in CI would add the time of the
  ML stack's install to every pull request.
- Deploying. That is DES-002's pipeline.
- Enforcing `ruff format` across the codebase. That is a large reformat and
  belongs in its own change.
- Checking the Tailwind build. The image build runs it (DES-008).
- Checking the Cloud Build YAML.
- Dependency and code scanning. Separate work.
- Running the resume parser's packages in tests. That is DES-012.

## Dependencies

| Design | What this design needs from it | Blocks |
|---|---|---|
| DES-002 | The Terraform roots `infra/terraform/shared` and `infra/terraform/envs/stage`, and the `home-env` module, which the Terraform job formats and validates | The Terraform job |
| DES-003 | `pyproject.toml` with the dev group, `uv.lock`, and `.python-version`, which the Python and lint jobs install from | The Python and lint jobs |

Before starting a gated step, check the backlog: every design listed above
must be **Done**. If any is not, stop and do not start the step.

DES-004 and DES-005 are not listed. The Python job sets the variables the
dev settings read, so the job does not depend on how the stage settings or
the secret loader are written. A later change to either design can still
break the tests, and the job would show it.

## Proposed Design

### Where it runs

One workflow file, `.github/workflows/ci.yml`, with three jobs: `python`,
`lint` and `terraform`. It runs on pull requests whose base is `develop`,
`staging` or `main`, and on pushes to those three branches, so a merge is
checked as well as the pull request that carried it. A newer run for the same
pull request cancels the older one.

The workflow sets read-only permissions for the repository contents and
refers to no secret anywhere. Every job runs on the standard Ubuntu runner.

Why GitHub Actions and not Cloud Build: Cloud Build already holds the
deploy credentials, and a check that runs for every pull request should not
run next to them. A pull request's checks also appear on the pull request on
GitHub, where review happens. The Cloud Build trigger is set up for pushes to
`staging`, not for pull requests (DES-002).

The repository is public, so a pull request from a fork runs the workflow
with a read-only token and no secrets. The repository's setting that holds
first-time contributors' workflow runs for approval stays on.

### Jobs

| Job | Needs | What it does |
|---|---|---|
| `python` | DES-003 | Starts a MySQL 8 service container. Installs Python 3.12 from `.python-version` and runs a frozen sync with the dev group and the `mysql` extra. Runs the system check with the dev settings, the migration check, and the test suite |
| `lint` | DES-003 | Installs the same frozen sync and runs ruff with the rules in `pyproject.toml` |
| `terraform` | DES-002 | Checks formatting across `infra/terraform`. For each root, initialises without the remote state backend and validates it |

The `mysql` extra is added to CI's install, which changes DES-003's CI row.
The dev settings use MySQL until DES-010, and the tests should run against
the engine local development uses. The runner installs the MySQL client
headers and `pkg-config` that the extra needs, through a system package step.

**The `python` job's checks, in order**

1. The system check (`manage.py check`) with the dev settings.
2. The migration check (`makemigrations --check --dry-run`). It fails when a
   model changed without a migration.
3. The test suite (`manage.py test`).

### Variables and the test database

The job sets its variables in the workflow itself: the dev settings module,
the database user and password, and a throwaway secret key. None of these
is a real credential. They exist only on the runner and in the workflow
file, which is public, so nothing in them may be reused anywhere else.

Django creates a separate test database, `test_localtools`, so the
service's root user is the one that can create it. Its password is the
throwaway value above. The database host is `localhost` on the service's
mapped port, which is where the dev settings already point.

The secret loader from DES-005 does not run in CI, because no `.env` file
exists on the runner and the variables are already set. Plain environment
variables win over a file, so the job's values are used either way.

### Lint

ruff is added to the dev group (DES-003). The `[tool.ruff]` table in
`pyproject.toml` sets what it checks and what it skips:

- It skips the directories that are not source: `venv`, `node_modules`,
  `media`, `static_files` (collected output, DES-006), and each app's
  `migrations` folder.
- It runs a small set of rules first: syntax errors and undefined names.
  Those are the failures that break the site at runtime. Style rules are
  added later, when the codebase is ready for them.

If the first run finds existing failures, they are fixed in the same change
or the file is excluded with a comment saying why. The count is recorded in
the pull request.

### Terraform

The `terraform` job uses one Terraform version, recorded in the workflow.
It is the newest stable release when the job is written, and it is updated
by hand. The `versions.tf` files require `>= 1.5`, so this version satisfies
them.

The job runs a recursive format check over `infra/terraform`. Then, for
`shared` and `envs/stage`, it initialises with the remote state backend
turned off and runs validate. Initialising still downloads the Google
provider from the public registry, but it does not read the state bucket and
needs no credentials. Validate does not call Google's APIs either.

### Action versions

Each third-party action is pinned to a full commit, with its version in a
comment. A new file, `.github/dependabot.yml`, lets Dependabot propose
updates for the GitHub Actions versions, so the pins do not go stale.

### Required checks

A passing run does not stop a merge on its own. Once the three jobs have run
green on two pull requests, the repository ruleset for `develop`, `staging`
and `main` should require them. That change is made by the repository admin
in the GitHub settings, by hand, and this design does not make it.

### Cost and time

The repository is public, so the standard runners are free. Each job is
expected to take three to five minutes; the MySQL service adds about half a
minute. The `python` job has the longest time and is the one to watch.

### Files

```
.github/
├── workflows/
│   └── ci.yml              # new: python, lint and terraform jobs
└── dependabot.yml          # new: updates the action pins
pyproject.toml              # ruff added to the dev group; [tool.ruff] table
```

`infra/README.md` already describes CI's Terraform check, so it does not
change.

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Cloud Build triggers on pull requests | One tool for deploy and checks | Gives the check access to the project; the first-generation GitHub App trigger is set up for branch pushes only (DES-002) | The check should not run next to the deploy credentials |
| Checks only in the deploy pipeline | Nothing extra to set up | Failures show up after the merge, on staging, not on the pull request | The point is to catch them before review |
| Terraform plan in CI with federated credentials | Shows the planned changes on every pull request | Gives GitHub access to the personal project and its state; plan is run by hand by decision (`infra/README.md`) | Keeps Google access out of GitHub |
| SQLite for the tests | No service container, faster | Different SQL behaviour from MySQL and PostgreSQL hides real bugs | Tests should use the engine the site runs on |
| Building the image in CI | Catches a broken Dockerfile before deploy | Installs the ML stack on every pull request; Cloud Build already builds it on the staging push | Revisit after DES-012 settles how the parser is served |
| Enforcing `ruff format` now | Consistent style | Reformats the whole codebase in one change, which hides real changes in review | Its own change, after this one |
| pre-commit hooks only | Catches problems before a commit | Not enforced: a commit can skip them, and the reviewer cannot see them | Could be added later as a convenience on top of CI |

## Implementation Plan

- [ ] **Gated.** Add ruff to the dev group in `pyproject.toml`, add the `[tool.ruff]` table, and record the baseline count of existing findings.
- [ ] **Gated.** Add `.github/workflows/ci.yml` with the `python` and `lint` jobs, and check it passes on a pull request.
- [ ] **Gated.** Add the `terraform` job to the same workflow file.
- [ ] Add `.github/dependabot.yml` for GitHub Actions. Not gated.
- [ ] Repository admin: add the three jobs as required checks in the ruleset, after two green pull requests. By hand.

## Testing / Verification

- **The workflow runs.** Each job is green on the pull request that adds it.
- **The checks catch what they should.** Once, on a throwaway branch that is
  not merged: a test that fails, a model change with no migration, a Terraform
  file that is not formatted, and a ruff error each turn their job red. Then
  the branch is discarded.
- **No secrets.** The workflow file references no `secrets.` value. A search
  of the file for `secrets` confirms it.
- **Fork pull request.** A test pull request from a fork runs the checks with
  no secret available, and the Terraform job still works.
- **Time.** Each job finishes under fifteen minutes on its first full run.
- **Action pins.** Each `uses:` line is a full commit hash with its version in
  a comment.

## Open Questions

- **Baseline test state.** The virtualenv in this clone has no Django
  installed, so it is not known which tests pass today. The first run of the
  `python` job records it. If the suite is red, fixing the failing tests is a
  separate change that comes first, and this design does not change them.
  Jeff to confirm that order.
- **Lint scope.** Recommend the small set (syntax errors and undefined names)
  now, and wider rules later. Jeff to confirm, or ask for the full default set
  from the start.

## Changelog

- 2026-11-19 — Created. CI is a GitHub Actions workflow with no cloud access.
  The `mysql` extra is added to CI's install (DES-003's CI row updated to match).
