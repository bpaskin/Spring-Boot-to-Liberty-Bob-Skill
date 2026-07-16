# Frontend assets, layout, and internationalization parity

Load this reference whenever the migrated slice contains templates, static assets, WebJars, message bundles, locale-selection code, or server-rendered layouts. Apply it with the contract-selected frontend reference.

## Capture the baseline contract

Record before editing:

- every rendered route, template, fragment/layout relationship, supported viewport, and important state such as initial GET, validation failure, authenticated navigation, and empty/data-filled views;
- every stylesheet, script, image, SVG, favicon, font, WebJar, CSS `url(...)` dependency, frontend build output, cache-busted filename, and external origin;
- the asset URL as rendered in HTML/CSS, application context root, dependency coordinates/version, WAR/JAR location, content type, cache policy, and integrity/CSP requirements;
- supported locales, default locale, selection inputs, precedence among query/cookie/session/`Accept-Language`, session propagation, message resolver, bundle basenames/encoding/fallback, formatting rules, and missing-key behavior.

Capture baseline browser screenshots or equivalent visual evidence for representative routes, states, viewports, and locales. Do not use screenshots as the only assertion; retain DOM, response, and resource evidence too.

## Resolve static resources and WebJars

Servlet containers expose resources packaged under a dependency's `META-INF/resources/` at their actual resource paths. A versionless WebJar URL can work in Spring Boot when a WebJars locator or Spring resource handler resolves it, but Liberty's Servlet resource handling does not recreate that locator implicitly.

For each WebJar:

1. Inspect the resolved dependency and packaged WAR instead of guessing its version or internal path.
2. Locate the asset under `META-INF/resources/webjars/<artifact>/<version>/...`.
3. Either generate a context-relative URL containing the pinned version or deliberately retain/configure a compatible locator and prove its mapping on Liberty.
4. Update layouts, fragments, CSS imports, JavaScript imports, tests, CSP, and cache rules together.

For example, if the packaged resource is `META-INF/resources/webjars/font-awesome/4.7.0/css/font-awesome.min.css`, a direct Servlet path is `/webjars/font-awesome/4.7.0/css/font-awesome.min.css`. In Thymeleaf, use a context-relative expression such as `th:href="@{/webjars/font-awesome/4.7.0/css/font-awesome.min.css}"`. Derive `4.7.0` from the resolved dependency; do not copy that example version into another application.

Do not stop after the top-level CSS returns `200`. Crawl the rendered asset graph and require:

- no same-origin asset request returns `4xx`/`5xx`, redirects to login unexpectedly, or returns an HTML error body;
- CSS/JavaScript/image/font responses have compatible content types and non-empty bodies;
- CSS `url(...)`, `@import`, source maps when required, font files, icon glyphs, responsive images, and dynamically loaded assets resolve under the deployed context root;
- browser console and network logs contain no missing-resource, CSP, mixed-content, module-loading, or font-decoding errors.

## Preserve layout and formatting

Preserve fragment inclusion, DOM order, CSS cascade/order, classes, theme variables, JavaScript load/defer order, responsive breakpoints, escaping, and context-relative links. Verify that layouts are included exactly once and do not produce duplicate IDs, nested document roots, missing navigation, or unstyled flashes.

Compare baseline and Liberty rendering at the contract-supported viewports and states. Check visible images/icons, font application, navigation, form alignment, validation messages, overflow, clipping, wrapping, focus/error styling, and interactive components. Longer translated labels must not break the layout. Record intentional visual changes separately from migration regressions.

## Preserve internationalization

Spring's message-source integration is not supplied by core Thymeleaf. Register the contract-selected `IMessageResolver` explicitly, including any application-provided `ClasspathResourceBundleMessageResolver`; preserve bundle basenames, UTF-8 handling, locale fallback, parameter substitution, and missing-key policy. Keep `#{...}` message expressions only after their keys resolve through the configured resolver.

Propagate the locale selected by the application into every rendering context. If a method such as `WebConfiguration.resolveLocale()` reads/writes the session locale, use its resolved value when constructing the Thymeleaf `WebContext`; do not fall back silently to the server default or request locale.

Test every supported locale and the complete switching lifecycle:

1. Render the default locale and assert representative layout plus validation messages.
2. Select another locale and assert known translated text—for example, a German home label such as `Startseite` when that is the application's bundle value.
3. Make a second request in the same session without the locale parameter and verify the selected locale persists.
4. Use a new session and verify the documented default/fallback behavior.
5. Test an unsupported locale, a missing key, message parameters, dates/numbers, redirects, validation failures, and localized layout fragments.

## Completion evidence

Mark frontend parity `PASS` only when the migration ledger contains:

- a rendered-route and locale matrix;
- an asset manifest mapping rendered URLs to packaged resources and dependency versions;
- automated HTTP/browser assertions for the transitive asset graph and locale persistence;
- visual/layout evidence for representative routes, states, viewports, and locales;
- zero unexplained browser console/network failures and no unresolved message placeholders.

Authoritative background: [WebJars documentation](https://www.webjars.org/documentation) and [Thymeleaf 3.1 message resolution and internationalization](https://www.thymeleaf.org/doc/tutorials/3.1/usingthymeleaf.html).
