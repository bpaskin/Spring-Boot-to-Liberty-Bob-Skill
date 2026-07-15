---
name: migrate-spring-to-liberty
description: Migrate Spring Boot applications to Jakarta EE 11 or rehost Spring Boot 3/4 applications unchanged on Open Liberty using a modular, gate-driven workflow. Use when the user asks to migrate, convert, rehost, deploy, or port a Spring Boot application to Open Liberty or Jakarta EE; retain or remove Spring; migrate a Maven or Gradle build; convert Spring MVC, Spring Data JPA, Spring Security, scheduling, configuration, tests, or @SpringBootApplication; or prepare an application for WebSphere Liberty or Open Liberty.
---

# Spring Boot Migration or Rehosting on Open Liberty

Modular, gate-driven selection between retaining Spring Boot on Open Liberty and rewriting to Jakarta EE 11.

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
- **Respect the selected architecture path.** When the contract selects retain Spring and rehost, preserve Spring code, dependencies, configuration, and tests; never run rewrite, cleanup, or Jakarta feature-inference instructions.
- **Never weaken security to make a migration compile.** Preserve authentication, authorization, CSRF, CORS, session, logout, transport, and security-header behavior until a contract-selected replacement passes positive and negative tests.

## Reference Files

Load the relevant reference file when working on a module:

| Reference | Use during |
|---|---|
| [references/dependency-map.md](references/dependency-map.md) | Build module: dependency and plugin mapping |
| [references/annotation-map.md](references/annotation-map.md) | Code/security modules: annotation candidates and semantic mapping boundaries |
| [references/complex-adapter-contract.md](references/complex-adapter-contract.md) | Every complex stack: common detect, characterize, migrate, verify, recovery, and rollback protocol |
| [modules/complexity-gate.md](modules/complexity-gate.md) | Preflight: reactive, cloud, integration, batch, SOAP/RPC, custom extensions, and non-relational stacks |
| [modules/staged-migration.md](modules/staged-migration.md) | Complex applications: rehost-first and bounded-slice migration orchestration |
| [modules/security.md](modules/security.md) | Security module: authentication, authorization, OAuth2/OIDC/JWT, registries, browser state, and negative tests |
| [modules/async-events.md](modules/async-events.md) | Async/events module: executors, event delivery, transaction semantics, retry, and recovery |
| [modules/messaging.md](modules/messaging.md) | Messaging module: broker topology, acknowledgment, ordering, retry/DLQ, transactions, and recovery |
| [modules/batch-scheduling.md](modules/batch-scheduling.md) | Batch/scheduling module: jobs, checkpoints, timers, overlap, misfire, restart, and operations |
| [modules/data-xa-schema.md](modules/data-xa-schema.md) | Databases, multiple datasources, XA, schema tools, naming, locking, and recovery |
| [modules/identity-observability.md](modules/identity-observability.md) | OIDC/JWT, health, metrics, telemetry, fail-closed identity, and exporter failure |
| [modules/reactive-cloud.md](modules/reactive-cloud.md) | WebFlux/R2DBC, Spring Cloud, custom starters, and non-mechanical runtime behavior |
| [modules/soap-nonrelational.md](modules/soap-nonrelational.md) | SOAP/RPC, Redis, caches, and non-relational data clients |
| [modules/deploy.md](modules/deploy.md) | Optional deployment module: images, Kubernetes/OpenShift, probes, secrets, and CI/CD |
| [references/jakarta-data.md](references/jakarta-data.md) | Code/build modules only when Spring Data repositories are present |
| [references/config-map.md](references/config-map.md) | Build module: configuration property migration |
| [references/jakarta-ee11-liberty-features.md](references/jakarta-ee11-liberty-features.md) | Canonical Jakarta EE 11 and MicroProfile-to-Liberty feature mapping |
| [references/migration-ledger.md](references/migration-ledger.md) | Every run: baseline, consolidated contract, module transactions, and resume behavior |
| [references/production-integration-testing.md](references/production-integration-testing.md) | External systems: disposable services, failure cases, XA/recovery, identity, brokers, telemetry, and deployment parity |
| [references/frontend-jakarta-mvc.md](references/frontend-jakarta-mvc.md) | Frontend module only when the contract selects Jakarta MVC/Krazo |
| [references/frontend-faces.md](references/frontend-faces.md) | Frontend module only when the contract selects Jakarta Faces |
| [references/frontend-thymeleaf.md](references/frontend-thymeleaf.md) | Frontend module only when the contract retains core Thymeleaf |
| [references/frontend-jsp-rest.md](references/frontend-jsp-rest.md) | Frontend module for REST-only or confirmed JSP/static paths |
| [references/frontend-binding-expressions.md](references/frontend-binding-expressions.md) | Frontend module when Spring MVC controller binding, Spring form tags, or Thymeleaf Spring field/error expressions are present |


