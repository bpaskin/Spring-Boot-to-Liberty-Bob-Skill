# JSP, static, and REST-only frontend paths

Load this reference for REST-only applications or Thymeleaf/templates that are not rendered by Spring MVC controllers.

## Contents

- [Determine the rendering owner](#determine-the-rendering-owner)
- [JSP and JSTL path](#jsp-and-jstl-path)
- [REST-only path](#rest-only-path)
- [Verification](#verification)

## Determine the rendering owner

Before replacing a template, find the code, framework, build step, or external service that renders it. A template directory without a Spring MVC controller is ambiguous. It may be dead code, email content, documentation generation, a custom servlet, or a client-side build input. If ownership cannot be established, leave it in place with a migration TODO and mark that path `BLOCKED`.

## JSP and JSTL path

Use JSP/JSTL only after confirming that server-side servlet rendering is intended. Enable `pages-4.0`, place JSP files under `src/main/webapp/WEB-INF/views/`, and forward from a Servlet/controller so views are not directly exposed.

Typical mappings:

| Thymeleaf | JSP/JSTL |
|---|---|
| `${value}` | escaped EL output such as `<c:out>` |
| `th:each` | `<c:forEach>` |
| `th:if` / `th:unless` | `<c:if>` |
| `th:href` / `th:src` | `<c:url>` |
| `th:replace` / fragments | JSP includes or tag files |

Replace form binding, validation messages, localization, and CSRF explicitly. Do not use scriptlets.

## REST-only path

Map `@RestController` resources to Jakarta REST:

| Spring | Jakarta REST |
|---|---|
| `@RestController` | CDI scope plus `@Path` |
| `@GetMapping` | `@GET` plus `@Path` |
| `@PostMapping` | `@POST` plus `@Path` |
| `@RequestBody` | entity/body parameter |
| `ResponseEntity` | `Response` |
| `@RequestParam` | `@QueryParam` |
| `@PathVariable` | `@PathParam` |

Preserve media types, status codes, headers, exception mapping, validation, pagination, CORS, and content negotiation. Register a Jakarta REST application only when the existing Liberty configuration does not already provide one; avoid duplicate base paths.

Static SPA assets are independent of REST controller migration. Preserve their build pipeline, fallback routing, context root, cache headers, and API base URL.

For bearer-token APIs, document why browser CSRF tokens are or are not applicable. Cookie-authenticated APIs still require a CSRF design.

## Verification

Compare representative successful and failing requests with the baseline: status, headers, content type, JSON shape, validation response, authentication, authorization, and CORS. For JSP, also verify render, submit, validation error, redirect, missing/invalid CSRF, and static assets.
