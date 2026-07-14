#!/usr/bin/env python3
"""Generate a reviewable Liberty server.xml scaffold from an inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr


REWRITE_FEATURES = {
    "web-api": {"cdi-4.1", "restfulWS-4.0", "jsonb-3.0"},
    "frontend": {"cdi-4.1", "servlet-6.1"},
    "repositories": {"cdi-4.1", "data-1.0", "persistence-3.2"},
    "security": {"appSecurity-6.0"},
    "async-events": {"cdi-4.1", "concurrent-3.1", "transaction-2.0"},
    "messaging": {"messaging-3.1"},
    "batch-scheduling": {"batch-2.1"},
    "data-xa-schema": {"persistence-3.2", "transaction-2.0"},
    "identity-observability": {"appSecurity-6.0", "mpHealth-4.0"},
}


def load_inventory(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("inventory must use schema_version 1")
    return data


def render(inventory: dict, scope: str, artifact: str, context_root: str) -> str:
    if not artifact or "/" in artifact or "\\" in artifact:
        raise ValueError("artifact must be the produced file name, not a path")
    if scope == "rehost":
        streams = inventory.get("spring", {}).get("boot_streams", [])
        if len(streams) != 1 or streams[0] not in {"3", "4"}:
            raise ValueError("rehost scaffolding requires exactly one detected Spring Boot 3 or 4 stream")
        stream = streams[0]
        features = [f"springBoot-{stream}.0", "servlet-6.0" if stream == "3" else "servlet-6.1"]
        deployment = (
            f"    <springBootApplication id=\"application\" location={quoteattr(artifact)}>\n"
            f"        <applicationArgument>--server.servlet.context-path={escape(context_root)}</applicationArgument>\n"
            "    </springBootApplication>"
        )
        description = "Rehost Spring Boot on Open Liberty"
    else:
        features = {"cdi-4.1"}
        for capability in inventory.get("capabilities", []):
            features.update(REWRITE_FEATURES.get(capability.get("id"), set()))
        features = sorted(features)
        deployment = (
            f"    <webApplication id=\"application\" location={quoteattr(artifact)} "
            f"contextRoot={quoteattr(context_root)}/>"
        )
        description = "Spring-to-Jakarta migration on Open Liberty"
    feature_xml = "\n".join(f"        <feature>{escape(feature)}</feature>" for feature in features)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        f"<server description={quoteattr(description)}>\n"
        "    <featureManager>\n"
        f"{feature_xml}\n"
        "    </featureManager>\n\n"
        "    <httpEndpoint id=\"defaultHttpEndpoint\" host=\"*\" httpPort=\"9080\" httpsPort=\"9443\"/>\n\n"
        f"{deployment}\n"
        "</server>\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--scope", choices=("rehost", "rewrite"), required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--context-root", default="/")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        content = render(load_inventory(args.inventory), args.scope, args.artifact, args.context_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not args.output:
        sys.stdout.write(content)
        return 0
    if args.output.exists() and not args.force:
        print(f"refusing to overwrite {args.output}; use --force", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