## Step 1: Analyze & Choose Scope

Create a deterministic read-only inventory, then confirm its evidence through semantic inspection:

```bash
python3 migrate-spring-to-liberty/scripts/analyze_project.py . \
  --output migration-inventory.json
```

Scan the application to understand whether it should be rewritten or rehosted:

- **Build system**: Read the build file (`pom.xml` for Maven, `build.gradle` or `build.gradle.kts` for Gradle) — Spring Boot version, starters, plugins
- **Build launcher**: Record whether `mvnw`/`gradlew` exists; do not assume a wrapper is present
- **Java code**: Search for Spring imports, annotations, API calls, configuration classes, repositories, scheduling/batch, async/executors, application events, transaction/retry semantics, messaging/integration flows, security, reactive APIs, Spring Cloud/custom extensions, and bootstrap code
- **Configuration**: Read `application.properties`/`application.yml`, check for profiles
- **UI / View layer**: Check for Thymeleaf/JSP templates, static resources, `Model`/`ModelAndView` patterns, `@Controller` (server-rendered) vs `@RestController` (API-only)
- **Tests**: Inventory every test source and test dependency, including plain JUnit tests with no Spring annotations
- **External and operational integrations**: Inventory databases/XA/schema tools, brokers, identity providers, service discovery/gateways, cache/NoSQL, Actuator/metrics/telemetry, SOAP/RPC, and deployment dependencies

Present a summary table with area, findings, and complexity. Then ask the user to choose a migration scope:

- **Complete Spring removal**: Replace all Spring APIs with Jakarta EE 11 and selected MicroProfile equivalents. Prefer this for long-term maintainability.
- **Staged migration**: Migrate a user-selected slice while documenting remaining Spring dependencies and interoperability risks. Do not claim the application is Spring-free.
- **Retain Spring and rehost on Liberty**: Keep Spring Boot application code, starters, configuration, and tests; add only Liberty packaging, the matching Spring Boot Support feature, deployment configuration, and runtime validation. Prefer this when the goal is Liberty hosting rather than Spring removal.

For rehosting, first verify that the application is Spring Boot 3.x or 4.x and has a valid executable bootstrap. Preserve Spring starters instead of replacing them with Jakarta EE or MicroProfile features. For rewrite scopes, MicroProfile complements Jakarta EE; inventory optional capabilities only after scope selection and add only those whose APIs or configuration are present. For a complex eligible Boot application, recommend rehosting first and then migrating characterized bounded slices unless the user explicitly selects a complete rewrite with a confirmed route for every critical adapter.

**Stop here and wait for the user's response before continuing.** Keep this first decision limited to scope.

## Step 2: Establish the Baseline and Migration Contract

After scope selection, perform a read-only baseline before changing files:

