# Migrate Spring and Spring Boot applications to Jakarta EE 11 and Liberty

An IBM Bob skill that migrates Spring Boot applications to **Jakarta EE 11 on Open Liberty** through a baseline-driven, resumable workflow. Each module is classified as `PASS`, `PARTIAL`, `SKIP`, or `BLOCKED` from project evidence, so complete and staged migrations follow the same safety model.

## Quick start

Install the skill:

```bash
cp -R migrate-spring-to-liberty ~/.bob/skills/
```

Then open a Bob task in a Spring Boot project and ask:

```text
Analyze this Spring Boot application for a complete migration to Jakarta EE 11 on Open Liberty. Do not change files until you show the migration inventory and I choose the scope.
```

The skill first inventories the build, Java APIs, configuration, views, tests, security, and operational requirements. It then records a read-only baseline and one consolidated migration contract before changing the project.

## Compatibility

| Component | Target |
|---|---|
| Jakarta EE | 11 |
| Java | 17 minimum; LTS targets 17, 21, or 25 |
| Open Liberty | A pinned release verified to install every selected feature |
| MicroProfile | Optional capabilities selected from the application's actual usage |
| Build tools | Maven or Gradle (wrappers preferred; installed launchers supported) |

## Important limitations

- WebFlux and Reactor pipelines do not have a mechanical Jakarta EE equivalent; redesign them deliberately or use staged migration.
- Complex Spring Security filter chains, OAuth client behavior, method expressions, and session policies require an explicit security design and negative tests.
- Spring Batch, Spring Integration, Spring Cloud, and custom Spring extensions require project-specific migration plans.
- Scheduling expressions and concurrency semantics must be verified; Spring, Enterprise Beans timers, Jakarta Concurrency, and Quartz are not interchangeable.
- `spring.jpa.hibernate.ddl-auto=update` has no portable Jakarta Persistence equivalent. Schema generation defaults to `none`; use a reviewed migration tool for durable environments.
- Applications without tests can be migrated, but the result cannot claim behavioral parity until representative positive, negative, and security cases exist.
- Never remove working CSRF protection, authentication, authorization, secrets handling, or transaction boundaries before the replacement is configured and tested.

---

## What this skill does

When activated, the skill follows six steps:

### Step 1 — Analyze & choose scope

The skill scans the project and presents a summary table covering:

- **Build file** (`pom.xml` / `build.gradle` / `build.gradle.kts`) — Spring Boot version, starters, plugins
- **Java source code** — Spring imports, annotations, API calls, configuration, repositories, security, scheduling, and bootstrap code
- **Configuration** — `application.properties` / `application.yml`, profiles
- **View layer** — Thymeleaf / JSP templates, static resources, Model+View patterns
- **Tests** — every test source/dependency, including plain JUnit tests

The user then chooses a migration scope:

| Scope | Description |
|---|---|
| **Complete Spring removal** | Replaces all Spring APIs with Jakarta EE 11 and selected MicroProfile equivalents. Best for long-term maintainability. |
| **Staged migration** | Migrates a selected slice and documents the remaining Spring dependencies and interoperability risks. |

MicroProfile complements Jakarta EE rather than replacing it. The skill detects and adds optional MicroProfile capabilities only when the application needs them.

---

### Step 2 — Baseline, migration contract, and optional Git branch

Before editing, the skill records the original build/test results, pre-existing worktree changes, application bootstrap, routes, views, datasource/schema behavior, security, external services, ports, and runtime constraints. Pre-existing failures remain separate from migration regressions.

It then presents one migration contract with the applicable JDK, exact branch/base, view technology, datasource and non-destructive schema policy, security model, test runtime, and external-service assumptions. Confirmed choices are not asked again. `migration-report.md` becomes the durable baseline, contract, module ledger, and resume point.

If Git isolation is selected, the exact branch choice from the contract is created from the detected base branch. Commit, push, and draft-PR actions still require separate explicit approval.

---

### Step 3 — Execute modules (gate-driven)

Each module runs only if its gate condition is met:

| Module | Gate | What it does |
|---|---|---|
| **jdk** | ALWAYS — stops migration if the JDK is unsupported | Enforces Java 17+ and applies the contract-selected LTS target 17, 21, or 25. |
| **build** | Spring build markers, or mixed Spring/Liberty build state | Detects Maven/Gradle, handles complete and partial migrations idempotently, preserves non-Spring runtime dependencies, and migrates runtime configuration. |
| **code** | Spring imports, API calls, TODOs, or mixed Spring/Jakarta code | Migrates the confirmed source slice while preserving transaction, security, persistence, scheduling, and configuration semantics. Schema generation defaults to `none`; destructive actions require a named environment, usable backup, exact impact, and explicit approval. |
| **frontend** | Templates/assets or controller/view-return signals | Loads only the contract-selected Jakarta MVC, Faces, retained Thymeleaf, JSP/static, or REST path. Replaces and negative-tests CSRF protection before removing Spring integration. |
| **testing** | Any test source, dependency, or configuration | Preserves plain JUnit tests, migrates Spring tests where needed, and compares counts/results with baseline. When no tests exist, the module is skipped and the ledger records a coverage risk. |
| **cleanup** | ALWAYS — runs after all other modules | Removes leftover Spring imports; converts only explicitly mapped Jakarta EE APIs from `javax.*` while preserving Java SE and third-party namespaces; removes unused Spring dependencies and stale configuration; creates `beans.xml` when CDI discovery needs it. |
| **feature-scan** | ALWAYS — runs after cleanup | Derives and verifies a minimal feature set. It pauses only when a feature change exceeds the contract or may alter descriptor/reflection-driven behavior. |
| **run-local** | ALWAYS — runs after feature-scan | Runs Liberty in a controlled foreground session with a readiness URL, timeout, log evidence, smoke tests, and guaranteed graceful cleanup; a packaged foreground run is available when dev mode is unsuitable. |

