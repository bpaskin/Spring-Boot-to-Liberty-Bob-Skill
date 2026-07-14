---
name: migrate-spring-to-liberty
description: Migrate Spring Boot applications to Jakarta EE 11 on Open Liberty with optional MicroProfile capabilities using a modular, gate-driven workflow. Use when the user asks to migrate, convert, or port a Spring Boot application to Open Liberty or Jakarta EE; remove Spring; migrate a Maven or Gradle build; convert Spring MVC, Spring Data JPA, Spring Security, scheduling, configuration, tests, or @SpringBootApplication; or prepare an application for WebSphere Liberty or Open Liberty.
---

# Spring Boot to Jakarta EE 11 + Open Liberty Migration

Modular, gate-driven migration of Spring Boot applications to Jakarta EE 11 running on Open Liberty.

## Critical Rules

- **Never delete code you cannot migrate.** If you cannot fully migrate a piece of code, leave the original in place with a `// TODO: Migration required — <reason>` comment explaining what needs to change and why. This applies to:
    - Methods, classes, or annotations you don't know how to convert
    - Spring-specific patterns without a clear Jakarta EE equivalent
    - Configuration or wiring code whose purpose is unclear
      If you must remove code (e.g., a Spring-only base class), document what was removed and why in a `// REMOVED:` comment at the same location.
- **Don't break the build.** Detect the project's build launcher first: use `./mvnw` or `./gradlew` when that wrapper exists, otherwise use an installed `mvn` or `gradle`. Run the resulting compile command after each phase. Never move to the next phase with a broken build.
- **Document every decision.** When choosing between migration approaches, explain the trade-off to the user.
- **No silent changes.** Every file modification must be intentional and traceable. If a check fails after a phase, diagnose and fix — don't skip the check or delete the failing code.
- **Default to non-destructive data handling.** Preserve the existing schema and data. Never select `drop`, `drop-and-create`, or another destructive database action without naming the affected environment, confirming a usable backup, showing the exact consequence, and receiving explicit approval.
- **Preserve user work.** Capture the pre-existing worktree state before editing. Never roll back, stage, or overwrite changes that were not created by this migration.

## Reference Files

Load the relevant reference file when working on a module:

| Reference | Use during |
|---|---|
| [references/dependency-map.md](references/dependency-map.md) | Build module: dependency and plugin mapping |
| [references/annotation-map.md](references/annotation-map.md) | Code module: annotation, DI, REST, Data, Security migration |
| [references/jakarta-data.md](references/jakarta-data.md) | Code/build modules only when Spring Data repositories are present |
| [references/config-map.md](references/config-map.md) | Build module: configuration property migration |
| [references/jakarta-ee11-liberty-features.md](references/jakarta-ee11-liberty-features.md) | Canonical Jakarta EE 11 and MicroProfile-to-Liberty feature mapping |
| [references/migration-ledger.md](references/migration-ledger.md) | Every run: baseline, consolidated contract, module transactions, and resume behavior |
| [references/frontend-jakarta-mvc.md](references/frontend-jakarta-mvc.md) | Frontend module only when the contract selects Jakarta MVC/Krazo |
| [references/frontend-faces.md](references/frontend-faces.md) | Frontend module only when the contract selects Jakarta Faces |
| [references/frontend-thymeleaf.md](references/frontend-thymeleaf.md) | Frontend module only when the contract retains core Thymeleaf |
| [references/frontend-jsp-rest.md](references/frontend-jsp-rest.md) | Frontend module for REST-only or confirmed JSP/static paths |


## Step 1: Analyze & Choose Scope

Scan the application to understand what needs to migrate:

- **Build system**: Read the build file (`pom.xml` for Maven, `build.gradle` or `build.gradle.kts` for Gradle) — Spring Boot version, starters, plugins
- **Build launcher**: Record whether `mvnw`/`gradlew` exists; do not assume a wrapper is present
- **Java code**: Search for Spring imports, annotations, API calls, configuration classes, repositories, scheduling, security, and bootstrap code
- **Configuration**: Read `application.properties`/`application.yml`, check for profiles
- **UI / View layer**: Check for Thymeleaf/JSP templates, static resources, `Model`/`ModelAndView` patterns, `@Controller` (server-rendered) vs `@RestController` (API-only)
- **Tests**: Inventory every test source and test dependency, including plain JUnit tests with no Spring annotations

