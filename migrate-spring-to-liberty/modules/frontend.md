# Module: Frontend / View Layer

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md).

If the contract selects retain Spring and rehost, log this module as `SKIP` and stop. Preserve Spring MVC, Thymeleaf, templates, static assets, and CSRF integration for parity testing.

Classify the view layer, load exactly one scenario reference, preserve browser behavior, and implement the CSRF contract established by the [security module](security.md) before removing Spring integration. When Spring MVC binding evidence is present, also load the shared [binding-expression reference](../references/frontend-binding-expressions.md). Do not independently choose a new authentication, CSRF, CORS, session, or logout policy here.

## What to do

- [ ] Re-read the migration contract and current source; do not repeat an answered view question
- [ ] Classify the application using semantic evidence, not template paths alone
- [ ] Load only the selected scenario reference
- [ ] Inventory and replace controller/template binding as one contract; preserve submitted values, conversion, validation, errors, and allowed fields
- [ ] Preserve routes, form methods, validation messages, redirects, content types, and static-asset URLs
- [ ] Replace and negative-test CSRF protection before removing Spring tokens
- [ ] Compile with the detected build launcher and update the module ledger

## Detection and routing

| Scenario | Evidence | Load |
|---|---|---|
| Server-rendered Spring MVC | `@Controller`, `Model`/`ModelAndView`, view-name returns, MVC config, Thymeleaf templates used by controllers, `@ModelAttribute`/`BindingResult`/`@InitBinder`, `th:field`/`#fields`, or Spring JSP form tags | The one contract-selected reference: [Jakarta MVC](../references/frontend-jakarta-mvc.md), [Jakarta Faces](../references/frontend-faces.md), or [retained Thymeleaf](../references/frontend-thymeleaf.md); also load [binding expressions](../references/frontend-binding-expressions.md) when detected |
| Thymeleaf without Spring MVC controllers | Templates exist but no server-rendered `@Controller`; determine who renders them before editing | [JSP and REST paths](../references/frontend-jsp-rest.md) |
| REST-only | `@RestController`/HTTP APIs with no server-rendered views; static SPA assets may still exist | [JSP and REST paths](../references/frontend-jsp-rest.md) |
| Static assets only | Files under `static/`, `public/`, or equivalent with no server-side view engine | This module's static-assets section only |

If evidence is mixed, mark the gate `PARTIAL`, list each route/controller/template, and select a path per coherent view stack. Do not default to JSP merely because the rendering owner is unclear. If the contract lacks a required view choice, present the three choices once and wait:

- Jakarta MVC + Krazo: closest action-based mapping; extra runtime dependencies
- Jakarta Faces + CDI: Liberty-native component model; larger template rewrite
- Retain core Thymeleaf: smallest template rewrite; manual CDI/Servlet integration and no Spring dialects

## Static assets

Move Spring Boot classpath assets only when required by the chosen WAR layout:

| Spring Boot | WAR target |
|---|---|
| `src/main/resources/static/css/` | `src/main/webapp/css/` |
| `src/main/resources/static/js/` | `src/main/webapp/js/` |
| `src/main/resources/static/images/` | `src/main/webapp/images/` |

Before moving, check whether the build already copies classpath resources or whether a frontend build owns the output. Preserve cache-busting filenames and update every affected reference. Do not overwrite existing webapp assets.

## CSRF migration gate

Treat `_csrf`, Spring Security dialect attributes, or state-changing browser forms as evidence that CSRF protection is expected. For every non-idempotent browser route:

1. Reuse the security module's record of the current token source, cookie/session behavior, header/field name, ignored routes, and failure response.
2. Implement the replacement appropriate to the selected view stack.
3. Add a positive test with a valid token.
4. Add negative tests with a missing token and an invalid token; both must be rejected.
5. Only after those tests pass, remove Spring token markup and Spring Security integration.

Jakarta REST endpoints using bearer tokens and no browser cookie authentication may not require a synchronizer token, but document that threat-model decision. Never infer safety merely from an endpoint being JSON.

## Transaction and resume rules

- Record the route/template inventory and selected scenario before editing.
- On rerun, detect already migrated templates/controllers and update rather than duplicate them.
- Keep old templates until the replacement renders and the relevant tests pass; then remove them with an entry in the migration report.
- If one view stack is blocked, mark only that path `BLOCKED`; continue with independent REST/static work.

## Verification

- Compile using the detected launcher.
- Run view/controller tests, binding/conversion/over-posting tests, and CSRF positive/negative tests.
- Start Liberty through the time-bounded runtime module and exercise representative GET, validation-error, conversion-error, POST, redirect, and static-asset paths.
- Compare status, content type, route, and visible behavior with the baseline.

## Watch out

- `@Controller` without an adjacent template is still frontend evidence; the template may be generated, external, or missing.
- Spring Security Thymeleaf dialects and Spring EL objects do not work with core Thymeleaf alone.
- Do not rewrite `${...}` or `*{...}` without proving which view engine, model root, and binding owner evaluates it.
- JSP/JSTL is not an automatic replacement for every standalone Thymeleaf use.
- Preserve explicit context roots and URL encoding; do not hard-code `/` assumptions.
