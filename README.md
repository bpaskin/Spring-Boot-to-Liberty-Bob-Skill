# Migrate or rehost Spring Boot applications on Open Liberty

An IBM Bob skill that first decides whether to **retain Spring Boot on Open Liberty** or rewrite it to **Jakarta EE 11**. Its baseline-driven, resumable workflow prevents a hosting-only request from turning into an unnecessary framework rewrite.

## Quick start

Install the skill:

```bash
cp -R migrate-spring-to-liberty ~/.bob/skills/
```

Then open a Bob task in a Spring Boot project and ask:

```text
Analyze this Spring Boot application for a complete migration to Jakarta EE 11 on Open Liberty. Do not change files until you show the migration inventory and I choose the scope.
```

For a hosting-only assessment, ask:

```text
Analyze whether this Spring Boot application can be rehosted on Open Liberty without rewriting Spring code. Do not change files until you show the inventory and scope choices.
```

The skill first inventories the build, Java APIs, configuration, views, tests, security, and operational requirements. It then records a read-only baseline and one consolidated migration contract before changing the project.

## Compatibility

| Component | Target |
|---|---|
| Jakarta EE | 11 |
| Spring Boot rehost | 3.x or 4.x with matching `springBoot-3.0` / `springBoot-4.0` Liberty support |
| Java | 17 minimum; LTS targets 17, 21, or 25 |
| Open Liberty | A pinned release verified to install every selected feature |
| MicroProfile | Optional capabilities selected from the application's actual usage |
| Build tools | Maven or Gradle (wrappers preferred; installed launchers supported) |

## Important limitations

- WebFlux and Reactor pipelines do not have a mechanical Jakarta EE equivalent; redesign them deliberately or use staged migration.
- Security rewrites use a dedicated gate and contract for filter chains, OAuth2/OIDC/JWT, registries, method expressions, sessions/logout, CORS/CSRF, trust, and anonymous/authenticated/forbidden tests. Complex expressions still require application-specific policy design.
- WebFlux/R2DBC, Spring Cloud, Spring Integration, custom starters, SOAP/RPC, messaging, batch/scheduling, and non-relational stores pass a hard preflight gate. Complete removal is blocked until each detected stack has a dedicated module, retained-library strategy, redesign, or staged exception.
- Kafka/JMS/RabbitMQ migrations preserve broker topology, schemas, headers, ordering, acknowledgment/offset ownership, retries/dead letters, transactions, security, recovery, and shutdown semantics; a dependency swap alone is not sufficient.
- Spring Batch and scheduling migrations preserve job identity, parameters, checkpoints/restart, repository ownership, misfire/overlap policy, time zones, cluster behavior, and operational controls.
- Scheduling expressions and concurrency semantics must be verified; Spring, Enterprise Beans timers, Jakarta Concurrency, and Quartz are not interchangeable.
- Spring `@Async`, application events, non-default transaction attributes, and Spring Retry/listener behavior use a dedicated semantic gate; they are not annotation-only conversions.
- `spring.jpa.hibernate.ddl-auto=update` has no portable Jakarta Persistence equivalent. Schema generation defaults to `none`; use a reviewed migration tool for durable environments.
- Spring Data repositories can migrate to Jakarta Data 1.0 when their CRUD and query semantics are supported, or to CDI + `EntityManager` when explicit persistence control is required. The skill inventories incompatible Spring Data extensions instead of treating Jakarta Data as a drop-in replacement, binds repositories to an explicit datastore, and disables Liberty table creation/removal by default.
- Applications without tests can be migrated, but the result cannot claim behavioral parity until representative positive, negative, and security cases exist.
- Never remove working CSRF protection, authentication, authorization, secrets handling, or transaction boundaries before the replacement is configured and tested.

---

## What this skill does

When activated, the skill follows six steps:

### Step 1 — Analyze & choose scope

The skill scans the project and presents a summary table covering:

- **Build file** (`pom.xml` / `build.gradle` / `build.gradle.kts`) — Spring Boot version, starters, plugins
- **Java source code** — Spring imports, annotations, API calls, configuration, repositories, security, reactive flows, messaging, batch/scheduling, SOAP/RPC, custom extensions, and bootstrap code
- **Configuration** — `application.properties` / `application.yml`, profiles
- **View layer** — Thymeleaf / JSP templates, static resources, Model+View patterns
- **Tests** — every test source/dependency, including plain JUnit tests

The user then chooses a migration scope:

