# Spring Boot to Open Liberty Dependency Map

## Contents

- [Core](#core)
- [Data and persistence](#data--persistence)
- [Third-party library placement](#third-party-library-placement)
- [Messaging](#messaging)
- [Templating](#templating)
- [Scheduling, DI, and configuration](#scheduling--di--config)
- [Cloud and observability](#cloud--observability)
- [Testing](#testing)
- [Build plugins](#build-plugin)
- [Jakarta EE API coordinates](#jakarta-ee-11-api-coordinates)

## Core

| Spring Boot | Open Liberty / Jakarta EE 11 |
|---|---|
| `spring-boot-starter-web` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` (provided) + `restfulWS-4.0` feature |
| `spring-boot-starter-webflux` | No mechanical equivalent. Preserve behavior requirements, then redesign with Jakarta REST asynchronous APIs plus `concurrent-3.1`, or keep a supported reactive library. Flag Reactor-specific pipelines for manual migration. |
| `spring-boot-starter-data-jpa` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` (provided) + `persistence-3.2` feature |
| `spring-boot-starter-validation` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` (provided) + `validation-3.1` feature |
| `spring-boot-starter-security` | `jakarta.platform:jakarta.jakartaee-api:11.0.0` + `appSecurity-6.0` feature + an explicitly designed registry, OIDC, or JWT configuration |
| `spring-boot-starter-actuator` | `org.eclipse.microprofile:microprofile:7.0` (provided) + `mpHealth-4.0` + `mpMetrics-5.1` features |
| `spring-boot-starter-cache` | JCache provider dependency (e.g., `com.hazelcast:hazelcast` or `org.ehcache:ehcache`) + `<cachingProvider>` in `server.xml` — **no Liberty `jcache` feature needed** |
| `spring-boot-starter-ws` / `javax.xml.bind:jaxb-api` / `jakarta.xml.bind:jakarta.xml.bind-api` | `jakarta.xml.bind:jakarta.xml.bind-api:4.0.5` (provided) + `xmlBinding-4.0` feature |
| `spring-boot-starter-test` | `org.microshed:microshed-testing-liberty` + `org.junit.jupiter:junit-jupiter` |

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

### Third-party Library Placement

When a driver or client library must be visible to the Liberty runtime (not just bundled inside the WAR), copy its JARs into a dedicated subdirectory under the server's `lib/` folder and declare a matching `<library>` element in `server.xml`. Each product gets its own subdirectory so libraries remain isolated and easy to update independently.

#### Directory convention

```
<server_name>/
└── lib/
    ├── db2/          ← IBM DB2 JDBC driver JARs
    ├── mq/           ← IBM MQ client JARs
    ├── oracle/       ← Oracle JDBC driver JARs
    ├── postgresql/   ← PostgreSQL JDBC driver JARs
    └── <product>/    ← any other third-party library
```

The Liberty variable `${server.config.dir}` resolves to the server's root directory (e.g. `wlp/usr/servers/<server_name>/`). Use it to keep paths portable across installations.

#### When to use each placement option

| Option | How | When to use |
|---|---|---|
| **Inside the WAR** | `<scope>runtime</scope>` (Maven) / `runtimeOnly` (Gradle) | Simple apps, no Liberty-managed data sources or connection factories |
| **Server lib directory** | Copy JARs to `lib/<product>/`, declare `<library>` in `server.xml` | Recommended for JDBC drivers, MQ clients, and any library referenced by a Liberty `<dataSource>`, `<connectionFactory>`, or `<jmsConnectionFactory>` |
| **Shared resources** | `${shared.resource.dir}/<product>/` | Same JARs shared across multiple servers in one Liberty installation |

> **Rule**: If `server.xml` has a `<dataSource>`, `<connectionFactory>`, or `<jmsConnectionFactory>` that needs a driver, the JARs **must** be in a `<library>` — Liberty cannot see inside the WAR for those elements.

---

### IBM DB2

Copy `db2jcc4.jar` (and `db2jcc_license_cu.jar` if required) to `<server_name>/lib/db2/`.

```xml
<!-- server.xml -->
<library id="DB2Lib">
    <fileset dir="${server.config.dir}/lib/db2" includes="*.jar"/>
</library>

<dataSource id="DefaultDataSource" jndiName="jdbc/myapp">
    <jdbcDriver libraryRef="DB2Lib"/>
    <properties.db2.jcc serverName="localhost" portNumber="50000"
                        databaseName="myapp" user="db2user" password="db2pass"/>
</dataSource>
```

Maven dependency (compile/test only — do **not** bundle in the WAR when using the lib directory):
```xml
<dependency>
    <groupId>com.ibm.db2</groupId>
    <artifactId>jcc</artifactId>
    <version>11.5.9.0</version>
    <scope>provided</scope>  <!-- provided = on Liberty classpath via <library>, not in WAR -->
</dependency>
```

---

### IBM MQ

Copy `com.ibm.mq.allclient.jar` (and `com.ibm.mq.jakarta.client.jar` for Jakarta EE) to `<server_name>/lib/mq/`.

```xml
<!-- server.xml -->
<library id="MQLib">
    <fileset dir="${server.config.dir}/lib/mq" includes="*.jar"/>
</library>

<jmsConnectionFactory id="MQConnectionFactory" jndiName="jms/MQFactory">
    <properties.wmqJms
        hostName="localhost"
        port="1414"
        channel="DEV.APP.SVRCONN"
        queueManager="QM1"
        transportType="CLIENT"/>
    <connectionManager maxPoolSize="10"/>
</jmsConnectionFactory>
```

Add the `messaging-3.1` and `wmqJmsClient-3.0` Liberty features:
```xml
<featureManager>
    <feature>messaging-3.1</feature>
    <feature>wmqJmsClient-3.0</feature>
</featureManager>
```

Maven dependency (provided scope — JARs are in `lib/mq/`, not in the WAR):
```xml
<dependency>
    <groupId>com.ibm.mq</groupId>
    <artifactId>com.ibm.mq.allclient</artifactId>
    <version>9.4.1.0</version>
    <scope>provided</scope>
</dependency>
```

---

### Oracle JDBC

Copy `ojdbc11.jar` to `<server_name>/lib/oracle/`.

```xml
<!-- server.xml -->
<library id="OracleLib">
    <fileset dir="${server.config.dir}/lib/oracle" includes="*.jar"/>
</library>

<dataSource id="DefaultDataSource" jndiName="jdbc/myapp">
    <jdbcDriver libraryRef="OracleLib"/>
    <properties.oracle URL="jdbc:oracle:thin:@localhost:1521:ORCL"
                       user="appuser" password="apppass"/>
</dataSource>
```

---

### PostgreSQL JDBC

Copy `postgresql-{version}.jar` to `<server_name>/lib/postgresql/`.

```xml
<!-- server.xml -->
<library id="PostgreSQLLib">
    <fileset dir="${server.config.dir}/lib/postgresql" includes="*.jar"/>
</library>

<dataSource id="DefaultDataSource" jndiName="jdbc/myapp">
    <jdbcDriver libraryRef="PostgreSQLLib"/>
    <properties.postgresql serverName="localhost" portNumber="5432"
                           databaseName="myapp" user="user" password="pass"/>
</dataSource>
```

---

### Other Libraries (general pattern)

For any other third-party library that Liberty must load directly (e.g. a custom LDAP provider, a JCA connector, a cryptography provider):

1. Create `<server_name>/lib/<product>/`
2. Copy the required JARs into that directory
3. Declare a `<library>` in `server.xml` pointing to it
4. Reference the library from the relevant Liberty config element via `libraryRef`

```xml
<!-- server.xml — generic pattern -->
<library id="MyProductLib">
    <fileset dir="${server.config.dir}/lib/<product>" includes="*.jar"/>
</library>
```

## Messaging

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter-amqp` | `com.rabbitmq:amqp-client` + MicroProfile Reactive Messaging (`mpReactiveMessaging-3.0` feature) |
| `spring-kafka` | `org.apache.kafka:kafka-clients` + `mpReactiveMessaging-3.0` + Kafka connector |
| `spring-boot-starter-jms` | `messaging-3.1` Liberty feature + configure `<connectionFactory>` in `server.xml` |

## Templating

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter-thymeleaf` | **Option A (recommended):** Jakarta Faces 4.1 (`faces-4.1` Liberty feature) — no Maven dep needed, Liberty provides impl; see [frontend.md Option B](../modules/frontend.md) |
| `spring-boot-starter-thymeleaf` | **Option B (keep Thymeleaf):** `org.thymeleaf:thymeleaf:3.1.3.RELEASE` (compile scope, bundled in WAR) — remove `thymeleaf-spring6`; wire `TemplateEngine` via CDI; see [frontend.md Option C](../modules/frontend.md) |
| `spring-boot-starter-freemarker` | `org.freemarker:freemarker` (compile scope) |

## Scheduling / DI / Config

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter` (DI) | CDI 4.1 included in `jakartaee-11.0` feature |
| `spring-boot-configuration-processor` | MicroProfile Config included in `microProfile-7.0` feature |
| `spring-boot-starter-quartz` | Preserve Quartz when jobs require its semantics, or migrate simple schedules to Jakarta Enterprise Beans `@Schedule` via `enterpriseBeansLite-4.0` |

## Cloud / Observability

| Spring Boot | Open Liberty |
|---|---|
| `micrometer-registry-prometheus` | `mpMetrics-5.1` Liberty feature (Prometheus-compatible `/metrics` endpoint) |
| `spring-boot-starter-logging` | Liberty logging and Java Util Logging; preserve an application logging facade only when required and configure Liberty `<logging>` explicitly |
| `opentelemetry` | `mpTelemetry-2.0` Liberty feature + `io.opentelemetry:opentelemetry-api` |
| `spring-cloud-starter-config` | MicroProfile Config `mpConfig-3.1` + custom `ConfigSource` implementations |

## Testing

| Spring Boot | Open Liberty |
|---|---|
| `spring-boot-starter-test` | `org.microshed:microshed-testing-liberty` + JUnit Jupiter |
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
