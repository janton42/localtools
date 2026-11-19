# DES-010: Data migration from PythonAnywhere MySQL

- **Status:** Designed
- **Area:** Infrastructure
- **Created:** 2026-11-19
- **Updated:** 2026-11-19
- **Depends on:** DES-002 (the stage database and the migrate job), DES-003 (the PostgreSQL driver and the locked Django version), DES-004 (stage settings, with the `DB_HOST` override), DES-007 (upload paths and the file copy)
- **Related:** DES-002 (non-goal: moving the live data), DES-004 (dev stays on MySQL until this is done), DES-005 (the database password on stage), DES-006 (static files, not copied), DES-008 (the image that runs the migrations), DES-011 (the cutover runs the final import from this design)

## Summary

The live site's data moves from the MySQL database on PythonAnywhere to the
PostgreSQL database on stage, and later to prod. The move is done with
Django's own dump and load, not with a MySQL-to-PostgreSQL conversion. The
dump is taken with the live code, loaded into a schema that Django builds
from the same migrations, and checked row by row against the source before
anyone relies on it. This design covers the procedure, a rehearsal on stage,
and the checks. The final load into prod is a step of the cutover (DES-011).

## Motivation / Problem

The live site has real accounts, and the data is what makes it the live
site: users and password hashes, the rate requests, the resume uploads and
their parsed results, the veteran applicant records, the homeorg inventory,
the informedvoter contributions and the task lists. Stage can't be tested
against real data, and prod can't start, until it has been moved.

DES-002 deliberately left the move out, and DES-007 and DES-004 both
point here. Without a written procedure, the first move would be the
cutover itself, with no rehearsal, no measured downtime and no way back.

## Goals and Non-goals

**Goals**

- Every row of every app's tables arrives on the target with the same
  values, and the checks say so.
- Passwords and login sessions work for users after the move (password
  hashes move unchanged).
- A full rehearsal on stage, timed, so the cutover's downtime is measured
  before it happens.
- The live MySQL database is not changed by the procedure, so the site can
  be returned to PythonAnywhere if the cutover fails.
- No personal data in git, in the image, or in a cloud bucket.

**Non-goals**

- Files on disk: resume uploads, informedvoter uploads, portfolio images and
  the `media/` folder. These are DES-007's upload paths and the file copy
  that DES-007 hands to this design. This design says when they are copied,
  not how the storage works.
- Moving local development off MySQL. DES-004 leaves that open; this design
  does not change it.
- The prod environment and the domain switch (DES-011).
- Changing the schema. The move copies data into the schema the migrations
  produce; any model change is its own design.
- A reverse sync from the new site back to MySQL. See Rollback for what is
  possible.

## Dependencies

| Design | What this design needs from it | Blocks |
|---|---|---|
| DES-002 | The stage PostgreSQL instance, the Cloud Run migrate job, and the database start step | Every step that touches stage's database |
| DES-003 | The PostgreSQL driver in the main group, and the frozen lock so the target and the source use the same Django version | The rehearsal load |
| DES-004 | Stage settings that load the PostgreSQL database through the `DB_HOST` override from a workstation | The rehearsal load |
| DES-007 | The new upload paths and the rule that old rows keep their stored names, so the file copy can match them | The file copy step |

Before starting a gated step, check the backlog: every design listed above
must be **Done**. If any is not, stop and do not start the step.

## Proposed Design

### Overview

```
  PythonAnywhere                         Workstation                      Stage / prod
  (MySQL, live code)                                                      (PostgreSQL 17)

  dump app data as JSON  ──transfer──▶  verify counts ──────────────▶  migrate (Django builds
  (no auth sessions,                    load through the proxy          the schema from the
   no content types,                    and the stage settings          same migrations)
   no migration log)                                                    then load the JSON
                                                                        ▲
  upload files on disk  ───────────────────────────────────────────────┘ (DES-007 paths)
```

The dump and the load go through Django, so the values arrive in the form
each field expects (booleans, decimals, timezone-aware datetimes), without
any translation between the two database engines. The dump is produced
where the live code and the live schema already match, so there is no
question about which version of a model wrote which row.

### What is copied

| Group | Copied | Why |
|---|---|---|
| App tables (all nine apps) | Yes | This is the data |
| Users and groups | Yes | Accounts and password hashes move unchanged, so users keep their logins |
| Permissions and content types | No | Django recreates them on migrate. Copying them would collide with the ids the target creates |
| Login sessions | No | Users log in once again after the move. Nothing in the data depends on a session |
| Cache table | No | The app's cache is rebuilt by use (DES-002's migrate job creates the table) |
| Migration history | No | The target's history comes from its own migrate run |
| Admin log | No | Records past admin edits, not site data |

The dump's exclusions are written as a list in the procedure, so the same
set is used for the rehearsal and for the cutover.

### Taking the dump

The dump is taken on PythonAnywhere, from the live code, after the code
has been brought to the commit that is being deployed to the target. The
live database's migrations are the ones already applied there, so the dump
matches the schema the code expects.

The file is written outside the repository and downloaded to the
workstation. It holds personal data and password hashes, so it is:

- never committed, never placed in the repo folder, and never copied into
  the container image or a cloud bucket;
- deleted from PythonAnywhere once the load has been verified;
- deleted from the workstation after the cutover is confirmed, or kept only
  under the same rule as the live data.

### Loading the target