| Scope | Description |
|---|---|
| **Complete Spring removal** | Replaces all Spring APIs with Jakarta EE 11 and selected MicroProfile equivalents. Best for long-term maintainability. |
| **Staged migration** | Migrates a selected slice and documents the remaining Spring dependencies and interoperability risks. |
| **Retain Spring and rehost** | Preserves Spring code, starters, configuration, and tests while adding Liberty packaging, deployment configuration, and runtime verification. Best when Liberty hosting—not framework removal—is the goal. |

For rehosting, the skill verifies Spring Boot 3/4 eligibility and preserves Spring starters. For rewrite scopes, MicroProfile complements Jakarta EE rather than replacing it, and optional capabilities are added only when the application needs them.

---

### Step 2 — Baseline, migration contract, and optional Git branch

Before editing, the skill records the original build/test results, pre-existing worktree changes, application bootstrap, routes, views, datasource/schema behavior, security, external services, ports, and runtime constraints. Pre-existing failures remain separate from migration regressions.

It then presents one migration contract with the applicable JDK, exact branch/base, view technology, datasource and non-destructive schema policy, security model, complex-stack routes, async/event/transaction/retry behavior, messaging and batch semantics, external integration test tier, test runtime, optional deployment track, and external-service assumptions. Confirmed choices are not asked again. `migration-report.md` becomes the durable baseline, contract, module ledger, and resume point.

If Git isolation is selected, the exact branch choice from the contract is created from the detected base branch. Commit, push, and draft-PR actions still require separate explicit approval.

---

### Step 3 — Execute modules (gate-driven)

Each module runs only if its gate condition is met:

| Module | Gate | What it does |
|---|---|---|
| **jdk** | ALWAYS — stops migration if the JDK is unsupported | Enforces Java 17+ and applies the contract-selected LTS target 17, 21, or 25. |
| **complexity-gate** | ALWAYS before a rewrite changes build/source files | Inventories reactive, Spring Cloud/Integration, custom starter, messaging, batch, SOAP/RPC, and non-relational stacks; blocks cleanup until each has a confirmed route. |
| **rehost-spring** | Contract selects retain Spring; Boot 3/4 and a valid bootstrap are present | Preserves Spring and adds the matching Liberty Spring Boot Support feature, plugin configuration, actual artifact deployment, and scope-aware validation. |
| **build** | Rewrite scope plus Spring build markers or mixed Spring/Liberty state | Detects Maven/Gradle, handles complete and partial rewrites idempotently, preserves non-Spring runtime dependencies, and migrates runtime configuration. |
| **code** | Rewrite scope plus Spring APIs, TODOs, or mixed Spring/Jakarta code | Migrates the confirmed non-security source slice while preserving transaction, persistence, scheduling, and configuration semantics. Spring Data repositories follow the contract-selected Jakarta Data 1.0, CDI + `EntityManager`, or staged path. |
| **async-events** | Rewrite scope plus Spring async/executors/events, advanced transactions, or retry/listener behavior | Builds an execution-semantics matrix and preserves executor, context, event phase/order, transaction, overload, retry, and recovery behavior. |
| **messaging** | Rewrite scope plus Kafka, JMS, RabbitMQ/AMQP, Spring Cloud Stream, or Spring Integration messaging | Selects a verified broker integration and preserves schema, ordering, acknowledgment/offset, retry/dead-letter, transaction, security, and recovery behavior. |
| **batch-scheduling** | Rewrite scope plus Spring Batch, Quartz, `@Scheduled`, or task scheduling | Selects Jakarta Batch, retained Quartz, Liberty timers/concurrency, or an external scheduler and verifies restart, checkpoint, misfire, overlap, and cluster behavior. |
| **security** | Rewrite scope plus Spring Security, filter chains, authorization expressions, OAuth2/OIDC/JWT, registries, sessions, CSRF, or CORS | Builds authentication and route-policy matrices, selects a compatible Liberty/Jakarta mechanism, preserves browser/session behavior, and requires positive and negative parity tests before Spring Security removal. |
| **frontend** | Rewrite scope plus templates/assets or controller/view-return signals | Loads only the contract-selected Jakarta MVC, Faces, retained Thymeleaf, JSP/static, or REST path. Replaces and negative-tests CSRF protection before removing Spring integration. |
| **testing** | Any test source, dependency, or configuration | Rewrite scopes migrate Spring-specific tests where needed; rehosting preserves the Spring test suite and adds only missing Liberty-hosted coverage. |
| **cleanup** | ALWAYS for rewrite scopes; SKIP for rehosting | Removes leftover Spring imports only when Spring removal was selected; rehosting preserves them. |
| **feature-scan** | ALWAYS for rewrite scopes; SKIP for rehosting | Derives the Jakarta EE/MicroProfile feature set for rewrites; the rehost module owns Spring Boot feature selection. |
| **run-local** | ALWAYS — runs after the applicable rewrite or rehost modules | Runs Liberty in a controlled foreground session with a readiness URL, timeout, log evidence, smoke tests, and guaranteed graceful cleanup; a packaged foreground run is available when dev mode is unsuitable. |
| **deploy** | Contract-selected; explicit `SKIP` is valid | Optionally creates and validates pinned Liberty images, Kubernetes/OpenShift or Operator resources, probes, secret wiring, and CI/CD. Publishing and deployment require separate approval. |

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

