# Backlog

Master index of all design work for localtools (the site behind jeffstock.us).
Every feature, infrastructure task, or refactor gets a row here. Bugs are
tracked separately in [buglog.md](buglog.md).

## How this works

| Phase | Meaning | Individual doc lives in |
|---|---|---|
| Idea | Rough idea; a single row here, no doc yet | — |
| Designed | Design doc written and agreed; not started | [`designed/`](designed/) |
| In Progress | Actively being built | [`active/`](active/) |
| Done | Shipped | [`archive/`](archive/) |
| Dropped | Rejected or abandoned after design; kept for the record | [`archive/`](archive/) |

**Conventions**

- **IDs:** `DES-001`, `DES-002`, … — sequential, never reused. Next free ID: **DES-012**.
- **File names:** `<ID>-<kebab-slug>.md`, e.g. `designed/DES-002-gcp-infrastructure.md`.
- **Promoting an idea:** copy [`templates/design-template.md`](templates/design-template.md)
  into `designed/`, fill it in, and link it from the row (changing its status to *Designed*).
- **Changing phase:** `git mv` the doc into the new phase's directory, update its
  `Status:` line, update the row's status and link — all in one commit.
- **No code in design docs.** A design doc explains what the code will do, in
  prose, tables and diagrams. Code lives in code files.
- **Merging.** Work is done in a git worktree on its own branch and reaches
  `develop` only through a pull request that is opened and reviewed first.
  Local changes are never merged into `develop`. Merging `origin/develop` into
  a working branch to bring it up to date is fine.

---

## Backlog

| ID | Title | Area | Doc | Updated | Status |
|---|---|---|---|---|---|
| DES-001 | Design docs system | Process | [doc](archive/DES-001-design-docs-system.md) | 2026-11-11 | Done |
| DES-002 | GCP infrastructure (stage on Cloud Run) | Infrastructure | [doc](active/DES-002-gcp-infrastructure.md) | 2026-11-11 | In Progress |
| DES-003 | Dependency management and Python version (Pipfile → pyproject) | Infrastructure | | 2026-11-11 | Idea |
| DES-004 | Settings package for cloud (stage settings, default settings module) | Infrastructure | | 2026-11-11 | Idea |
| DES-005 | Environment config and secrets | Infrastructure | | 2026-11-11 | Idea |
| DES-006 | Static files (stop tracking build output, serve from the container) | Infrastructure | | 2026-11-11 | Idea |
| DES-007 | Media storage for user uploads | Infrastructure | | 2026-11-11 | Idea |
| DES-008 | Container image (Tailwind build, ML dependencies) | Infrastructure | | 2026-11-11 | Idea |
| DES-009 | CI pipeline: tests, lint, Terraform checks | Infrastructure | | 2026-11-11 | Idea |
| DES-010 | Data migration from PythonAnywhere MySQL | Infrastructure | | 2026-11-11 | Idea |
| DES-011 | Prod environment and jeffstock.us cutover | Infrastructure | | 2026-11-11 | Idea |
