# Migrate Spring and Spring Boot applications to Jakarta EE 11 and Liberty

An IBM Bob skill that migrates Spring Boot applications to **Jakarta EE 11 running on Open Liberty**, following a modular, gate-driven approach. Each stage of the migration is gated on what is actually present in the project — modules are skipped if they don't apply.

---

## What this skill does

When activated, the skill follows six steps:

### Step 1 — Analyze & choose strategy

The skill scans the project and presents a summary table covering:

- **Build file** (`pom.xml` / `build.gradle` / `build.gradle.kts`) — Spring Boot version, starters, plugins
- **Java source code** — Spring annotations (DI, REST, Data, Security, Scheduling)
- **Configuration** — `application.properties` / `application.yml`, profiles
- **View layer** — Thymeleaf / JSP templates, static resources, Model+View patterns
- **Tests** — `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`

The user then chooses a migration strategy:

| Strategy | Description |
|---|---|
| **Jakarta EE 11 (Full Migration)** | Replaces all Spring annotations with CDI / JAX-RS / Jakarta EE equivalents. Best long-term maintainability. |
| **MicroProfile** | Adds MicroProfile APIs on top of Jakarta EE for cloud-native features (health, metrics, fault tolerance, config, JWT). Recommended for microservices. |

---

### Step 2 — Git branch (optional)

If the project is a git repository, the skill proposes an isolated migration branch (`migration/run-01`, `migration/run-02`, …) created from `main`. Before committing, it scans for accidentally exposed secrets (hardcoded tokens, API keys, private keys) and ensures AI agent session directories (`.claude/`, `.cursor/`, `.copilot/`, etc.) are listed in `.gitignore`. All changes land in a single commit; a draft PR is opened against `main` as a permanent diff and discussion record. The user can decline and the skill proceeds without any git management.

---

### Step 3 — Execute modules (gate-driven)

Each module runs only if its gate condition is met:

| Module | Gate | What it does |
|---|---|---|
| **jdk** | ALWAYS — stops migration if JDK is not 17, 21, or 25 | Verifies a supported JDK is installed; asks the user to confirm the target version (`JAVA_VERSION`). IBM Semeru Runtimes are recommended for production. |
| **build** | Spring Boot build markers found in build file | Detects Maven or Gradle and delegates to the matching sub-module. **Maven**: removes Spring Boot parent, changes packaging to `war`, adds Jakarta EE 11 BOM + `liberty-maven-plugin` + `jandex-maven-plugin`, creates `server.xml`. **Gradle**: removes Spring plugins, applies `war` + Liberty Gradle plugin + `com.github.vlsi.jandex`, configures `providedCompile`. Both sub-modules scan for non-Spring runtime dependencies (JDBC drivers, MQ clients, etc.) and carry them forward. Migrates `application.properties` → `server.xml` + `microprofile-config.properties`. |
| **code** | Spring annotations found in Java sources | Migrates all Java source: entities (`javax.persistence` → `jakarta.persistence`), repositories (Spring Data → CDI `@ApplicationScoped` + `EntityManager`), services (`@Service` → `@ApplicationScoped`), controllers (`@RestController` → JAX-RS `@Path`), DI (`@Autowired` → `@Inject`), config injection (`@Value` → `@ConfigProperty`), `@Bean` methods → CDI `@Produces`, `CommandLineRunner` → CDI `@Observes Startup`, removes `@SpringBootApplication` main class. Entity fields with Spring Boot snake_case column names are mapped with explicit `@Column(name="...")` annotations — EclipseLink has no equivalent naming strategy. `DataSource` is injected via `@Resource(lookup="jdbc/myapp")` (not `@Inject`) since Liberty's `<dataSource>` is JNDI-bound. |
| **frontend** | Thymeleaf / JSP templates or static resources found | Asks the user to choose a target view technology (Jakarta Faces 4.1, Jakarta MVC 2.1 + Eclipse Krazo, or JSP). When Krazo is chosen, adds `jakarta.mvc-api:3.0.0` (provided) and `krazo-resteasy:4.0.0` to the build file alongside `restfulWS-4.0`, `jsonb-3.0`, `jsonp-2.1`, `cdi-4.1`, and `beanValidation-3.1` features. Converts Thymeleaf templates and Spring MVC controllers; moves static assets from `src/main/resources/static/` to `src/main/webapp/`; removes Spring CSRF tokens from HTML and JavaScript. |
| **testing** | Spring test annotations found in test sources | Migrates `@SpringBootTest` integration tests to MicroShed Testing (`@MicroShedTest`) using `org.microshed:microshed-testing-liberty`; creates a shared `AppDeploymentConfig`; replaces `@MockBean` with Mockito / CDI `@Alternative`; replaces `TestRestTemplate` / MockMvc with MicroShed REST clients or REST Assured; moves integration tests to `*IT` naming convention. Adds `org.hibernate.validator:hibernate-validator` at test scope (required by MicroShed). Requires Docker or Podman for MicroShed container startup. |
| **cleanup** | ALWAYS — runs after all other modules | Removes leftover `org.springframework.*` imports; converts `javax.*` → `jakarta.*`; removes unused Spring dependencies (`spring-boot-devtools`, `spring-boot-configuration-processor`, etc.); deletes stale `application.properties` properties; creates `beans.xml` if CDI discovery needs it. |
| **feature-scan** | ALWAYS — runs after cleanup | Scans migrated sources and config files for actual API usage (CDI, JAX-RS, JPA, MicroProfile, etc.) using the Feature Trigger Table; derives a minimal `<featureManager>` list; presents the proposed list to the user with rationale; updates `server.xml` only after confirmation. |
| **run-local** | ALWAYS — runs after feature-scan | Starts Liberty in dev mode (`liberty:dev` / `libertyDev`), reads startup logs, triages and fixes errors across nine categories (feature conflicts, WAR not found, CDI wiring, JPA / DataSource, JAX-RS 404s, ClassNotFoundException, javax/jakarta split-package, port conflicts, JSON-B serialization), verifies the app responds to HTTP. |