Nine ordered checks distinguish migration failures, baseline failures, unavailable external dependencies (`BLOCKED`), and an explicitly skipped deployment track:

| # | Check | Pass criteria |
|---|---|---|
| 1 | Builds | The detected Maven or Gradle launcher completes a clean package/build with no compilation errors |
| 2 | Spring dependency scope | Zero for complete removal, only approved Spring for staged migration, or preserved baseline Spring dependencies for rehosting |
| 3 | Has Liberty | Rewrite has Jakarta EE features; rehost has the matching Spring Boot Support feature, required web feature, and actual Boot artifact declaration |
| 4 | Tests pass | Rewrite tests use the selected Jakarta/Liberty path; rehost preserves Spring tests and adds only missing Liberty smoke coverage |
| 5 | Starts up | Readiness within the recorded timeout; app responds; logs have no unresolved application errors; owned process stops cleanly |
| 6 | View scope | Rewrite matches the selected view path; rehost preserves baseline Spring view behavior |
| 7 | Security parity | Applicable positive and negative authentication, authorization, browser-state, and logout cases pass |
| 8 | External integration and recovery | Contract-selected disposable/Liberty/platform tests pass for applicable database, XA, schema, identity, broker, observability, restart, outage, and recovery cases; unavailable systems are `BLOCKED`, never reported as passes |
| 9 | Deployment track | Explicitly skipped or validated to the selected files/image/deployment evidence level, including readiness and a failure rollout where applicable |

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
| [`references/annotation-map.md`](migrate-spring-to-liberty/references/annotation-map.md) | Code/security modules — DI, REST, Data, Security, Scheduling, Cache, and Lifecycle mapping candidates and boundaries |
| [`references/jakarta-data.md`](migrate-spring-to-liberty/references/jakarta-data.md) | Conditionally loaded Spring Data repository strategy, compatibility inventory, Jakarta Data conversion, and Open Liberty provider guidance |
| [`references/config-map.md`](migrate-spring-to-liberty/references/config-map.md) | Build module — `application.properties` property migration covering server, datasource, JPA, logging, profiles, CORS, cache, security, health, and static resources |
| [`references/jakarta-ee11-liberty-features.md`](migrate-spring-to-liberty/references/jakarta-ee11-liberty-features.md) | Canonical Jakarta EE 11 and MicroProfile feature names, Maven/Gradle coordinates, profile membership, JCache provider guidance, security examples, and typical `<featureManager>` sets |
| [`references/migration-ledger.md`](migrate-spring-to-liberty/references/migration-ledger.md) | Baseline, consolidated contract, module state, transaction boundaries, and resume protocol |
| [`references/production-integration-testing.md`](migrate-spring-to-liberty/references/production-integration-testing.md) | Evidence tiers and positive/failure/restart contracts for PostgreSQL, XA, schema tools, OIDC/JWT, messaging, observability, and deployment |
| [`references/frontend-jakarta-mvc.md`](migrate-spring-to-liberty/references/frontend-jakarta-mvc.md) | Loaded only when the contract selects Jakarta MVC with Krazo |
| [`references/frontend-faces.md`](migrate-spring-to-liberty/references/frontend-faces.md) | Loaded only when the contract selects Jakarta Faces |
| [`references/frontend-thymeleaf.md`](migrate-spring-to-liberty/references/frontend-thymeleaf.md) | Loaded only when core Thymeleaf is intentionally retained |
| [`references/frontend-jsp-rest.md`](migrate-spring-to-liberty/references/frontend-jsp-rest.md) | Loaded for confirmed JSP/static paths or REST-only applications |

---

## Module files

