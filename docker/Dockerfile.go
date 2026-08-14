FROM golang:1.23-bookworm

# Package sources, overridable at build time:
#   docker build --build-arg APT_MIRROR=mirrors.aliyun.com \
#                --build-arg GOPROXY=https://goproxy.cn,direct ...
#
# The defaults are the canonical hosts, which is the opposite of
# Dockerfile.base. That file was written for a network where deb.debian.org and
# PyPI were unreachable and an unbuildable base image blocked every scoring run.
# On the host this file was written for, deb.debian.org, proxy.golang.org and
# mirrors.aliyun.com all answer, so the canonical hosts are the default and the
# mirrors stay one flag away.
ARG APT_MIRROR=deb.debian.org
ARG GOPROXY=https://proxy.golang.org,direct

RUN if [ "${APT_MIRROR}" != "deb.debian.org" ]; then \
        for f in /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list; do \
            [ -f "$f" ] && sed -i "s|deb.debian.org|${APT_MIRROR}|g; s|security.debian.org|${APT_MIRROR}|g" "$f"; \
        done; \
    fi; true

# Python is not optional here: GoRunner.provenance() returns a `python3 -c`
# command, and provenance is what catches a `go mod edit -replace` that silently
# did not apply, leaving a published module in play instead of the candidate.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl python3 && \
    rm -rf /var/lib/apt/lists/*

# GoRunner.setup() runs `go mod edit` and `go mod tidy` against the oracle
# module. The default -mod=readonly refuses both.
ENV GOFLAGS=-mod=mod
ENV GOPROXY=${GOPROXY}
ENV GOTOOLCHAIN=local

WORKDIR /workspace
