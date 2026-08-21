FROM maven:3.9.12-eclipse-temurin-17

# Package sources, overridable at build time:
#   docker build --build-arg APT_MIRROR=mirrors.aliyun.com \
#                --build-arg MAVEN_MIRROR_URL=<internal mirror> ...
#
# See Dockerfile.go for why the defaults are the canonical hosts rather than the
# mirrors Dockerfile.base defaults to.
ARG APT_MIRROR=deb.debian.org
ARG MAVEN_MIRROR_URL=
ARG JUNIT_VERSION=5.11.3
ARG SUREFIRE_VERSION=3.5.4

RUN if [ "${APT_MIRROR}" != "deb.debian.org" ]; then \
        for f in /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list; do \
            [ -f "$f" ] && sed -i "s|deb.debian.org|${APT_MIRROR}|g; s|security.debian.org|${APT_MIRROR}|g" "$f"; \
        done; \
    fi; true

# Python reshapes `dependency:list` output for JavaRunner.provenance(); Java has
# no interpreter on PATH for a one-line probe.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl python3 && \
    rm -rf /var/lib/apt/lists/*

RUN if [ -n "${MAVEN_MIRROR_URL}" ]; then \
        mkdir -p /root/.m2 && printf '%s\n' \
        '<settings><mirrors><mirror>' \
        '  <id>configured</id><mirrorOf>central</mirrorOf>' \
        "  <url>${MAVEN_MIRROR_URL}</url>" \
        '</mirror></mirrors></settings>' > /root/.m2/settings.xml; \
    fi

# Warm the local repository with a throwaway build, then delete the project.
#
# Caching the oracle's declared dependencies is not enough: a batch runs
# `mvn -o test`, and the `test` lifecycle pulls in maven-resources-plugin,
# maven-compiler-plugin and their transitive dependencies. Provenance runs
# `mvn -o dependency:list`, which pulls in maven-dependency-plugin. Maven in
# offline mode also resolves the plugins bound to phases it will not execute,
# so clean, install, deploy and site are warmed too.
#
# Scoring runs with the network disconnected, where anything absent here fails
# every batch identically with "Cannot access central in offline mode" -- which
# reads as a candidate that implemented nothing rather than as a missing plugin.
# Each of the commands below was verified to fail offline before being added.
RUN mkdir -p /tmp/warm/src/test/java/warm && cd /tmp/warm && \
    printf '%s\n' \
      '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>' \
      '<groupId>warm</groupId><artifactId>warm</artifactId><version>1.0</version>' \
      '<properties><maven.compiler.source>17</maven.compiler.source>' \
      '<maven.compiler.target>17</maven.compiler.target>' \
      '<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding></properties>' \
      '<dependencies><dependency><groupId>org.junit.jupiter</groupId>' \
      "<artifactId>junit-jupiter</artifactId><version>${JUNIT_VERSION}</version>" \
      '<scope>test</scope></dependency></dependencies>' \
      '<build><plugins><plugin><groupId>org.apache.maven.plugins</groupId>' \
      '<artifactId>maven-surefire-plugin</artifactId>' \
      "<version>${SUREFIRE_VERSION}</version></plugin></plugins></build></project>" \
      > pom.xml && \
    printf '%s\n' \
      'package warm;' \
      'import org.junit.jupiter.api.Test;' \
      'import org.junit.jupiter.params.ParameterizedTest;' \
      'import org.junit.jupiter.params.provider.ValueSource;' \
      'import static org.junit.jupiter.api.Assertions.*;' \
      'class WarmTest {' \
      '  @Test void plain() { assertEquals(2, 1 + 1); }' \
      '  @ParameterizedTest @ValueSource(ints = {1, 2}) void parameterised(int n) { assertTrue(n > 0); }' \
      '}' \
      > src/test/java/warm/WarmTest.java && \
    mvn -B clean test install && \
    mvn -B dependency:list -DoutputAbsoluteArtifactFilename=true && \
    mvn -B dependency:resolve dependency:resolve-plugins && \
    cd / && rm -rf /tmp/warm && \
    rm -rf /root/.m2/repository/warm

WORKDIR /workspace
