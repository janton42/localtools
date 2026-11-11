# Buglog

Master index of all bugs for localtools. Feature and infrastructure work is
tracked separately in [backlog.md](backlog.md).

## How this works

| Phase | Meaning | Individual doc lives in |
|---|---|---|
| Reported | One-line report; a single row here, no doc yet | — |
| Triaged | Investigated; root cause and fix written up | [`bugfixes/open/`](bugfixes/open/) |
| Fixing | Fix underway | [`bugfixes/open/`](bugfixes/open/) |
| Closed | Fixed or Won't Fix | [`bugfixes/closed/`](bugfixes/closed/) |

**Conventions**

- **IDs:** `BUG-001`, `BUG-002`, … — sequential, never reused. Next free ID: **BUG-005**.
- **File names:** `<ID>-<kebab-slug>.md`, e.g. `bugfixes/open/BUG-001-node-modules-tracked-in-git.md`.
- **Triaging a report:** copy [`templates/bugfix-template.md`](templates/bugfix-template.md)
  into `bugfixes/open/`, fill it in, and link it from the row (moving the row to *Triaged*).
- **Changing phase:** update the doc's `Status:` line, move the row to the matching
  section below, and when closing, `git mv` the doc into `bugfixes/closed/` and fix
  the link — all in one commit.

---

## Reported

| ID | Title | Area | Doc | Updated |
|---|---|---|---|---|
| BUG-001 | `node_modules/` is tracked in git | Infrastructure | | 2026-11-11 |
| BUG-002 | `static_files/` (collectstatic output) is tracked in git | Infrastructure | | 2026-11-11 |
| BUG-003 | `manage.py` defaults to `localtools.settings`, which is a directory with no settings in it; `wsgi.py` sets no default at all | Infrastructure | | 2026-11-11 |
| BUG-004 | `README.md` is still the placeholder template | Process | | 2026-11-11 |

## Triaged

| ID | Title | Area | Doc | Updated |
|---|---|---|---|---|

## Fixing

| ID | Title | Area | Doc | Updated |
|---|---|---|---|---|

## Closed

| ID | Title | Area | Doc | Updated |
|---|---|---|---|---|
