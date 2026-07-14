# Module: Security

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md). Security migration is a behavior-preservation exercise, not an annotation cleanup.

If the contract selects retain Spring and rehost, log this module as `SKIP` and stop. Preserve Spring Security, its `SecurityFilterChain`, dependencies, configuration, and tests on that path.

For a rewrite, do not remove or disable Spring Security until the replacement security contract is explicit and the applicable positive and negative tests pass. A detected security gate can be `PASS` while the module execution state becomes `BLOCKED` because the contract is incomplete; record both distinctly. Do not create a permissive temporary configuration.

## 1. Inventory the existing security behavior

Inspect source, build files, configuration, templates, descriptors, and tests. Record:

- every `SecurityFilterChain`, its order, security matcher, request matcher, dispatcher handling, and default rule
- authentication providers, `UserDetailsService`, password encoders, user/role stores, LDAP settings, and custom filters
- form login, HTTP Basic, OAuth2/OIDC client login, resource server, JWT, opaque-token introspection, and custom authentication flows
- issuer, JWK/JWKS source, audience, accepted algorithms, clock skew, principal claim, group/role claim, and role-prefix rules
- method security annotations, especially every `@PreAuthorize` and `@PostAuthorize` expression
- session creation, fixation protection, concurrency, timeout, saved requests, remember-me, cookie attributes, and logout behavior
- CSRF token repository, request parameter/header, ignored routes, and browser integration
- CORS origins, methods, headers, credentials, exposed headers, preflight behavior, and cache duration
- transport guarantees and security headers such as HSTS, CSP, frame options, and content-type protection

Create two durable tables in `migration-report.md` before editing.

### Authentication mechanisms

| Entry point / client | Mechanism | Identity and trust source | Principal | Role/group mapping | Session/cookie | Logout |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

### Authorization matrix

| HTTP method and route / method call | Anonymous | Authenticated without role | Allowed role/claim/owner | Expected denial | Policy source |
|---|---|---|---|---|---|
| ... | ... | ... | ... | `401` or `403` | matcher, annotation, or expression |

Distinguish unauthenticated `401` behavior from authenticated-but-forbidden `403` behavior. Preserve redirects only where the browser-login contract requires them.

## 2. Select an authentication strategy

Choose per coherent entry point; an application can legitimately use browser OIDC and bearer JWT on different routes.

| Existing behavior | Candidate Liberty/Jakarta replacement | Required decision |
|---|---|---|
| HTTP Basic or form login | Jakarta Security 4.0 with `appSecurity-6.0` and a reviewed Liberty registry or Jakarta Security `IdentityStore` | realm, password storage, challenge/redirect behavior, and role mapping |
| Browser OIDC login | Jakarta Security `@OpenIdAuthenticationMechanismDefinition` with `appSecurity-6.0`, **or** Liberty-managed `openidConnectClient-1.0` | choose exactly one owner; define redirect URI, scopes, claims, session, and provider logout |
| JWT bearer resource server | MicroProfile JWT 2.1 with `mpJwt-2.1` and `mpConfig-3.1` | issuer, keys/JWKS, audience, algorithms, principal, groups, expiry, and clock-skew policy |
| LDAP or a basic registry | Liberty registry configuration used by `appSecurity-6.0` | bind/search settings, group-to-role mapping, password policy, and secret source |
| Opaque bearer tokens, introspection, custom filters, or multiple dynamic issuers | Explicit custom or staged design | do not claim MicroProfile JWT parity unless the token and trust model are compatible |

Externalize client secrets, bind passwords, registry passwords, keys, and tokens through an approved secret source or environment/server variables. Never commit live credentials or put an example password into executable configuration.

## 3. Preserve authorization semantics

- A literal single-role rule such as `hasRole('ADMIN')` may become `@RolesAllowed("ADMIN")` only after confirming the `ROLE_` prefix and identity-store group mapping.
- Complex `@PreAuthorize` or `@PostAuthorize` expressions cannot safely become `@RolesAllowed` mechanically. This includes boolean combinations, ownership checks, method arguments, return-object checks, bean calls, permission evaluators, and claims beyond simple role membership.
- For complex rules, implement an explicit tested policy component, interceptor/resource check, or approved staged exception. If parity cannot yet be demonstrated, retain the original Spring expression **and its required Spring dependencies** with a migration TODO, mark the scope `PARTIAL`/`BLOCKED`, and do not claim complete Spring removal.
- Preserve class/method precedence, default-deny behavior, and `@PermitAll`/`@DenyAll` semantics. Do not add a broad permit rule to make tests compile.
- Map application roles to registry groups or JWT groups explicitly; do not assume matching strings imply matching authorization.

