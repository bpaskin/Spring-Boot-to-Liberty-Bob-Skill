# Module: Feature Scan & server.xml Update

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md); update an existing feature set rather than appending a second one.

If the contract selects retain Spring and rehost, log this module as `SKIP` and stop. The [rehost module](rehost-spring.md) derives the Spring Boot Support and web-container features without interpreting retained Spring imports as Jakarta EE usage.

After all migration modules have compiled cleanly, scan the migrated Java sources and configuration files to derive the exact set of Open Liberty features the application needs. Replace the placeholder `jakartaee-11.0` / `microProfile-7.0` umbrella features with a precise, minimal feature list.

Load [references/jakarta-ee11-liberty-features.md](../references/jakarta-ee11-liberty-features.md) before deriving the list. Treat it as the canonical mapping and verify uncertain feature names against the Open Liberty feature documentation.

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
- [ ] Create the Liberty assembly, then verify features: `./mvnw liberty:create` followed by `./mvnw liberty:install-feature` (Maven), or `./gradlew libertyCreate` followed by `./gradlew libertyInstallFeature` (Gradle)
- [ ] Compile: `./mvnw clean compile -DskipTests` (Maven) or `./gradlew clean compileJava -x test` (Gradle)

## Step 1 — Scan the Migrated Application

Run each search against `src/main/` (excluding `src/test/`).

### 1a. Jakarta EE APIs

```bash
# CDI
grep -rn "jakarta.enterprise\|jakarta.inject\|@ApplicationScoped\|@RequestScoped\|@SessionScoped\|@Inject\|@Named\|@Dependent" src/main/java/

# Jakarta REST (JAX-RS)
grep -rn "jakarta.ws.rs\|@Path\|@GET\|@POST\|@PUT\|@DELETE\|@PATCH\|@ApplicationPath\|@Produces\|@Consumes" src/main/java/

# JPA / Persistence
grep -rn "jakarta.persistence\|@Entity\|@PersistenceContext\|@NamedQuery\|EntityManager" src/main/java/
# Also check for persistence.xml
ls src/main/resources/META-INF/persistence.xml 2>/dev/null && echo "persistence.xml found"

# Jakarta Data repositories
grep -rn "jakarta.data" src/main/java/

# Bean Validation
grep -rn "jakarta.validation\|@NotNull\|@NotBlank\|@Size\|@Min\|@Max\|@Valid\|@Validated" src/main/java/

# Jakarta Transactions
grep -rn "jakarta.transaction\|@Transactional" src/main/java/

# Jakarta Concurrency / CDI events
grep -rn "jakarta.enterprise.concurrent\|ManagedExecutorService\|ManagedScheduledExecutorService\|@Asynchronous\|@Observes\|@ObservesAsync\|Event<" src/main/java/

# Jakarta Security / Roles / annotated OIDC
grep -rn "jakarta.annotation.security\|@RolesAllowed\|@DeclareRoles\|@PermitAll\|@DenyAll\|appSecurity\|SecurityContext\|OpenIdAuthenticationMechanismDefinition" src/main/java/

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

# Jakarta Batch / XML Web Services / Jakarta Messaging
grep -rn "jakarta.batch\|JobOperator\|@BatchProperty\|jakarta.jws\|jakarta.xml.ws\|@WebService\|jakarta.jms\|@JMSConnectionFactoryDefinition" src/main/
```

### 1b. MicroProfile APIs

```bash
# MicroProfile Config
grep -rn "@ConfigProperty\|@ConfigProperties\|ConfigProvider" src/main/java/

# MicroProfile Health
grep -rn "@Liveness\|@Readiness\|HealthCheck\b\|HealthCheckResponse" src/main/java/

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

# Check server.xml for existing datasource, data-provider, registry, JWT, or OIDC settings
cat src/main/liberty/config/server.xml
```

## Step 2 — Build the Feature List

Use the scan results and the table below to determine which features are required.  
**Do not include a feature if its trigger condition was not found in Step 1.**

### Feature Trigger Table

