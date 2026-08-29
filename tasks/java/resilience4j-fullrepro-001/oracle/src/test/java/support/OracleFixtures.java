package support;

import io.github.resilience4j.core.ContextAwareScheduledThreadPoolExecutor;
import io.github.resilience4j.spring6.fallback.CompletionStageFallbackDecorator;
import io.github.resilience4j.spring6.fallback.DefaultFallbackDecorator;
import io.github.resilience4j.spring6.fallback.FallbackDecorators;
import io.github.resilience4j.spring6.fallback.FallbackExecutor;
import io.github.resilience4j.spring6.fallback.FallbackMethod;
import io.github.resilience4j.spring6.spelresolver.DefaultSpelResolver;
import io.github.resilience4j.spring6.spelresolver.SpelResolver;
import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import org.springframework.beans.factory.support.DefaultListableBeanFactory;
import org.springframework.core.DefaultParameterNameDiscoverer;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.aspectj.lang.ProceedingJoinPoint;
import reactor.core.publisher.Mono;

/** Public, specification-shaped fixtures shared by the generated oracle. */
public final class OracleFixtures {
    private OracleFixtures() { }

    public static DefaultSpelResolver resolver() {
        DefaultListableBeanFactory beans = new DefaultListableBeanFactory();
        beans.registerSingleton("chromaticName", new NameBean("ultraviolet-731"));
        return new DefaultSpelResolver(new SpelExpressionParser(), new DefaultParameterNameDiscoverer(), beans);
    }

    public static Method expressionMethod() throws NoSuchMethodException {
        return ExpressionService.class.getMethod("combine", String.class, int.class);
    }

    public static FallbackMethod fallback(String fallbackName, String originalName, Class<?>... parameterTypes) throws Exception {
        ProjectionService service = new ProjectionService();
        Method original = ProjectionService.class.getMethod(originalName, parameterTypes);
        Object[] arguments = parameterTypes.length == 0 ? new Object[0] : new Object[]{"quartz-481"};
        return FallbackMethod.create(fallbackName, original, arguments, service, service);
    }

    public static FallbackMethod stringFallback(String fallbackName) throws Exception {
        ProjectionService service = new ProjectionService();
        Method original = ProjectionService.class.getMethod("original", String.class);
        return FallbackMethod.create(fallbackName, original, new Object[]{"quartz-481"}, service, service);
    }

    public static FallbackMethod stageFallback(String fallbackName) throws Exception {
        ProjectionService service = new ProjectionService();
        Method original = ProjectionService.class.getMethod("stageOriginal", String.class);
        return FallbackMethod.create(fallbackName, original, new Object[]{"quartz-481"}, service, service);
    }

    public static FallbackMethod monoFallback(String fallbackName) throws Exception {
        ProjectionService service = new ProjectionService();
        Method original = ProjectionService.class.getMethod("monoOriginal", String.class);
        return FallbackMethod.create(fallbackName, original, new Object[]{"quartz-481"}, service, service);
    }

    public static FallbackExecutor fallbackExecutor() {
        SpelResolver literalResolver = (method, args, value) -> value;
        return new FallbackExecutor(literalResolver,
            new FallbackDecorators(List.of(new CompletionStageFallbackDecorator(), new DefaultFallbackDecorator())));
    }

    public static ContextAwareScheduledThreadPoolExecutor scheduler() {
        return ContextAwareScheduledThreadPoolExecutor.newScheduledThreadPool().corePoolSize(1).build();
    }

    public static ProceedingJoinPoint proceedingJoinPoint(Object projection) {
        return (ProceedingJoinPoint) Proxy.newProxyInstance(OracleFixtures.class.getClassLoader(),
            new Class<?>[]{ProceedingJoinPoint.class}, (proxy, method, args) -> {
                if (method.getName().equals("proceed")) return projection;
                if (method.getName().equals("getArgs")) return new Object[0];
                if (method.getReturnType().equals(String.class)) return "oracle-joinpoint";
                if (method.getReturnType().equals(boolean.class)) return false;
                if (method.getReturnType().equals(int.class)) return 0;
                return null;
            });
    }

    public static final class NameBean {
        private final String value;
        public NameBean(String value) { this.value = value; }
        public String value() { return value; }
    }

    public static class ExpressionService {
        public String combine(String token, int count) { return token + count; }
    }

    public static class ProjectionService {
        public String original(String token) { return "primary:" + token; }
        public String recover(String token, IllegalArgumentException failure) { return "specific:" + token; }
        public String recover(String token, RuntimeException failure) { return "runtime:" + token; }
        public String recover(String token, Throwable failure) { return "throwable:" + token; }
        public String throwableOnly(IllegalStateException failure) { return "only:" + failure.getClass().getSimpleName(); }
        public String stateOnly(String token, IllegalStateException failure) { return "state:" + token; }
        public Integer wrongReturn(String token, IllegalArgumentException failure) { return 481; }
        public String duplicate(String token, IllegalArgumentException failure) { return "args"; }
        public String duplicate(IllegalArgumentException failure) { return "only"; }
        public String explode(String token, IllegalArgumentException failure) { throw new UnsupportedOperationException("fallback-signal-883"); }
        public CompletionStage<String> stageOriginal(String token) { return CompletableFuture.completedFuture("stage-primary:" + token); }
        public CompletionStage<String> stageRecover(String token, IllegalArgumentException failure) {
            return CompletableFuture.completedFuture("stage-fallback:" + token);
        }
        public CompletionStage<String> stageExplode(String token, IllegalArgumentException failure) {
            return CompletableFuture.failedFuture(new UnsupportedOperationException("stage-fallback-signal-997"));
        }
        public Mono<String> monoOriginal(String token) { return Mono.just("mono-primary:" + token); }
        public Mono<String> monoRecover(String token, IllegalArgumentException failure) { return Mono.just("mono-fallback:" + token); }
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @Inherited
    public @interface Marker { String value(); }

    @Marker("direct-211") public static class DirectMarked { }
    @Marker("base-307") public static class MarkedBase { }
    public static class MarkedChild extends MarkedBase { }
    @Marker("child-401") public static class DirectMarkedChild extends MarkedBase { }
    @Marker("interface-419") public interface MarkedContract { String call(); }
    public static class MarkedImplementation implements MarkedContract { public String call() { return "ok"; } }
    public interface PlainContract { String call(); }
}
