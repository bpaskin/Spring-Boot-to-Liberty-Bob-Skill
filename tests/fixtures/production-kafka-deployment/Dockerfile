# Dockerfile: build artifact is supplied by the verified pipeline.
FROM icr.io/appcafe/open-liberty:kernel-slim-java21-openj9-ubi-minimal
COPY --chown=1001:0 target/app.war /config/apps/app.war
