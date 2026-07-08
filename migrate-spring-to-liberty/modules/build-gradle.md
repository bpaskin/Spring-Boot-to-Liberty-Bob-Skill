# Submodule: Build System (Gradle)

Gradle-specific build migration steps. Called from [build.md](build.md).
Covers both Groovy DSL (`build.gradle`) and Kotlin DSL (`build.gradle.kts`).

Detect which DSL the project uses by the file extension. Use the matching syntax in all examples shown to the user. Do not mix DSLs.

## What to do

- [ ] Remove Spring Boot Gradle plugin and `io.spring.dependency-management`
- [ ] Apply `war` plugin and `liberty` Gradle plugin
- [ ] Add Jakarta EE 11 `providedCompile` / `compileOnly` dependency
- [ ] Configure Java compiler (`-parameters` flag, Java `{JAVA_VERSION}`)
- [ ] Replace Spring starters with Jakarta EE equivalents (use dependency-map.md)
- [ ] Remove unused Spring-only dependencies
- [ ] Carry forward non-Spring runtime dependencies found in the original build file (JDBC drivers, messaging clients, etc.) — see **Non-Spring Runtime Dependencies** below
- [ ] Create `src/main/liberty/config/server.xml` (handled in build.md)
- [ ] Compile: `./gradlew clean compileJava -x test`

## Plugin Block

**Groovy DSL** (`build.gradle`):

```groovy
// BEFORE: Spring Boot
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.x.x'
    id 'io.spring.dependency-management' version '1.x.x'
}

// AFTER: Open Liberty
plugins {
    id 'java'
    id 'war'
    id 'io.openliberty.tools.gradle.Liberty' version '3.9.4'
    id 'com.github.vlsi.jandex' version '1.90'
}
```

**Kotlin DSL** (`build.gradle.kts`):

```kotlin
// BEFORE: Spring Boot
plugins {
    java
    id("org.springframework.boot") version "3.x.x"
    id("io.spring.dependency-management") version "1.x.x"
}

// AFTER: Open Liberty
plugins {
    java
    war
    id("io.openliberty.tools.gradle.Liberty") version "3.9.4"
    id("com.github.vlsi.jandex") version "1.90"
}
```

## Java Compiler Configuration

**Groovy DSL**:

```groovy
java {
    sourceCompatibility = JavaVersion.VERSION_{JAVA_VERSION}
    targetCompatibility = JavaVersion.VERSION_{JAVA_VERSION}
}

compileJava {
    options.encoding = 'UTF-8'
    options.compilerArgs.add('-parameters')
}
```

**Kotlin DSL**:

```kotlin
java {
    sourceCompatibility = JavaVersion.VERSION_{JAVA_VERSION}
    targetCompatibility = JavaVersion.VERSION_{JAVA_VERSION}
}

tasks.compileJava {
    options.encoding = "UTF-8"
    options.compilerArgs.add("-parameters")
}
```

## Jakarta EE 11 Dependencies

**Groovy DSL**:

```groovy
configurations {
    providedCompile
}

dependencies {
    // Jakarta EE 11 API — provided by the Liberty runtime
    providedCompile 'jakarta.platform:jakarta.jakartaee-api:11.0.0'
    // MicroProfile 7 API — provided by Liberty
    providedCompile 'org.eclipse.microprofile:microprofile:7.0'

    // Non-Spring runtime dependencies carried forward from the original build file.
    // Add whichever drivers/clients were present — see "Non-Spring Runtime Dependencies" below.
    // e.g.: runtimeOnly 'com.ibm.db2:jcc:11.5.9.0'

    // Test
    testImplementation 'io.openliberty.tools:microshed-testing-liberty:0.9.2'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.12.2'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}
```

**Kotlin DSL**:

```kotlin
val providedCompile by configurations.creating

dependencies {
    providedCompile("jakarta.platform:jakarta.jakartaee-api:11.0.0")
    providedCompile("org.eclipse.microprofile:microprofile:7.0")

    // Non-Spring runtime dependencies carried forward from the original build file.
    // e.g.: runtimeOnly("com.ibm.db2:jcc:11.5.9.0")

    testImplementation("io.openliberty.tools:microshed-testing-liberty:0.9.2")
    testImplementation("org.junit.jupiter:junit-jupiter:5.12.2")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
```

## Non-Spring Runtime Dependencies

Scan the original `build.gradle` / `build.gradle.kts` for dependencies whose group does **not** start with `org.springframework` and that are not replaced by a Jakarta EE API. Carry them forward unchanged unless a newer version is required. Common examples:

