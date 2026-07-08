# Spring Boot to Jakarta EE 11 Annotation Map

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
| `@Conditional*` | `@IfBuildProfile` / `@LookupIfProperty` (MicroProfile) | CDI extension or MicroProfile extensions |
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
- Constructor injection works without `@Inject` if there is only one constructor and all parameters are injectable.
- `@Inject` on a field performs field injection. Constructor injection is preferred for testability.

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

**JPA 3.2 naming strategy**: Liberty/Hibernate uses the JPA-compliant default which preserves Java field names. To match Spring Boot's snake_case convention add:
```xml
<property name="hibernate.physical_naming_strategy"
          value="org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy"/>
```

## Scheduling (Spring → MicroProfile Scheduler)

| Spring | MicroProfile Scheduler (`mpScheduler`) | Notes |
|---|---|---|
| `@Scheduled(cron="...")` | `@Scheduled(cron="...")` (`org.eclipse.microprofile.reactive.messaging` OR use Jakarta EE Timer) | Requires `mpScheduler` or EJB `@Schedule` |
| `@Scheduled(fixedRate=1000)` | `@Schedule(second="*/1", ...)` (EJB) or MicroProfile | |
| `@EnableScheduling` | Not needed | Enable via `mpScheduler` feature or EJB |

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

Add `ejbLite-4.0` or `ejb-4.0` feature to `server.xml`.

## Security (Spring Security → MicroProfile JWT / Jakarta Security)

| Spring | Jakarta EE 11 / MicroProfile | Notes |
|---|---|---|
| `@Secured("ROLE_ADMIN")` | `@RolesAllowed("ADMIN")` (`jakarta.annotation.security.RolesAllowed`) | Enable `appSecurity-5.0` feature |
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

## Cache (Spring Cache → MicroProfile LRA / CDI)

| Spring | Jakarta EE 11 / MicroProfile | Notes |
|---|---|---|
| `@Cacheable("name")` | JCache (`@CacheResult`) or manual `Map` cache | Requires `jcache` Liberty feature |
| `@CacheEvict("name")` | `@CacheRemove` | |
| `@EnableCaching` | Not needed | Enable via `jcache` feature in `server.xml` |

## Configuration Properties (Spring → MicroProfile Config)

| Spring | MicroProfile Config 3.1 | Notes |
|---|---|---|
| `@ConfigurationProperties(prefix="app")` | `@ConfigProperties(prefix="app")` (`org.eclipse.microprofile.config.inject.ConfigProperties`) | Interface-based only |
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
