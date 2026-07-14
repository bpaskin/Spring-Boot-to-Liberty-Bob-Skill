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

## Reference Files

Load the relevant reference file when working on a module:

| Reference | Use during |
|---|---|
| [references/dependency-map.md](references/dependency-map.md) | Build module: dependency and plugin mapping |
| [references/annotation-map.md](references/annotation-map.md) | Code module: annotation, DI, REST, Data, Security migration |
| [references/config-map.md](references/config-map.md) | Build module: configuration property migration |
| [references/jakarta-ee11-liberty-features.md](references/jakarta-ee11-liberty-features.md) | Canonical Jakarta EE 11 and MicroProfile-to-Liberty feature mapping |


## Step 1: Analyze & Choose Scope

Scan the application to understand what needs to migrate:

- **Build system**: Read the build file (`pom.xml` for Maven, `build.gradle` or `build.gradle.kts` for Gradle) — Spring Boot version, starters, plugins
- **Build launcher**: Record whether `mvnw`/`gradlew` exists; do not assume a wrapper is present
- **Java code**: Search for Spring annotations (DI, REST, Data, Security, Scheduling)
- **Configuration**: Read `application.properties`/`application.yml`, check for profiles
- **UI / View layer**: Check for Thymeleaf/JSP templates, static resources, `Model`/`ModelAndView` patterns, `@Controller` (server-rendered) vs `@RestController` (API-only)
- **Tests**: Check for `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`

Present a summary table with area, findings, and complexity. Then ask the user to choose a migration scope:

- **Complete Spring removal**: Replace all Spring APIs with Jakarta EE 11 and selected MicroProfile equivalents. Prefer this for long-term maintainability.
- **Staged migration**: Migrate a user-selected slice while documenting remaining Spring dependencies and interoperability risks. Do not claim the application is Spring-free.

MicroProfile complements Jakarta EE; it is not a competing migration approach. After scope selection, inventory which optional capabilities are actually needed, such as Config, Health, Metrics, Fault Tolerance, JWT, OpenAPI, Rest Client, Telemetry, or Reactive Messaging. Add only those capabilities whose APIs or configuration are present.

**Stop here and wait for the user's response before continuing.** Do not ask about git workflow or anything else in the same message.

