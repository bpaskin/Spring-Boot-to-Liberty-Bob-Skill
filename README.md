# Migrate Spring and Spring Boot applications to Jakarta EE 11 and Liberty

An IBM Bob skill that migrates Spring Boot applications to **Jakarta EE 11 running on Open Liberty**, following a modular, gate-driven approach. Each stage of the migration is gated on what is actually present in the project — modules are skipped if they don't apply.

## Quick start

Install the skill:

```bash
cp -R migrate-spring-to-liberty ~/.bob/skills/
```

Then open a Bob task in a Spring Boot project and ask:

```text
Analyze this Spring Boot application for a complete migration to Jakarta EE 11 on Open Liberty. Do not change files until you show the migration inventory and I choose the scope.
```

The skill first inventories the build, Java APIs, configuration, views, tests, security, and operational requirements. It then pauses for scope and workflow decisions before changing the project.

## Compatibility

| Component | Target |
|---|---|
| Jakarta EE | 11 |
| Java | 17 minimum; LTS targets 17, 21, or 25 |
| Open Liberty | A pinned release verified to install every selected feature |
| MicroProfile | Optional capabilities selected from the application's actual usage |
| Build tools | Maven Wrapper, Gradle Wrapper (Groovy or Kotlin DSL) |

## Important limitations

- WebFlux and Reactor pipelines do not have a mechanical Jakarta EE equivalent; redesign them deliberately or use staged migration.
- Complex Spring Security filter chains, OAuth client behavior, method expressions, and session policies require an explicit security design and negative tests.
- Spring Batch, Spring Integration, Spring Cloud, and custom Spring extensions require project-specific migration plans.
- Scheduling expressions and concurrency semantics must be verified; Spring, Enterprise Beans timers, Jakarta Concurrency, and Quartz are not interchangeable.
- Never remove working CSRF protection, authentication, authorization, secrets handling, or transaction boundaries before the replacement is configured and tested.

---

## What this skill does

When activated, the skill follows six steps:

### Step 1 — Analyze & choose scope

The skill scans the project and presents a summary table covering:

- **Build file** (`pom.xml` / `build.gradle` / `build.gradle.kts`) — Spring Boot version, starters, plugins
- **Java source code** — Spring annotations (DI, REST, Data, Security, Scheduling)
- **Configuration** — `application.properties` / `application.yml`, profiles
- **View layer** — Thymeleaf / JSP templates, static resources, Model+View patterns
- **Tests** — `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`

The user then chooses a migration scope:

| Scope | Description |
|---|---|
| **Complete Spring removal** | Replaces all Spring APIs with Jakarta EE 11 and selected MicroProfile equivalents. Best for long-term maintainability. |
| **Staged migration** | Migrates a selected slice and documents the remaining Spring dependencies and interoperability risks. |

MicroProfile complements Jakarta EE rather than replacing it. The skill detects and adds optional MicroProfile capabilities only when the application needs them.

---

### Step 2 — Git branch (optional)

If the project is a git repository, the skill proposes an isolated migration branch (`migration/run-01`, `migration/run-02`, …) created from `main`. Before committing, it scans for accidentally exposed secrets (hardcoded tokens, API keys, private keys) and ensures AI agent session directories (`.claude/`, `.cursor/`, `.copilot/`, etc.) are listed in `.gitignore`. All changes land in a single commit; a draft PR is opened against `main` as a permanent diff and discussion record. The user can decline and the skill proceeds without any git management.

---

### Step 3 — Execute modules (gate-driven)

Each module runs only if its gate condition is met:

| Module | Gate | What it does |
|---|---|---|
| **jdk** | ALWAYS — stops migration if the JDK is unsupported | Enforces the Jakarta EE 11 minimum of Java 17 and supports LTS targets 17, 21, and 25; asks the user to confirm `JAVA_VERSION`. |
| **build** | Spring Boot build markers found in build file | Detects Maven or Gradle and delegates to the matching sub-module. **Maven**: removes Spring Boot parent, changes packaging to `war`, adds Jakarta EE 11 BOM + `liberty-maven-plugin` + `jandex-maven-plugin`, creates `server.xml`. **Gradle**: removes Spring plugins, applies `war` + Liberty Gradle plugin + `com.github.vlsi.jandex`, configures `providedCompile`. Both sub-modules scan for non-Spring runtime dependencies (JDBC drivers, MQ clients, etc.) and carry them forward. Migrates `application.properties` → `server.xml` + `microprofile-config.properties`. |
| **code** | Spring annotations found in Java sources | Migrates all Java source: entities (`javax.persistence` → `jakarta.persistence`), repositories (Spring Data → CDI `@ApplicationScoped` + `EntityManager`), services (`@Service` → `@ApplicationScoped`), controllers (`@RestController` → JAX-RS `@Path`), DI (`@Autowired` → `@Inject`), config injection (`@Value` → `@ConfigProperty`), `@Bean` methods → CDI `@Produces`, `CommandLineRunner` → CDI `@Observes Startup`, removes `@SpringBootApplication` main class. Entity fields with Spring Boot snake_case column names are mapped with explicit `@Column(name="...")` annotations — EclipseLink has no equivalent naming strategy. `DataSource` is injected via `@Resource(lookup="jdbc/myapp")` (not `@Inject`) since Liberty's `<dataSource>` is JNDI-bound. |
| **frontend** | Thymeleaf / JSP templates or static resources found | Asks the user to choose Jakarta Faces 4.1, Jakarta MVC 3.0 + Eclipse Krazo, or preserved Thymeleaf. Converts templates and controllers, moves static assets into the WAR, and replaces Spring CSRF integration with verified protection for the chosen target before removing Spring Security. |
| **testing** | Spring test annotations found in test sources | Migrates integration tests to a Jakarta-compatible MicroShed release and unit tests to JUnit/Mockito; preserves test intent, uses `*IT` naming for integration tests, and adds validation dependencies only when tests execute validation outside Liberty. Requires a compatible container runtime for MicroShed. |
| **cleanup** | ALWAYS — runs after all other modules | Removes leftover Spring imports; converts only explicitly mapped Jakarta EE APIs from `javax.*` while preserving Java SE and third-party namespaces; removes unused Spring dependencies and stale configuration; creates `beans.xml` when CDI discovery needs it. |
| **feature-scan** | ALWAYS — runs after cleanup | Scans migrated sources and config files for actual API usage (CDI, JAX-RS, JPA, MicroProfile, etc.) using the Feature Trigger Table; derives a minimal `<featureManager>` list; presents the proposed list to the user with rationale; updates `server.xml` only after confirmation. |
| **run-local** | ALWAYS — runs after feature-scan | Starts Liberty in dev mode (`liberty:dev` / `libertyDev`), reads startup logs, triages and fixes errors across nine categories (feature conflicts, WAR not found, CDI wiring, JPA / DataSource, JAX-RS 404s, ClassNotFoundException, javax/jakarta split-package, port conflicts, JSON-B serialization), verifies the app responds to HTTP. |