| Module file | Purpose |
|---|---|
| [`modules/jdk.md`](migrate-spring-to-liberty/modules/jdk.md) | JDK version check — supports 17, 21, 25 |
| [`modules/complexity-gate.md`](migrate-spring-to-liberty/modules/complexity-gate.md) | Hard preflight for non-mechanical reactive, Cloud, Integration, custom starter, messaging, batch, SOAP/RPC, and non-relational stacks |
| [`modules/rehost-spring.md`](migrate-spring-to-liberty/modules/rehost-spring.md) | Hosting-only route for Spring Boot 3/4 using Liberty Spring Boot Support without a framework rewrite |
| [`modules/build.md`](migrate-spring-to-liberty/modules/build.md) | Build system dispatcher + `server.xml` / MicroProfile Config creation |
| [`modules/build-maven.md`](migrate-spring-to-liberty/modules/build-maven.md) | Maven-specific migration (`pom.xml`, `liberty-maven-plugin`, `jandex-maven-plugin`) |
| [`modules/build-gradle.md`](migrate-spring-to-liberty/modules/build-gradle.md) | Gradle-specific migration (Groovy DSL and Kotlin DSL, Liberty Gradle plugin, Jandex) |
| [`modules/code.md`](migrate-spring-to-liberty/modules/code.md) | Java source migration (entities, repositories, services, controllers, DI, lifecycle) |
| [`modules/async-events.md`](migrate-spring-to-liberty/modules/async-events.md) | Async executors, CDI events, transaction propagation/phase, Spring Retry/listeners, recovery, and overload semantics |
| [`modules/messaging.md`](migrate-spring-to-liberty/modules/messaging.md) | Kafka, JMS, RabbitMQ/AMQP, Stream, and Integration topology/semantics with real broker failure checks |
| [`modules/batch-scheduling.md`](migrate-spring-to-liberty/modules/batch-scheduling.md) | Batch jobs, checkpoints/restart, scheduling, Quartz, overlap/misfire, clustering, and operational controls |
| [`modules/security.md`](migrate-spring-to-liberty/modules/security.md) | Dedicated security gate for authentication, authorization, OAuth2/OIDC/JWT, registries, sessions/logout, CORS/CSRF, trust, and negative tests |
| [`modules/frontend.md`](migrate-spring-to-liberty/modules/frontend.md) | View-layer scenario router, static assets, and verified CSRF replacement |
| [`modules/testing.md`](migrate-spring-to-liberty/modules/testing.md) | Jakarta-compatible MicroShed integration tests, JUnit 5, Mockito, and optional REST Assured |
| [`modules/cleanup.md`](migrate-spring-to-liberty/modules/cleanup.md) | Leftover Spring imports, selective Jakarta namespace conversion, and CDI discovery |
| [`modules/feature-scan.md`](migrate-spring-to-liberty/modules/feature-scan.md) | Minimal `<featureManager>` derivation and `server.xml` update |
| [`modules/run-local.md`](migrate-spring-to-liberty/modules/run-local.md) | Time-bounded Liberty startup, readiness/smoke evidence, log triage, and graceful cleanup |
| [`modules/deploy.md`](migrate-spring-to-liberty/modules/deploy.md) | Optional container/Kubernetes/OpenShift deployment artifacts, probes, secrets, CI/CD, and evidence levels |
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

The validator checks frontmatter, internal links, canonical Jakarta EE 11 and Spring Boot feature declarations, destructive schema examples, known nonportable mappings, module safety invariants, 15 gate-classification fixtures, and the golden/evaluation manifests. The same static checks run on every pull request.

### Evaluation fixtures

