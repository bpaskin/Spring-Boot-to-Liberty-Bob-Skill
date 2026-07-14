#!/usr/bin/env python3
"""Validate the migration skill's structure and high-risk invariants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"

INVALID_TEXT = {
    "<feature>beanValidation-3.1</feature>": "Jakarta EE 11 uses validation-3.1",
    "<feature>appSecurity-5.0</feature>": "Jakarta EE 11 uses appSecurity-6.0",
    "<feature>ejbLite-4.0</feature>": "use enterpriseBeansLite-4.0",
    "<feature>ejb-4.0</feature>": "use enterpriseBeans-4.0",
    "<feature>messaging-3.0</feature>": "Jakarta EE 11 uses messaging-3.1",
    "<feature>servlet-6.0</feature>": "Jakarta EE 11 uses servlet-6.1",
    "<feature>concurrent-3.0</feature>": "Jakarta EE 11 uses concurrent-3.1",
    "io.openliberty.tools:microshed-testing-liberty": "MicroShed uses org.microshed",
    "quarkus-rest": "Quarkus artifacts do not belong in a Liberty mapping",
    "@IfBuildProfile": "not a portable CDI or MicroProfile annotation",
    "@LookupIfProperty": "not a portable CDI or MicroProfile annotation",
    "MicroProfile Scheduler (`mpScheduler`)": "there is no mpScheduler feature",
    "Jakarta EE 11 mandates Java 21": "Jakarta EE 11 has a Java 17 minimum",
    "Remove Spring CSRF tokens from HTML and JavaScript": "replace and test CSRF protection first",
    "LibertyServerContainerConfiguration": "MicroShed documents SharedContainerConfiguration with ApplicationContainer",
    "new LibertyServerContainer(": "MicroShed documents ApplicationContainer",
}

REQUIRED_CANONICAL_FEATURES = {
    "servlet-6.1",
    "validation-3.1",
    "appSecurity-6.0",
    "concurrent-3.1",
    "enterpriseBeansLite-4.0",
    "enterpriseBeans-4.0",
    "messaging-3.1",
}

ALLOWED_DECLARED_FEATURES = REQUIRED_CANONICAL_FEATURES | {
    "appSecurity-6.0",
    "cdi-4.1",
    "faces-4.1",
    "jakartaee-11.0",
    "jsonb-3.0",
    "jsonp-2.1",
    "messaging-3.1",
    "microProfile-7.0",
    "mpConfig-3.1",
    "mpHealth-4.0",
    "mpJwt-2.1",
    "mpMetrics-5.1",
    "mpOpenAPI-4.0",
    "pages-4.0",
    "persistence-3.2",
    "restfulWS-4.0",
    "servlet-6.1",
    "validation-3.1",
    "webProfile-11.0",
    "wmqJmsClient-3.0",
    "xmlBinding-4.0",
}

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FEATURE_DECLARATION = re.compile(r"<feature>([^<]+)</feature>")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
DANGEROUS_SCHEMA_DECLARATION = re.compile(
    r'<property\s+name="jakarta\.persistence\.schema-generation\.database\.action"'
    r'\s+value="(?:drop|drop-and-create|create|create-only)"\s*/?>'
)


def markdown_files() -> list[Path]:
    return sorted(REPO_ROOT.rglob("*.md"))


def validate_frontmatter(errors: list[str]) -> None:
    skill_file = SKILL_ROOT / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append("SKILL.md: missing YAML frontmatter")
        return
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        errors.append("SKILL.md: unterminated YAML frontmatter")
        return
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if line and not line[0].isspace() and ":" in line
    }
    if keys != {"name", "description"}:
        errors.append(
            "SKILL.md: frontmatter must contain only name and description; "
            f"found {sorted(keys)}"
        )


def validate_invariants(errors: list[str]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for invalid, reason in INVALID_TEXT.items():
            if invalid in text:
                errors.append(f"{path.relative_to(REPO_ROOT)}: {invalid!r}: {reason}")
        for feature in FEATURE_DECLARATION.findall(text):
            if feature not in ALLOWED_DECLARED_FEATURES:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: unreviewed Liberty feature "
                    f"declaration {feature!r}"
                )
        if DANGEROUS_SCHEMA_DECLARATION.search(text):
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: destructive schema action appears "
                "in an executable XML example; examples must default to none"
            )

    canonical = (
        SKILL_ROOT / "references" / "jakarta-ee11-liberty-features.md"
    ).read_text(encoding="utf-8")
    for feature in sorted(REQUIRED_CANONICAL_FEATURES):
        if feature not in canonical:
            errors.append(f"canonical feature reference is missing {feature}")


def validate_links(errors: list[str]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, anchor = target.partition("#")
            resolved = (path.parent / file_part).resolve() if file_part else path.resolve()
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: broken internal link {target}"
                )
                continue
            if anchor and resolved.suffix.lower() == ".md":
                slugs: set[str] = set()
                counts: dict[str, int] = {}
                for heading in MARKDOWN_HEADING.findall(
                    resolved.read_text(encoding="utf-8")
                ):
                    slug = re.sub(r"[^\w\- ]", "", heading.lower())
                    slug = re.sub(r"\s", "-", slug.strip())
                    count = counts.get(slug, 0)
                    counts[slug] = count + 1
                    slugs.add(slug if count == 0 else f"{slug}-{count}")
                if unquote(anchor).lower() not in slugs:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: broken Markdown anchor {target}"
                    )


def fixture_text(root: Path, *, tests: bool | None = None) -> str:
    parts: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "expected.json":
            continue
        is_test = "src/test" in path.as_posix()
        if tests is not None and is_test != tests:
            continue
        try:
            parts.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
    return "\n".join(parts)


def classify_fixture(root: Path) -> dict[str, str | bool]:
    main_text = fixture_text(root, tests=False)
    build_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(root.iterdir())
        if path.is_file()
        and (path.name == "pom.xml" or path.name.startswith("build.gradle"))
    )

    spring_build = "org.springframework" in build_text
    liberty_build = any(
        marker in build_text
        for marker in ("io.openliberty", "jakarta.platform", "liberty-maven-plugin")
    )
    if spring_build and liberty_build:
        build = "PARTIAL"
    elif spring_build:
        build = "PASS"
    else:
        build = "SKIP"

    spring_code = "org.springframework" in main_text
    migrated_code = "import jakarta." in main_text or "Migration required" in main_text
    if spring_code and migrated_code:
        code = "PARTIAL"
    elif spring_code:
        code = "PASS"
    else:
        code = "SKIP"

    view_files = any(
        part in path.as_posix()
        for path in root.rglob("*")
        for part in ("/templates/", "/static/", "/public/")
    )
    server_view_code = any(
        marker in main_text
        for marker in ("@Controller", "ModelAndView", "org.springframework.ui.Model")
    )
    frontend = "PASS" if view_files or server_view_code else "SKIP"

    test_files = [path for path in root.rglob("*") if path.is_file() and "src/test" in path.as_posix()]
    testing = "PASS" if test_files else "SKIP"

    return {
        "build": build,
        "code": code,
        "frontend": frontend,
        "testing": testing,
        "coverage_risk": not bool(test_files),
    }


def validate_fixtures(errors: list[str]) -> None:
    if not FIXTURES_ROOT.is_dir():
        errors.append("tests/fixtures: evaluation fixtures are missing")
        return
    fixtures = sorted(path for path in FIXTURES_ROOT.iterdir() if path.is_dir())
    if len(fixtures) < 4:
        errors.append("tests/fixtures: expected at least four representative scenarios")
    for fixture in fixtures:
        expected_path = fixture / "expected.json"
        if not expected_path.is_file():
            errors.append(f"{fixture.relative_to(REPO_ROOT)}: missing expected.json")
            continue
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        actual = classify_fixture(fixture)
        if actual != expected:
            errors.append(
                f"{fixture.relative_to(REPO_ROOT)}: gate classification mismatch; "
                f"expected {expected}, got {actual}"
            )


def main() -> int:
    errors: list[str] = []
    validate_frontmatter(errors)
    validate_invariants(errors)
    validate_links(errors)
    validate_fixtures(errors)
    if not (REPO_ROOT / "LICENSE").is_file():
        errors.append("repository is missing LICENSE")

    if errors:
        print("Skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Skill validation passed: {len(markdown_files())} Markdown files and "
        f"{len(list(FIXTURES_ROOT.iterdir()))} fixtures checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
