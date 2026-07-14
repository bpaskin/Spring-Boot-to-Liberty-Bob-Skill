#!/usr/bin/env python3
"""Validate the migration skill's structure and high-risk invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent

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
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            resolved = (path.parent / file_part).resolve()
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: broken internal link {target}"
                )


def main() -> int:
    errors: list[str] = []
    validate_frontmatter(errors)
    validate_invariants(errors)
    validate_links(errors)
    if not (REPO_ROOT / "LICENSE").is_file():
        errors.append("repository is missing LICENSE")

    if errors:
        print("Skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Skill validation passed: {len(markdown_files())} Markdown files checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
