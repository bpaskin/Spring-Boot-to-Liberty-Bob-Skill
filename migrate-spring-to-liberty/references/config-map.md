# Spring Boot to Open Liberty Configuration Map

## Contents

- [Server](#server)
- [Datasource](#datasource)
- [Persistence](#jpa--hibernate)
- [Logging](#logging)
- [Profiles](#profiles)
- [CORS](#cors)
- [Cache](#cache)
- [Security](#security)
- [Health](#health-actuator--microprofile-health)
- [Static resources](#static-resources)
- [Templating](#templating)
- [MicroProfile Config profiles](#microprofile-config-profiles)

## Server

| Spring Boot | Open Liberty (`server.xml`) |
|---|---|
| `server.port=9080` | `<httpEndpoint httpPort="9080"/>` |
| `server.servlet.context-path=/api` | `contextRoot="/api"` in `<webApplication/>` |
| `server.ssl.key-store=...` | `<keyStore>` element in `server.xml` |
| `server.compression.enabled=true` | `<httpOptions decompressionEnabled="true"/>` |

**Default ports**: Open Liberty uses `9080` (HTTP) and `9443` (HTTPS) by default. Update any client code, load balancers, and health checks accordingly.

### server.xml httpEndpoint example

```xml
<httpEndpoint id="defaultHttpEndpoint"
              host="*"
              httpPort="9080"
              httpsPort="9443"/>
```

Use Liberty variables to make the port configurable:

```xml
<variable name="httpPort" defaultValue="9080"/>
<httpEndpoint id="defaultHttpEndpoint" host="*" httpPort="${httpPort}" httpsPort="9443"/>
```

Override via environment variable: `httpPort=8080 ./mvnw liberty:dev`

## Datasource

Datasource configuration moves from `application.properties` to `server.xml`. The JDBC driver JAR must be accessible to the Liberty runtime.

```xml
<!-- server.xml -->
<library id="MySQLLib">
    <fileset dir="${shared.resource.dir}/mysql" includes="*.jar"/>
</library>

<dataSource id="DefaultDataSource" jndiName="jdbc/myapp">
    <jdbcDriver libraryRef="MySQLLib"/>
    <properties url="jdbc:mysql://localhost:3306/myapp"
                user="root"
                password="${env.DB_PASSWORD}"/>
</dataSource>
```

| Spring Boot | Open Liberty |
|---|---|
| `spring.datasource.url` | `<properties url="..."/>` in `<dataSource/>` |
| `spring.datasource.username` | `<properties user="..."/>` |
| `spring.datasource.password` | `<properties password="${env.DB_PASSWORD}"/>` |
| `spring.datasource.driver-class-name` | `<jdbcDriver libraryRef="..."/>` (driver auto-detected from URL) |

**Injecting a DataSource into application code**: Liberty's `<dataSource>` is bound to JNDI — it is **not** a CDI bean and cannot be injected with `@Inject`. Use `@Resource` with the matching `jndiName` instead:

```java
import jakarta.annotation.Resource;
import javax.sql.DataSource;

// WRONG — will fail at runtime: CDI cannot resolve a DataSource from server.xml
// @Inject
// private DataSource dataSource;

// CORRECT — inject via JNDI name declared in server.xml <dataSource jndiName="jdbc/myapp">
@Resource(lookup = "jdbc/myapp")
private DataSource dataSource;
```

**Production secrets**: Use Liberty variables or MicroProfile Config to inject credentials from environment variables at runtime:

```xml
<variable name="db.password" value="${env.DB_PASSWORD}"/>
<dataSource ...>
    <properties url="${db.url}" user="${db.user}" password="${db.password}"/>
</dataSource>
```

## JPA / Hibernate

JPA configuration moves from `application.properties` to `persistence.xml`.

| Spring Boot | `persistence.xml` property |
|---|---|
| `spring.jpa.hibernate.ddl-auto=update` | No portable incremental equivalent; default the runtime action to `none` and use a reviewed schema-migration tool |
| `spring.jpa.show-sql=true` | `hibernate.show_sql=true` |
| `spring.jpa.properties.hibernate.dialect` | `hibernate.dialect` (usually auto-detected) |
| `spring.jpa.properties.hibernate.format_sql` | `hibernate.format_sql=true` |
| `spring.jpa.open-in-view=false` | Not applicable (no OSIV in Liberty) |
| `spring.jpa.hibernate.naming.physical-strategy` | `@Column(name="...")` on each entity field |

**Naming strategy warning**: Spring Boot defaults to `SpringPhysicalNamingStrategy` (camelCase → snake_case). EclipseLink (the JPA provider on Liberty) has no equivalent naming strategy hook. Annotate each entity field explicitly with `@Column` to preserve the snake_case column names:

```java
@Column(name = "first_name")
private String firstName;
```

### Schema generation values mapping

| Spring Boot `ddl-auto` | Jakarta EE `schema-generation.database.action` |
|---|---|
| `none` | `none` |
| `validate` | `none`; add an explicit validation step because provider behavior is not equivalent |
| `update` | No portable equivalent; use Flyway, Liquibase, or the existing migration mechanism |
| `create` | Destructive intent; use `drop-and-create` only for the named disposable environment after backup/impact confirmation and explicit approval |
| `create-drop` | Destructive intent; use `drop-and-create` only for the named disposable environment after backup/impact confirmation and explicit approval |

The generated `persistence.xml` must use `none` until the migration contract records a different approved policy. Never infer that a local-looking datasource is disposable.

## Logging

| Spring Boot | Open Liberty (`server.xml`) |
|---|---|
| `logging.level.root=INFO` | `<logging consoleLogLevel="INFO"/>` |
| `logging.level.com.example=DEBUG` | `<logging traceSpecification="com.example.*=debug"/>` |
| `logging.file.name=app.log` | `<logging logDirectory="/logs" traceFileName="trace.log"/>` |
| `logging.pattern.console=...` | `<logging consoleFormat="json"/>` (structured) or `<logging consoleFormat="simple"/>` |

Full example:

```xml
<logging consoleLogLevel="INFO"
         traceSpecification="com.example.*=debug:com.other.*=all"
         consoleFormat="json"
         jsonFieldMappings="ibm_datetime:timestamp;ibm_sequence:seq"/>
```

## Profiles

| Spring Boot | Open Liberty |
|---|---|
| `application-{profile}.properties` | Liberty server variables or separate `server.xml` includes |
| `spring.profiles.active=dev` | `<include location="server-dev.xml"/>` or env var `WLP_SERVER_CONFIG_DIR` |
| `SPRING_PROFILES_ACTIVE=prod` (env var) | `WLP_INSTALL_DIR`, Liberty config dropins |
| `@Profile("dev")` | No portable one-to-one mapping; use MicroProfile Config with a CDI producer/extension, separate deployment configuration, or document a staged-migration TODO |
| `application-test.properties` | Test-scope MicroProfile Config file or `microprofile-config-test.properties` |

MicroProfile Config property sources in priority order (highest first):
1. System properties (`-D` flags)
2. Environment variables
3. `microprofile-config.properties` in `META-INF/`
4. Default values in `@ConfigProperty`

## CORS

| Spring Boot | Open Liberty (`server.xml`) |
|---|---|
| `@CrossOrigin` or `WebMvcConfigurer` | `<cors>` element in `server.xml` |
| `allowed-origins=http://localhost:3000` | `<cors domain="http://localhost:3000" .../>` |
| `allowed-methods=GET,POST` | `allowedMethods="GET, POST"` |

```xml
<cors domain="http://localhost:3000"
      allowedOrigins="http://localhost:3000"
      allowedMethods="GET, POST, PUT, DELETE, OPTIONS"
      allowedHeaders="Content-Type, Authorization"
      exposeHeaders="Content-Type"
      maxAge="3600"/>
```

## Cache

| Spring Boot | Open Liberty |
|---|---|
| `spring.cache.type=caffeine` | JCache provider dependency (Hazelcast, EhCache, etc.) + `<cachingProvider>` in `server.xml` — no Liberty `jcache` feature needed |
| `@Cacheable("name")` | `@CacheResult(cacheName="name")` — uses `javax.cache` annotations (not yet migrated to `jakarta` namespace) |
| `@CacheEvict("name")` | `@CacheRemove(cacheName="name")` |

## Security

These are strategy candidates, not property renames. Follow the [security module](../modules/security.md), confirm the complete security contract, and test behavior before removing Spring configuration.

| Spring Boot | Open Liberty (`server.xml`) |
|---|---|
| `spring.security.user.name` + `spring.security.user.password` | Candidate: reviewed `<basicRegistry>` or another contracted identity source; externalize credentials |
| `spring.security.oauth2.client.*` | Candidate: Jakarta Security annotated OIDC with `appSecurity-6.0`, or Liberty `<openidConnectClient>` with `openidConnectClient-1.0`; choose one owner |
| `spring.security.oauth2.resourceserver.jwt.issuer-uri` | Candidate for compatible JWT bearer tokens: `mp.jwt.verify.issuer` plus complete trust/claim configuration in `microprofile-config.properties` |

### Basic registry example

```xml
<basicRegistry id="basic" realm="BasicRealm">
    <user name="admin" password="${env.BASIC_ADMIN_PASSWORD}"/>
    <user name="user" password="${env.BASIC_USER_PASSWORD}"/>
    <group name="admins">
        <member name="admin"/>
    </group>
</basicRegistry>
```

### MicroProfile JWT configuration

```properties
# microprofile-config.properties
mp.jwt.verify.issuer=https://my-auth-server.example.com
mp.jwt.verify.publickey.location=publicKey.pem
```

## Health (Actuator → MicroProfile Health)

| Spring Boot | Open Liberty |
|---|---|
| `/actuator/health` | `/health` (with `mpHealth-4.0` feature) |
| `/actuator/metrics` | `/metrics` (with `mpMetrics-5.1` feature) |
| `/actuator/info` | Implement an explicit application endpoint or expose build metadata through a documented operational mechanism; there is no `mpInfo` feature |
| `management.endpoints.web.exposure.include=*` | All endpoints auto-exposed at default paths |

```xml
<!-- server.xml — enable health and metrics -->
<featureManager>
    <feature>mpHealth-4.0</feature>
    <feature>mpMetrics-5.1</feature>
</featureManager>
```

Implement custom health checks:

```java
import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.health.HealthCheck;
import org.eclipse.microprofile.health.HealthCheckResponse;
import org.eclipse.microprofile.health.Readiness;

@Readiness
@ApplicationScoped
public class DatabaseHealthCheck implements HealthCheck {
    @Override
    public HealthCheckResponse call() {
        return HealthCheckResponse.named("database").up().build();
    }
}
```

## Static Resources

| Spring Boot | Open Liberty (WAR) |
|---|---|
| `src/main/resources/static/` | `src/main/webapp/` |
| `src/main/resources/public/` | `src/main/webapp/` |
| `spring.web.resources.static-locations` | Liberty always serves from `webapp/` root |

## Templating

| Spring Boot (Thymeleaf) | Open Liberty |
|---|---|
| `spring.thymeleaf.prefix=classpath:/templates/` | Facelets in `src/main/webapp/` |
| `spring.thymeleaf.cache=false` | Faces development mode: `<faces:development/>` in `server.xml` |
| Missing variable → empty string | Missing EL expression → empty string (Facelets) |

## MicroProfile Config Profiles

MicroProfile Config 3.1 supports profiles. Set the active profile via:

```bash
# System property
-Dmp.config.profile=prod

# Environment variable
MP_CONFIG_PROFILE=prod
```

Then in `microprofile-config.properties`:

```properties
# Applied in all profiles
app.name=MyApp

# Applied only when profile=prod
%prod.db.url=jdbc:mysql://prod-host:3306/myapp
%prod.db.password=${env.DB_PASSWORD}

# Applied only when profile=test  
%test.db.url=jdbc:h2:mem:testdb
```