Update [the annotation map](../references/annotation-map.md) only as a guide to candidates. The authorization matrix is the source of truth for this migration.

## 4. Preserve browser and state behavior

### CSRF

Cookie-authenticated browser requests remain CSRF-sensitive. Record token source, rotation, header/field name, ignored routes, and failure status before replacement. Require successful requests with a valid token and rejection with missing and invalid tokens before removing Spring CSRF integration.

A bearer-only API can omit a synchronizer token only after documenting why ambient browser credentials are not accepted. JSON alone is not evidence that CSRF is irrelevant. The [frontend module](frontend.md) implements template/token integration using this module's security contract.

### CORS

Define allowed origins, methods, request headers, exposed headers, credentials, preflight handling, and cache duration explicitly. Test an allowed origin, a denied origin, and preflight. Never combine wildcard origins with credentialed requests.

### Sessions and logout

Preserve session creation policy, fixation protection, concurrency rules, timeout, saved-request behavior, and cookie `Secure`, `HttpOnly`, `SameSite`, path, and domain attributes. Verify that logout invalidates the local session/tokens and that reuse fails. When OIDC is used, decide whether provider-initiated or relying-party-initiated logout is required; local logout is not automatically provider logout.

Preserve transport and security-header behavior unless the contract explicitly replaces it with tested Liberty/proxy configuration.

## 5. Implement in controlled slices

1. Add the selected Jakarta Security, MicroProfile JWT, registry, or OIDC configuration without removing the baseline path.
2. Configure trust and role/group mapping with externalized secrets.
3. Migrate route-level authorization from the authorization matrix.
4. Migrate only simple method role checks mechanically; implement complex policies explicitly.
5. Implement CSRF, CORS, session, cookie, logout, transport, and security-header behavior.
6. Add the negative-test matrix below and compare its results with the baseline.
7. Remove Spring Security dependencies and configuration only after the replacement passes.
8. Compile with the detected build launcher and record exact results and remaining exceptions.

If old and new security mechanisms cannot coexist safely, migrate and validate one independently deployable slice at a time. Never expose an intermediate permissive deployment.

## 6. Required security tests

Add every applicable case; record deliberate non-applicability with evidence.

| Area | Required evidence |
|---|---|
| Route authorization | anonymous, authenticated, allowed role, forbidden role, and default/unmatched route |
| Object/method policy | allowed owner, wrong authenticated user, each important boolean branch, and return-object rule |
| JWT | valid token; missing token; expired token; invalid signature, issuer, and audience; absent/malformed group claim |
| Browser CSRF | valid, missing, and invalid token on each state-changing route family |
| CORS | allowed origin, denied origin, allowed preflight, and denied preflight |
| Session | fixation/session-id behavior, timeout where material, cookie flags, and concurrency policy |
| Logout | session/token invalidation, reuse rejection, and provider logout where contracted |
| Registry | valid user, bad password, disabled/unknown user, and group-to-role mapping |

Assert status, redirects/challenges, relevant response headers, and audit-relevant behavior—not merely that access failed.

## Completion gate

Mark `PASS` only when:

- authentication and authorization tables are complete and match the confirmed contract
- trust, secrets, groups, and roles are explicitly configured
- complex method expressions have tested semantic replacements or documented staged exceptions
- applicable CSRF, CORS, session, logout, transport, and header behavior is preserved
- anonymous/authenticated/forbidden and mechanism-specific negative tests pass
- Spring Security is removed only for the completed rewrite scope

Otherwise mark `PARTIAL` or `BLOCKED` and name the exact exposed or unverified behavior. A successful compile alone is never security parity.

## Primary references

- [Jakarta Security 4.0](https://jakarta.ee/specifications/security/4.0/)
- [Open Liberty Application Security 6.0](https://www.openliberty.io/docs/latest/reference/feature/appSecurity-6.0.html)
- [Open Liberty MicroProfile JWT 2.1](https://www.openliberty.io/docs/latest/reference/feature/mpJwt-2.1.html)
- [Open Liberty OpenID Connect Client 1.0](https://www.openliberty.io/docs/latest/reference/feature/openidConnectClient-1.0.html)
- [Open Liberty annotated OIDC client guidance](https://www.openliberty.io/docs/latest/enable-openid-connect-client.html)
