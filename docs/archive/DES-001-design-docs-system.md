# DES-001: Design docs system

- **Status:** Done
- **Area:** Process
- **Created:** 2026-11-11
- **Updated:** 2026-11-11
- **Related:** branch `design/docs-and-infra-plan`

## Summary

A two-layer documentation system in `docs/`: index files that list every item
by phase, plus one design doc per item, filed in a directory that matches its
phase.

## Motivation / Problem

localtools has grown app by app with no written designs. The next stretch of
work is infrastructure: moving the site off PythonAnywhere and onto Google
Cloud. That is a chain of dependent changes, and each one needs to be agreed
before it is built. Without one place that lists what is planned, active and
finished, the designs would drift and get lost.

## Goals and Non-goals

**Goals**

- One place to see all work at a glance, grouped by phase.
- Bugs tracked in a separate index with the same format.
- Every item past the rough-idea phase has its own doc, in a directory that
  matches its phase.
- Design docs stay readable as designs: they explain what the code will do
  and never contain the code.

**Non-goals**

- Replacing an issue tracker or adding tooling or automation. This is plain
  Markdown in git.

## Proposed Design

**Layer 1: index files**

- [`docs/backlog.md`](../backlog.md) lists features and infrastructure work
  with a status of Idea, Designed, In Progress, Done or Dropped.
- [`docs/buglog.md`](../buglog.md) lists bugs in the phases Reported →
  Triaged → Fixing → Closed, one table per phase.

**Layer 2: per-item docs**

```
docs/
├── backlog.md
├── buglog.md
├── designed/        # DES docs: designed, not started
├── active/          # DES docs: in progress
├── archive/         # DES docs: done or dropped
├── bugfixes/
│   ├── open/        # BUG docs: triaged or fixing
│   └── closed/      # BUG docs: fixed or won't fix
└── templates/
    ├── design-template.md
    └── bugfix-template.md
```

An idea is one row in the backlog. When it is designed, the design template
is copied into `designed/` and the row links to it. When its phase changes,
the doc is moved to the matching directory and the row is updated in the same
commit. Bugs work the same way with the bugfix template.

**Rules**

- IDs are `DES-NNN` and `BUG-NNN`, sequential and never reused. Each index
  records the next free ID.
- File names are the ID followed by a kebab-case slug.
- A design doc contains prose, tables and diagrams (directory trees
  included). It contains no code. Code lives in code files, and the doc says
  what that code will do and where it will live.
- Work is done in a git worktree on its own branch and reaches `develop` only
  through a reviewed pull request. Local changes are never merged into
  `develop`; merging `origin/develop` into a working branch is fine.

The structure and both templates follow the ones used in the hl_vae project,
so the two repos read the same way. Nothing else is shared with that project.

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| GitHub Issues and Projects | Built-in tracking, links to PRs | Designs live outside the repo and aren't reviewed with the code | Designs should be reviewed in PRs and versioned with the code |
| One large design document | Everything in one file | Hard to review, no per-item status | Items move through phases independently |

## Implementation Plan

- [x] Create the `docs/` tree with placeholder files for empty directories.
- [x] Add the design and bugfix templates.
- [x] Add `backlog.md` and `buglog.md`, seeded from the first review of the repo.
- [x] File this doc in `archive/` as Done.

## Testing / Verification

Every relative link in the two index files resolves. Each doc sits in the
directory that matches its `Status:` line.

## Open Questions

- None.

## Changelog

- 2026-11-11 — Created and delivered in the same PR.