| Dependency | Groovy DSL | Scope |
|---|---|---|
| **IBM DB2 JDBC** | `runtimeOnly 'com.ibm.db2:jcc:{version}'` | `runtimeOnly` |
| **Oracle JDBC** | `runtimeOnly 'com.oracle.database.jdbc:ojdbc11:{version}'` | `runtimeOnly` |
| **PostgreSQL JDBC** | `runtimeOnly 'org.postgresql:postgresql:{version}'` | `runtimeOnly` |
| **MySQL Connector/J** | `runtimeOnly 'com.mysql:mysql-connector-j:{version}'` | `runtimeOnly` |
| **Microsoft SQL Server JDBC** | `runtimeOnly 'com.microsoft.sqlserver:mssql-jdbc:{version}'` | `runtimeOnly` |
| **IBM MQ JMS client** | `runtimeOnly 'com.ibm.mq:com.ibm.mq.allclient:{version}'` | `runtimeOnly` |
| **ActiveMQ client** | `runtimeOnly 'org.apache.activemq:activemq-client:{version}'` | `runtimeOnly` |
| **Apache Kafka client** | `runtimeOnly 'org.apache.kafka:kafka-clients:{version}'` | `runtimeOnly` |
| **Bouncy Castle crypto** | `runtimeOnly 'org.bouncycastle:bcprov-jdk18on:{version}'` | `runtimeOnly` |
| **Lombok** | `compileOnly 'org.projectlombok:lombok:{version}'` | `compileOnly` |
| **MapStruct** | `compileOnly 'org.mapstruct:mapstruct:{version}'` | `compileOnly` |

> **Rule**: If the original build file contains a driver or client library that is not a Spring starter and is not part of Jakarta EE 11 or MicroProfile 7, copy it into the migrated build file with the same (or latest compatible) version and `runtimeOnly` scope. Do not silently drop it.

> **Do NOT use `io.openliberty:openliberty-kernel`**. Always use `io.openliberty:openliberty-runtime` when a Liberty runtime artifact must be referenced. The Liberty server installation is managed by the Liberty Gradle plugin via `server.xml` — do not add it as a dependency.
>
> **Resolve the latest Open Liberty version** by fetching the IBM DHE release index and parsing the highest version directory:
> ```bash
> curl -s https://public.dhe.ibm.com/ibmdl/export/pub/software/openliberty/runtime/release/ \
>   | grep -oP '(?<=href=")[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(?=/)' \
>   | sort -V | tail -1
> ```
> Use the version returned as the `runtimeVersion` property in the Liberty Gradle plugin configuration.

## Jandex Configuration

The `com.github.vlsi.jandex` plugin generates a Jandex index (`META-INF/jandex.idx`) at build time. CDI and JAX-RS on Liberty use this index for fast bean and annotation discovery — without it, Liberty falls back to classpath scanning which is slower and can miss beans in some configurations.

**Groovy DSL** — no extra config needed; the plugin auto-indexes `main` sources:

```groovy
// Applied automatically when the plugin is applied — no block required.
// To customise which source sets are indexed:
jandex {
    processDefaultFileSet = true   // index src/main/java (default: true)
}
```

**Kotlin DSL**:

```kotlin
jandex {
    processDefaultFileSet = true
}
```

The generated index is placed at `build/classes/java/main/META-INF/jandex.idx` and included in the WAR automatically.

## Liberty Plugin Configuration

**Groovy DSL**:

```groovy
liberty {
    server {
        name = 'defaultServer'
        // server.xml is read from src/main/liberty/config/server.xml by default
    }
}
```

**Kotlin DSL**:

```kotlin
liberty {
    server {
        name = "defaultServer"
    }
}
```

## WAR Configuration

Ensure the WAR is built without requiring `web.xml` (Jakarta EE 11 / Servlet 6.1 supports annotation-only configuration):

**Groovy DSL**:
```groovy
war {
    archiveFileName = "${project.name}.war"
}
```

**Kotlin DSL**:
```kotlin
tasks.war {
    archiveFileName.set("${project.name}.war")
}
```

## Liberty Gradle Tasks

| Task | Description |
|---|---|
| `libertyCreate` | Download and create a Liberty server instance |
| `libertyInstallFeature` | Install features declared in `server.xml` |
| `libertyDeploy` | Deploy the WAR to the server |
| `libertyRun` | Start the server in the foreground |
| `libertyStart` | Start the server in the background |
| `libertyStop` | Stop the background server |
| `libertyDev` | **Start in dev mode (hot reload on file change) — use this to test** |
| `libertyPackage` | Package server + app into a runnable JAR |

## Testing the Application

When ready to test, use `libertyDev` to start the server with hot reload, then `libertyStop` when finished:

```bash
# Start the server in dev mode — reloads automatically on source changes
./gradlew libertyDev
```

Press `Enter` in the terminal to run tests while the server is running.

```bash
# Stop the server when done testing
./gradlew libertyStop
```

## Gradle-specific watch out

- **`io.spring.dependency-management` plugin**: Must be removed entirely.
- **`bootJar` / `bootRun` tasks**: These are Spring Boot tasks and no longer exist after removing the plugin. Use `libertyRun` / `libertyDev` instead.
- **`providedCompile` scope**: Gradle does not have `provided` scope by default for the `java` plugin (it exists in `war` plugin). Jakarta EE APIs must be `providedCompile` (or `compileOnly`) so they are not bundled in the WAR — Liberty provides them at runtime.
- **Gradle wrapper**: Always use `./gradlew` if the project has `gradlew`/`gradlew.bat`.
- **Groovy vs Kotlin DSL**: Do not mix `.gradle` and `.gradle.kts` syntax.
- **Multi-project builds**: Apply the Liberty plugin only to the subproject containing the application, not the root project.