- Record the current branch, default branch, remote, and complete worktree status. Treat every existing change as user-owned.
- Detect the build launcher and installed JDK. Run the original compile/package and existing test commands when they are safe and available; do not install software, start external services, or change configuration merely to make the baseline pass.
- Record pre-existing build/test failures separately from migration regressions.
- Inventory application bootstrap, endpoints, views, tests, datasource/driver/schema/XA settings, authentication/authorization, async/executor/event/transaction/retry behavior, scheduled and batch work, messaging/integration topology, reactive/Cloud/custom-extension stacks, observability, existing deployment artifacts, external services, expected ports, container-runtime availability, and required network access.
- Flag missing essentials such as an application entry point, datasource configuration, JDBC driver, test coverage, credentials, or required local services.
- Treat `migration-inventory.json` as generated evidence, not as a substitute for code understanding. Record false positives/negatives in the report.

Then present one **Migration Contract** containing only applicable decisions and ask for one response:

- scope: complete Spring removal, an exact staged slice, or retain Spring and rehost on Liberty
- target JDK: always require an explicit user selection in this consolidated contract. Show the detected installed JDK and offer only supported targets from 17, 21, and 25 whose major version is less than or equal to the installed JDK. When the installed JDK is higher than 25, offer all three targets—17, 21, and 25—but never offer the newer installed major as a migration target. Do not infer the target from project files or the installed JDK, and do not supply a default. Stop before migration changes until the user selects an offered value. A previously confirmed migration contract with the user's explicit JDK answer satisfies this gate and must not be asked again.
- exact branch name and base branch, or an explicit choice to stay on the current branch
- view technology when server-rendered Spring MVC or Thymeleaf is present
- datasource/environment assumptions, explicit Jakarta Data `dataStore` binding when applicable, and schema policy; default schema action to `none` and Liberty table creation/removal to disabled
- repository strategy when Spring Data repositories are present: Jakarta Data 1.0, CDI + `EntityManager`, or a documented staged exception
- when Spring Security is present: authentication mechanism/source, role and claim/group mapping, protected-route policy, session/cookie/logout behavior, CSRF/CORS policy, trust material, and required negative tests
- when async/events/advanced transactions/retry are present: executor and context policy, event delivery/ordering/transaction phase, transaction attributes, retry/recovery behavior, and overload/failure tests
- for every non-mechanical stack: dedicated module, retained library, explicit redesign, staged exception, or rehost strategy; complete removal remains blocked while any strategy or baseline semantics are unknown
- when messaging/integration is present: broker/provider, destinations/groups, schemas/headers, acknowledgment/ordering/concurrency, transaction/XA, retry/DLQ/idempotency, security, recovery, and failure tests
- when batch/scheduling is present: trigger/time zone/misfire/overlap, job identity, checkpoints/restart, repository/schema, transaction, clustering, operations, and crash-recovery tests
- test approach and whether a compatible container runtime is available
- known external-service constraints and which runtime checks may be blocked
- external-integration test tier: static contract, disposable integration, Liberty integration, or target-platform parity, with required negative/failure cases
- deployment track: explicit `SKIP`, files only, local image validation, publish, or deploy; when selected include target platform, pinned image/JDK, registry/tag policy, configuration/secrets owner, probes, resources, and CI requirements
- for rehosting only: Spring Boot stream, JAR/WAR and full/thin artifact choice, actual artifact name, context root/ports, and whether Liberty or Spring properties own each runtime setting