The target's database is migrated first, from the same code, so every
table exists and every later migration has run. The dump is then loaded
through the stage settings and the Cloud SQL Auth Proxy, with the `DB_HOST`
override from DES-004. The load runs from the workstation, not from a Cloud
Run job, so the dump never reaches Google's infrastructure, and no service
account or bucket is needed.

Loading resets the database sequences, so new rows get ids after the old
ones. The procedure checks that the first row created after the load gets
a fresh id.

### Checks

Before anyone uses the target, the checks compare the two sides:

- **Row counts** per table, from the live MySQL database and from the target,
  must match for every table that was copied. Each difference is explained
  or the load is repeated.
- **Spot checks** of known records: one account that can log in, one rate
  request, one resume with its parsed result, one informedvoter record with
  its links.
- **Login.** A test account, not a real user's, logs in on the target. The
  owner's own account logs in after the cutover.
- **Pages.** Each app's main page renders with the copied data. The pages are
  listed in the rehearsal's checklist.
- **Character data.** Names, notes and descriptions with accents or emoji
  read the same on both sides. Any stored null byte is found by the load
  itself, since PostgreSQL refuses it, and is reported rather than dropped.
- **Uploads.** Each copied upload row resolves to a file on the target
  (DES-007).

### The rehearsal on stage

Before any prod work, the whole procedure runs against stage:

1. Take the dump, and time it.
2. Transfer it, and time it.
3. Load it into stage, and time it.
4. Run the checks.
5. Record every step and its time in the design's changelog, so the cutover
   can be planned from real numbers.

Stage keeps the copy for testing. Before the cutover, stage's data is reset,
so stage holds real personal data only while it is being used for tests
(see Open Questions).

### The cutover (DES-011)

DES-011 owns the cutover. Its steps for the data are these:

1. Take the live site offline, for example by disabling the web app on
   PythonAnywhere's Web tab, so no writes happen after the dump.
2. Take the final dump.
3. Transfer it, load it into prod, and run the checks.
4. Point the domain at prod.
5. Leave the MySQL database and the PythonAnywhere app in place, unchanged,
   for the rollback window.

The downtime is the time from step 1 to step 4. The rehearsal's timings give
the expected figure. The target is under an hour, and DES-011 confirms it
against the rehearsal.

### Rollback

Until the first write lands on the new site, the cutover can be reversed by
switching the domain back and enabling the PythonAnywhere app again, which is
unchanged. After that point, reversing would mean exporting the new site's
data back into MySQL, which this design does not cover. The window in which
rollback is simple is therefore short, and DES-011 says how long it stays
open.

### Files

```
docs/designed/DES-010-data-migration.md   # this design
```

The procedure itself is written by hand into `infra/README.md`'s runbook
(DES-002 creates the runbook section), with its exclusions list. Any helper
command the load needs is a code change in a later pull request, not part of
this design.

## Alternatives Considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Convert the MySQL dump's SQL to PostgreSQL | Fast, no Django needed | Types, quoting and boolean encoding differ between the engines, and the conversion has to be trusted without checking each value | The dump and load through Django give the same values with less risk |
| pgloader from MySQL straight into the migrated schema | Fast, loads data directly, handles types | An extra tool to install and trust; it reads the MySQL schema, so the mapping has to be checked for each column | Possible later for a large dataset. The data here is small enough for Django's own load |
| Load through a Cloud Run job, with the dump in a bucket | Runs inside Google, no workstation | A personal-data dump in a bucket, and a job that holds the password for longer | The workstation keeps the dump out of the cloud |
| Copy sessions and the cache as well | Users stay logged in at cutover | Sessions and cache have no value to keep; copying them tangles the auto-id ranges | Users log in once after the move |
| Freeze writes without taking the site offline | No downtime | PythonAnywhere offers no read-only mode for the web app | Downtime is short and measured, so offline is simpler |

## Implementation Plan

- [ ] **Gated.** Record the live database's size, table count and character set on PythonAnywhere in this doc, before the rehearsal.
- [ ] **Gated.** Write the exclusions list and the take, transfer, load and check steps into `infra/README.md`'s runbook.
- [ ] **Gated.** Rehearsal on stage, as described above. Record the timings in the changelog.
- [ ] **Gated.** Write the load helper as a code change, if the manual load needs one, with a test that it skips the excluded groups.
- [ ] Hand the rehearsal's downtime figure to DES-011.

## Testing / Verification

- **Counts.** Every copied table's row count matches the live database.
- **Logins.** A rehearsal account logs in on stage with its existing password.
- **Pages.** Each app's main page renders with copied data on stage, with no
  error in the Cloud Run logs.
- **Ids.** A new row created after the load gets an id above the largest
  copied id.
- **Uploads.** Each copied upload row opens on stage.
- **Timing.** The rehearsal's total time is recorded; the cutover's downtime is
  within the figure in the design.

## Open Questions

- **Does stage hold a copy of the live data?** Recommend: yes, for the
  rehearsal and for testing, reset to empty before the cutover, so real
  personal data sits on stage only while it is used. Jeff to decide.
- **Should users log in again after the move?** Recommend: yes, since
  sessions are not copied and the first login after the cutover is one
  password entry. Jeff to confirm.
- **Live database size and character set.** Not known from this clone; they
  are checked on PythonAnywhere before the rehearsal, and the implementation
  records them here. If the character set is not utf8mb4, the character-data
  check is widened before the rehearsal.

## Changelog

- 2026-11-19 — Created. Procedure is a Django dump and load, not an SQL
  conversion. Sessions, the cache and migration history are not copied.
  Rehearsal on stage comes before any prod work.