After every module the skill runs a compile check with the project's wrapper when present, or the installed `mvn`/`gradle` command otherwise. It never advances to the next module with a broken build.

**Safety rules baked in:**

- Never deletes code it cannot migrate — leaves a `// TODO: Migration required — <reason>` comment instead
- Documents every decision and trade-off
- No silent changes — every file modification is intentional and traceable
- Every module records `NOT_STARTED`, `IN_PROGRESS`, `PASS`, `PARTIAL`, `SKIP`, or `BLOCKED` and can resume idempotently
- Every module captures its pre-diff, intended files, validation, and safe rollback boundary
- Database schema actions default to non-destructive `none`

---

### Step 4 — Verify the migration

Six ordered checks distinguish migration failures, baseline failures, and unavailable external dependencies (`BLOCKED`):

| # | Check | Pass criteria |
|---|---|---|
| 1 | Builds | The detected Maven or Gradle launcher completes a clean package/build with no compilation errors |
| 2 | Spring dependency scope | Zero Spring dependencies for complete removal; only contract-approved dependencies remain for a staged migration |
| 3 | Has Liberty | Liberty BOM / plugin and at least one Jakarta EE feature present |
| 4 | Tests pass | All tests pass using MicroShed or Arquillian |
| 5 | Starts up | Readiness within the recorded timeout; app responds; logs have no unresolved application errors; owned process stops cleanly |
| 6 | View migration scope | No obsolete templates remain; retained Thymeleaf or staged views match the migration contract |

---

### Step 5 — Migration report (self-reflection)

After verification the skill assigns the highest demonstrated evidence level: `ANALYZED`, `COMPILED`, `TESTED`, `RUNTIME_VERIFIED`, or `BEHAVIOR_PARITY_VERIFIED`. The report covers:

- Baseline, migration contract, durable module ledger, resume points, scope, capabilities, and checks
- Agent/model and token usage only when the runtime exposes reliable values
- Changes by module (files changed, key changes)
- Validation results table
- Unmigrated code (`// TODO` items) with reasons
- Removed code with justification
- Skill improvement suggestions (missing mappings, edge cases found)

---

### Step 6 — Commit and PR (only if git workflow was accepted)

Scans for accidentally exposed secrets before staging. Shows the staged summary and asks for confirmation before committing, then asks again before pushing and opening a draft PR. The skill never merges automatically; the user decides whether a verified migration should be merged.

---

## Reference files

The skill uses canonical mapping references plus conditionally loaded frontend and migration-state guidance:

| Reference | Used during |
|---|---|
| [`references/dependency-map.md`](migrate-spring-to-liberty/references/dependency-map.md) | Build module — Spring → Liberty dependency and plugin mapping, JDBC driver placement, individual Jakarta EE 11 / MicroProfile 7 API coordinates |
| [`references/annotation-map.md`](migrate-spring-to-liberty/references/annotation-map.md) | Code module — DI, REST, Data, Security, Scheduling, Cache, Lifecycle annotation mapping |
| [`references/config-map.md`](migrate-spring-to-liberty/references/config-map.md) | Build module — `application.properties` property migration covering server, datasource, JPA, logging, profiles, CORS, cache, security, health, and static resources |
| [`references/jakarta-ee11-liberty-features.md`](migrate-spring-to-liberty/references/jakarta-ee11-liberty-features.md) | Canonical Jakarta EE 11 and MicroProfile feature names, Maven/Gradle coordinates, profile membership, JCache provider guidance, security examples, and typical `<featureManager>` sets |
| [`references/migration-ledger.md`](migrate-spring-to-liberty/references/migration-ledger.md) | Baseline, consolidated contract, module state, transaction boundaries, and resume protocol |
| [`references/frontend-jakarta-mvc.md`](migrate-spring-to-liberty/references/frontend-jakarta-mvc.md) | Loaded only when the contract selects Jakarta MVC with Krazo |
| [`references/frontend-faces.md`](migrate-spring-to-liberty/references/frontend-faces.md) | Loaded only when the contract selects Jakarta Faces |
| [`references/frontend-thymeleaf.md`](migrate-spring-to-liberty/references/frontend-thymeleaf.md) | Loaded only when core Thymeleaf is intentionally retained |
| [`references/frontend-jsp-rest.md`](migrate-spring-to-liberty/references/frontend-jsp-rest.md) | Loaded for confirmed JSP/static paths or REST-only applications |