Do not repeat a contract question later. Ask a new question only when newly discovered evidence changes the migration design or would authorize a destructive/external action. After confirmation, create `migration-report.md` as the durable contract, baseline, and module ledger. Generate `migration-characterization.json` before the first production-code change and capture baseline evidence for every applicable case. If the Git workflow is selected, follow [modules/git.md](modules/git.md) using the already-confirmed branch details.

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
| [complexity-gate](modules/complexity-gate.md) | Rewrite scope plus reactive, Spring Cloud/Integration/Batch, messaging, SOAP/RPC, custom extension, or non-relational stack evidence | **PASS** when every detected stack has a confirmed route; **SKIP** when none exist or for rehost; **BLOCKED** while any semantic strategy is unknown |
| [staged-migration](modules/staged-migration.md) | Staged scope or a complex eligible application whose route is rehost-first with bounded rewrites | **PASS/PARTIAL** while selected slices are migrated and parity-verified; **SKIP** for direct rehost or complete rewrite |
| [rehost-spring](modules/rehost-spring.md) | Contract selects retain Spring and rehost; application is Spring Boot 3.x/4.x with a valid bootstrap | **PASS** for an unconfigured eligible app; **PARTIAL** when Liberty rehost configuration exists; **SKIP** for rewrite scopes; **BLOCKED** for an unsupported stream or missing bootstrap |
| [build](modules/build.md)       | Rewrite scope plus Spring Boot build markers or existing Liberty/Jakarta build artifacts | **PASS** for Spring build markers; **PARTIAL** when Spring and Liberty/Jakarta artifacts coexist; **SKIP** for rehosting or when no rewrite build work is needed |
| [code](modules/code.md)         | Rewrite scope plus non-security Spring APIs, configuration, repositories, bootstrap, scheduling, or migration TODOs | **PASS** for Spring usage; **PARTIAL** when Spring and Jakarta code coexist or TODOs remain; **SKIP** for rehosting or after semantic inspection finds no rewrite work |
| [async-events](modules/async-events.md) | Rewrite scope plus `@Async`, Spring executors/events, non-default transaction semantics, Spring Retry/listeners, or mixed migrated equivalents | **PASS** for detected Spring semantics; **PARTIAL** for mixed implementations; **SKIP** for rehosting or no matching behavior; **BLOCKED** when the semantic contract is unknown |
| [messaging](modules/messaging.md) | Rewrite scope plus Kafka, JMS, AMQP/RabbitMQ, Pulsar, Spring Cloud Stream, or Spring Integration messaging flows | **PASS** for detected flows; **PARTIAL** for mixed implementations; **SKIP** when absent or rehosting; **BLOCKED** until delivery, failure, and transaction semantics are confirmed |
| [batch-scheduling](modules/batch-scheduling.md) | Rewrite scope plus Spring Batch, Quartz, `@Scheduled`, `TaskScheduler`, or mixed jobs/timers | **PASS** for detected jobs; **PARTIAL** for mixed implementations; **SKIP** when absent or rehosting; **BLOCKED** until restart/trigger/failure semantics are confirmed |
| [data-xa-schema](modules/data-xa-schema.md) | Rewrite/staged slice plus external databases, multiple datasources, XA, Flyway/Liquibase, or non-default persistence semantics | **PASS/PARTIAL** with durable-state and recovery evidence; **SKIP** when absent or rehosting; **BLOCKED** until data/schema/XA semantics are confirmed |
| [identity-observability](modules/identity-observability.md) | Rewrite/staged slice plus OIDC/JWT, Actuator, Micrometer, OpenTelemetry, or custom health behavior | **PASS/PARTIAL** with identity and telemetry parity; **SKIP** when absent or rehosting; **BLOCKED** until fail-closed and outage behavior is confirmed |
| [reactive-cloud](modules/reactive-cloud.md) | Rewrite/staged slice plus WebFlux/R2DBC, Spring Cloud, custom starters, or custom runtime hooks | **PASS/PARTIAL** only after a retained/redesigned route and load/failure evidence; **SKIP** when absent or rehosting; otherwise **BLOCKED** |
| [soap-nonrelational](modules/soap-nonrelational.md) | Rewrite/staged slice plus SOAP/RPC, Redis/cache, or a non-relational store | **PASS/PARTIAL** with wire/data and recovery parity; **SKIP** when absent or rehosting; **BLOCKED** until provider/protocol semantics are confirmed |
| [security](modules/security.md) | Rewrite scope plus Spring Security dependencies/configuration, filter chains, authorization annotations/expressions, OAuth2/OIDC/JWT, registries, sessions, CSRF, or CORS | **PASS** for Spring Security; **PARTIAL** for mixed Spring/Jakarta/Liberty security; **SKIP** for rehosting or when no security behavior exists; **BLOCKED** until a security design is confirmed |
| [frontend](modules/frontend.md) | Rewrite scope plus templates/static assets, controllers, model/view returns, or MVC configuration | **PASS** for a Spring/view layer; **PARTIAL** for mixed views; **SKIP** for rehosting or a verified API-only application |
| [testing](modules/testing.md)   | Any test source, test dependency, test configuration, or absence of tests that must be recorded as a coverage gap | **PASS** when tests exist; **PARTIAL** for mixed Spring/plain/Jakarta tests; **SKIP** only when no tests exist, after recording the coverage risk |
| [cleanup](modules/cleanup.md)   | Rewrite scopes after the other rewrite modules | **ALWAYS** for rewrite scopes; **SKIP** for rehosting because Spring must remain |
| [feature-scan](modules/feature-scan.md) | Rewrite scopes — derive a minimal Jakarta EE/MicroProfile feature set | **ALWAYS** for rewrite scopes; **SKIP** for rehosting because `rehost-spring` owns its feature set |
| [run-local](modules/run-local.md) | Start the migrated or rehosted application on Liberty and verify behavior | **ALWAYS** — runs after the applicable build/rehost and testing modules |
| [deploy](modules/deploy.md) | Contract requests deployment deliverables or explicitly records deployment out of scope | **PASS/PARTIAL** for requested deployment work; **SKIP** when explicitly out of scope; external publish/deploy remains **BLOCKED** without separate approval |

