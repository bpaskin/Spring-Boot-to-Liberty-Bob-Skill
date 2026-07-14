#!/usr/bin/env python3
"""Plan or apply the narrow, semantics-preserving namespace codemod set."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


IGNORED_PARTS = {".git", ".gradle", "build", "target"}
APPROVED_PREFIXES = {
    "javax.activation": "jakarta.activation",
    "javax.annotation": "jakarta.annotation",
    "javax.batch": "jakarta.batch",
    "javax.decorator": "jakarta.decorator",
    "javax.ejb": "jakarta.ejb",
    "javax.el": "jakarta.el",
    "javax.enterprise": "jakarta.enterprise",
    "javax.faces": "jakarta.faces",
    "javax.inject": "jakarta.inject",
    "javax.interceptor": "jakarta.interceptor",
    "javax.jms": "jakarta.jms",
    "javax.json": "jakarta.json",
    "javax.jws": "jakarta.jws",
    "javax.mail": "jakarta.mail",
    "javax.persistence": "jakarta.persistence",
    "javax.resource": "jakarta.resource",
    "javax.security.enterprise": "jakarta.security.enterprise",
    "javax.security.jacc": "jakarta.security.jacc",
    "javax.servlet": "jakarta.servlet",
    "javax.transaction": "jakarta.transaction",
    "javax.validation": "jakarta.validation",
    "javax.websocket": "jakarta.websocket",
    "javax.ws.rs": "jakarta.ws.rs",
    "javax.xml.bind": "jakarta.xml.bind",
    "javax.xml.soap": "jakarta.xml.soap",
    "javax.xml.ws": "jakarta.xml.ws",
}
PROTECTED_PREFIXES = (
    "javax.annotation.processing",
    "javax.cache",
    "javax.crypto",
    "javax.naming",
    "javax.net",
    "javax.security.auth",
    "javax.security.cert",
    "javax.security.sasl",
    "javax.sql",
    "javax.transaction.xa",
)


def java_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.java")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.relative_to(root).parts)
    )


def transform(text: str) -> tuple[str, list[dict[str, str | int]]]:
    changes: list[dict[str, str | int]] = []
    updated_lines = []
    pattern = re.compile(r"\b(import|package)\s+(javax\.[\w.*]+)(\s*;)")
    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        original = line

        def replace(match: re.Match[str]) -> str:
            name = match.group(2)
            if name.startswith(PROTECTED_PREFIXES):
                return match.group(0)
            for old, new in APPROVED_PREFIXES.items():
                if name == old or name.startswith(old + "."):
                    migrated = new + name[len(old) :]
                    return f"{match.group(1)} {migrated}{match.group(3)}"
            return match.group(0)

        line = pattern.sub(replace, line)
        if line != original:
            changes.append(
                {
                    "line": number,
                    "before": original.rstrip("\r\n"),
                    "after": line.rstrip("\r\n"),
                }
            )
        updated_lines.append(line)
    return "".join(updated_lines), changes


def plan(root: Path, apply: bool) -> dict:
    root = root.resolve()
    files = []
    for path in java_files(root):
        original = path.read_text(encoding="utf-8")
        updated, changes = transform(original)
        if not changes:
            continue
        files.append({"path": path.relative_to(root).as_posix(), "changes": changes})
        if apply:
            path.write_text(updated, encoding="utf-8")
    return {
        "schema_version": 1,
        "operation": "approved-javax-to-jakarta-imports",
        "mode": "apply" if apply else "dry-run",
        "files": files,
        "changed_file_count": len(files),
        "protected_prefixes": list(PROTECTED_PREFIXES),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-apply", action="store_true")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.apply and not args.confirm_apply:
        print("--apply requires --confirm-apply", file=sys.stderr)
        return 2
    if not args.project.is_dir():
        print(f"project root is not a directory: {args.project}", file=sys.stderr)
        return 2
    result = plan(args.project, args.apply)
    content = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
