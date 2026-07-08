# Spring Boot to Open Liberty Dependency Map

## Core

| Spring Boot | Open Liberty / Jakarta EE 11 |
|---|---|
| `spring-boot-starter-web` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` (provided) + `restfulWS-4.0` feature |
| `spring-boot-starter-webflux` | `quarkus-rest` with reactive — Liberty uses Jakarta REST 4.0 with `concurrent-3.0` feature for async |
| `spring-boot-starter-data-jpa` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` (provided) + `persistence-3.2` feature |
| `spring-boot-starter-validation` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` (provided) + `beanValidation-3.1` feature |
| `spring-boot-starter-security` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` + `appSecurity-5.0` feature + `<basicRegistry>` or OIDC |
| `spring-boot-starter-actuator` | `org.eclipse.microprofile:microprofile:7.0` (provided) + `mpHealth-4.0` + `mpMetrics-5.1` features |
| `spring-boot-starter-cache` | JCache via `jcache-1.1` Liberty feature + JCache provider (EhCache, Hazelcast) |
| `spring-boot-starter-test` | `io.openliberty.tools:microshed-testing-liberty` + `org.junit.jupiter:junit-jupiter` |

## Data / Persistence

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter-data-mongodb` | `com.mongodb:mongodb-driver-sync` + `mongoDBClient` Liberty feature (or CDI bean) |
| `spring-boot-starter-data-redis` | Lettuce or Jedis client + configure `<connectionFactory>` in `server.xml` |
| `spring-boot-starter-jdbc` | JDBC driver JAR in WAR + `<dataSource>` in `server.xml` |
| `h2` (test DB) | `com.h2database:h2` (test scope) + `jdbc-4.3` feature |
| `postgresql` | `org.postgresql:postgresql` (runtime) + `<dataSource>` in `server.xml` |
| `mysql-connector-j` | `com.mysql:mysql-connector-j` (runtime) + `<dataSource>` in `server.xml` |
| `flyway` | `org.flywaydb:flyway-core` (compile) — no Liberty feature needed, call programmatically or via CDI `@Startup` |
| `liquibase` | `org.liquibase:liquibase-core` (compile) — call programmatically |

### JDBC Driver placement

JDBC drivers can be placed:

1. **Inside the WAR** (`<scope>runtime</scope>` in Maven): simplest, driver is bundled with the app
2. **Shared library** (recommended for production): place the JAR in `${wlp.user.dir}/shared/resources/` and reference via `<library>` in `server.xml`

```xml
<!-- server.xml — shared library approach -->
<library id="PostgreSQLLib">
    <fileset dir="${shared.resource.dir}/postgresql" includes="*.jar"/>
</library>

<dataSource id="DefaultDataSource" jndiName="jdbc/myapp">
    <jdbcDriver libraryRef="PostgreSQLLib"/>
    <properties.postgresql serverName="localhost" portNumber="5432"
                           databaseName="myapp" user="user" password="pass"/>
</dataSource>
```

## Messaging

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter-amqp` | `com.rabbitmq:amqp-client` + MicroProfile Reactive Messaging (`mpReactiveMessaging-3.0` feature) |
| `spring-kafka` | `org.apache.kafka:kafka-clients` + `mpReactiveMessaging-3.0` + Kafka connector |
| `spring-boot-starter-jms` | `messaging-3.0` Liberty feature + configure `<connectionFactory>` in `server.xml` |

## Templating

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter-thymeleaf` | Jakarta Faces 4.1 (`faces-4.1` Liberty feature) — no Maven dep needed, Liberty provides impl |
| `spring-boot-starter-freemarker` | `org.freemarker:freemarker` (compile scope) |

## Scheduling / DI / Config

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter` (DI) | CDI 4.1 included in `jakartaee-11.0` feature |
| `spring-boot-configuration-processor` | MicroProfile Config included in `microProfile-7.0` feature |
| `spring-boot-starter-quartz` | `org.quartz-scheduler:quartz` (compile) or EJB `@Schedule` via `ejbLite-4.0` feature |

## Cloud / Observability