### Execution Protocol

Choose exactly one route from the confirmed contract:

```
IF scope == RETAIN_SPRING_REHOST:
  MODULES = [jdk, rehost-spring, testing, run-local, deploy]
  LOG complexity-gate, staged-migration, build, code, async-events, messaging, batch-scheduling, data-xa-schema, identity-observability, reactive-cloud, soap-nonrelational, security, frontend, cleanup, feature-scan as SKIP — Spring rewrite not selected
ELSE IF scope == STAGED_MIGRATION:
  MODULES = [jdk, complexity-gate, staged-migration, selected slice adapters, build, code, testing, feature-scan, run-local, deploy]
  KEEP every non-selected Spring slice and dependency intact
ELSE:
  MODULES = [jdk, complexity-gate, build, code, async-events, messaging, batch-scheduling, data-xa-schema, identity-observability, reactive-cloud, soap-nonrelational, security, frontend, testing, cleanup, feature-scan, run-local, deploy]

FOR module IN MODULES:

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
  6. EXECUTE — generate/review deterministic scaffolding and codemod manifests; apply only missing work; update existing entries instead of appending duplicate dependencies, features, classes, or descriptors
  7. COMPILE — run the project's detected build launcher (`./mvnw`/`./gradlew` when present, otherwise `mvn`/`gradle`) with the module's compile arguments
     Fails → diagnose and fix before proceeding
  8. REVIEW — inspect the module diff and verify that no pre-existing user change was overwritten
  9. LOG — record `PASS`, `PARTIAL`, or `BLOCKED`, changed files, command result, and next resume point
```

If `complexity-gate` is `BLOCKED`, do not execute build/code/cleanup work that would remove or invalidate a blocked stack. Resume at the preflight contract after the user selects a strategy.

If a module cannot be repaired, reverse only edits made by that module when they do not overlap pre-existing user changes. Never use a broad reset/restore. When safe surgical rollback is impossible, leave the evidence in place, mark `BLOCKED`, and ask the user before altering shared work.

### Running Individual Modules

To run a single module outside the full migration flow, read its file directly:

- "Read `modules/build.md` and execute it"
- "Retain Spring and run only the rehost path"
- "Run the analyzer and staged-migration orchestrator"
- "Run only the data/XA or reactive/Cloud adapter"
- "Run only the frontend module"
- "Re-run the cleanup module"
- "Re-run the feature-scan module"