Present a summary table with area, findings, and complexity. Then ask the user to choose a migration scope:

- **Complete Spring removal**: Replace all Spring APIs with Jakarta EE 11 and selected MicroProfile equivalents. Prefer this for long-term maintainability.
- **Staged migration**: Migrate a user-selected slice while documenting remaining Spring dependencies and interoperability risks. Do not claim the application is Spring-free.

MicroProfile complements Jakarta EE; it is not a competing migration approach. After scope selection, inventory which optional capabilities are actually needed, such as Config, Health, Metrics, Fault Tolerance, JWT, OpenAPI, Rest Client, Telemetry, or Reactive Messaging. Add only those capabilities whose APIs or configuration are present.

**Stop here and wait for the user's response before continuing.** Keep this first decision limited to scope.

## Step 2: Establish the Baseline and Migration Contract

After scope selection, perform a read-only baseline before changing files:

- Record the current branch, default branch, remote, and complete worktree status. Treat every existing change as user-owned.
- Detect the build launcher and installed JDK. Run the original compile/package and existing test commands when they are safe and available; do not install software, start external services, or change configuration merely to make the baseline pass.
- Record pre-existing build/test failures separately from migration regressions.
- Inventory application bootstrap, endpoints, views, tests, datasource/driver/schema settings, authentication/authorization, scheduled work, messaging, external services, expected ports, container-runtime availability, and required network access.
- Flag missing essentials such as an application entry point, datasource configuration, JDBC driver, test coverage, credentials, or required local services.

Then present one **Migration Contract** containing only applicable decisions and ask for one response:

- migration scope and the exact staged slice, if any
- target JDK (17, 21, or 25)
- exact branch name and base branch, or an explicit choice to stay on the current branch
- view technology when server-rendered Spring MVC or Thymeleaf is present
- datasource/environment assumptions, explicit Jakarta Data `dataStore` binding when applicable, and schema policy; default schema action to `none` and Liberty table creation/removal to disabled
- repository strategy when Spring Data repositories are present: Jakarta Data 1.0, CDI + `EntityManager`, or a documented staged exception
- authentication source and authorization expectations when Spring Security is present
- test approach and whether a compatible container runtime is available
- known external-service constraints and which runtime checks may be blocked

Do not repeat a contract question later. Ask a new question only when newly discovered evidence changes the migration design or would authorize a destructive/external action. After confirmation, create `migration-report.md` as the durable contract, baseline, and module ledger. If the Git workflow is selected, follow [modules/git.md](modules/git.md) using the already-confirmed branch details.

## Step 3: Execute Modules

## Instructions

- Execute the instructions of the modules according to the following Decision Gate Table
- Maintain each module in `migration-report.md` as `NOT_STARTED`, `IN_PROGRESS`, `PASS`, `PARTIAL`, `SKIP`, or `BLOCKED`.
- Log each evaluated gate as `Gate result: <STATUS> — <evidence>`.

### Decision Gate Table 

- Execute modules whose gate is `PASS`, `PARTIAL`, or `ALWAYS`. Use `PARTIAL` when a prior run already migrated some of the area or Spring and Jakarta/Liberty artifacts coexist.
- Inspect the project to determine the gate result — do not rely on blind grep commands; use your understanding of the codebase.

