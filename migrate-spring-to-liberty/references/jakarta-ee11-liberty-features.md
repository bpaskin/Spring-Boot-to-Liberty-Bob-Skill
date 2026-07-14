# Jakarta EE 11 Specifications and Open Liberty Features

## Contents

- [Jakarta EE 11 BOM](#quickstart--jakarta-ee-11-bom)
- [Core Profile APIs](#core-profile)
- [Web Profile APIs](#web-profile-adds-to-core-profile)
- [Platform APIs](#platform-adds-to-web-profile)
- [CDI and persistence descriptors](#beansxml--cdi-bean-discovery)
- [Distributed caching](#distributed-caching-with-jcache)
- [Security](#security)
- [MicroProfile 7](#microprofile-7--liberty-features)
- [Typical feature sets](#typical-serverxml-feature-sets)
- [Official references](#official-references)

A reference mapping every Jakarta EE 11 specification to its Open Liberty feature name and Maven/Gradle API coordinates, organised by profile.

Profile membership: **Platform ⊇ Web Profile ⊇ Core Profile**. All Web Profile specs are also in Platform. All Core Profile specs are in both.

---

## Quickstart — Jakarta EE 11 BOM

Instead of declaring each API individually, import the platform BOM and omit versions:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>jakarta.platform</groupId>
            <artifactId>jakarta.jakartaee-bom</artifactId>
            <version>11.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

Or use an all-in-one umbrella artifact:

| Umbrella Artifact | Covers |
|---|---|
| `jakarta.platform:jakarta.jakartaee-api:11.0.0` | Full Platform |
| `jakarta.platform:jakarta.jakartaee-web-api:11.0.0` | Web Profile |
| `jakarta.platform:jakarta.jakartaee-core-api:11.0.0` | Core Profile |

All umbrella artifacts use `<scope>provided</scope>` (Maven) or `compileOnly` (Gradle) — the Liberty runtime provides the implementation.

In `server.xml`, use `jakartaee-11.0` or `webProfile-11.0` as a convenience feature, or select individual features for a smaller runtime surface. Open Liberty does not provide a `coreProfile-11.0` convenience feature.

> **Tip**: Prefer `webProfile-11.0` or a verified individual feature set when the application does not need the full platform.

---

## Core Profile

| Specification | Version | Maven Coordinate | Liberty Feature |
|---|---|---|---|
| Jakarta RESTful Web Services | 4.0 | `jakarta.ws.rs:jakarta.ws.rs-api:4.0.0` | `restfulWS-4.0` |
| Jakarta CDI Lite | 4.1 | `jakarta.enterprise:jakarta.enterprise.cdi-api:4.1.0`<br>`jakarta.enterprise:jakarta.enterprise.lang-model:4.1.0` | `cdi-4.1` |
| Jakarta Dependency Injection | 2.0 | `jakarta.inject:jakarta.inject-api:2.0.1` | `cdi-4.1` (included) |
| Jakarta Interceptors | 2.2 | `jakarta.interceptor:jakarta.interceptor-api:2.2.0` | `cdi-4.1` (included) |
| Jakarta JSON Processing | 2.1 | `jakarta.json:jakarta.json-api:2.1.3` | `jsonp-2.1` |
| Jakarta JSON Binding | 3.0 | `jakarta.json.bind:jakarta.json.bind-api:3.0.1` | `jsonb-3.0` |
| Jakarta Annotations | 3.0 | `jakarta.annotation:jakarta.annotation-api:3.0.0` | n/a (pulled in by various Liberty features) |

---

## Web Profile (adds to Core Profile)

| Specification | Version | Maven Coordinate | Liberty Feature |
|---|---|---|---|
| Jakarta Servlet | 6.1 | `jakarta.servlet:jakarta.servlet-api:6.1.0` | `servlet-6.1` |
| Jakarta Persistence | 3.2 | `jakarta.persistence:jakarta.persistence-api:3.2.0` | `persistence-3.2` |
| Jakarta Faces | 4.1 | `jakarta.faces:jakarta.faces-api:4.1.2` | `faces-4.1` |
| Jakarta Pages | 4.0 | `jakarta.servlet.jsp:jakarta.servlet.jsp-api:4.0.0` | `pages-4.0` |
| Jakarta Standard Tag Library | 3.0 | `jakarta.servlet.jsp.jstl:jakarta.servlet.jsp.jstl-api:3.0.2` | `pages-4.0` (included) |
| Jakarta WebSocket | 2.2 | `jakarta.websocket:jakarta.websocket-api:2.2.0`<br>`jakarta.websocket:jakarta.websocket-client-api:2.2.0` | `websocket-2.2`<br>`websocketClient-2.2` |
| Jakarta Enterprise Beans Lite | 4.0 | `jakarta.ejb:jakarta.ejb-api:4.0.1` | `enterpriseBeansLite-4.0` |
| Jakarta Security | 4.0 | `jakarta.security.enterprise:jakarta.security.enterprise-api:4.0.0` | `appSecurity-6.0` |
| Jakarta Authentication | 3.1 | `jakarta.authentication:jakarta.authentication-api:3.1.0` | `appAuthentication-3.1` |
| Jakarta Expression Language | 6.0 | `jakarta.el:jakarta.el-api:6.0.1` | `expressionLanguage-6.0` |
| Jakarta Validation | 3.1 | `jakarta.validation:jakarta.validation-api:3.1.1` | `validation-3.1` |
| Jakarta Transactions | 2.0 | `jakarta.transaction:jakarta.transaction-api:2.0.1` | `transaction-2.0` |
| Jakarta Concurrency | 3.1 | `jakarta.enterprise.concurrent:jakarta.enterprise.concurrent-api:3.1.1` | `concurrent-3.1` |
| Jakarta CDI (Full) | 4.1 | `jakarta.enterprise:jakarta.enterprise.cdi-api:4.1.0`<br>`jakarta.enterprise:jakarta.enterprise.lang-model:4.1.0`<br>`jakarta.enterprise:jakarta.enterprise.cdi-el-api:4.1.0` | `cdi-4.1` |
| Jakarta Data (**NEW**) | 1.0 | `jakarta.data:jakarta.data-api:1.0.1` | `data-1.0` |

---

## Platform (adds to Web Profile)

| Specification | Version | Maven Coordinate | Liberty Feature |
|---|---|---|---|
| Jakarta Enterprise Beans | 4.0 | `jakarta.ejb:jakarta.ejb-api:4.0.1` | `enterpriseBeans-4.0` |
| Jakarta Messaging | 3.1 | `jakarta.jms:jakarta.jms-api:3.1.0` | `messaging-3.1` |
| Jakarta Mail | 2.1 | `jakarta.mail:jakarta.mail-api:2.1.3` | `mail-2.1` |
| Jakarta Activation | 2.1 | `jakarta.activation:jakarta.activation-api:2.1.3` | `mail-2.1` (included) |
| Jakarta Connectors | 2.1 | `jakarta.resource:jakarta.resource-api:2.1.0` | `connectors-2.1` |
| Jakarta Authorization | 3.0 | `jakarta.authorization:jakarta.authorization-api:3.0.0` | `appAuthorization-3.0` |
| Jakarta Batch | 2.1 | `jakarta.batch:jakarta.batch-api:2.1.1` | `batch-2.1` |

### Optional: Jakarta XML Binding (JAXB)

JAXB is not part of the Jakarta EE 11 Platform profile but may be required if your application binds Java objects to XML. Add it explicitly as a `provided` dependency:

**Maven:**
```xml
<dependency>
    <groupId>jakarta.xml.bind</groupId>
    <artifactId>jakarta.xml.bind-api</artifactId>
    <version>4.0.5</version>
    <scope>provided</scope>
</dependency>
```

**Gradle:**
```groovy
compileOnly 'jakarta.xml.bind:jakarta.xml.bind-api:4.0.5'
```

Enable the corresponding Liberty feature in `server.xml`:

```xml
<featureManager>
    <feature>xmlBinding-4.0</feature>
</featureManager>
```

---

## beans.xml — CDI bean discovery

```xml
<!-- src/main/webapp/WEB-INF/beans.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="https://jakarta.ee/xml/ns/jakartaee"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="https://jakarta.ee/xml/ns/jakartaee
           https://jakarta.ee/xml/ns/jakartaee/beans_4_0.xsd"
       bean-discovery-mode="annotated"
       version="4.0">
</beans>
```

`bean-discovery-mode="annotated"` (CDI 4.0+ default) — only classes annotated with a CDI scope annotation are considered beans. Use `all` only if you need unannotated beans discovered.

---

## persistence.xml skeleton

```xml
<!-- src/main/resources/META-INF/persistence.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<persistence xmlns="https://jakarta.ee/xml/ns/persistence"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="https://jakarta.ee/xml/ns/persistence
                 https://jakarta.ee/xml/ns/persistence/persistence_3_2.xsd"
             version="3.2">
    <persistence-unit name="myapp-pu" transaction-type="JTA">
        <jta-data-source>jdbc/myapp</jta-data-source>
        <properties>
            <property name="jakarta.persistence.schema-generation.database.action" value="create"/>
        </properties>
    </persistence-unit>
</persistence>
```

---

## Bean Validation example

```java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class Product {
    @NotBlank
    @Size(max = 255)
    private String name;

    @Min(0)
    private BigDecimal price;
}
```

Trigger validation in a JAX-RS resource by adding `@Valid` to the parameter:

```java
@POST
@Consumes(MediaType.APPLICATION_JSON)
public Response create(@Valid Product product) { ... }
```

---

## Distributed Caching with JCache

JCache (`javax.cache`) is a standard Java caching API. Open Liberty supports JCache for distributed application caching, HTTP session caching, distributed authentication caching, and distributed logged-out cookie caching.

> **Important**: Liberty does **not** implement JCache itself — there is no `jcache` Liberty feature to enable. Instead, bring in a JCache-compliant provider as a Maven/Gradle dependency and configure it in `server.xml` via `<cachingProvider>`. The `javax.cache` namespace has **not** been migrated to `jakarta.cache` in JCache 1.1 — keep all `javax.cache.*` imports as-is.

Add the JCache provider to `pom.xml` (choose one):

```xml
<!-- Hazelcast -->
<dependency>
    <groupId>com.hazelcast</groupId>
    <artifactId>hazelcast</artifactId>
    <version>5.5.0</version>
</dependency>

<!-- EhCache -->
<dependency>
    <groupId>org.ehcache</groupId>
    <artifactId>ehcache</artifactId>
    <version>3.10.8</version>
</dependency>
```

### Configuration elements

| Element | Purpose |
|---|---|
| `<cachingProvider>` | Configures a single `javax.cache.spi.CachingProvider` instance — loads the provider JAR via a `<library>` reference |
| `<cacheManager>` | Configures a single `javax.cache.CacheManager` — accepts a `uri` for provider-specific config and `<properties>` child elements |
| `<cache>` | Configures a single named `javax.cache.Cache` instance — if the named cache does not exist in the `CacheManager`, Liberty creates it |

### server.xml configuration

Declare a `<library>` pointing to the provider JAR, then configure a `<cache>` with a nested `<cacheManager>` and `<cachingProvider>`:

```xml
<library id="JCacheLib">
    <file name="${shared.resource.dir}/jcacheprovider.jar"/>
</library>

<cache id="SampleCache" name="SampleCache">
    <cacheManager
            uri="file:///${shared.resource.dir}/jcacheconfig.xml">
        <properties
            org.acme.jcache.prop1="value1"
            org.acme.jcache.prop2="value2"/>
        <cachingProvider
            providerClass="org.acme.CachingProvider"
            jCacheLibraryRef="JCacheLib"/>
    </cacheManager>
</cache>
```

- `uri` — path to a provider-specific config file (optional; omit if the provider needs no external config)
- `<properties>` — provider-specific key/value pairs passed to the `CacheManager` (optional)
- `providerClass` — fully-qualified `CachingProvider` implementation; if omitted, Liberty uses the default declared in `META-INF/services/javax.cache.spi.CachingProvider` inside the provider JAR
- `jCacheLibraryRef` — references the `<library>` id that contains the provider JAR

### Multiple caches sharing one CacheManager

When multiple Liberty components (e.g., authentication cache + session cache) share the same provider, define `<cacheManager>` at the top level with an `id` and reference it from each `<cache>` via `cacheManagerRef`:

```xml
<library id="JCacheLib">
    <file name="${shared.resource.dir}/jcacheprovider.jar"/>
</library>

<!-- Built-in Liberty caches that can be distributed via JCache -->
<cache id="io.openliberty.cache.authentication"
       name="io.openliberty.cache.authentication"
       cacheManagerRef="CacheManager"/>
<cache id="io.openliberty.cache.loggedoutcookie"
       name="io.openliberty.cache.loggedoutcookie"
       cacheManagerRef="CacheManager"/>

<cacheManager id="CacheManager">
    <cachingProvider jCacheLibraryRef="JCacheLib"/>
</cacheManager>
```

### JCache use cases in Open Liberty

| Use case | Liberty feature required | Notes |
|---|---|---|
| Application-level caching (`@CacheResult` etc.) | None | Provider dependency + `<cachingProvider>` in `server.xml` |
| Distributed HTTP session caching | `sessionCache-1.0` | Provider dependency + `<cachingProvider>` in `server.xml` |
| Distributed authentication cache | `appSecurity-6.0` | Provider dependency + `<cachingProvider>` in `server.xml` |
| Distributed logged-out cookie tracking | `appSecurity-6.0` | Provider dependency + `<cachingProvider>` in `server.xml` |

> **Provider note**: Any JCache-compliant provider works (Hazelcast, EhCache, Infinispan, Redis via Redisson, etc.). Place the provider JAR in `${shared.resource.dir}/` and reference it via a `<library>` element, or include it in the WAR as a regular compile/runtime dependency.

---

## Security

### Declarative security on a JAX-RS resource

```java
import jakarta.annotation.security.RolesAllowed;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;

@Path("/admin")
@ApplicationScoped
@RolesAllowed("admin")
public class AdminResource {

    @GET
    public String secret() {
        return "admin-only data";
    }
}
```

Add to `server.xml`:

```xml
<featureManager>
    <feature>appSecurity-6.0</feature>
    <feature>restfulWS-4.0</feature>
    <feature>jsonb-3.0</feature>
    <feature>jsonp-2.1</feature>
</featureManager>

<basicRegistry id="basic" realm="BasicRealm">
    <user name="admin" password="adminpass"/>
    <group name="admin">
        <member name="admin"/>
    </group>
</basicRegistry>
```

---

## MicroProfile 7 — Liberty Features

MicroProfile is not part of Jakarta EE but is supported by Open Liberty alongside it. Use the umbrella feature or individual features.

| Specification | Version | Liberty Feature | API Artifact |
|---|---|---|---|
| MicroProfile (umbrella) | 7.0 | `microProfile-7.0` | `org.eclipse.microprofile:microprofile:7.0:pom` |
| MicroProfile Config | 3.1 | `mpConfig-3.1` | `org.eclipse.microprofile.config:microprofile-config-api:3.1` |
| MicroProfile Health | 4.0 | `mpHealth-4.0` | `org.eclipse.microprofile.health:microprofile-health-api:4.0.1` |
| MicroProfile Metrics | 5.1 | `mpMetrics-5.1` | `org.eclipse.microprofile.metrics:microprofile-metrics-api:5.1.1` |
| MicroProfile JWT Auth | 2.1 | `mpJwt-2.1` | `org.eclipse.microprofile.jwt:microprofile-jwt-auth-api:2.1` |
| MicroProfile Fault Tolerance | 4.1 | `mpFaultTolerance-4.1` | `org.eclipse.microprofile.fault-tolerance:microprofile-fault-tolerance-api:4.1.1` |
| MicroProfile OpenAPI | 4.0 | `mpOpenAPI-4.0` | `org.eclipse.microprofile.openapi:microprofile-openapi-api:4.0` |
| MicroProfile Rest Client | 4.0 | `mpRestClient-4.0` | `org.eclipse.microprofile.rest.client:microprofile-rest-client-api:4.0` |
| MicroProfile Telemetry | 2.0 | `mpTelemetry-2.0` | `io.opentelemetry:opentelemetry-api:1.39.0` |
| MicroProfile Reactive Messaging | 3.0 | `mpReactiveMessaging-3.0` | `org.eclipse.microprofile.reactive.messaging:microprofile-reactive-messaging-api:3.0` |

---

## Typical server.xml Feature Sets

### Minimal REST API (Jakarta REST + CDI + JSON-B + JSON-P)

```xml
<featureManager>
    <feature>restfulWS-4.0</feature>
    <feature>jsonb-3.0</feature>
    <feature>jsonp-2.1</feature>
    <feature>cdi-4.1</feature>
</featureManager>
```

### REST API + JPA + Security

```xml
<featureManager>
    <feature>restfulWS-4.0</feature>
    <feature>jsonb-3.0</feature>
    <feature>jsonp-2.1</feature>
    <feature>cdi-4.1</feature>
    <feature>persistence-3.2</feature>
    <feature>validation-3.1</feature>
    <feature>appSecurity-6.0</feature>
    <feature>mpJwt-2.1</feature>
</featureManager>
```

### Full Web Profile (convenience — enables all Web Profile specs)

```xml
<featureManager>
    <feature>webProfile-11.0</feature>
</featureManager>
```

### REST API + MicroProfile observability

```xml
<featureManager>
    <feature>restfulWS-4.0</feature>
    <feature>jsonb-3.0</feature>
    <feature>jsonp-2.1</feature>
    <feature>cdi-4.1</feature>
    <feature>mpHealth-4.0</feature>
    <feature>mpMetrics-5.1</feature>
    <feature>mpConfig-3.1</feature>
    <feature>mpOpenAPI-4.0</feature>
</featureManager>
```

---

## Official References

| Resource | URL |
|---|---|
| Open Liberty Jakarta EE platform and feature names | https://openliberty.io/docs/latest/reference/platform/JakartaEE.html |
| Jakarta EE 11 Specifications | https://jakarta.ee/specifications/platform/11/ |
| Jakarta EE 11 API Javadoc | https://jakarta.ee/specifications/platform/11/apidocs/ |
| Open Liberty Features (IBM Docs) | https://www.ibm.com/docs/en/was-liberty/base?topic=management-liberty-features |
| Open Liberty Distributed Caching with JCache | https://openliberty.io/docs/latest/distributed-caching-jcache.html |
| Open Liberty Guides | https://openliberty.io/guides/ |
| MicroProfile 7.0 Specification | https://microprofile.io/specifications/ |
| Open Liberty Maven Plugin | https://github.com/OpenLiberty/ci.maven |
| Open Liberty GitHub | https://github.com/OpenLiberty/open-liberty |
