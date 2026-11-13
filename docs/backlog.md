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

- **IDs:** `DES-001`, `DES-002`, … — sequential, never reused. Next free ID: **DES-013**.
- **File names:** `<ID>-<kebab-slug>.md`, e.g. `designed/DES-002-gcp-infrastructure.md`.
- **Promoting an idea:** copy [`templates/design-template.md`](templates/design-template.md)
  into `designed/`, fill it in, and link it from the row (changing its status to *Designed*).
- **Changing phase:** `git mv` the doc into the new phase's directory, update its
  `Status:` line, update the row's status and link — all in one commit.
- **Dependencies.** When one design needs another to be finished first, the
  dependency goes in the doc's `Depends on:` line and Dependencies section,
  and in the row's *Depends on* column here. The steps it blocks are marked
  as gated; before starting one, check that every listed design is *Done*.
  Another design is never written as a step of a plan. For ideas without a
  doc, the column holds what is already known and is completed when the doc
  is written.
- **No code in design docs.** A design doc explains what the code will do, in
  prose, tables and diagrams. Code lives in code files.
- **Merging.** Claude's work is done in a git worktree on its own branch and
  is committed, pushed and opened as a pull request by the machine account
  `janton42-claude`. Jeff reviews, approves and merges; Claude never merges.
  A repository ruleset enforces this on `main`, `develop` and `staging`: a
  pull request with one approval is required, a new push dismisses an earlier
  approval, and only the repository admin can bypass. Jeff may push his own
  changes directly. Local changes are never merged into `develop`. Merging
  `origin/develop` into a working branch to bring it up to date is fine.
- **Attribution.** Commits written by Claude are authored by
  `janton42-claude` and carry no co-author trailer. Commits authored by Jeff
  are Jeff's own work.

---

## Backlog

| ID | Title | Area | Doc | Depends on | Updated | Status |
|---|---|---|---|---|---|---|
| DES-001 | Design docs system | Process | [doc](archive/DES-001-design-docs-system.md) | — | 2026-11-11 | Done |
| DES-002 | GCP infrastructure (stage on Cloud Run) | Infrastructure | [doc](active/DES-002-gcp-infrastructure.md) | DES-003, DES-004, DES-005, DES-006, DES-007, DES-008 | 2026-11-11 | In Progress |
| DES-003 | Dependency management and Python version (Pipfile → pyproject) | Infrastructure | [doc](designed/DES-003-dependencies-python-version.md) | — | 2026-11-11 | Designed |
| DES-004 | Settings package for cloud (stage settings, default settings module) | Infrastructure | | — | 2026-11-11 | Idea |
| DES-005 | Environment config and secrets | Infrastructure | | — | 2026-11-11 | Idea |
| DES-006 | Static files (stop tracking build output, serve from the container) | Infrastructure | [doc](designed/DES-006-static-files.md) | — | 2026-11-12 | Designed |
| DES-007 | Media storage for user uploads | Infrastructure | | — | 2026-11-11 | Idea |
| DES-008 | Container image (Tailwind build, ML dependencies) | Infrastructure | | DES-003 | 2026-11-11 | Idea |
| DES-009 | CI pipeline: tests, lint, Terraform checks | Infrastructure | | DES-002 (Terraform roots) | 2026-11-11 | Idea |
| DES-010 | Data migration from PythonAnywhere MySQL | Infrastructure | | DES-002 | 2026-11-11 | Idea |
| DES-011 | Prod environment and jeffstock.us cutover | Infrastructure | | DES-002 | 2026-11-11 | Idea |
| DES-012 | Serving the resume parser (models no longer load; ML stack kept out of the web image) | Feature | | DES-003 | 2026-11-11 | Idea |
