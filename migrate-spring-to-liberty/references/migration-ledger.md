# Migration contract, ledger, and module transactions

Use this reference for every full or single-module migration. Keep one `migration-report.md` in the target project as the durable source of truth.

## Contents

- [Baseline](#baseline)
- [Contract](#contract)
- [Module ledger](#module-ledger)
- [Transaction protocol](#transaction-protocol)
- [Resume protocol](#resume-protocol)

## Baseline

Record before any migration edit:

```markdown
## Baseline

- Timestamp and project path:
- Branch/default branch/remote:
- Pre-existing worktree changes:
- Build launcher and JDK:
- Compile/package command and result:
- Test command, counts, and result:
- Application bootstrap and expected routes:
- Views/static assets:
- Datasource, driver, schema policy, and required services:
- Authentication/authorization:
- Container runtime, ports, and network constraints:
- Pre-existing failures/blockers:
- Generated inventory: `migration-inventory.json` command/result and reviewed false positives/negatives
- Characterization contract: `migration-characterization.json` and baseline evidence root
```

Do not mutate the project to improve the baseline. If a command is unsafe or would require unavailable infrastructure, record `BLOCKED` and why.

## Contract

Record the user's consolidated response verbatim enough to avoid asking again:

```markdown
## Migration Contract

- Scope and staged exclusions:
- Target JDK:
- Git base and migration branch, or no branch:
- View technology by view stack:
- Datasource/environment assumptions:
- Schema policy (default `none`):
- Authentication source and authorization expectations:
- Test/runtime strategy:
- External services and accepted blocked checks:
- Explicit destructive approvals: none
```

Never broaden a staged scope or infer destructive approval from a general migration request.

## Module ledger

Initialize all rows before editing:

```markdown
## Module Ledger

| Module | Gate | State | Evidence / changed files | Validation | Resume point |
|---|---|---|---|---|---|
| jdk | ALWAYS | NOT_STARTED | | | |
| complexity-gate | rewrite/staged preflight | NOT_STARTED | | | |
| staged-migration | staged/complex route | NOT_STARTED | | | |
| rehost-spring | rehost route | NOT_STARTED | | | |
| build | | NOT_STARTED | | | |
| code | | NOT_STARTED | | | |
| async-events | | NOT_STARTED | | | |
| messaging | | NOT_STARTED | | | |
| batch-scheduling | | NOT_STARTED | | | |
| data-xa-schema | | NOT_STARTED | | | |
| identity-observability | | NOT_STARTED | | | |
| reactive-cloud | | NOT_STARTED | | | |
| soap-nonrelational | | NOT_STARTED | | | |
| security | | NOT_STARTED | | | |
| frontend | | NOT_STARTED | | | |
| testing | | NOT_STARTED | | | |
| cleanup | ALWAYS | NOT_STARTED | | | |
| feature-scan | ALWAYS | NOT_STARTED | | | |
| run-local | ALWAYS | NOT_STARTED | | | |
```

Allowed states are `NOT_STARTED`, `IN_PROGRESS`, `PASS`, `PARTIAL`, `SKIP`, and `BLOCKED`. A skipped test module must still record the no-tests coverage risk.

## Transaction protocol

For each module:

1. Re-read the current files and ledger; do not assume the previous process finished.
2. Record worktree status, existing diffs, intended files, and the validation command.
3. Set the module to `IN_PROGRESS` before editing.
4. Apply only missing changes. Update existing dependencies, XML elements, beans, routes, and tests instead of creating duplicates.
5. Run the module validation and inspect the resulting diff.
6. Verify pre-existing user edits are still present.
7. Record `PASS`, `PARTIAL`, or `BLOCKED` with exact evidence and a resume point.

For complex adapters, record the inventory capability ID, bounded slice, baseline behavior signatures, generated scaffolding/codemod manifest, target evidence, failure/recovery cases, and parity-grader result. Do not replace these artifacts with a prose-only claim.

If validation fails, diagnose first. Reverse only edits created by the current module and only when they do not overlap pre-existing work. Never use a broad reset, checkout, restore, stash, or clean. If surgical rollback is unsafe, leave the evidence, mark `BLOCKED`, and request direction.

## Resume protocol

On resume:

1. Read the baseline, contract, and ledger.
2. Compare the recorded branch, HEAD, worktree, and relevant files with current state.
3. Treat `IN_PROGRESS` as untrusted: inspect what actually landed and re-run its validation.
4. Re-evaluate every remaining gate. Use `PARTIAL` when Spring and Jakarta/Liberty artifacts coexist or migration TODOs remain.
5. Continue at the earliest incomplete dependency, not merely the next row.
6. Do not repeat confirmed questions unless new evidence changes the design or authority required.
