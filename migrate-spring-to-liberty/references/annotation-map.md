# Spring Boot to Jakarta EE 11 Annotation Map

## Contents

- [Dependency injection](#dependency-injection-spring--cdi-41)
- [REST and web](#rest--web-spring-mvc--jakarta-rest--jax-rs-40)
- [Data and persistence](#data--jpa-spring-data--jakarta-jpa-32)
- [Scheduling](#scheduling-spring--jakarta-ee-or-retained-scheduler)
- [Security](#security-spring-security--microprofile-jwt--jakarta-security)
- [Caching](#cache-spring-cache--jcache-provider-or-retained-library)
- [Configuration](#configuration-properties-spring--microprofile-config)
- [Lifecycle](#application-lifecycle)
- [Testing](#testing)

## Dependency Injection (Spring → CDI 4.1)

| Spring | Jakarta EE 11 / CDI 4.1 | Notes |
|---|---|---|
| `@Component` | `@ApplicationScoped` | Default scope for singletons |
| `@Service` | `@ApplicationScoped` | No semantic difference in CDI |
| `@Repository` | `@ApplicationScoped` | No semantic difference in CDI |
| `@Autowired` | `@Inject` (`jakarta.inject.Inject`) | Field, constructor, and setter injection all supported |
| `@Qualifier("name")` | `@Named("name")` (`jakarta.inject.Named`) or custom CDI `@Qualifier` | |
| `@Value("${prop}")` | `@ConfigProperty(name = "prop")` (`org.eclipse.microprofile.config.inject.ConfigProperty`) | Requires MicroProfile Config or `mpConfig` feature |
| `@Value("${prop:default}")` | `@ConfigProperty(name = "prop", defaultValue = "default")` | Inline defaults work |
| `@Configuration` | `@ApplicationScoped` | CDI producer class |
| `@Bean` | `@Produces` (`jakarta.enterprise.inject.Produces`) | Method annotated with `@Produces` in a CDI bean |
| `@Primary` | `@Default` or `@Alternative` + `@Priority` | CDI uses `@Alternative` + `@Priority(1)` to override |
| `@Conditional*` | No portable one-to-one mapping | Model the condition with MicroProfile Config plus a CDI producer/extension, or leave a documented TODO when lifecycle semantics cannot be preserved |
| `@Scope("singleton")` | `@Singleton` (`jakarta.inject.Singleton`) | Eager singleton, no proxy |
| `@Scope("prototype")` | `@Dependent` (`jakarta.enterprise.context.Dependent`) | New instance per injection point |
| `@Scope("request")` | `@RequestScoped` (`jakarta.enterprise.context.RequestScoped`) | Per-HTTP-request lifecycle |
| `@Scope("session")` | `@SessionScoped` (`jakarta.enterprise.context.SessionScoped`) | Per-session lifecycle |
| `@Scope("application")` | `@ApplicationScoped` | Application-wide singleton with proxy |
| `@Lazy` | Default in CDI — all beans are lazy | No annotation needed |
| `@PostConstruct` | `@PostConstruct` (`jakarta.annotation.PostConstruct`) | Same annotation, only package changes from `javax` to `jakarta` |
| `@PreDestroy` | `@PreDestroy` (`jakarta.annotation.PreDestroy`) | Same annotation |

**CDI notes:**
- CDI beans are discovered by default in a bean archive (WAR with `beans.xml` or CDI 4.0+ annotated discovery).
- Constructor injection requires `@Inject` in portable CDI. Do not rely on framework-specific implicit constructor injection.
- `@Inject` on a field performs field injection. Constructor injection is preferred for testability.
- **`DataSource` cannot be injected with `@Inject`** — Liberty's `<dataSource>` is JNDI-bound, not a CDI bean. Use `@Resource(lookup = "jdbc/myapp")` (`jakarta.annotation.Resource`) matching the `jndiName` in `server.xml`.

## REST / Web (Spring MVC → Jakarta REST / JAX-RS 4.0)

| Spring | Jakarta REST 4.0 (JAX-RS) | Notes |
|---|---|---|
| `@RestController` | `@Path` + `@ApplicationScoped` | Class-level path + CDI scope |
| `@Controller` | `@Path` + Jakarta Faces `@Named` backing bean | Only for view-oriented controllers |
| `@RequestMapping("/path")` | `@Path("/path")` | Supports HTTP method, produces, consumes |
| `@GetMapping` | `@GET` | |
| `@PostMapping` | `@POST` | |
| `@PutMapping` | `@PUT` | |
| `@DeleteMapping` | `@DELETE` | |
| `@PatchMapping` | `@PATCH` | |
| `@PathVariable` | `@PathParam` | |
| `@RequestParam` | `@QueryParam` | `defaultValue` attribute supported |
| `@RequestBody` | No annotation needed on parameter | JAX-RS auto-deserializes the entity body |
| `@RequestHeader` | `@HeaderParam` | |
| `@CookieValue` | `@CookieParam` | |
| `@ResponseStatus(HttpStatus.CREATED)` | Return `Response.status(201).entity(...).build()` | |
| `@ExceptionHandler` | `@Provider` + `ExceptionMapper<E>` implementation | |
| `@ControllerAdvice` / `@RestControllerAdvice` | `@Provider` + `ExceptionMapper<E>` | One per exception type |
| `@CrossOrigin` | Configure `<cors>` in `server.xml` | See config-map.md |
| `ResponseEntity<T>` | `jakarta.ws.rs.core.Response` | |
| `HttpStatus.OK` | `Response.Status.OK` | |

**JAX-RS notes:**
- Return type `void` → Liberty sends `204 No Content` automatically
- To produce JSON, annotate with `@Produces(MediaType.APPLICATION_JSON)` — Liberty's JSON-B 3.0 handles serialization
- JAX-RS `@ApplicationPath` on the `Application` class sets the root path

## Data / JPA (Spring Data → Jakarta JPA 3.2)

| Spring | Jakarta JPA 3.2 | Notes |
|---|---|---|
| `@Entity` | `@Entity` (`jakarta.persistence.Entity`) | Same — only package changes |
| `@Table` | `@Table` (`jakarta.persistence.Table`) | Same |
| `@Id` | `@Id` (`jakarta.persistence.Id`) | Same |
| `@GeneratedValue` | `@GeneratedValue` (`jakarta.persistence.GeneratedValue`) | Same |
| `@Column` | `@Column` (`jakarta.persistence.Column`) | Same |
| `@Transactional` | `@Transactional` (`jakarta.transaction.Transactional`) | **NOT** Spring's `@Transactional` |
| `@PersistenceContext` | `@PersistenceContext` (`jakarta.persistence.PersistenceContext`) | Injects `EntityManager` |
| `JpaRepository<T,ID>` | CDI `@ApplicationScoped` bean with `EntityManager` | See code.md for full example |
| `CrudRepository<T,ID>` | CDI `@ApplicationScoped` bean with `EntityManager` | |
| `@Query("JPQL")` | `EntityManager.createQuery(...)` or `@NamedQuery` | JPQL is the same |
| `@Modifying` | `EntityManager.createQuery(...).executeUpdate()` | |
| `@EnableJpaRepositories` | Not needed | CDI + JPA auto-discovered via `persistence.xml` |
| `spring.jpa.hibernate.ddl-auto` | `jakarta.persistence.schema-generation.database.action` in `persistence.xml` | Values: `create`, `drop-and-create`, `create-only`, `drop`, `none` |

**JPA 3.2 naming strategy**: EclipseLink (the JPA provider on Liberty) preserves Java field names as-is — there is no naming strategy equivalent to Spring Boot's `SpringPhysicalNamingStrategy`. To match Spring Boot's snake_case column names, add `@Column` explicitly to each entity field:

```java
@Column(name = "first_name")
private String firstName;
```

## Scheduling (Spring → Jakarta EE or retained scheduler)

| Spring | Jakarta EE / library option | Notes |
|---|---|---|
| `@Scheduled(cron="...")` | Jakarta Enterprise Beans `@Schedule`, or retained Quartz | Verify cron semantics; Spring and EJB expressions are not identical |
| `@Scheduled(fixedRate=1000)` | `ManagedScheduledExecutorService.scheduleAtFixedRate(...)` | Use `concurrent-3.1`; define lifecycle and overlap behavior explicitly |
| `@EnableScheduling` | No direct equivalent | Enable the selected scheduler through its Liberty feature or application configuration |

For simpler scheduling, use Jakarta EJB `@Singleton` + `@Schedule`:

```java
import jakarta.ejb.Schedule;
import jakarta.ejb.Singleton;

@Singleton
public class ScheduledTask {
    @Schedule(second="0", minute="*/5", hour="*", persistent=false)
    public void runEvery5Minutes() {
        // scheduled logic
    }
}
```

Add `enterpriseBeansLite-4.0` or `enterpriseBeans-4.0` to `server.xml` when using EJB timers.

## Security (Spring Security → MicroProfile JWT / Jakarta Security)

| Spring | Jakarta EE 11 / MicroProfile | Notes |
|---|---|---|
| `@Secured("ROLE_ADMIN")` | `@RolesAllowed("ADMIN")` (`jakarta.annotation.security.RolesAllowed`) | Enable `appSecurity-6.0` and design an authentication mechanism |
| `@PreAuthorize("hasRole('ADMIN')")` | `@RolesAllowed("ADMIN")` | |
| `@EnableWebSecurity` | Not needed | Configure in `server.xml` |
| `@AuthenticationPrincipal` | `@Context SecurityContext` (JAX-RS) or `@Inject JsonWebToken` (MicroProfile JWT) | |
| `spring.security.user.name` | `<basicRegistry>` in `server.xml` or LDAP/OIDC configuration | |
| `spring.security.oauth2.resourceserver.jwt.issuer-uri` | `mp.jwt.verify.issuer` in `microprofile-config.properties` | Requires `mpJwt-2.1` feature |

**Jakarta Security 4.0** provides declarative security for REST endpoints:
```java
@DeclareRoles({"admin", "user"})
@Path("/admin")
@RolesAllowed("admin")
@ApplicationScoped
public class AdminResource { ... }
```

## Cache (Spring Cache → JCache provider or retained library)

| Spring | Jakarta EE 11 / MicroProfile | Notes |
|---|---|---|
| `@Cacheable("name")` | JCache (`@CacheResult(cacheName="name")`) | `javax.cache` namespace — add the JCache API and a compatible provider explicitly; it is not part of Jakarta EE 11 |
| `@CacheEvict("name")` | `@CacheRemove(cacheName="name")` | |
| `@EnableCaching` | Not needed | Configure `<cachingProvider>` in `server.xml`; no Liberty `jcache` feature required |

## Configuration Properties (Spring → MicroProfile Config)

| Spring | MicroProfile Config 3.1 | Notes |
|---|---|---|
| `@ConfigurationProperties(prefix="app")` | `@ConfigProperties(prefix="app")` (`org.eclipse.microprofile.config.inject.ConfigProperties`) | Map to a property class with a public zero-argument constructor; verify defaults, conversion, nesting, and validation rather than assuming Spring binding semantics |
| `@Value("${prop}")` | `@ConfigProperty(name = "prop")` | Field injection in CDI bean |
| `@EnableConfigurationProperties` | Not needed | Auto-discovered |
| `@Validated` on config class | `@Valid` | Requires Bean Validation |

## Application Lifecycle

| Spring | Jakarta EE 11 / CDI 4.1 | Notes |
|---|---|---|
| `@SpringBootApplication` | No equivalent needed | Jakarta EE apps have no bootstrap annotation |
| `SpringApplication.run()` | No main class needed | Liberty manages lifecycle |
| `CommandLineRunner` | `@Observes Startup` event (CDI) | `jakarta.enterprise.event.Startup` |
| `ApplicationRunner` | `@Observes Startup` event (CDI) | |
| `@EventListener` | `@Observes` (CDI event) | |

## Testing

| Spring | Jakarta EE 11 / MicroShed | Notes |
|---|---|---|
| `@SpringBootTest` | `@MicroShedTest` | Requires Docker/Podman |
| `@WebMvcTest` | `@MicroShedTest` + REST Assured | |
| `@DataJpaTest` | JUnit 5 + in-memory H2 + `EntityManager` directly | |
| `@MockBean` | Mockito `@Mock` / CDI `@Alternative` + `@Priority(1)` | |
| `@ActiveProfiles("test")` | Liberty server variables / MicroProfile Config overrides | |
| `TestRestTemplate` | MicroShed `@RESTClient` or REST Assured | |
| `@LocalServerPort` | MicroShed `server.getBaseURL()` | |
