# Server-rendered views with Jakarta MVC and Krazo

Load this reference only when the migration contract selects Jakarta MVC for Spring MVC views.

## Contents

- [Dependencies and features](#dependencies-and-features)
- [Controller mapping](#controller-mapping)
- [Template migration](#template-migration)
- [Security and verification](#security-and-verification)

## Dependencies and features

Resolve a Jakarta EE 11-compatible Jakarta MVC API and Krazo implementation from official project metadata. Pin verified versions in one build property; do not copy a stale example version. Provide the Jakarta MVC API at compile time and package the Krazo runtime modules required by the chosen servlet/JSP integration.

Use only the Liberty features justified by the migrated code, typically:

```xml
<featureManager>
    <feature>cdi-4.1</feature>
    <feature>servlet-6.1</feature>
    <feature>pages-4.0</feature>
    <feature>validation-3.1</feature>
</featureManager>
```

Add JSON-B/JSON-P/REST features only when the application uses them. Verify the exact feature list through the feature-scan module.

## Controller mapping

Map action-based concepts deliberately:

| Spring MVC | Jakarta MVC |
|---|---|
| `@Controller` | CDI scope plus `@Controller` |
| `@GetMapping("/todos")` | `@GET @Path("/todos")` |
| `@PostMapping` | `@POST` plus the same path |
| `Model.addAttribute` | `Models.put` |
| method return view name | `return "view-name"` |
| `RedirectView` / `redirect:` | Jakarta MVC redirect/navigation response |
| `@RequestParam` | `@QueryParam` or `@FormParam` |
| `@PathVariable` | `@PathParam` |
| `@Valid` and `BindingResult` | Bean Validation plus explicit violation/model handling |

Use portable CDI constructor injection with `@Inject`. Preserve route methods, parameter names, validation behavior, redirects, flash-message semantics, and response codes. Do not mechanically translate annotations while dropping Spring MVC interceptors, binders, converters, exception handlers, locale handling, or multipart behavior; inventory and redesign each one.

## Template migration

Place JSP views under `src/main/webapp/WEB-INF/views/` so clients cannot request them directly. Configure the Krazo view-engine path explicitly and preserve the existing logical view names.

Translate Thymeleaf expressions by behavior, not text substitution:

| Thymeleaf | JSP/JSTL |
|---|---|
| `${value}` | `${value}` with escaped output where needed |
| `th:each` | `<c:forEach>` |
| `th:if` / `th:unless` | `<c:if>` with the appropriate condition |
| `th:href` / `th:src` | `<c:url>` |
| `th:field` | explicit form name/value/error rendering |
| fragments/layout dialects | JSP includes/tag files or an explicitly selected layout mechanism |

Preserve HTML escaping. Treat raw/unescaped rendering as a security-sensitive exception and test it.

## Security and verification

Implement CSRF protection before removing Spring tokens. Ensure the Jakarta Security authentication mechanism and role checks are applied to the same routes. Test anonymous, authenticated, unauthorized, valid-CSRF, missing-CSRF, and invalid-CSRF paths where applicable.

Verify at least one successful render, validation failure, form submission, redirect, missing resource, and static asset. Compare the response status, content type, route, and user-visible result with the baseline.
