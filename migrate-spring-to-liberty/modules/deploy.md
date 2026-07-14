# Module: Optional Deployment Track

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md). Local Liberty runtime verification remains mandatory; this module runs only when the confirmed contract includes deployment deliverables or explicitly declares them out of scope.

Do not deploy to a cluster, registry, or shared environment without separate explicit authorization for the external state change. Generating and locally validating files does not authorize image publication or deployment.

## Gate and contract

Inventory existing `Dockerfile`/`Containerfile`, `.dockerignore`, CI workflows, Helm/Kustomize files, Kubernetes/OpenShift manifests, Open Liberty Operator resources, image registry conventions, service accounts, policies, routes/ingress, probes, and secret mechanisms.

Record:

- target: container artifact only, Kubernetes, OpenShift, Open Liberty Operator, or existing platform pipeline
- environment names and promotion model
- pinned Liberty image/runtime and JDK, supported architectures, and image registry/repository/tag policy
- configuration ownership: image, ConfigMap, Secret/external secret store, environment, or server variables
- ports, context root, resources, scaling, disruption/rolling-update policy, persistence, and network policy
- startup, liveness, and readiness behavior
- build/sign/SBOM/vulnerability policy and required CI checks
- whether this run is **files only**, **local image validation**, **publish**, or **deploy**

If deployment is not requested, record `SKIP — deployment track outside confirmed scope`; this is a valid terminal state.

## Container image

Prefer a pinned `icr.io/appcafe/open-liberty` `kernel-slim` tag compatible with the selected JDK. Do not use a moving `latest` tag for a reproducible deliverable.

A rewrite WAR image normally follows this order:

```dockerfile
ARG LIBERTY_IMAGE
FROM ${LIBERTY_IMAGE}

COPY --chown=1001:0 src/main/liberty/config/ /config/
RUN features.sh
COPY --chown=1001:0 target/app.war /config/apps/
RUN configure.sh
```

Derive the real artifact name and deployment element; do not copy `app.war` literally unless the build creates it. A rehost must copy the actual executable artifact and preserve its `<springBootApplication>` configuration. Use the non-root image user and correct ownership. Exclude `.git`, credentials, keys, local build caches, logs, and unrelated artifacts through `.dockerignore`.

Pin the exact image digest or version tag according to the contract. Run `features.sh` after server configuration and `configure.sh` after application/configuration content so the image is fit-for-purpose and caches are populated.

## Kubernetes or OpenShift

Generate only the selected platform format; do not add raw Kubernetes, Helm, Kustomize, and Operator manifests simultaneously without a reason.

- use immutable image references for promoted environments
- expose only required ports and preserve the contracted context root
- set requests and limits from measured or explicitly provisional values; label provisional sizing
- use `/health/started`, `/health/live`, and `/health/ready` only when `mpHealth-4.0` is enabled and those endpoints are verified
- size probe delays/thresholds from measured startup and dependency behavior, not copied defaults
- keep credentials, tokens, certificates, and private keys out of manifests and images; reference the approved Secret/external-secret mechanism
- preserve TLS termination, forwarded-header, session-affinity, CORS, and security requirements across proxy/ingress boundaries
- define rolling-update/disruption behavior and graceful termination for in-flight requests and async work
- add NetworkPolicy, service account, RBAC, and persistent storage only when the application/environment requires them

For the Open Liberty Operator, use `OpenLibertyApplication` resources only when the operator and CRD version are confirmed in the target cluster.

## CI/CD integration

Prefer extending the repository's current pipeline. Separate these stages:

1. build and unit/integration tests
2. Liberty feature resolution and runtime smoke test
3. image build and local scan
4. SBOM/signing/attestation according to policy
5. registry push
6. environment deployment and post-deploy smoke/security checks
7. promotion or rollback

Never store registry or cluster credentials in the repository. Use the CI platform's OIDC/secret mechanism and least-privilege identities. Pin third-party CI actions by the repository's security policy.

## Validation and evidence

For files-only work, run available schema/render checks (`docker build --check`, `kubectl apply --dry-run=client`, `kustomize build`, `helm template`/`helm lint`) without contacting a cluster. Tool absence is `BLOCKED`, not `PASS`.

For local image validation, build the image, inspect its configured user and exposed content, start it with explicit non-secret test configuration, wait with a timeout, probe readiness and representative routes, scan logs, and stop it gracefully.

Publishing or deploying requires separate approval immediately before the command. After an authorized deployment, capture image digest, target namespace/environment, rollout status, probe results, application smoke/security results, and rollback instructions. Never claim deployment success from manifest generation alone.

## Primary references

- [Open Liberty container images](https://www.openliberty.io/docs/latest/container-images.html)
- [Open Liberty health checks](https://www.openliberty.io/docs/latest/health-check-microservices.html)
- [Open Liberty Kubernetes health probes](https://www.openliberty.io/guides/kubernetes-microprofile-health.html)
- [Open Liberty Operator deployment](https://www.openliberty.io/guides/openliberty-operator-intro.html)
