# Module: Cleanup

Remove leftover Spring artifacts that survived the per-module migration: orphaned imports, unused dependencies, stale configuration, and the Spring Boot main class (if not already removed).

## What to do

- [ ] Remove the `@SpringBootApplication` main class (if still present)
- [ ] Remove leftover Spring imports from all Java files
- [ ] Remove unused Spring dependencies from the build file (`pom.xml` or `build.gradle(.kts)`)
- [ ] Remove stale Spring configuration properties from `application.properties` / `application.yml`
- [ ] Delete `application.properties` / `application.yml` entirely if all properties have been migrated to `server.xml` and `microprofile-config.properties`
- [ ] Compile: `./mvnw clean compile -DskipTests` (Maven) or `./gradlew clean compileJava -x test` (Gradle)

## Main class removal

If the main class was already removed during the code module, mark this as done.

Otherwise, delete the class that contains `SpringApplication.run(...)`. Jakarta EE applications deployed on Open Liberty do not need a `main` method — Liberty manages the lifecycle.

## Leftover Spring imports

Search all Java files for remaining `org.springframework.*` imports:

```bash
grep -rn "import org.springframework" src/
```

For each hit:
- If the class has a Jakarta EE / CDI equivalent → replace the import (use annotation-map.md)
- If it's an unused import → delete it
- If there is no equivalent and removal breaks the build → leave a `// TODO: Migration required — <reason>` comment

Also search for `javax.*` imports that might represent Jakarta EE APIs from older applications:

```bash
grep -rn "import javax\." src/
```

Convert only packages covered by an explicit Jakarta EE mapping, such as persistence, inject, enterprise, validation, transaction, servlet, and REST APIs. Never perform a global `javax.` to `jakarta.` replacement. Preserve Java SE and third-party namespaces including `javax.sql`, `javax.naming`, `javax.crypto`, and JCache's `javax.cache` unless a specific dependency migration proves otherwise.

## Unused Spring dependencies

Check the build file (`pom.xml` or `build.gradle(.kts)`) for Spring dependencies that are no longer referenced anywhere in the code:

- `spring-boot-devtools` → always remove (use `liberty:dev` or `libertyDev` instead)
- `spring-boot-configuration-processor` → remove (use MicroProfile Config `@ConfigProperty`)
- `spring-boot-starter-actuator` → remove if replaced by `mpHealth-4.0` / `mpMetrics-5.1` features in `server.xml`
- Any `spring-boot-starter-*` without matching code usage → remove
- `spring-boot-starter-parent` / `spring-boot-dependencies` BOM → must be removed

## Stale configuration

Check `application.properties` / `application.yml` for properties still using `spring.*` prefix that were missed during the build module. Either:

- Migrate them using config-map.md to `server.xml` or `microprofile-config.properties`
- Remove them if the feature they configure is no longer used

Common stragglers:

| Spring property | Action |
|---|---|
| `spring.datasource.*` | Migrate to `<dataSource/>` in `server.xml` or MicroProfile Config |
| `spring.jpa.*` | Migrate to `persistence.xml` properties |
| `spring.profiles.active` | Use MicroProfile Config profiles or Liberty server variables |
| `server.port` | Migrate to `<httpEndpoint httpPort="..."/>` in `server.xml` |
| `logging.level.*` | Migrate to `<logging/>` in `server.xml` |

## beans.xml (CDI discovery)

If CDI beans are not being discovered at runtime, create a minimal `beans.xml` in `src/main/webapp/WEB-INF/beans.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="https://jakarta.ee/xml/ns/jakartaee"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="https://jakarta.ee/xml/ns/jakartaee
                           https://jakarta.ee/xml/ns/jakartaee/beans_4_0.xsd"
       version="4.0"
       bean-discovery-mode="annotated">
</beans>
```

For library JARs that contain CDI beans but do not declare a `beans.xml`, CDI 4.0 annotated discovery mode will only find beans annotated with a scope annotation — this is sufficient for most cases.
