# syntax=docker/dockerfile:1

# Meraki documents Chainguard Python images through this scanned Artifactory
# proxy. The 3.14 tags track the current patch release in the Python 3.14 line.
ARG PYTHON_IMAGE=docker-proxy-scanned.artifactory.ikarem.io/sto-cg-docker/python

FROM ${PYTHON_IMAGE}:3.14-dev AS build
WORKDIR /tmp/build
COPY requirements.txt ./requirements.txt
RUN python -m venv /tmp/venv \
    && /tmp/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM ${PYTHON_IMAGE}:3.14
WORKDIR /app
ENV PATH="/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1
COPY --from=build /tmp/venv /venv
COPY --chown=65532:65532 src/project/ /app/

# Meraki's container guidance requires service and team ownership metadata.
ARG MERAKI_TEAM
LABEL com.meraki.service="mule-bot" \
      com.meraki.team="${MERAKI_TEAM}" \
      com.meraki.repository="https://github.com/rxantonio/mule-bot"

USER 65532

# Use the virtual environment created in the build stage. The base image's
# default entrypoint points at its system Python, which has no app dependencies.
ENTRYPOINT ["/venv/bin/python"]
CMD ["main.py"]