> **Spring MVC server-rendered views detected?** If the analysis in the step above finds `@Controller` classes (not `@RestController`) with `Model`/`ModelAndView` return types or Thymeleaf templates, an **additional question must be asked before the frontend module runs** — see Step 3 gate for `frontend` module and [modules/frontend.md](modules/frontend.md#view-technology-decision).

## Step 2: Git branch (optional)

After the user has chosen a scope, check if the target project is a git repository. If it is, propose the git workflow:

> **Migration workflow:** Each migration run can be isolated in its own branch (`migration/run-01`, `migration/run-02`, ...) created from the repository's confirmed base branch. The branch can contain one reviewed commit with the migration report, followed by a draft PR for discussion. The skill never merges automatically. **Would you like to use this workflow?**

- **User accepts** → follow [modules/git.md](modules/git.md) — **Pre-migration** section. Propose the branch name and wait for confirmation before creating it.
- **User declines** → skip git management entirely, proceed with migration in the current branch.
- **Not a git repo** → inform the user, skip git management, proceed normally.

## Step 3: Execute Modules

## Instructions

- Execute the instructions of the modules according to the following Decision Gate Table
- Always log which Module and Gate check is evaluated and the status using the format:
  Gate result: <STATUS> and <CONDITION_EVALUATED>

### Decision Gate Table 

- For each module, evaluate whether it applies to this project. A module executes only when its gate status is: **PASS**.
- Inspect the project to determine the gate result — do not rely on blind grep commands; use your understanding of the codebase.

| Module                          | Gate Check                                                                                                                | Gate Result                                                                              |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [jdk](modules/jdk.md)           | Jakarta EE 11 requires Java 17+; this skill targets supported LTS JDKs 17, 21, and 25 | **ALWAYS** -- stop migration if unsupported |
| [build](modules/build.md)       | Spring Boot parent/starters/`spring-boot-maven-plugin` in `pom.xml`, or Spring Boot/`io.spring.dependency-management` plugins in `build.gradle(.kts)` | **PASS** if Spring Boot build markers found; **SKIP** otherwise                          |
| [code](modules/code.md)         | Spring annotations in Java sources (`@Component`, `@Service`, `@Controller`, `@Repository`, `@Entity`, `@Autowired`, etc.) | **PASS** if Spring annotations found; **SKIP** otherwise                                 |
| [frontend](modules/frontend.md) | Thymeleaf/JSP templates in `templates/` or static resources in `static/`                                                  | **PASS** if view layer found; **SKIP** otherwise                                         |
| [testing](modules/testing.md)   | Spring test annotations in test sources (`@SpringBootTest`, `@WebMvcTest`, `@MockBean`)                                   | **PASS** if Spring tests found; **SKIP** otherwise                                       |
| [cleanup](modules/cleanup.md)   | Leftover Spring artifacts after all other modules                                                                          | **ALWAYS** — runs after all other modules                                                |
| [feature-scan](modules/feature-scan.md) | Always — scan migrated sources and config to build a minimal `<featureManager>` list and update `server.xml`      | **ALWAYS** — runs after cleanup, before run-local                                        |
| [run-local](modules/run-local.md) | Always — start Liberty locally, read logs, and fix runtime errors before finalising                                     | **ALWAYS** — runs after feature-scan                                                     |

### Execution Protocol

```
FOR module IN [build, code, frontend, testing, cleanup, feature-scan, run-local]:

  1. EVALUATE — inspect the project for the gate condition
  2. DECIDE
     IF gate == ALWAYS → proceed to step 3
     IF gate == PASS   → proceed to step 3
     IF gate == SKIP   → log "Module {name}: SKIPPED — {reason}", mark checkbox, continue
  3. LOAD — read the module file and relevant reference files
  4. EXECUTE — follow the module instructions, adapting to the chosen migration scope and required MicroProfile capabilities
  5. COMPILE — run the project's detected build launcher (`./mvnw`/`./gradlew` when present, otherwise `mvn`/`gradle`) with the module's compile arguments
     Fails → diagnose and fix before proceeding
  6. LOG — mark checkbox as done
```

### Running Individual Modules

To run a single module outside the full migration flow, read its file directly:

- "Read `modules/build.md` and execute it"
- "Run only the frontend module"
- "Re-run the cleanup module"
- "Re-run the feature-scan module"

The module will use the current project state and chosen migration scope. If no scope has been chosen, the module must ask before changing files.

## Step 4: Verify the Migration

Run each check in order. A check fails = stop and fix before continuing.

| # | Check | Command (Maven / Gradle) | Pass criteria |
|---|-------|---------|---------------|
| 1 | **Builds** | Maven: `clean package -DskipTests`; Gradle: `clean build -x test` (using the detected launcher) | Exit code 0, no compilation errors |
| 2 | **No Spring deps** | Search build file for `org.springframework` | Zero Spring dependencies remaining |
| 3 | **Has Liberty** | Search build file for `io.openliberty` or `liberty-maven-plugin` | Liberty BOM/plugin and at least one Jakarta EE feature present |
| 4 | **Tests pass** | Maven: `test`; Gradle: `test` (using the detected launcher) | All tests pass using MicroShed or Arquillian |
| 5 | **Starts up** | Maven: `liberty:dev`; Gradle: `libertyDev` (using the detected launcher) — follow [modules/run-local.md](modules/run-local.md) | `CWWKF0011I` message in console; app responds to HTTP requests; no errors in `messages.log` |
| 6 | **No leftover templates** | Search for Thymeleaf references | None remaining (unless intentionally kept) |

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

### Summary
- Scope: [Complete Spring removal / Staged migration]
- Optional MicroProfile capabilities: [list or none]
- Agent: [AI agent name, if available]
- Model: [model name, if available]
- Modules completed: [X/8]
- Checks passed: [X/6]
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
| Check | Result | Notes |
|-------|--------|-------|
| Builds | PASS/FAIL | |
| No Spring deps | PASS/FAIL | |
| Has Liberty | PASS/FAIL | |
| Tests pass | PASS/FAIL | |
| Starts up | PASS/FAIL | Log errors fixed: Y/N — list errors resolved |
| No leftover templates | PASS/FAIL | |

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
