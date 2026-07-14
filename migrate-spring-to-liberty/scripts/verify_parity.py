#!/usr/bin/env python3
"""Grade baseline and Liberty-target evidence against a characterization contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError(f"{path}: unsupported schema_version")
    return data


def result_map(evidence: dict, side: str, errors: list[str]) -> dict[str, dict]:
    if evidence.get("side") != side:
        errors.append(f"{side}: evidence side is {evidence.get('side')!r}")
    results: dict[str, dict] = {}
    for result in evidence.get("cases", []):
        identifier = result.get("id") if isinstance(result, dict) else None
        if not identifier or identifier in results:
            errors.append(f"{side}: invalid or duplicate case id {identifier!r}")
            continue
        results[identifier] = result
    return results


def validate_artifact(
    side: str,
    identifier: str,
    result: dict,
    evidence_root: Path,
    errors: list[str],
) -> None:
    artifact_value = result.get("artifact")
    if not artifact_value:
        errors.append(f"{side}/{identifier}: missing artifact")
        return
    artifact = Path(artifact_value)
    if artifact.is_absolute() or ".." in artifact.parts:
        errors.append(f"{side}/{identifier}: artifact must be relative to the evidence root")
        return
    path = evidence_root / artifact
    if not path.is_file() or path.stat().st_size == 0:
        errors.append(f"{side}/{identifier}: artifact is missing or empty: {artifact}")


def grade(contract: dict, baseline: dict, target: dict, evidence_root: Path) -> list[str]:
    errors: list[str] = []
    cases = contract.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["contract: cases must be a non-empty array"]
    baseline_results = result_map(baseline, "baseline", errors)
    target_results = result_map(target, "target", errors)
    for case in cases:
        identifier = case.get("id") if isinstance(case, dict) else None
        if not identifier:
            errors.append("contract: every case needs an id")
            continue
        for side, results in (("baseline", baseline_results), ("target", target_results)):
            result = results.get(identifier)
            if result is None:
                errors.append(f"{side}/{identifier}: missing result")
                continue
            if result.get("status") != "PASS":
                errors.append(f"{side}/{identifier}: status is {result.get('status', 'UNKNOWN')}, not PASS")
            if not result.get("observed"):
                errors.append(f"{side}/{identifier}: missing observed behavior")
            if not result.get("signature"):
                errors.append(f"{side}/{identifier}: missing normalized behavior signature")
            validate_artifact(side, identifier, result, evidence_root, errors)
        before = baseline_results.get(identifier, {})
        after = target_results.get(identifier, {})
        if before.get("status") == after.get("status") == "PASS":
            if before.get("signature") != after.get("signature"):
                errors.append(
                    f"parity/{identifier}: baseline signature {before.get('signature')!r} "
                    f"does not match target signature {after.get('signature')!r}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        contract = load_json(args.contract)
        baseline = load_json(args.baseline)
        target = load_json(args.target)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    errors = grade(contract, baseline, target, args.evidence_root)
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Behavior parity evidence passed for {len(contract['cases'])} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