| Spring Boot | Open Liberty |
|---|---|
| `micrometer-registry-prometheus` | `mpMetrics-5.1` Liberty feature (Prometheus-compatible `/metrics` endpoint) |
| `spring-boot-starter-logging` | Liberty's built-in JBoss Logging; configure via `<logging>` in `server.xml` |
| `opentelemetry` | `mpTelemetry-2.0` Liberty feature + `io.opentelemetry:opentelemetry-api` |
| `spring-cloud-starter-config` | MicroProfile Config `mpConfig-3.1` + custom `ConfigSource` implementations |

## Testing

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter-test` | `io.openliberty.tools:microshed-testing-liberty` + JUnit Jupiter |
| `spring-boot-test` (`@SpringBootTest`) | `org.microshed.testing:microshed-testing-liberty` — `@MicroShedTest` |
| `spring-security-test` | REST Assured with auth headers or MicroProfile JWT test tokens |

## Build Plugin

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-maven-plugin` | `io.openliberty.tools:liberty-maven-plugin` |
| `spring-boot-gradle-plugin` | `io.openliberty.tools.gradle.Liberty` Gradle plugin |

## Dependency Syntax by Build Tool

| Maven | Gradle |
|---|---|
| `<dependency>` (default scope) | `implementation 'groupId:artifactId:version'` |
| `<scope>provided</scope>` | `providedCompile 'groupId:artifactId:version'` (WAR plugin) or `compileOnly` |
| `<scope>test</scope>` | `testImplementation 'groupId:artifactId:version'` |
| `<scope>runtime</scope>` | `runtimeOnly 'groupId:artifactId:version'` |

## Jakarta EE 11 API Coordinates

Use the umbrella API artifact (provided scope) for access to all Jakarta EE 11 APIs:

**Maven:**
```xml
<dependency>
    <groupId>jakarta.platform</groupId>
    <artifactId>jakarta.jakartaee-api</artifactId>
    <version>11.0.0</version>
    <scope>provided</scope>
</dependency>

<!-- Jandex — generates META-INF/jandex.idx for fast CDI/JAX-RS annotation discovery -->
<!-- Maven: add io.smallrye:jandex-maven-plugin to <build><plugins>           -->
<!-- Gradle: apply plugin 'com.github.vlsi.jandex' version '1.90'              -->
```

Or individual APIs if you want minimal compile-time surface:

| API | Artifact |
|---|---|
| CDI 4.1 | `jakarta.enterprise:jakarta.enterprise.cdi-api:4.1.0` |
| Jakarta REST 4.0 | `jakarta.ws.rs:jakarta.ws.rs-api:4.0.0` |
| JPA 3.2 | `jakarta.persistence:jakarta.persistence-api:3.2.0` |
| JSON-B 3.0 | `jakarta.json.bind:jakarta.json.bind-api:3.0.1` |
| JSON-P 2.1 | `jakarta.json:jakarta.json-api:2.1.3` |
| Bean Validation 3.1 | `jakarta.validation:jakarta.validation-api:3.1.0` |
| Servlet 6.1 | `jakarta.servlet:jakarta.servlet-api:6.1.0` |
| Transactions 2.0 | `jakarta.transaction:jakarta.transaction-api:2.0.1` |

**MicroProfile 7 API:**
```xml
<dependency>
    <groupId>org.eclipse.microprofile</groupId>
    <artifactId>microprofile</artifactId>
    <version>7.0</version>
    <type>pom</type>
    <scope>provided</scope>
</dependency>
```

Individual MicroProfile APIs:

| API | Artifact |
|---|---|
| MicroProfile Config 3.1 | `org.eclipse.microprofile.config:microprofile-config-api:3.1` |
| MicroProfile Health 4.0 | `org.eclipse.microprofile.health:microprofile-health-api:4.0.1` |
| MicroProfile Metrics 5.1 | `org.eclipse.microprofile.metrics:microprofile-metrics-api:5.1.1` |
| MicroProfile JWT 2.1 | `org.eclipse.microprofile.jwt:microprofile-jwt-auth-api:2.1` |
| MicroProfile Fault Tolerance 4.1 | `org.eclipse.microprofile.fault-tolerance:microprofile-fault-tolerance-api:4.1.1` |
| MicroProfile OpenAPI 4.0 | `org.eclipse.microprofile.openapi:microprofile-openapi-api:4.0` |
