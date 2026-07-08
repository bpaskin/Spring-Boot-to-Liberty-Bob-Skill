# Module: Build System

Migrate the build descriptor and configuration files from Spring Boot to Open Liberty with Jakarta EE 11.

## Instructions

- Detect the build tool by checking which files exist at the project root:

| File | Build tool | Sub-module |
|---|---|---|
| `pom.xml` | Maven | [build-maven.md](build-maven.md) |
| `build.gradle` or `build.gradle.kts` | Gradle | [build-gradle.md](build-gradle.md) |

- Load [references/dependency-map.md](../references/dependency-map.md) and [references/config-map.md](../references/config-map.md) before starting.
- Then load and execute the matching submodule above.
- After the submodule completes, return here and continue with the Configuration Migration and Watch Out sections below.

## Configuration Migration

Spring Boot uses `application.properties` / `application.yml` for runtime configuration. On Open Liberty the primary server configuration lives in `src/main/liberty/config/server.xml`, with runtime values supplied via MicroProfile Config (`src/main/resources/META-INF/microprofile-config.properties`).

### Create server.xml

Create `src/main/liberty/config/server.xml` if it does not exist. Start with the minimum required features and add more as needed:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<server description="Spring Boot to Liberty migration">

    <featureManager>
        <!-- Jakarta EE 11 convenience feature — includes CDI, REST, JPA, Bean Validation, etc. -->
        <feature>jakartaee-11.0</feature>
        <!-- MicroProfile 7 — Config, Health, Metrics, Fault Tolerance, JWT, OpenAPI -->
        <feature>microProfile-7.0</feature>
    </featureManager>

    <!-- HTTP endpoint — default port 9080 (HTTP) and 9443 (HTTPS) -->
    <httpEndpoint id="defaultHttpEndpoint"
                  host="*"
                  httpPort="9080"
                  httpsPort="9443"/>

    <!-- Application deployment -->
    <webApplication location="${server.config.dir}/apps/app.war"
                    contextRoot="${app.context.root}"/>

</server>
```

**Add individual features** instead of the convenience umbrella if you want a leaner server. Common ones:

| Capability | Feature |
|---|---|
| CDI 4.1 | `cdi-4.1` |
| Jakarta REST 4.0 (JAX-RS) | `restfulWS-4.0` |
| JPA 3.2 | `persistence-3.2` |
| JSON-B 3.0 | `jsonb-3.0` |
| Bean Validation 3.1 | `beanValidation-3.1` |
| Transactions 2.0 | `transaction-2.0` |
| MicroProfile Config 3.1 | `mpConfig-3.1` |
| MicroProfile Health 4.0 | `mpHealth-4.0` |
| MicroProfile JWT 2.1 | `mpJwt-2.1` |
| MicroProfile Metrics 5.1 | `mpMetrics-5.1` |
| MicroProfile Fault Tolerance 4.1 | `mpFaultTolerance-4.1` |

### Key property mappings

Migrate Spring properties to Liberty/MicroProfile Config equivalents using config-map.md:

- `server.port` → `<httpEndpoint httpPort="..."/>` in `server.xml`
- `server.servlet.context-path` → `contextRoot` in `<webApplication .../>` or `microprofile-config.properties`
- `spring.datasource.*` → `<dataSource .../>` + `<jdbcDriver .../>` in `server.xml`, or `%prod.` MicroProfile Config props
- `spring.jpa.hibernate.ddl-auto` → `<properties.hibernate.hbm2ddl.auto value="..."/>` in persistence unit
- `logging.level.*` → `<logging .../>` element in `server.xml`

### MicroProfile Config properties

For values that change per environment, use `src/main/resources/META-INF/microprofile-config.properties`:

```properties
# Application context root
app.context.root=/

# Database connection (override via env vars in production)
javax.sql.DataSource.myDS.dataSourceClass=com.mysql.cj.jdbc.MysqlDataSource
javax.sql.DataSource.myDS.url=jdbc:mysql://localhost:3306/mydb
javax.sql.DataSource.myDS.user=root
javax.sql.DataSource.myDS.password=root
```

Environment variable overrides follow MicroProfile's relaxed naming: `APP_CONTEXT_ROOT` overrides `app.context.root`.

## Watch out

- **Port**: Open Liberty defaults to `9080` (HTTP) and `9443` (HTTPS), not `8080`. Update any client configurations accordingly.
- **Context root**: The default context root for a WAR deployed to Liberty is `/<artifactId>`. Set `contextRoot="/"` in `server.xml` if the app expects to be at the root.
- **Naming strategy**: Spring Boot defaults to snake_case column naming (`firstName` → `first_name`). Hibernate on Liberty uses the JPA-compliant default (preserves Java names). Set `hibernate.physical_naming_strategy` in `persistence.xml` if needed: `org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy`.
- **Build tool wrapper**: If the project has `mvnw`/`gradlew`, always use `./mvnw` or `./gradlew`. This ensures reproducible builds.
- **Packaging**: Open Liberty applications are packaged as WAR files and deployed to the Liberty runtime. The `liberty-maven-plugin` / `liberty-gradle-plugin` handle server download, configuration, and deployment automatically.