| Module                          | Gate Check                                                                                                                | Gate Result                                                                              |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [jdk](modules/jdk.md)           | Jakarta EE 11 requires Java 17+; this skill targets supported LTS JDKs 17, 21, and 25 | **ALWAYS** -- stop migration if unsupported |
| [build](modules/build.md)       | Spring Boot parent, plugin, BOM, starters, or Spring dependencies in a Maven/Gradle build; existing Liberty configuration also counts for partial runs | **PASS** for Spring build markers; **PARTIAL** when Spring and Liberty/Jakarta build artifacts coexist; **SKIP** only when no build migration is needed |
| [code](modules/code.md)         | Spring imports, annotations, API calls, configuration, repositories, bootstrap, security, scheduling, or known migration TODOs | **PASS** for Spring usage; **PARTIAL** when Spring and Jakarta code coexist or migration TODOs remain; **SKIP** only after semantic inspection finds no code work |
| [frontend](modules/frontend.md) | Templates/static assets, `@Controller`, `Model`/`ModelAndView`, view-name returns, MVC configuration, or retained Thymeleaf | **PASS** for a Spring/view layer; **PARTIAL** for mixed/previously migrated views; **SKIP** for a verified API-only application |
| [testing](modules/testing.md)   | Any test source, test dependency, test configuration, or absence of tests that must be recorded as a coverage gap | **PASS** when tests exist; **PARTIAL** for mixed Spring/plain/Jakarta tests; **SKIP** only when no tests exist, after recording the coverage risk |
| [cleanup](modules/cleanup.md)   | Leftover Spring artifacts after all other modules                                                                          | **ALWAYS** — runs after all other modules                                                |
| [feature-scan](modules/feature-scan.md) | Always — scan migrated sources and config to build a minimal `<featureManager>` list and update `server.xml`      | **ALWAYS** — runs after cleanup, before run-local                                        |
| [run-local](modules/run-local.md) | Always — start Liberty locally, read logs, and fix runtime errors before finalising                                     | **ALWAYS** — runs after feature-scan                                                     |

### Execution Protocol

```
FOR module IN [jdk, build, code, frontend, testing, cleanup, feature-scan, run-local]:

  1. RESUME — read the contract and ledger; inspect current files instead of trusting stale status
  2. EVALUATE — inspect the project for the gate condition
  3. DECIDE
     IF gate == ALWAYS → proceed to step 4
     IF gate == PASS   → proceed to step 4
     IF gate == PARTIAL → proceed to step 4 and avoid duplicating completed work
     IF gate == SKIP   → log "Module {name}: SKIPPED — {reason}", mark checkbox, continue
     IF gate == BLOCKED → record the blocker and continue only with independent modules
  4. LOAD — read the module file and only the references required for the detected path
  5. CHECKPOINT — set `IN_PROGRESS`; record the pre-module worktree status/diff, intended files, and validation command
  6. EXECUTE — apply only missing work; update existing entries instead of appending duplicate dependencies, features, classes, or descriptors
  7. COMPILE — run the project's detected build launcher (`./mvnw`/`./gradlew` when present, otherwise `mvn`/`gradle`) with the module's compile arguments
     Fails → diagnose and fix before proceeding
  8. REVIEW — inspect the module diff and verify that no pre-existing user change was overwritten
  9. LOG — record `PASS`, `PARTIAL`, or `BLOCKED`, changed files, command result, and next resume point
```

If a module cannot be repaired, reverse only edits made by that module when they do not overlap pre-existing user changes. Never use a broad reset/restore. When safe surgical rollback is impossible, leave the evidence in place, mark `BLOCKED`, and ask the user before altering shared work.

### Running Individual Modules

To run a single module outside the full migration flow, read its file directly:

- "Read `modules/build.md` and execute it"
- "Run only the frontend module"
- "Re-run the cleanup module"
- "Re-run the feature-scan module"

The module will use the current project state and chosen migration scope. If no scope has been chosen, the module must ask before changing files.

## Step 4: Verify the Migration

Run each check in order. Distinguish `FAIL` (a migration regression) from `BLOCKED` (an unavailable external dependency) and from a documented baseline failure. Never report `BLOCKED` as `PASS`.

| # | Check | Command (Maven / Gradle) | Pass criteria |
|---|-------|---------|---------------|
| 1 | **Builds** | Maven: `clean package -DskipTests`; Gradle: `clean build -x test` (using the detected launcher) | Exit code 0, no compilation errors |
| 2 | **No Spring deps** | Search build file for `org.springframework` | Zero Spring dependencies remaining |
| 3 | **Has Liberty** | Search build file for `io.openliberty` or `liberty-maven-plugin` | Liberty BOM/plugin and at least one Jakarta EE feature present |
| 4 | **Tests pass** | Maven: `test`; Gradle: `test` (using the detected launcher) | All tests pass using MicroShed or Arquillian |
| 5 | **Starts up** | Use the time-bounded lifecycle in [modules/run-local.md](modules/run-local.md) | Readiness detected within the recorded timeout; app responds; logs contain no unresolved application errors; process is stopped gracefully |
| 6 | **No leftover templates** | Search for Thymeleaf references | None remaining unless the contract intentionally retains Thymeleaf |

