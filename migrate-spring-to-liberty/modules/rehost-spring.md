# Module: Retain Spring Boot and Rehost on Open Liberty

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md). Run this module only when the migration contract selects **retain Spring and rehost on Liberty**.

The goal is a hosting change, not a framework rewrite. Preserve Spring application code, starters, configuration, tests, security behavior, transaction boundaries, templates, and the executable bootstrap. Add the smallest Liberty build and deployment configuration needed to run the same application.

## Eligibility gate

Before editing, verify all of the following:

- The resolved Spring Boot stream is 3.x or 4.x. Use `springBoot-3.0` for Boot 3 and `springBoot-4.0` for Boot 4.
- A valid `@SpringBootApplication` or equivalent `SpringApplication.run(...)` bootstrap exists.
- The original executable JAR or WAR builds and its existing tests have baseline results.
- The contract selects one deployable artifact and records its actual generated filename.
- The application does not already depend on running multiple Spring Boot applications in one Liberty server configuration; Liberty supports one Spring Boot application per server configuration.

Mark the module `BLOCKED` instead of upgrading Spring Boot silently when the stream is unsupported, the bootstrap is missing, or the artifact cannot be identified. A framework upgrade is a separate approved change.

## Preserve the application

- Keep the Spring Boot parent/BOM, Spring Boot Maven or Gradle plugin, starters, `application.properties`/YAML, profiles, and Spring tests.
- Do not run the rewrite `build`, `code`, `frontend`, `cleanup`, or `feature-scan` modules.
- Do not add Jakarta EE convenience features to replace Spring starters. Open Liberty's Spring Boot Support feature does not integrate Spring applications with Liberty Application Security, Jakarta REST, or other application-programming-model features.
- Do not replace the embedded-container dependency manually. Liberty disables the embedded web container when it hosts the Spring Boot application.
- Preserve the baseline datasource, schema, security, actuator, session, scheduling, and transaction configuration unless the contract explicitly changes ownership of a setting.

## Build integration

Keep the Spring Boot plugin and add the Liberty plugin after it. Pin a tested Liberty plugin version consistently with the repository's existing version policy.

For Maven executable JAR deployment, configure the Liberty plugin to deploy the Spring Boot project:

```xml
<plugin>
    <groupId>io.openliberty.tools</groupId>
    <artifactId>liberty-maven-plugin</artifactId>
    <version>3.11.4</version>
    <configuration>
        <serverName>defaultServer</serverName>
        <installAppPackages>spring-boot-project</installAppPackages>
    </configuration>
</plugin>
```

The `spring-boot-maven-plugin` must remain earlier in the plugin list so it creates the executable artifact before Liberty deploys it. Some direct `deploy`-goal documentation names the parameter `deployPackages`; use only the parameter documented for the selected plugin version and goal, and record the verification rather than including both by guesswork.

For Gradle, preserve the Spring Boot plugin and `bootJar`/`bootWar` task, add `io.openliberty.tools.gradle.Liberty`, and configure deployment from the actual generated Boot artifact. Do not apply the rewrite module's `war`/Jandex substitutions. Verify the exact Gradle plugin configuration against its current documentation and the produced artifact before starting Liberty.

## server.xml

Create or update `src/main/liberty/config/server.xml`. Use the Spring Boot Support feature matching the detected stream and only the web-container features required by the application's starters.

Spring Boot 3 web example:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<server description="Rehost Spring Boot on Open Liberty">
    <featureManager>
        <feature>springBoot-3.0</feature>
        <feature>servlet-6.1</feature>
    </featureManager>

    <httpEndpoint id="defaultHttpEndpoint"
                  host="*"
                  httpPort="9080"
                  httpsPort="9443"/>

    <springBootApplication id="application"
                           location="{ACTUAL_BOOT_ARTIFACT}"/>
</server>
```

Use `springBoot-4.0` for Boot 4. Add a WebSocket or Pages feature only when the matching starter or application behavior requires it. Do not add `appSecurity`, Jakarta REST, or MicroProfile features merely because similarly named Spring starters exist; retain the starter implementation.

Derive `{ACTUAL_BOOT_ARTIFACT}` after packaging from Maven `artifactId`/`version`/`finalName` or Gradle `bootJar`/`bootWar` output. Do not hard-code an example filename. Use `<springBootApplication>`, not `<webApplication>`, for optimized Spring Boot deployment.

## Configuration ownership

Record which layer owns each setting:

| Concern | Default rehost owner |
|---|---|
| Spring profiles, application properties, security, actuator, data/JPA | Spring Boot configuration |
| Listener host and Liberty HTTP/HTTPS ports | Liberty `server.xml` |
| Spring context path and dispatcher path | Spring properties or explicit `<applicationArgument>` values |
| JVM options and environment variables | Liberty server environment/deployment platform |

Do not migrate Spring properties to MicroProfile Config. When passing a Spring command-line override, use an `<applicationArgument>` inside `<springBootApplication>` and preserve the baseline value unless the contract changes it.

## Full versus thin artifact

Default to the original full executable artifact for the first behavior-parity run. Choose a thin artifact only when image layering or transfer size is an explicit goal and the environment can manage Liberty's shared library cache. Record that a thinned WAR is Liberty-specific and no longer behaves as a standalone WAR.

## Validation

1. Package and test the unchanged Spring application with its detected launcher.
2. Confirm the produced artifact name matches `<springBootApplication location="...">` and contains the executable Spring Boot launcher.
3. Run the original Spring tests unchanged; add only missing Liberty-hosted smoke tests.
4. Execute [run-local.md](run-local.md) with a time-bounded Liberty foreground run.
5. Compare baseline and Liberty-hosted routes, status codes, response bodies, redirects, cookies/session behavior, authentication/authorization failures, actuator behavior, database effects, scheduled work, and shutdown.
6. Verify logs show one Spring Boot application, no unresolved deployment errors, and graceful process cleanup.

## Completion criteria

- Spring application code and dependencies were preserved except for explicitly approved changes.
- The matching Spring Boot Support and required web features install successfully.
- The actual JAR/WAR is deployed through `<springBootApplication>`.
- Existing tests pass, Liberty starts, smoke/security checks match the baseline, and the owned process stops cleanly.
- The report states **REHOSTED — SPRING RETAINED**, never “Spring-free” or “migrated to Jakarta EE.”

## Authoritative references

- [Configure and deploy Spring Boot applications to Open Liberty](https://openliberty.io/docs/latest/deploy-spring-boot.html)
- [Open Liberty Spring Boot Support 3.0](https://openliberty.io/docs/latest/reference/feature/springBoot-3.0.html)
- [Open Liberty Spring Boot Support 4.0](https://openliberty.io/docs/latest/reference/feature/springBoot-4.0.html)
- [Open Liberty Maven plugin Spring Boot support](https://github.com/OpenLiberty/ci.maven/blob/main/docs/spring-boot-support.md)