After every module the skill runs a compile check with the project's wrapper when present, or the installed `mvn`/`gradle` command otherwise. It never advances to the next module with a broken build.

**Safety rules baked in:**

- Never deletes code it cannot migrate — leaves a `// TODO: Migration required — <reason>` comment instead
- Documents every decision and trade-off
- No silent changes — every file modification is intentional and traceable

---

### Step 4 — Verify the migration

Six ordered checks, each must pass before the next runs:

| # | Check | Pass criteria |
|---|---|---|
| 1 | Builds | The detected Maven or Gradle launcher completes a clean package/build with no compilation errors |
| 2 | No Spring deps | Zero `org.springframework` dependencies remaining in the build file |
| 3 | Has Liberty | Liberty BOM / plugin and at least one Jakarta EE feature present |
| 4 | Tests pass | All tests pass using MicroShed or Arquillian |
| 5 | Starts up | `CWWKF0011I` message in console; app responds to HTTP; no errors in `messages.log` |
| 6 | No leftover templates | No Thymeleaf references remaining (unless intentionally kept) |

---

### Step 5 — Migration report (self-reflection)

After verification the skill answers six self-reflection questions (what migrated cleanly, what required manual judgment, every `// TODO` left behind, any removed code, initial check failures and how they were fixed, missing skill mappings) and presents a structured `## Migration Report` covering:

- Migration scope, optional MicroProfile capabilities, modules completed, and checks passed
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

The skill ships four reference tables used internally during migration:

| Reference | Used during |
|---|---|
| [`references/dependency-map.md`](migrate-spring-to-liberty/references/dependency-map.md) | Build module — Spring → Liberty dependency and plugin mapping, JDBC driver placement, individual Jakarta EE 11 / MicroProfile 7 API coordinates |
| [`references/annotation-map.md`](migrate-spring-to-liberty/references/annotation-map.md) | Code module — DI, REST, Data, Security, Scheduling, Cache, Lifecycle annotation mapping |
| [`references/config-map.md`](migrate-spring-to-liberty/references/config-map.md) | Build module — `application.properties` property migration covering server, datasource, JPA, logging, profiles, CORS, cache, security, health, and static resources |
| [`references/jakarta-ee11-liberty-features.md`](migrate-spring-to-liberty/references/jakarta-ee11-liberty-features.md) | Canonical Jakarta EE 11 and MicroProfile feature names, Maven/Gradle coordinates, profile membership, JCache provider guidance, security examples, and typical `<featureManager>` sets |

---

## Module files

| Module file | Purpose |
|---|---|
| [`modules/jdk.md`](migrate-spring-to-liberty/modules/jdk.md) | JDK version check — supports 17, 21, 25 |
| [`modules/build.md`](migrate-spring-to-liberty/modules/build.md) | Build system dispatcher + `server.xml` / MicroProfile Config creation |
| [`modules/build-maven.md`](migrate-spring-to-liberty/modules/build-maven.md) | Maven-specific migration (`pom.xml`, `liberty-maven-plugin`, `jandex-maven-plugin`) |
| [`modules/build-gradle.md`](migrate-spring-to-liberty/modules/build-gradle.md) | Gradle-specific migration (Groovy DSL and Kotlin DSL, Liberty Gradle plugin, Jandex) |
| [`modules/code.md`](migrate-spring-to-liberty/modules/code.md) | Java source migration (entities, repositories, services, controllers, DI, lifecycle) |
| [`modules/frontend.md`](migrate-spring-to-liberty/modules/frontend.md) | View-layer migration, static assets, and verified CSRF replacement |
| [`modules/testing.md`](migrate-spring-to-liberty/modules/testing.md) | Jakarta-compatible MicroShed integration tests, JUnit 5, Mockito, and optional REST Assured |
| [`modules/cleanup.md`](migrate-spring-to-liberty/modules/cleanup.md) | Leftover Spring imports, selective Jakarta namespace conversion, and CDI discovery |
| [`modules/feature-scan.md`](migrate-spring-to-liberty/modules/feature-scan.md) | Minimal `<featureManager>` derivation and `server.xml` update |
| [`modules/run-local.md`](migrate-spring-to-liberty/modules/run-local.md) | Liberty dev mode startup, log triage, nine error categories and fixes |
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

The validator checks frontmatter, internal links, canonical Jakarta EE 11 feature declarations, known nonportable mappings, and security-critical wording. The same check runs in GitHub Actions.

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