The module will use the current project state and chosen migration scope. If no scope has been chosen, the module must ask before changing files.

## Step 4: Verify the Migration or Rehost

Run each check in order. Distinguish `FAIL` (a migration regression) from `BLOCKED` (an unavailable external dependency) and from a documented baseline failure. Never report `BLOCKED` as `PASS`.

| # | Check | Command (Maven / Gradle) | Pass criteria |
|---|-------|---------|---------------|
| 1 | **Builds** | Maven: `clean package -DskipTests`; Gradle: `clean build -x test` (using the detected launcher) | Exit code 0, no compilation errors |
| 2 | **Spring dependency scope** | Inspect resolved build dependencies | Complete removal: zero Spring; staged: only contract-approved Spring; rehost: baseline Spring dependencies remain except approved upgrades |
| 3 | **Has Liberty** | Inspect build and `server.xml` | Rewrite: Liberty plugin plus Jakarta EE features; rehost: Liberty plugin, matching `springBoot-3.0`/`springBoot-4.0`, required web feature, and `springBootApplication` pointing to the actual artifact |
| 4 | **Tests pass** | Maven: `test`; Gradle: `test` (using the detected launcher) | Rewrite tests use the selected Jakarta/Liberty approach; rehost preserves existing Spring tests and adds only required Liberty smoke coverage |
| 5 | **Starts up** | Use the time-bounded lifecycle in [modules/run-local.md](modules/run-local.md) | Readiness detected within the recorded timeout; app responds; logs contain no unresolved application errors; process is stopped gracefully |
| 6 | **View scope** | Inspect templates and view configuration | Rewrite matches the selected view path; rehost preserves baseline Spring view behavior |
| 7 | **Security parity** | Run the contract's positive and negative security matrix | Authentication, authorization, CSRF/CORS, session/logout, trust, and denial behavior match the completed scope; non-applicable rows have evidence |
| 8 | **Integration and recovery parity** | Run messaging, batch, database/XA/schema, identity, and observability matrices from the applicable modules/reference | Positive behavior plus duplicate, unavailable-dependency, rollback/restart/recovery, and security failures match the contract; unavailable infrastructure is `BLOCKED` |
| 9 | **Deployment track** | Inspect the deployment contract and run selected local/render/deployment checks | Explicit `SKIP`, or selected files/image/deployment level has matching evidence; external actions without approval remain `BLOCKED` |

For staged or complex migrations, do not assign behavior parity from narrative comparison. Grade the baseline and target evidence artifacts:

```bash
python3 migrate-spring-to-liberty/scripts/verify_parity.py \
  --contract migration-characterization.json \
  --baseline evidence/baseline.json \
  --target evidence/target.json \
  --evidence-root evidence
```

Assign the highest evidence level actually achieved:

1. `ANALYZED` — inventory and contract only
2. `COMPILED` — migrated build compiles
3. `TESTED` — applicable automated tests pass
4. `RUNTIME_VERIFIED` — Liberty starts and smoke tests pass
5. `BEHAVIOR_PARITY_VERIFIED` — baseline behaviors and negative/security cases are demonstrated equivalent

## Step 5: Migration Review (Self-Reflection)

Answer each question honestly:

1. **What migrated or rehosted cleanly?** Rewritten patterns or preserved hosting behavior.
2. **What required manual judgment?** Non-obvious decisions made.
3. **What was left as TODO?** Every `// TODO: Migration required` comment and why.
4. **Was any code removed?** What, where, justification. Flag runtime risks.
5. **What checks failed initially?** Failures from Step 4 and how you fixed them.
6. **What's missing from the skill references?** Mappings you had to figure out.

### Migration Report

Present the review as a structured report:

