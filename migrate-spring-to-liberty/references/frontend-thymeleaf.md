# Retaining core Thymeleaf on Liberty

Load this reference only when the migration contract explicitly retains Thymeleaf.

Apply the shared [binding-expression contract](frontend-binding-expressions.md) when Spring MVC or the Thymeleaf Spring dialect owns form population, conversion, validation, or error rendering.

## Contents

- [Dependencies](#dependencies)
- [CDI integration](#cdi-integration)
- [Controller path](#controller-path)
- [Spring-specific features](#spring-specific-features)
- [Security and verification](#security-and-verification)

## Dependencies

Remove `thymeleaf-spring*` and Spring Security dialect artifacts. Resolve and pin a Jakarta-compatible core Thymeleaf version. Package it in the WAR because Liberty does not provide Thymeleaf.

## CDI integration

Create one application-scoped producer/configuration for `TemplateEngine`. Use a servlet-context template resolver, UTF-8, HTML mode, caching appropriate to the environment, and a prefix/suffix matching the migrated template location. Do not create a new engine per request.

```java
@ApplicationScoped
public class ThymeleafConfig {
    @Produces
    @ApplicationScoped
    TemplateEngine templateEngine(ServletContext context) {
        WebApplicationTemplateResolver resolver = createResolver(context);
        TemplateEngine engine = new TemplateEngine();
        engine.setTemplateResolver(resolver);
        return engine;
    }
}
```

Use the actual Thymeleaf Jakarta web integration API selected by the pinned version; verify the example compiles instead of guessing package names.

## Controller path

Replace Spring MVC controllers with either:

- a Servlet that builds the Thymeleaf web context and writes the response, or
- a Jakarta REST/Servlet bridge whose ownership, response buffering, status codes, and redirects are explicit.

Prefer a Servlet for server-rendered form workflows. Preserve routes, request encoding, model names, form binding, validation errors, redirect semantics, locale, and exception behavior. Use CDI `@Inject` for services.

## Spring-specific features

Inventory and replace every Spring-only expression/dialect before removing dependencies:

- `sec:*` attributes and Spring Security authorization objects
- Spring MVC form binding and `BindingResult`
- Spring message-source integration
- Spring URL/context helpers
- Spring EL objects and conversion service
- layout dialects or custom processors tied to Spring

Do not claim complete Spring removal while any Spring dialect remains.

## Security and verification

Core Thymeleaf does not recreate Spring Security CSRF integration. Implement an explicit synchronizer-token or equivalent application/container filter for cookie-authenticated browser flows. Generate the token, bind it to the user session, render it, validate it before state change, and rotate it according to the selected design.

Test valid, missing, and invalid tokens; anonymous and forbidden access; escaping; form validation; redirect; and representative static assets. Confirm no `org.thymeleaf.spring*`, `sec:*`, `_csrf`, or Spring expression objects remain unless the staged contract documents them.
