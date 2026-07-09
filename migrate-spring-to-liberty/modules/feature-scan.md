# Module: Feature Scan & server.xml Update

After all migration modules have compiled cleanly, scan the migrated Java sources and configuration files to derive the exact set of Open Liberty features the application needs. Replace the placeholder `jakartaee-11.0` / `microProfile-7.0` umbrella features with a precise, minimal feature list.

A lean `featureManager` block:
- Reduces Liberty's startup time and memory footprint
- Makes the feature surface area explicit and reviewable
- Prevents unexpected feature interactions from unused capabilities

## What to do

- [ ] Scan Java sources for API usage (annotations, imports, types)
- [ ] Scan `persistence.xml` and `server.xml` for JPA and datasource configuration
- [ ] Scan `microprofile-config.properties` for MicroProfile API usage
- [ ] Build the required feature list from the scan results (use the Feature Trigger Table below)
- [ ] Update `src/main/liberty/config/server.xml` — replace umbrella features with the precise list
- [ ] Verify: `./mvnw liberty:install-feature` (Maven) or `./gradlew libertyInstallFeature` (Gradle)
- [ ] Compile: `./mvnw clean compile -DskipTests` (Maven) or `./gradlew clean compileJava -x test` (Gradle)

## Step 1 — Scan the Migrated Application

Run each search against `src/main/` (excluding `src/test/`).

### 1a. Jakarta EE APIs

```bash
# CDI
grep -rn "jakarta.enterprise\|@ApplicationScoped\|@RequestScoped\|@SessionScoped\|@Inject\|@Produces\|@Named\|@Dependent" src/main/java/

# Jakarta REST (JAX-RS)
grep -rn "jakarta.ws.rs\|@Path\|@GET\|@POST\|@PUT\|@DELETE\|@PATCH\|@ApplicationPath\|@Produces\|@Consumes" src/main/java/

# JPA / Persistence
grep -rn "jakarta.persistence\|@Entity\|@PersistenceContext\|@NamedQuery\|EntityManager" src/main/java/
# Also check for persistence.xml
ls src/main/resources/META-INF/persistence.xml 2>/dev/null && echo "persistence.xml found"

# Bean Validation
grep -rn "jakarta.validation\|@NotNull\|@NotBlank\|@Size\|@Min\|@Max\|@Valid\|@Validated" src/main/java/

# Jakarta Transactions
grep -rn "jakarta.transaction\|@Transactional" src/main/java/

# Jakarta Security / Roles
grep -rn "jakarta.annotation.security\|@RolesAllowed\|@DeclareRoles\|@PermitAll\|@DenyAll\|appSecurity\|SecurityContext" src/main/java/

# Jakarta Faces (JSF)
grep -rn "jakarta.faces\|FacesContext\|@ManagedBean\|\.xhtml" src/main/

# Jakarta Servlet
grep -rn "jakarta.servlet\|HttpServlet\|@WebServlet\|@WebFilter" src/main/java/

# Jakarta WebSocket
grep -rn "jakarta.websocket\|@ServerEndpoint\|@ClientEndpoint" src/main/java/

# Jakarta JSON-B
grep -rn "jakarta.json.bind\|@JsonbProperty\|@JsonbTransient\|Jsonb\b" src/main/java/

# Jakarta JSON-P
grep -rn "jakarta.json\b\|JsonObject\|JsonArray\|JsonObjectBuilder" src/main/java/

# Jakarta Mail
grep -rn "jakarta.mail\|@MailSessionDefinition\|Session.*mail" src/main/java/

# Jakarta EJB (timers, scheduling)
grep -rn "jakarta.ejb\|@Singleton\|@Schedule\|@Stateless\|@Stateful\|@MessageDriven" src/main/java/
```

### 1b. MicroProfile APIs