| Fixture | Behavior covered |
|---|---|
| [`rest-maven`](tests/fixtures/rest-maven) | Maven REST application with plain JUnit tests; frontend skips while testing still runs |
| [`mvc-jpa-security`](tests/fixtures/mvc-jpa-security) | Spring MVC, Thymeleaf, JPA, a route-ordered `SecurityFilterChain`, JWT resource server, complex method expression, CSRF, and Spring integration tests |
| [`partial-gradle-kotlin`](tests/fixtures/partial-gradle-kotlin) | Mixed Spring/Jakarta Gradle Kotlin project classified as a partial migration |
| [`no-tests`](tests/fixtures/no-tests) | Spring configuration with no tests; records an explicit coverage risk |
| [`spring-data-repository`](tests/fixtures/spring-data-repository) | Detects Spring Data repository interfaces and requires an explicit Jakarta Data, `EntityManager`, or staged strategy |
| [`rehost-spring-boot`](tests/fixtures/rehost-spring-boot) | Detects an eligible Spring Boot 3 application with an executable bootstrap and preserves its Spring test path |
| [`async-events-transactions`](tests/fixtures/async-events-transactions) | Detects named `@Async`, application events, retry, and non-default transaction semantics that require a dedicated strategy |
| [`deployment-existing`](tests/fixtures/deployment-existing) | Detects existing image and Kubernetes artifacts so the deployment contract preserves their ownership |
| [`reactive-cloud-custom`](tests/fixtures/reactive-cloud-custom) | Hard-gates WebFlux, R2DBC, Spring Cloud Gateway/OpenFeign, and custom auto-configuration metadata |
| [`messaging-integration`](tests/fixtures/messaging-integration) | Detects Kafka, RabbitMQ, and Spring Integration messaging that requires a semantic strategy |
| [`batch-scheduling`](tests/fixtures/batch-scheduling) | Detects Spring Batch, Quartz, and zoned scheduling contracts |
| [`soap-redis`](tests/fixtures/soap-redis) | Prevents SOAP from being reduced to JAXB and Redis from being treated like a JDBC connection factory |
| [`production-data-xa`](tests/fixtures/production-data-xa) | PostgreSQL, multiple datasources/XA, Flyway/Liquibase, rollback, restart, and schema-failure contract markers |
| [`production-identity-observability`](tests/fixtures/production-identity-observability) | OIDC/JWT, Actuator, Micrometer/OpenTelemetry, authorization, issuer, readiness, and exporter outage markers |
| [`production-kafka-deployment`](tests/fixtures/production-kafka-deployment) | Kafka listener, image/deployment probes, poison record, broker outage, rebalance, and shutdown markers |

Each fixture includes `expected.json`. The validator derives its build, code, frontend, and testing gates; repository, async/event, security, reactive, messaging, batch, SOAP, non-relational, external-data, identity, and observability strategy requirements; deployment artifacts; missing security-test coverage; and rehost eligibility.

### Golden end-to-end evaluations

[`tests/e2e/scenarios.json`](tests/e2e/scenarios.json) defines complete before/after migrations for Maven security/events, Gradle Jakarta Data/frontend CSRF, partial-migration resume, Maven Spring Boot 3 rehosting, and Gradle Spring Boot 4 rehosting. Run static checks locally:

```bash
python3 migrate-spring-to-liberty/scripts/run_e2e.py --mode static
```

With Maven, Gradle, a compatible JDK, and network access, `--mode build` compiles and tests the migrated golden projects. The scheduled/manual [online compatibility workflow](.github/workflows/compatibility.yml) additionally builds the Boot 3/Maven and Boot 4/Gradle rehosting examples on Java 17, 21, and 25; resolves the pinned plugins/runtime; installs `server.xml` features; starts Liberty; performs HTTP smoke tests; and stops each server. This separates deterministic pull-request validation from version-drift checks that require external repositories.

### Agent and production evaluations

The agent harness copies a raw Spring project to an isolated workspace, gives an external agent only the migration prompt and this skill, then grades the resulting files and executes its build:

```bash
python3 migrate-spring-to-liberty/scripts/run_agent_eval.py --mode static
python3 migrate-spring-to-liberty/scripts/run_agent_eval.py --mode run \
  --agent-command-json '["your-agent", "--workspace", "{workspace}", "--prompt", "{prompt_file}"]'
```

The production harness validates explicit positive and failure contracts for PostgreSQL/XA/schema tools, OIDC/telemetry, and Kafka/deployment. [`tests/production/README.md`](tests/production/README.md) defines the evidence format. `evidence` mode accepts only named real environments with a non-empty artifact/log and observed result for every required case; compile-only or unavailable-dependency claims do not pass:

```bash
python3 migrate-spring-to-liberty/scripts/run_production_evals.py --mode static
python3 migrate-spring-to-liberty/scripts/run_production_evals.py --mode evidence \
  --evidence-root /path/to/real-evidence
```

---

## Trigger phrases

The skill activates on: `"spring to liberty"`, `"rehost Spring Boot"`, `"retain Spring on Liberty"`, `"liberty migration"`, `"migrate to Jakarta EE"`, `"replace spring"`, `"migrate pom.xml"`, `"migrate build.gradle"`, `"Spring MVC"`, `"Spring Data JPA"`, `"@SpringBootApplication"`, `"WebSphere Liberty"`, `"Open Liberty"`

---

## Learn more

- [Open Liberty documentation](https://openliberty.io/docs/)
- [Deploy Spring Boot applications to Open Liberty](https://openliberty.io/docs/latest/deploy-spring-boot.html)
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
