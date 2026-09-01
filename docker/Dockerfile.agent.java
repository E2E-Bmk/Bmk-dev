ARG BASE_IMAGE=spec2repo-java:latest
FROM ${BASE_IMAGE}

# Java AGENT image: the scoring toolchain plus the artifacts a Java spec
# promises are on the compile classpath.
#
# The agent container runs with --network=none from the first command, while
# the scoring container still has the network while it runs setup. So the
# scoring image gets away with resolving a dependency on demand and the agent
# image does not: anything a candidate legitimately declares but that is absent
# here fails with "Cannot access central in offline mode", and the agent cannot
# compile or test a single line. It then submits unverified code, which scores
# near zero and reads as a hard task rather than a missing jar.
#
# spec2repo-java carries slf4j-api 1.7.36 only, and only as a transitive of
# Maven's own plugins. Java specs name 2.0.16, so that is the version warmed
# here. Keep this in step with the `Appendix A: Environment` of the Java tasks.
#
# javassist 3.30.2-GA is warmed for the same reason. Every japicmp-derived Java
# task names it as provided on the compile classpath, and it is reachable from
# nothing Maven already pulls. Without it a candidate that resolves the declared
# dependency offline is stuck, and the observed way out is to hand-write a
# javassist stub under /tmp, install it as the real coordinates and then code
# against its own invented signatures. That produces a zero which measures the
# image, not the model.

ARG SLF4J_VERSION=2.0.16
ARG JAVASSIST_VERSION=3.30.2-GA

RUN mkdir -p /tmp/warm/src/main/java/warm && cd /tmp/warm && \
    printf '%s\n' \
      '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>' \
      '<groupId>warm</groupId><artifactId>warm</artifactId><version>1.0</version>' \
      '<packaging>jar</packaging>' \
      '<properties><maven.compiler.source>21</maven.compiler.source>' \
      '<maven.compiler.target>21</maven.compiler.target>' \
      '<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding></properties>' \
      '<dependencies><dependency><groupId>org.slf4j</groupId>' \
      "<artifactId>slf4j-api</artifactId><version>${SLF4J_VERSION}</version>" \
      '</dependency><dependency><groupId>org.javassist</groupId>' \
      "<artifactId>javassist</artifactId><version>${JAVASSIST_VERSION}</version>" \
      '</dependency></dependencies></project>' \
      > pom.xml && \
    printf '%s\n' \
      'package warm;' \
      'import org.slf4j.Logger;' \
      'import org.slf4j.LoggerFactory;' \
      'import javassist.ClassPool;' \
      'public class Warm { static final Logger LOG = LoggerFactory.getLogger(Warm.class);' \
      '  static final ClassPool POOL = ClassPool.getDefault(); }' \
      > src/main/java/warm/Warm.java && \
    mvn -B clean install && \
    cd / && rm -rf /tmp/warm && \
    rm -rf /root/.m2/repository/warm

# Prove the warm set is sufficient offline. A build that only ever succeeded
# with the network is not evidence for a container that has none, and this is
# the one place the difference is cheap to catch.
RUN mkdir -p /tmp/verify/src/main/java/v && cd /tmp/verify && \
    printf '%s\n' \
      '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>' \
      '<groupId>v</groupId><artifactId>v</artifactId><version>1.0</version>' \
      '<packaging>jar</packaging>' \
      '<properties><maven.compiler.source>21</maven.compiler.source>' \
      '<maven.compiler.target>21</maven.compiler.target>' \
      '<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding></properties>' \
      '<dependencies><dependency><groupId>org.slf4j</groupId>' \
      "<artifactId>slf4j-api</artifactId><version>${SLF4J_VERSION}</version>" \
      '</dependency><dependency><groupId>org.javassist</groupId>' \
      "<artifactId>javassist</artifactId><version>${JAVASSIST_VERSION}</version>" \
      '<scope>provided</scope></dependency></dependencies></project>' \
      > pom.xml && \
    printf '%s\n' \
      'package v;' \
      'import org.slf4j.LoggerFactory;' \
      'import javassist.ClassPool;' \
      'import javassist.CtClass;' \
      'import javassist.CtNewMethod;' \
      'import javassist.bytecode.ConstPool;' \
      'import javassist.bytecode.AnnotationsAttribute;' \
      'import javassist.bytecode.annotation.Annotation;' \
      'import javassist.bytecode.annotation.ClassMemberValue;' \
      'import javassist.bytecode.annotation.EnumMemberValue;' \
      'public class V {' \
      '  public static void main(String[] a) throws Exception {' \
      '    LoggerFactory.getLogger(V.class);' \
      '    CtClass k = ClassPool.getDefault().makeClass("v.Probe");' \
      '    k.addMethod(CtNewMethod.make("public void run(){}", k));' \
      '    ConstPool cp = k.getClassFile().getConstPool();' \
      '    AnnotationsAttribute at =' \
      '        new AnnotationsAttribute(cp, AnnotationsAttribute.visibleTag);' \
      '    Annotation an = new Annotation("v.Marker", cp);' \
      '    an.addMemberValue("type", new ClassMemberValue("java.lang.String", cp));' \
      '    at.addAnnotation(an);' \
      '    new EnumMemberValue(cp);' \
      '  }' \
      '}' \
      > src/main/java/v/V.java && \
    mvn -B -o clean install && \
    cd / && rm -rf /tmp/verify && \
    rm -rf /root/.m2/repository/v

WORKDIR /workspace