| If you found … | Add this feature |
|---|---|
| CDI scope/injection annotations or `jakarta.enterprise.*` imports | `cdi-4.1` |
| `@Path`, `@GET/@POST/@PUT/@DELETE/@PATCH`, `@ApplicationPath`, JAX-RS `Application` class | `restfulWS-4.0`; add the JSON feature derived from the separate JSON-B/JSON-P rows when the endpoint uses it |
| `@Entity`, `@PersistenceContext`, `EntityManager`, `persistence.xml` present | `persistence-3.2` |
| `jakarta.data.*`, Jakarta Data `@Repository`, `DataRepository`, `BasicRepository`, or `CrudRepository` | `data-1.0`; also add `persistence-3.2` for Jakarta Persistence entities |
| `@NotNull`, `@NotBlank`, `@Valid`, `@Size`, Jakarta Validation imports | `validation-3.1` |
| `@Transactional` (jakarta.transaction) | `transaction-2.0` |
| Jakarta Concurrency imports, managed executors, or Jakarta Concurrency `@Asynchronous` | `concurrent-3.1` |
| `@RolesAllowed`, `@DeclareRoles`, Security APIs, or an authentication configuration in `server.xml` | `appSecurity-6.0` |
| `@OpenIdAuthenticationMechanismDefinition` | `appSecurity-6.0` |
| `<openidConnectClient>` or a contract-selected Liberty-managed browser OIDC client | `openidConnectClient-1.0` |
| `jakarta.faces.*`, `.xhtml` Facelets templates | `faces-4.1` |
| `jakarta.servlet.*`, `HttpServlet`, `@WebServlet`, `@WebFilter` | `servlet-6.1` |
| `@ServerEndpoint`, `@ClientEndpoint`, WebSocket imports | `websocket-2.2` |
| `jakarta.json.bind.*`, `@JsonbProperty`, `Jsonb` | `jsonb-3.0` |
| `jakarta.json.*`, `JsonObject`, `JsonArray`, `JsonObjectBuilder` | `jsonp-2.1` |
| `jakarta.mail.*` | `mail-2.1` |
| `@Stateless`, `@Stateful`, `@MessageDriven` (full Enterprise Beans) | `enterpriseBeans-4.0` |
| `jakarta.ejb.Singleton` + `@Schedule` (timer only) | `enterpriseBeansLite-4.0` |
| Jakarta Batch APIs, job XML, `JobOperator`, `@BatchProperty` | `batch-2.1` |
| `jakarta.jws.*`, `jakarta.xml.ws.*`, `@WebService`, or JAX-WS descriptors | `xmlWS-4.0` |
| Jakarta Messaging consumer implemented as `@MessageDriven` | `messaging-3.1` + `mdb-4.0` and the provider resource adapter |
| `@ConfigProperty`, `@ConfigProperties`, `ConfigProvider` | `mpConfig-3.1` |
| `@Liveness`, `@Readiness`, `HealthCheck` | `mpHealth-4.0` |
| `@Counted`, `@Timed`, `@Gauge`, `MetricRegistry` | `mpMetrics-5.1` |
| `@LoginConfig`, `JsonWebToken`, `mp.jwt.*` in config | `mpJwt-2.1` |
| `@Retry`, `@Timeout`, `@Fallback`, `@CircuitBreaker`, `@Bulkhead` | `mpFaultTolerance-4.1` |
| `@Operation`, `@APIResponse`, `@Schema` (OpenAPI) | `mpOpenAPI-4.0` |
| `@RegisterRestClient`, `@RestClient`, `RestClientBuilder` | `mpRestClient-4.0` |
| MicroProfile Telemetry annotations/configuration or OpenTelemetry integration intended to be container-managed | `mpTelemetry-2.0` |
| `@Incoming`, `@Outgoing`, `@Channel`, `Emitter` (Reactive Messaging) | `mpReactiveMessaging-3.0` |
| `<dataSource>` in server.xml or JDBC driver in WAR | `jdbc-4.3` |
| `<connectionFactory>` or Jakarta Messaging annotations | `messaging-3.1` |
| `@CacheResult`, `@CacheRemove`, `JCache` usage | No Liberty feature required — add the JCache provider as a dependency (e.g., Hazelcast, EhCache) and configure `<cachingProvider>` in `server.xml` |
| `@XmlRootElement`, `@XmlElement`, `@XmlAttribute`, `JAXBContext`, `jakarta.xml.bind.*` imports | `xmlBinding-4.0` + add `jakarta.xml.bind:jakarta.xml.bind-api:4.0.5` (provided) to `pom.xml` |

### JSON serialization note

Add `jsonb-3.0` when REST endpoints bind JSON objects, records, collections, or maps, or use JSON-B APIs/annotations. Add `jsonp-2.1` directly only for programmatic JSON-P use when `jsonb-3.0` is absent. Open Liberty's `jsonb-3.0` feature already enables `jsonp-2.1`, so declaring both is redundant. Plain text/HTML REST endpoints need neither JSON feature unless another source trigger requires it.

### Feature compatibility rules