---

## Module files

| Module file | Purpose |
|---|---|
| [`modules/jdk.md`](migrate-spring-to-liberty/modules/jdk.md) | JDK version check — supports 17, 21, 25 |
| [`modules/build.md`](migrate-spring-to-liberty/modules/build.md) | Build system dispatcher + `server.xml` / MicroProfile Config creation |
| [`modules/build-maven.md`](migrate-spring-to-liberty/modules/build-maven.md) | Maven-specific migration (`pom.xml`, `liberty-maven-plugin`, `jandex-maven-plugin`) |
| [`modules/build-gradle.md`](migrate-spring-to-liberty/modules/build-gradle.md) | Gradle-specific migration (Groovy DSL and Kotlin DSL, Liberty Gradle plugin, Jandex) |
| [`modules/code.md`](migrate-spring-to-liberty/modules/code.md) | Java source migration (entities, repositories, services, controllers, DI, lifecycle) |
| [`modules/frontend.md`](migrate-spring-to-liberty/modules/frontend.md) | View-layer scenario router, static assets, and verified CSRF replacement |
| [`modules/testing.md`](migrate-spring-to-liberty/modules/testing.md) | Jakarta-compatible MicroShed integration tests, JUnit 5, Mockito, and optional REST Assured |
| [`modules/cleanup.md`](migrate-spring-to-liberty/modules/cleanup.md) | Leftover Spring imports, selective Jakarta namespace conversion, and CDI discovery |
| [`modules/feature-scan.md`](migrate-spring-to-liberty/modules/feature-scan.md) | Minimal `<featureManager>` derivation and `server.xml` update |
| [`modules/run-local.md`](migrate-spring-to-liberty/modules/run-local.md) | Time-bounded Liberty startup, readiness/smoke evidence, log triage, and graceful cleanup |
| [`modules/git.md`](migrate-spring-to-liberty/modules/git.md) | Optional git branch, secrets scan, commit, and draft PR workflow |

---

## Installation

Copy the [`migrate-spring-to-liberty`](migrate-spring-to-liberty) directory into your Bob global skills folder:

```bash
cp -r migrate-spring-to-liberty ~/.bob/skills/
```

The skill will be available in your next Bob task.

---

## Validate changes

Before contributing an update, run:

```bash
python3 migrate-spring-to-liberty/scripts/validate_skill.py
```

The validator checks frontmatter, internal links, canonical Jakarta EE 11 feature declarations, destructive schema examples, known nonportable mappings, security-critical wording, and four gate-classification fixtures. The same checks run in GitHub Actions.

### Evaluation fixtures

| Fixture | Behavior covered |
|---|---|
| [`rest-maven`](tests/fixtures/rest-maven) | Maven REST application with plain JUnit tests; frontend skips while testing still runs |
| [`mvc-jpa-security`](tests/fixtures/mvc-jpa-security) | Spring MVC, Thymeleaf, JPA, Security, CSRF, and Spring integration tests |
| [`partial-gradle-kotlin`](tests/fixtures/partial-gradle-kotlin) | Mixed Spring/Jakarta Gradle Kotlin project classified as a partial migration |
| [`no-tests`](tests/fixtures/no-tests) | Spring configuration with no tests; records an explicit coverage risk |

Each fixture includes `expected.json`. The validator derives its build, code, frontend, and testing gates and fails CI when the result changes unexpectedly.

---

## Trigger phrases

The skill activates on: `"spring to liberty"`, `"liberty migration"`, `"migrate to Jakarta EE"`, `"replace spring"`, `"migrate pom.xml"`, `"migrate build.gradle"`, `"Spring MVC"`, `"Spring Data JPA"`, `"@SpringBootApplication"`, `"WebSphere Liberty"`, `"Open Liberty"`

---

## Learn more

- [Open Liberty documentation](https://openliberty.io/docs/)
- [Jakarta EE 11 specification](https://jakarta.ee/specifications/)
- [MicroProfile 7 specification](https://microprofile.io/)
- [IBM Semeru Runtimes (JDK)](https://developer.ibm.com/languages/java/semeru-runtimes/)
- [liberty-maven-plugin](https://github.com/OpenLiberty/ci.maven)
- [liberty-gradle-plugin](https://github.com/OpenLiberty/ci.gradle)
- [MicroShed Testing](https://microshed.org/microshed-testing/)

---

## Acknowledgements

A big thank you to the **Red Hat team** for their initial help and inspiration. This skill was informed by their work on migrating Spring Boot applications to Quarkus — the original document can be found here:

[migrate-spring-to-quarkus SKILL.md](https://github.com/quarkusio/skills/blob/main/skills/migrate-spring-to-quarkus/SKILL.md)