Before delivery, compare the ledger row names with the canonical list below. Every module must have exactly one row, including modules that are `SKIP` or `BLOCKED`; a missing row is an incomplete report. Likewise, include every Step 4 validation row even when it is non-applicable or blocked.

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
| complexity-gate | rewrite preflight | ... | ... | ... | ... |
| staged-migration | staged/complex route | ... | ... | ... | ... |
| rehost-spring | ... | ... | ... | ... | ... |
| build | ... | ... | ... | ... | ... |
| code | ... | ... | ... | ... | ... |
| async-events | ... | ... | ... | ... | ... |
| messaging | ... | ... | ... | ... | ... |
| batch-scheduling | ... | ... | ... | ... | ... |
| data-xa-schema | ... | ... | ... | ... | ... |
| identity-observability | ... | ... | ... | ... | ... |
| reactive-cloud | ... | ... | ... | ... | ... |
| soap-nonrelational | ... | ... | ... | ... | ... |
| security | ... | ... | ... | ... | ... |
| frontend | ... | ... | ... | ... | ... |
| testing | ... | ... | ... | ... | ... |
| cleanup | rewrite only | ... | ... | ... | ... |
| feature-scan | rewrite only | ... | ... | ... | ... |
| run-local | ALWAYS | ... | ... | ... | ... |
| deploy | contract-selected | ... | ... | ... | ... |

### Summary
- Scope: [Complete Spring removal / Staged migration / Retain Spring and rehost]
- Optional MicroProfile capabilities: [list or none]
- Agent: [AI agent name, if available]
- Model: [model name, if available]
- Modules completed: [X/applicable modules]
- Checks passed: [X/applicable checks; deployment may be SKIP]
- Evidence level: [ANALYZED / COMPILED / TESTED / RUNTIME_VERIFIED / BEHAVIOR_PARITY_VERIFIED]
- Baseline failures: [list or none]
- Token usage: [include only when the current agent exposes reliable session statistics]

### Changes by Module
| Module | Files changed | Key changes |
|--------|--------------|-------------|
| rehost-spring | build file, server.xml | ... |
| build | pom.xml or build.gradle(.kts), application.properties, server.xml | ... |
| code | ... | ... |
| complexity-gate | migration report | ... |
| staged-migration | inventory, slice contracts, parity evidence | ... |
| async-events | source/config/tests | ... |
| messaging | source/config/broker tests | ... |
| batch-scheduling | jobs/timers/config/restart tests | ... |
| data-xa-schema | datasource/schema/config/recovery tests | ... |
| identity-observability | identity/health/telemetry config and tests | ... |
| reactive-cloud | retained/redesigned slice and load/failure tests | ... |
| soap-nonrelational | protocol/client/store config and tests | ... |
| security | server.xml, security classes/config, deployment descriptors, tests | ... |
| frontend | ... | ... |
| testing | ... | ... |
| feature-scan | server.xml (featureManager block) | ... |
| run-local | server.xml, persistence.xml, beans.xml (fixes applied during local run) | ... |
| deploy | Dockerfile/Containerfile, manifests, CI configuration | ... |

### Validation Results
| Check | Result | Evidence |
|-------|--------|-------|
| Builds | PASS/FAIL/BLOCKED | command and exit code |
| Spring dependency scope | PASS/FAIL | removal, staged exceptions, or rehost preservation evidence |
| Has Liberty | PASS/FAIL | build and server configuration evidence |
| Tests pass | PASS/FAIL/BLOCKED | command, counts, and baseline comparison |
| Starts up | PASS/FAIL/BLOCKED | readiness probe, log path, errors resolved |
| View scope | PASS/FAIL | retained-template contract or search evidence |
| Security parity | PASS/FAIL/BLOCKED | anonymous/authenticated/forbidden results and applicable mechanism, browser-state, and logout evidence |
| Integration/recovery parity | PASS/FAIL/BLOCKED/SKIP | broker, batch, data/XA/schema, identity, observability, restart, and failure evidence |
| Deployment track | PASS/FAIL/BLOCKED/SKIP | files/image/deployment evidence and target, or explicit out-of-scope decision |

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
