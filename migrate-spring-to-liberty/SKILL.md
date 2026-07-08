---
name: migrate-spring-to-liberty
description: Migrates Spring Boot applications to Jakarta EE 11 running on Open Liberty using a modular, gate-driven approach.
  Use when the user wants to migrate, convert, or port a Spring Boot app to Open Liberty or Jakarta EE, mentions "spring to liberty",
  "liberty migration", "replace spring", "migrate to Jakarta EE", asks about migrating "pom.xml", "build.gradle", "Spring MVC",
  "Spring Data JPA", "@SpringBootApplication", or wants to run on WebSphere Liberty / Open Liberty.
license: Apache-2.0
metadata:
  author: IBM Open Liberty Community - https://openliberty.io
---

# Spring Boot to Jakarta EE 11 + Open Liberty Migration

Modular, gate-driven migration of Spring Boot applications to Jakarta EE 11 running on Open Liberty.

## Critical Rules

- **Never delete code you cannot migrate.** If you cannot fully migrate a piece of code, leave the original in place with a `// TODO: Migration required — <reason>` comment explaining what needs to change and why. This applies to:
    - Methods, classes, or annotations you don't know how to convert
    - Spring-specific patterns without a clear Jakarta EE equivalent
    - Configuration or wiring code whose purpose is unclear
      If you must remove code (e.g., a Spring-only base class), document what was removed and why in a `// REMOVED:` comment at the same location.
- **Don't break the build.** Run the compile command after each phase (`./mvnw clean compile -DskipTests` for Maven, `./gradlew clean compileJava -x test` for Gradle). Never move to the next phase with a broken build.
- **Document every decision.** When choosing between migration approaches, explain the trade-off to the user.
- **No silent changes.** Every file modification must be intentional and traceable. If a check fails after a phase, diagnose and fix — don't skip the check or delete the failing code.

## Reference Files

Load the relevant reference file when working on a module:

| Reference | Use during |
|---|---|
| [references/dependency-map.md](references/dependency-map.md) | Build module: dependency and plugin mapping |
| [references/annotation-map.md](references/annotation-map.md) | Code module: annotation, DI, REST, Data, Security migration |
| [references/config-map.md](references/config-map.md) | Build module: configuration property migration |


## Step 1: Analyze & Choose Strategy

Scan the application to understand what needs to migrate:

- **Build system**: Read the build file (`pom.xml` for Maven, `build.gradle` or `build.gradle.kts` for Gradle) — Spring Boot version, starters, plugins
- **Java code**: Search for Spring annotations (DI, REST, Data, Security, Scheduling)
- **Configuration**: Read `application.properties`/`application.yml`, check for profiles
- **UI / View layer**: Check for Thymeleaf/JSP templates, static resources, `Model`/`ModelAndView` patterns, `@Controller` (server-rendered) vs `@RestController` (API-only)
- **Tests**: Check for `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`

Present a summary table with area, findings, and complexity. Then ask the user to choose a strategy:

- **Jakarta EE 11 (Full Migration)**: Replace all Spring annotations with CDI/JAX-RS/Jakarta EE equivalents. Full Open Liberty experience, best long-term maintainability.
- **MicroProfile**: Adds MicroProfile APIs on top of Jakarta EE for cloud-native features (health, metrics, fault tolerance, config). Recommended for microservices.

**Stop here and wait for the user's response before continuing.** Do not ask about git workflow or anything else in the same message.

> **Spring MVC server-rendered views detected?** If the analysis in the step above finds `@Controller` classes (not `@RestController`) with `Model`/`ModelAndView` return types or Thymeleaf templates, an **additional question must be asked before the frontend module runs** — see Step 3 gate for `frontend` module and [modules/frontend.md](modules/frontend.md#view-technology-decision).

## Step 2: Git branch (optional)

After the user has chosen a strategy, check if the target project is a git repository. If it is, propose the git workflow:

> **Migration workflow:** Each migration run can be isolated in its own branch (`migration/run-01`, `migration/run-02`, ...) created from `main`. The branch will contain a single commit with all changes plus a migration report. A draft PR against `main` will be created for review — it is never merged, it serves as a permanent diff and discussion record. **Would you like to use this workflow?**

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
| [jdk](modules/jdk.md)           | JDK 21+ required (Jakarta EE 11 mandates Java 21)                                   | **ALWAYS** -- stop migration if < 21 |
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
  4. EXECUTE — follow the module instructions, adapting to the chosen strategy
  5. COMPILE — run the project's compile command (`./mvnw clean compile -DskipTests` for Maven, `./gradlew clean compileJava -x test` for Gradle)
     Fails → diagnose and fix before proceeding
  6. LOG — mark checkbox as done
```

### Running Individual Modules

To run a single module outside the full migration flow, read its file directly:

- "Read `modules/build.md` and execute it"
- "Run only the frontend module"
- "Re-run the cleanup module"
- "Re-run the feature-scan module"

The module will use the current project state and the chosen strategy (if already decided). If no strategy has been chosen, the module will ask.

## Step 4: Verify the Migration

Run each check in order. A check fails = stop and fix before continuing.

| # | Check | Command (Maven / Gradle) | Pass criteria |
|---|-------|---------|---------------|
| 1 | **Builds** | `./mvnw clean package -DskipTests` / `./gradlew clean build -x test` | Exit code 0, no compilation errors |
| 2 | **No Spring deps** | Search build file for `org.springframework` | Zero Spring dependencies remaining |
| 3 | **Has Liberty** | Search build file for `io.openliberty` or `liberty-maven-plugin` | Liberty BOM/plugin and at least one Jakarta EE feature present |
| 4 | **Tests pass** | `./mvnw test` / `./gradlew test` | All tests pass using MicroShed or Arquillian |
| 5 | **Starts up** | `./mvnw liberty:dev` / `./gradlew libertyDev` — follow [modules/run-local.md](modules/run-local.md) | `CWWKF0011I` message in console; app responds to HTTP requests; no errors in `messages.log` |
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
- Strategy: [Full Jakarta EE 11 / MicroProfile]
- Agent: [AI agent name - e.g claude, pi, opencode, gemini, etc]
- Model: [model name — e.g. claude-sonnet-4-6, check system context]
- Modules completed: [X/4]
- Checks passed: [X/6]
- Token usage: [input tokens / output tokens — check session stats]
- Estimated cost: [~$X.XX — token counts × per-model pricing from anthropic.com/pricing]

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