- **Avoid redundant umbrella and sub-features**: if you keep `jakartaee-11.0`, omit the individual Jakarta EE features it already enables. Redundancy obscures the intended runtime surface; incompatible versions are the actual conflict.
- **`jsonb-3.0` already enables `jsonp-2.1`** — declare only `jsonb-3.0` when both APIs are needed; declare `jsonp-2.1` alone for programmatic JSON-P without JSON-B.
- **`transaction-2.0` is included in `persistence-3.2`** — omit it if `persistence-3.2` is already in the list.
- **`data-1.0` includes Open Liberty's relational Jakarta Data provider** — use it for migrated repository interfaces. `dataContainer-1.0` exposes only the Jakarta Data API and is valid only when the application deliberately supplies another provider.
- **Every Jakarta Data repository needs a reviewed datastore binding** — resolve its `@Repository(dataStore = "...")` value to a persistence-unit reference, datasource, or `databaseStore`. Do not rely on `java:comp/DefaultDataSource` accidentally. Keep `createTables` and `dropTables` disabled unless the destructive-action gate was explicitly satisfied.
- **`cdi-4.1` is required by almost everything** — if any other feature is present, `cdi-4.1` must also be present.
- **`appSecurity-6.0` requires an authentication design** — do not infer a registry, OIDC provider, or JWT trust configuration from authorization annotations alone.
- **Choose one browser OIDC owner** — annotated Jakarta Security OIDC uses `appSecurity-6.0`; an explicit Liberty-managed client uses `openidConnectClient-1.0`. Do not configure both for the same entry point.
- **`mpJwt-2.1` requires `mpConfig-3.1`** — always add both together.
- **Executor presence is not enough to infer defaults** — `concurrent-3.1` supplies managed execution, but pool, queue, context, rejection, and shutdown behavior still come from the async/events contract.
- **`mpFaultTolerance-4.1` does not reproduce Spring Retry listeners or recovery mechanically** — add it only after the retry contract selects MicroProfile Fault Tolerance.
- **Messaging features do not select a broker/provider automatically** — `mpReactiveMessaging-3.0` has a Liberty Kafka connector; `messaging-3.1` requires an actual Jakarta Connectors provider/resource adapter. Follow the messaging contract.
- **`batch-2.1` does not prove Spring Batch restart parity** — require a reviewed job repository and crash/checkpoint/restart tests before removing Spring Batch.
- **XML Binding is not a SOAP runtime** — use `xmlWS-4.0` for a selected Jakarta XML Web Services endpoint/client design; do not map Spring-WS to `xmlBinding-4.0` alone.

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
    <feature>persistence-3.2</feature>
    <feature>validation-3.1</feature>
    <!-- MicroProfile -->
    <feature>mpConfig-3.1</feature>
    <feature>mpHealth-4.0</feature>
</featureManager>
```

Show the proposed `<featureManager>` block with a short rationale for each feature (one line). If it follows the confirmed contract and only removes unused placeholder features, update `server.xml` as part of the authorized migration without another pause.

> Here is the minimal feature set derived from scanning the migrated sources:
>
> | Feature | Reason |
> |---|---|
> | `cdi-4.1` | `@ApplicationScoped`, `@Inject` found in X classes |
> | `restfulWS-4.0` | `@Path`, `@GET` found in Y resource classes |
> | `persistence-3.2` | `@Entity`, `persistence.xml` found |
> | … | … |
>
Ask before writing only when the scan introduces a capability not covered by the contract, removes a feature that may be needed through descriptors/reflection, or changes a security/messaging/data behavior. Record the final feature evidence in the migration ledger.

## Step 4 — Install & Verify

After updating `server.xml`, install the declared features and recompile to confirm nothing was missed:

**Maven:**
```bash
./mvnw liberty:create
./mvnw liberty:install-feature
./mvnw clean compile -DskipTests
```

**Gradle:**
```bash
./gradlew libertyCreate
./gradlew libertyInstallFeature
./gradlew clean compileJava -x test
```

`liberty:create` / `libertyCreate` first installs the configured Liberty assembly and creates the server. `liberty:install-feature` / `libertyInstallFeature` requires that pre-installed assembly; it then downloads any feature JARs not already in the local Liberty installation and validates that the feature names are recognised. Use the detected build launcher, and repeat the create step when the local assembly is missing or the pinned Liberty version changes.

If `liberty:install-feature` reports an unknown feature name:
- Check the exact name against the [Open Liberty feature list](https://openliberty.io/docs/latest/reference/feature/feature-overview.html)
- Verify the selected Liberty runtime supports every declared feature. Do not rely on a hard-coded first-supported release; run the feature-install goal against the pinned runtime.
- Correct the name in `server.xml` and re-run

## Watch out

- **Start minimal — add on demand**: If uncertain whether a feature is needed, omit it and add it later when the error `CWWKF0001E` or a missing class error surfaces at runtime.
- **Umbrella features are fine for prototyping**: Switching to a minimal feature set is an optimisation step. If the project is under active development, it is acceptable to keep `jakartaee-11.0` temporarily and revisit this module before production deployment.
- **Feature order does not matter**: Liberty resolves feature dependencies regardless of declaration order in `<featureManager>`.
- **`mpConfig-3.1` is nearly always required**: Any class using `@ConfigProperty` or `@ConfigProperties` needs it — and many MicroProfile features implicitly depend on MicroProfile Config at runtime.
- **Do not add both `enterpriseBeans-4.0` and `enterpriseBeansLite-4.0`**: the full feature is a superset; use the Lite feature for supported timer/scheduler-only use cases.