Assign the highest evidence level actually achieved:

1. `ANALYZED` — inventory and contract only
2. `COMPILED` — migrated build compiles
3. `TESTED` — applicable automated tests pass
4. `RUNTIME_VERIFIED` — Liberty starts and smoke tests pass
5. `BEHAVIOR_PARITY_VERIFIED` — baseline behaviors and negative/security cases are demonstrated equivalent

## Step 5: Migration Review (Self-Reflection)

Answer each question honestly:

1. **What migrated cleanly?** Patterns that mapped 1:1.
2. **What required manual judgment?** Non-obvious decisions made.
3. **What was left as TODO?** Every `// TODO: Migration required` comment and why.
4. **Was any code removed?** What, where, justification. Flag runtime risks.
5. **What checks failed initially?** Failures from Step 4 and how you fixed them.
6. **What's missing from the skill references?** Mappings you had to figure out.

### Migration Report

Present the review as a structured report:

```
## Migration Report: [app-name]

### Baseline
- Original branch/HEAD and pre-existing worktree changes: ...
- Build and test commands/results before migration: ...
- Application/runtime dependencies and pre-existing blockers: ...

### Migration Contract
- Scope and staged exclusions: ...
- JDK, Git branch/base, view, data/schema, security, test/runtime, and external-service decisions: ...
- Explicit destructive approvals: [none or exact approved action/environment/backup evidence]

### Module Ledger
| Module | Gate | State | Evidence / changed files | Validation | Resume point |
|---|---|---|---|---|---|
| jdk | ALWAYS | ... | ... | ... | ... |
| build | ... | ... | ... | ... | ... |
| code | ... | ... | ... | ... | ... |
| frontend | ... | ... | ... | ... | ... |
| testing | ... | ... | ... | ... | ... |
| cleanup | ALWAYS | ... | ... | ... | ... |
| feature-scan | ALWAYS | ... | ... | ... | ... |
| run-local | ALWAYS | ... | ... | ... | ... |

### Summary
- Scope: [Complete Spring removal / Staged migration]
- Optional MicroProfile capabilities: [list or none]
- Agent: [AI agent name, if available]
- Model: [model name, if available]
- Modules completed: [X/8]
- Checks passed: [X/6]
- Evidence level: [ANALYZED / COMPILED / TESTED / RUNTIME_VERIFIED / BEHAVIOR_PARITY_VERIFIED]
- Baseline failures: [list or none]
- Token usage: [include only when the current agent exposes reliable session statistics]

### Changes by Module
| Module | Files changed | Key changes |
|--------|--------------|-------------|
| build | pom.xml or build.gradle(.kts), application.properties, server.xml | ... |
| code | ... | ... |
| frontend | ... | ... |
| testing | ... | ... |
| feature-scan | server.xml (featureManager block) | ... |
| run-local | server.xml, persistence.xml, beans.xml (fixes applied during local run) | ... |

### Validation Results
| Check | Result | Evidence |
|-------|--------|-------|
| Builds | PASS/FAIL/BLOCKED | command and exit code |
| No Spring deps | PASS/FAIL | search evidence and staged-scope exceptions |
| Has Liberty | PASS/FAIL | build and server configuration evidence |
| Tests pass | PASS/FAIL/BLOCKED | command, counts, and baseline comparison |
| Starts up | PASS/FAIL/BLOCKED | readiness probe, log path, errors resolved |
| No leftover templates | PASS/FAIL | retained-template contract or search evidence |

### Unmigrated Code (TODOs)
| File | Line | What | Why not migrated |
|------|------|------|-----------------|

### Removed Code
| File | What was removed | Justification |
|------|-----------------|---------------|

### Skill Improvement Suggestions
- [Any missing mappings, unclear instructions, or edge cases discovered]
```

## Step 6: Commit and PR (only if git workflow was accepted)

Follow [modules/git.md](modules/git.md) — **Post-migration** section. Ask the user for confirmation before committing, and again before pushing / creating the draft PR. Do not proceed with either action without explicit user approval.