```bash
# MicroProfile Config
grep -rn "@ConfigProperty\|@ConfigProperties\|ConfigProvider" src/main/java/

# MicroProfile Health
grep -rn "@Liveness\|@Readiness\|@Startup\|HealthCheck\b\|HealthCheckResponse" src/main/java/

# MicroProfile Metrics
grep -rn "@Counted\|@Timed\|@Gauge\|@ConcurrentGauge\|@Metered\|MetricRegistry\b" src/main/java/

# MicroProfile JWT
grep -rn "@LoginConfig\|JsonWebToken\|@Claim\|mp\.jwt\." src/main/

# MicroProfile Fault Tolerance
grep -rn "@Retry\|@Timeout\|@Fallback\|@CircuitBreaker\|@Bulkhead\|@Asynchronous" src/main/java/

# MicroProfile OpenAPI
grep -rn "@Operation\|@APIResponse\|@Schema\|@Tag\|@Parameter\b" src/main/java/

# MicroProfile Rest Client
grep -rn "@RegisterRestClient\|RestClientBuilder\|@RestClient" src/main/java/

# MicroProfile Telemetry / OpenTelemetry
grep -rn "opentelemetry\|@WithSpan\|Tracer\b" src/main/java/

# MicroProfile Reactive Messaging
grep -rn "@Incoming\|@Outgoing\|@Channel\|Emitter\b" src/main/java/
```

### 1c. Configuration files

```bash
# Check microprofile-config.properties for mp.jwt or mp.config profile prefixes
cat src/main/resources/META-INF/microprofile-config.properties 2>/dev/null

# Check server.xml for existing dataSource / library definitions
cat src/main/liberty/config/server.xml
```

## Step 2 — Build the Feature List

Use the scan results and the table below to determine which features are required.  
**Do not include a feature if its trigger condition was not found in Step 1.**

### Feature Trigger Table

| If you found … | Add this feature |
|---|---|
| `@ApplicationScoped`, `@Inject`, `@Produces`, `CDI` imports | `cdi-4.1` |
| `@Path`, `@GET/@POST/@PUT/@DELETE/@PATCH`, `@ApplicationPath`, JAX-RS `Application` class | `restfulWS-4.0` + `jsonb-3.0` + `jsonp-2.1` |
| `@Entity`, `@PersistenceContext`, `EntityManager`, `persistence.xml` present | `persistence-3.2` |
| `@NotNull`, `@NotBlank`, `@Valid`, `@Size`, Bean Validation imports | `beanValidation-3.1` |
| `@Transactional` (jakarta.transaction) | `transaction-2.0` |
| `@RolesAllowed`, `@DeclareRoles`, `SecurityContext`, `<basicRegistry>` in server.xml | `appSecurity-5.0` |
| `jakarta.faces.*`, `.xhtml` Facelets templates | `faces-4.1` |
| `jakarta.servlet.*`, `HttpServlet`, `@WebServlet`, `@WebFilter` | `servlet-6.1` |
| `@ServerEndpoint`, `@ClientEndpoint`, WebSocket imports | `websocket-2.2` |
| `jakarta.json.bind.*`, `@JsonbProperty`, `Jsonb` | `jsonb-3.0` |
| `jakarta.json.*`, `JsonObject`, `JsonArray`, `JsonObjectBuilder` | `jsonp-2.1` |
| `jakarta.mail.*` | `mail-2.1` |
| `@Stateless`, `@Stateful`, `@MessageDriven` (full EJB) | `ejb-4.0` |
| `@Singleton` + `@Schedule` (timer only) | `ejbLite-4.0` |
| `@ConfigProperty`, `@ConfigProperties`, `ConfigProvider` | `mpConfig-3.1` |
| `@Liveness`, `@Readiness`, `HealthCheck` | `mpHealth-4.0` |
| `@Counted`, `@Timed`, `@Gauge`, `MetricRegistry` | `mpMetrics-5.1` |
| `@LoginConfig`, `JsonWebToken`, `mp.jwt.*` in config | `mpJwt-2.1` |
| `@Retry`, `@Timeout`, `@Fallback`, `@CircuitBreaker`, `@Bulkhead` | `mpFaultTolerance-4.1` |
| `@Operation`, `@APIResponse`, `@Schema` (OpenAPI) | `mpOpenAPI-4.0` |
| `@RegisterRestClient`, `@RestClient`, `RestClientBuilder` | `mpRestClient-4.0` |
| `@WithSpan`, `Tracer`, OpenTelemetry imports | `mpTelemetry-2.0` |
| `@Incoming`, `@Outgoing`, `@Channel`, `Emitter` (Reactive Messaging) | `mpReactiveMessaging-3.0` |
| `<dataSource>` in server.xml or JDBC driver in WAR | `jdbc-4.3` |
| `<connectionFactory>` or JMS annotations | `messaging-3.0` |
| `@CacheResult`, `@CacheRemove`, `JCache` usage | No Liberty feature required — add the JCache provider as a dependency (e.g., Hazelcast, EhCache) and configure `<cachingProvider>` in `server.xml` |
| `@XmlRootElement`, `@XmlElement`, `@XmlAttribute`, `JAXBContext`, `jakarta.xml.bind.*` imports | `xmlBinding-4.0` + add `jakarta.xml.bind:jakarta.xml.bind-api:4.0.5` (provided) to `pom.xml` |