After every module the skill runs a compile check (`./mvnw clean compile -DskipTests` or `./gradlew clean compileJava -x test`). It never advances to the next module with a broken build.

**Safety rules baked in:**

- Never deletes code it cannot migrate — leaves a `// TODO: Migration required — <reason>` comment instead
- Documents every decision and trade-off
- No silent changes — every file modification is intentional and traceable

---

### Step 4 — Verify the migration

Six ordered checks, each must pass before the next runs:

| # | Check | Pass criteria |
|---|---|---|
| 1 | Builds | `./mvnw clean package -DskipTests` exits 0, no compilation errors |
| 2 | No Spring deps | Zero `org.springframework` dependencies remaining in the build file |
| 3 | Has Liberty | Liberty BOM / plugin and at least one Jakarta EE feature present |
| 4 | Tests pass | All tests pass using MicroShed or Arquillian |
| 5 | Starts up | `CWWKF0011I` message in console; app responds to HTTP; no errors in `messages.log` |
| 6 | No leftover templates | No Thymeleaf references remaining (unless intentionally kept) |

---

### Step 5 — Migration report (self-reflection)

After verification the skill answers six self-reflection questions (what migrated cleanly, what required manual judgment, every `// TODO` left behind, any removed code, initial check failures and how they were fixed, missing skill mappings) and presents a structured `## Migration Report` covering:

- Strategy used, agent and model name, modules completed, checks passed
- Token usage and estimated cost
- Changes by module (files changed, key changes)
- Validation results table
- Unmigrated code (`// TODO` items) with reasons
- Removed code with justification
- Skill improvement suggestions (missing mappings, edge cases found)

---

### Step 6 — Commit and PR (only if git workflow was accepted)

Scans for accidentally exposed secrets before staging. Shows staged changes summary and asks for confirmation before committing, and again before pushing and opening the draft PR. The draft PR is never merged — `main` always retains the original Spring Boot code.

---

## Reference files

The skill ships four reference tables used internally during migration:

| Reference | Used during |
|---|---|
| [`references/dependency-map.md`](migrate-spring-to-liberty/references/dependency-map.md) | Build module — Spring → Liberty dependency and plugin mapping, JDBC driver placement, individual Jakarta EE 11 / MicroProfile 7 API coordinates |
| [`references/annotation-map.md`](migrate-spring-to-liberty/references/annotation-map.md) | Code module — DI, REST, Data, Security, Scheduling, Cache, Lifecycle annotation mapping |
| [`references/config-map.md`](migrate-spring-to-liberty/references/config-map.md) | Build module — `application.properties` property migration covering server, datasource, JPA, logging, profiles, CORS, cache, security, health, and static resources |
| [`references/jakarta-ee11-liberty-features.md`](migrate-spring-to-liberty/references/jakarta-ee11-liberty-features.md) | Feature-scan module — every Jakarta EE 11 spec and MicroProfile 7 API mapped to its Open Liberty feature name, Maven/Gradle coordinates, profile membership (`coreProfile`, `webProfile`, `jakartaee`), JCache provider configuration (`javax.cache` namespace — no Liberty `jcache` feature needed), security examples, typical `<featureManager>` sets including `jsonb-3.0` + `jsonp-2.1` always paired with `restfulWS-4.0`, and `persistence.xml` / `beans.xml` skeletons |

---

## Module files

| Module file | Purpose |
|---|---|
| [`modules/jdk.md`](migrate-spring-to-liberty/modules/jdk.md) | JDK version check — supports 17, 21, 25 |
| [`modules/build.md`](migrate-spring-to-liberty/modules/build.md) | Build system dispatcher + `server.xml` / MicroProfile Config creation |
| [`modules/build-maven.md`](migrate-spring-to-liberty/modules/build-maven.md) | Maven-specific migration (`pom.xml`, `liberty-maven-plugin`, `jandex-maven-plugin`) |
| [`modules/build-gradle.md`](migrate-spring-to-liberty/modules/build-gradle.md) | Gradle-specific migration (Groovy DSL and Kotlin DSL, Liberty Gradle plugin, Jandex) |
| [`modules/code.md`](migrate-spring-to-liberty/modules/code.md) | Java source migration (entities, repositories, services, controllers, DI, lifecycle) |
| [`modules/frontend.md`](migrate-spring-to-liberty/modules/frontend.md) | View layer migration (Thymeleaf → Jakarta MVC 2.1 + Krazo / JSF 4.1 / JSP, static assets, CSRF removal) |
| [`modules/testing.md`](migrate-spring-to-liberty/modules/testing.md) | Test migration (`org.microshed:microshed-testing-liberty`, JUnit 5, Mockito, Hibernate Validator, REST Assured) |
| [`modules/cleanup.md`](migrate-spring-to-liberty/modules/cleanup.md) | Leftover Spring imports, `javax.*` → `jakarta.*`, `beans.xml` creation |
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
