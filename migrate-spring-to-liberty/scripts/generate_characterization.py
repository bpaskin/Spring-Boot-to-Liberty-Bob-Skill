#!/usr/bin/env python3
"""Generate an executable-evidence contract from a migration inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CORE_CASES = (
    ("build-package", "positive", "Build, test, and package with the detected launcher."),
    ("liberty-startup", "positive", "Start the packaged application on Liberty within the agreed timeout."),
    ("public-api-smoke", "positive", "Exercise every externally supported route or protocol at least once."),
)
DEPENDENCY_CASES = (
    ("dependency-unavailable", "failure", "Make one required dependency unavailable and observe bounded failure and recovery."),
    ("restart-recovery", "recovery", "Restart Liberty and verify durable state and in-flight work follow the contract."),
)
DEPENDENCY_CAPABILITIES = {
    "async-events",
    "batch-scheduling",
    "custom-spring-runtime",
    "data-xa-schema",
    "deployment",
    "identity-observability",
    "messaging",
    "reactive-cloud",
    "repositories",
    "soap-nonrelational",
}

CAPABILITY_CASES = {
    "web-api": (
        ("api-success-contract", "positive", "Preserve status, headers, and body for representative successful requests."),
        ("api-invalid-input", "failure", "Preserve validation status and safe error shape for invalid input."),
    ),
    "frontend": (
        ("view-rendering", "positive", "Render each supported view with the expected model and static assets."),
        ("view-csrf-rejection", "failure", "Reject a state-changing browser request without the contracted CSRF proof."),
    ),
    "repositories": (
        ("repository-query-parity", "positive", "Compare CRUD, derived query, pagination, and ordering behavior."),
        ("repository-constraint-failure", "failure", "Preserve the observable result of a uniqueness or validation failure."),
    ),
    "security": (
        ("security-authorized", "positive", "Allow a valid identity with the required role or claim."),
        ("security-unauthenticated", "failure", "Return 401 for a protected route without valid authentication."),
        ("security-forbidden", "failure", "Return 403 for an authenticated identity lacking authority."),
        ("security-session-logout", "recovery", "Verify session, cookie, CSRF, and logout invalidation behavior."),
    ),
    "async-events": (
        ("async-context-delivery", "positive", "Preserve executor, context propagation, event phase, and ordering behavior."),
        ("async-overload", "failure", "Exercise queue saturation or concurrency limits without unbounded growth."),
        ("async-retry-exhaustion", "recovery", "Verify retry exhaustion, listener callbacks, and recovery side effects."),
    ),
    "messaging": (
        ("message-publish-consume", "positive", "Preserve payload, headers, key, ordering, and acknowledgment behavior."),
        ("message-duplicate", "failure", "Redeliver a boundary record and verify idempotent side effects."),
        ("message-poison-dlq", "failure", "Send an incompatible record and verify bounded retries and DLQ behavior."),
        ("message-broker-recovery", "recovery", "Interrupt the broker and verify reconnect, redelivery, and no silent loss."),
    ),
    "batch-scheduling": (
        ("job-success", "positive", "Run the job or timer with the contracted parameters, time zone, and identity."),
        ("job-overlap-misfire", "failure", "Exercise overlap and misfire behavior under a delayed execution."),
        ("job-crash-restart", "recovery", "Crash during work and verify checkpoint and restart semantics."),
    ),
    "data-xa-schema": (
        ("data-commit", "positive", "Commit representative writes and verify durable state and naming parity."),
        ("data-bad-credentials", "failure", "Reject bad credentials without leaking secrets and recover after correction."),
        ("data-pool-exhaustion", "failure", "Exhaust the pool and verify bounded timeout behavior."),
        ("xa-second-resource-failure", "failure", "Fail the second enlisted resource and verify no partial business commit."),
        ("schema-idempotent-restart", "recovery", "Start twice and verify non-destructive schema-tool behavior."),
    ),
    "identity-observability": (
        ("identity-valid-telemetry", "positive", "Authorize a valid token and capture correlated metric, trace, and log evidence."),
        ("identity-wrong-issuer-audience", "failure", "Reject correctly signed tokens with a wrong issuer or audience."),
        ("identity-jwks-rotation", "recovery", "Rotate keys during a bounded JWKS outage and verify fail-closed behavior."),
        ("telemetry-exporter-down", "failure", "Stop the exporter and verify bounded loss and memory behavior."),
    ),
    "reactive-cloud": (
        ("reactive-backpressure", "positive", "Preserve backpressure, cancellation, concurrency, and context behavior."),
        ("reactive-downstream-timeout", "failure", "Exercise timeout, fallback, and cancellation against a slow dependency."),
        ("cloud-route-discovery", "recovery", "Verify routing, discovery, refresh, and failover behavior after topology change."),
    ),
    "soap-nonrelational": (
        ("protocol-cache-success", "positive", "Preserve WSDL/protocol or cache/store read-write behavior."),
        ("protocol-invalid-message", "failure", "Preserve SOAP fault or invalid-data behavior without information leakage."),
        ("store-unavailable-recovery", "recovery", "Interrupt the store and verify consistency, reconnect, and timeout behavior."),
    ),
    "custom-spring-runtime": (
        ("custom-extension-bootstrap", "positive", "Verify every custom auto-configuration or extension activates under the same conditions."),
        ("custom-extension-disabled", "failure", "Verify disabled or missing prerequisites do not activate the extension."),
    ),
    "deployment": (
        ("deployment-ready", "positive", "Deploy the immutable image and pass startup, readiness, and liveness probes."),
        ("deployment-bad-secret", "failure", "Roll out invalid configuration and verify unready rollback without secret leakage."),
        ("deployment-termination-drain", "recovery", "Terminate an instance with in-flight work and verify drain or redelivery."),
    ),
}


def load_inventory(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("capabilities"), list):
        raise ValueError("inventory must be schema_version 1 with a capabilities array")
    return data


def generate(inventory: dict) -> dict:
    raw_cases = list(CORE_CASES)
    capability_ids = {capability["id"] for capability in inventory["capabilities"]}
    if capability_ids & DEPENDENCY_CAPABILITIES:
        raw_cases.extend(DEPENDENCY_CASES)
    for capability in sorted(inventory["capabilities"], key=lambda item: item["id"]):
        raw_cases.extend(CAPABILITY_CASES.get(capability["id"], ()))
    seen: set[str] = set()
    cases = []
    capability_by_case: dict[str, str] = {}
    for capability in inventory["capabilities"]:
        for case in CAPABILITY_CASES.get(capability["id"], ()):
            capability_by_case[case[0]] = capability["id"]
    for identifier, kind, description in raw_cases:
        if identifier in seen:
            continue
        seen.add(identifier)
        cases.append(
            {
                "id": identifier,
                "capability": capability_by_case.get(identifier, "core"),
                "kind": kind,
                "description": description,
                "comparison": "behavioral-equivalence",
                "required_sides": ["baseline", "target"],
            }
        )
    return {
        "schema_version": 1,
        "project": inventory.get("project", "unknown"),
        "route": inventory.get("recommended_migration", {}).get("route", "unselected"),
        "evidence_levels": [
            "ANALYZED",
            "COMPILED",
            "TESTED",
            "RUNTIME_VERIFIED",
            "BEHAVIOR_PARITY_VERIFIED",
        ],
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        contract = generate(load_inventory(args.inventory))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    content = json.dumps(contract, indent=2, sort_keys=True) + "\n"
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