### JSON serialization note

Always add `jsonb-3.0` and `jsonp-2.1` whenever `restfulWS-4.0` is enabled. This ensures full JSON serialization support (JSON-B for object binding and JSON-P for programmatic JSON building) is available alongside JAX-RS.

### Feature compatibility rules

- **Never mix umbrella and sub-features**: if you keep `jakartaee-11.0`, do **not** also add `cdi-4.1`, `restfulWS-4.0`, etc. — they conflict.
- **`transaction-2.0` is included in `persistence-3.2`** — omit it if `persistence-3.2` is already in the list.
- **`cdi-4.1` is required by almost everything** — if any other feature is present, `cdi-4.1` must also be present.
- **`appSecurity-5.0` requires `cdi-4.1`** — always pair them.
- **`mpJwt-2.1` requires `mpConfig-3.1`** — always add both together.

## Step 3 — Update server.xml

Replace the umbrella feature block with the minimal computed set. The structure stays the same; only the `<featureManager>` content changes.

**Before (umbrella):**
```xml
<featureManager>
    <feature>jakartaee-11.0</feature>
    <feature>microProfile-7.0</feature>
</featureManager>
```

**After (minimal, example for a REST + JPA + Health app):**
```xml
<featureManager>
    <!-- Jakarta EE -->
    <feature>cdi-4.1</feature>
    <feature>restfulWS-4.0</feature>
    <feature>jsonb-3.0</feature>
    <feature>jsonp-2.1</feature>
    <feature>persistence-3.2</feature>
    <feature>beanValidation-3.1</feature>
    <!-- MicroProfile -->
    <feature>mpConfig-3.1</feature>
    <feature>mpHealth-4.0</feature>
</featureManager>
```

Show the proposed `<featureManager>` block to the user with a short rationale for each feature (one line), then ask for confirmation before writing to `server.xml`.

> Here is the minimal feature set derived from scanning the migrated sources:
>
> | Feature | Reason |
> |---|---|
> | `cdi-4.1` | `@ApplicationScoped`, `@Inject` found in X classes |
> | `restfulWS-4.0` | `@Path`, `@GET` found in Y resource classes |
> | `persistence-3.2` | `@Entity`, `persistence.xml` found |
> | … | … |
>
> Shall I update `server.xml` with this list?

Only write the file after the user confirms.

## Step 4 — Install & Verify

After updating `server.xml`, install the declared features and recompile to confirm nothing was missed:

**Maven:**
```bash
./mvnw liberty:install-feature
./mvnw clean compile -DskipTests
```

**Gradle:**
```bash
./gradlew libertyInstallFeature
./gradlew clean compileJava -x test
```

`liberty:install-feature` / `libertyInstallFeature` downloads any feature JARs not already in the local Liberty installation and validates that the feature names are recognised.

If `liberty:install-feature` reports an unknown feature name:
- Check the exact name against the [Open Liberty feature list](https://openliberty.io/docs/latest/reference/feature/feature-overview.html)
- Verify the Liberty version in the plugin configuration supports the feature (e.g., `jakartaee-11.0` requires Open Liberty 24.0.0.6+)
- Correct the name in `server.xml` and re-run

## Watch out

- **Start minimal — add on demand**: If uncertain whether a feature is needed, omit it and add it later when the error `CWWKF0001E` or a missing class error surfaces at runtime.
- **Umbrella features are fine for prototyping**: Switching to a minimal feature set is an optimisation step. If the project is under active development, it is acceptable to keep `jakartaee-11.0` temporarily and revisit this module before production deployment.
- **Feature order does not matter**: Liberty resolves feature dependencies regardless of declaration order in `<featureManager>`.
- **`mpConfig-3.1` is nearly always required**: Any class using `@ConfigProperty` or `@ConfigProperties` needs it — and many MicroProfile features implicitly depend on MicroProfile Config at runtime.
- **Do not add both `ejb-4.0` and `ejbLite-4.0`**: `ejb-4.0` is a superset; use `ejbLite-4.0` for timer/scheduler-only use cases.
