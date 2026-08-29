# `resilience4j-spring6` Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`resilience4j-spring6` is a Java integration library that applies named resilience policies to Spring Framework 6 beans through annotations, external configuration, registries, expression-based names, return-type adapters, and fallback methods.

A single annotated invocation is visible through its caller-facing result or failure, the named registry component and configuration, fallback selection, asynchronous or reactive completion, component events, timer measurements, and aspect ordering.

## Non-Goals

- This specification does not require Spring Boot auto-configuration or Spring Boot property binding.
- This specification does not require implementations of the companion Circuit Breaker, Retry, Rate Limiter, Bulkhead, Time Limiter, Timer, annotation, Reactor, or RxJava artifacts.
- This specification does not define private fields, helper algorithms, cache layout, reflection caches, exact exception messages, log wording, or object text representations.
- This specification does not require external services, live network calls, persistent storage, HTTP endpoints, or a command-line application.
- This specification does not define dependency versions or build-tool choices beyond the Maven delivery contract in Appendix A.

## Representative Workflows

### Named Circuit Breaker with Fallback

```java
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

final class GreetingService {
    @CircuitBreaker(name = "greeting", configuration = "shared", fallbackMethod = "recover")
    public String greet(String name) { throw new IllegalStateException(name); }
    public String recover(String name, IllegalStateException failure) { return "hello " + name; }
}

try (var context = new AnnotationConfigApplicationContext(AppConfig.class)) {
    String value = context.getBean(GreetingService.class).greet("Ada");
    assert value.equals("hello Ada");
}
```

The annotation selects a component named `greeting`, obtains configuration `shared`, records the failed primary call through that component, and projects the compatible fallback result to the caller.

### Expression-Selected Retry with Asynchronous Completion

```java
import io.github.resilience4j.retry.annotation.Retry;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;

final class RemoteService {
    @Retry(name = "#{#tenant}", fallbackMethod = "recover")
    public CompletionStage<String> load(String tenant) {
        return CompletableFuture.failedFuture(new IllegalArgumentException(tenant));
    }
    public CompletionStage<String> recover(String tenant, IllegalArgumentException failure) {
        return CompletableFuture.completedFuture("cached:" + tenant);
    }
}
```

The expression uses the method argument to select a registry name, and the returned stage retains its asynchronous family while its terminal failure is replaced by the compatible fallback stage.

## Annotation Interception and Policy Resolution

Annotation-driven interception connects a Spring invocation to a named resilience component and a deterministic configuration choice.

**Annotation discovery.**

- WHEN a proxied method or its target class carries a supported resilience annotation, THEN the corresponding aspect must intercept the invocation.
- WHEN neither the method, target class, nor proxied interface exposes the matching annotation, THEN the aspect advice must invoke the join point exactly once without applying a resilience component.

**Name and configuration selection.**

- WHEN an annotation supplies `name`, THEN the aspect must resolve that value through the configured `SpelResolver` using the invoked method and arguments.
- WHEN an annotation supplies an empty `configuration`, THEN the aspect must use the resolved `name` as the registry configuration key.
- WHEN an annotation supplies a non-empty `configuration`, THEN the aspect must use that value as the registry configuration key while retaining the resolved `name` as the instance name.

**Registry lookup.**

- WHEN the selected registry contains the configuration key, THEN the aspect must create or retrieve the named component with that registered configuration.
- WHEN the selected registry lacks the configuration key, THEN the aspect must create or retrieve the named component with the registry default configuration.

**Fallback boundary.**

- WHEN annotation processing produces an invocation failure and `fallbackMethod` resolves to a compatible fallback, THEN the aspect must return the fallback projection instead of the failed primary projection.

## Synchronous, Asynchronous, and Reactive Execution

Execution adapters preserve each public return family while applying the selected resilience policy at the correct completion boundary.

**Synchronous and stage values.**

- WHEN a Circuit Breaker, Rate Limiter, Retry, Bulkhead, or Timer aspect receives an ordinary synchronous return type, THEN the aspect must execute the join point through the corresponding checked-supplier policy.
- WHEN Circuit Breaker, Rate Limiter, Retry, Bulkhead, Timer, or Time Limiter advice receives a `CompletionStage` return type, THEN the aspect must preserve asynchronous completion while applying the corresponding policy to success and failure signals.

**Extension dispatch.**

- WHERE an ordered aspect-extension list is present, the aspect must invoke the first extension whose `canHandleReturnType` accepts the declared return type.
- WHEN no registered extension accepts the return type, THEN Circuit Breaker, Rate Limiter, Retry, Bulkhead, and Timer advice must use their documented synchronous or `CompletionStage` fallback path.

**Time limits.**

- IF Time Limiter advice receives neither `CompletionStage` nor a return type accepted by a registered extension, THEN the advice must raise `IllegalReturnTypeException`.

**Bulkhead modes.**

- WHEN a Bulkhead annotation selects `Bulkhead.Type.SEMAPHORE`, THEN the aspect must execute ordinary values through `Bulkhead` and `CompletionStage` values through its asynchronous semaphore path.
- WHEN a Bulkhead annotation selects `Bulkhead.Type.THREADPOOL` for a `CompletionStage`, THEN the aspect must execute through the named `ThreadPoolBulkhead` and return a completion-stage projection.
- IF a thread-pool Bulkhead is applied to a non-`CompletionStage` return type, THEN the aspect must raise `IllegalStateException`.
- IF a thread-pool Bulkhead rejects a `CompletionStage` invocation, THEN the aspect must return an exceptionally completed future whose failure is the rejection.

**Reactive adapters.**

- WHERE Reactor is present, the Reactor extensions must preserve `Mono` and `Flux` shapes while applying Circuit Breaker, Rate Limiter, Retry, Bulkhead, Time Limiter, and Timer policies to their terminal signals.
- WHERE RxJava 2 is present, the RxJava 2 extensions must preserve supported reactive shapes while applying the selected policy to their terminal signals.
- WHERE RxJava 3 is present, the RxJava 3 extensions must preserve supported reactive shapes while applying the selected policy to their terminal signals.

## Fallback Selection and Projection

Fallback resolution maps a primary failure to the most specific compatible recovery method without changing the caller-facing value family.

**Fallback lookup.**

- WHEN `fallbackMethod` is empty or resolves to no compatible method, THEN `FallbackExecutor.execute` must invoke the primary function.
- WHEN `fallbackMethod` resolves to a simple method name, THEN fallback lookup must target the proxied service and accept either the original parameter list followed by a `Throwable` subtype or a single `Throwable` subtype parameter.
- WHEN `fallbackMethod` resolves to `beanName::methodName`, THEN fallback lookup must target that Spring bean and the named method.
- IF `FallbackMethod.create` finds no method with a compatible name, parameter contract, and assignable return type, THEN it must raise `NoSuchMethodException`.

**Exception specificity.**

- WHEN multiple compatible fallback overloads exist, THEN `FallbackMethod.fallback` must select the overload whose final exception parameter is nearest to the thrown exception in its superclass chain.
- WHEN the available fallback overloads do not accept the thrown exception, THEN `FallbackMethod.fallback` must rethrow the original exception.
- IF two fallback declarations cover the same exception type with different parameter lists, THEN fallback extraction must raise `IllegalStateException`.

**Invocation projection.**

- WHEN a selected fallback accepts the failure, THEN it must receive the original invocation arguments followed by the failure, except that a throwable-only fallback must receive only the failure.
- IF the selected fallback itself throws, THEN fallback invocation must propagate the fallback failure rather than an invocation-wrapper exception.

**Async and reactive fallback.**

- WHEN a `CompletionStage` primary completes exceptionally, THEN `CompletionStageFallbackDecorator` must complete its returned stage with the fallback value or the resulting fallback failure.
- WHERE Reactor or RxJava fallback decorators support the declared return type, the decorator must recover terminal errors without changing the reactive family.

## Configuration, Registries, and Aspect Order

Spring configuration assembles registries, customizers, events, conditional adapters, and deterministic aspect precedence for annotated beans.

**Registry construction.**

- WHEN a Spring configuration class creates a component registry, THEN it must apply named configurations, registry event consumers, event-consumer buffers, tags, and matching customizers supplied through the corresponding configuration properties.
- WHEN multiple config customizers are supplied, THEN the configuration class must expose a composite customizer that applies the matching customizers to each named configuration.
- WHEN no registry event consumer is supplied, THEN the configuration class must expose a no-op composite consumer that leaves registry creation usable.
- WHEN configured event-consumer buffer sizes name a resilience instance, THEN the registry initialization must attach that instance to the corresponding `EventConsumerRegistry` buffer.

**Conditional beans.**

- WHERE AspectJ is present, each configuration class must expose its corresponding aspect bean.
- WHERE Reactor, RxJava 2, or RxJava 3 is present together with AspectJ, the configuration class must expose the matching optional aspect-extension bean.

**Aspect ordering.**

- The default aspect orders must be Retry at `Ordered.LOWEST_PRECEDENCE - 5`, Circuit Breaker at minus 4, Rate Limiter at minus 3, Time Limiter at minus 2, Bulkhead at minus 1, and Timer at `Ordered.LOWEST_PRECEDENCE`.
- WHEN an aspect-order property setter receives a new integer, THEN the matching aspect `getOrder` projection must return that integer.

**Executor lifecycle.**

- WHEN `RetryAspect.close` or `TimeLimiterAspect.close` is invoked, THEN the aspect must shut down its scheduler and preserve interruption by restoring the current thread interrupt flag.

## Expression and Annotation Resolution

Expression and annotation resolution turn literal, placeholder, method, bean, class, and proxy metadata into names used by every aspect.

**Expression forms.**

- WHEN `SpelResolver.resolve` receives null, empty, or plain text, THEN it must return that value unchanged.
- WHERE an embedded value resolver is present, a full `${...}` placeholder must resolve through that embedded value resolver.
- WHEN a value contains a `#{...}` template, THEN `DefaultSpelResolver` must evaluate the template as a String with method arguments and Spring bean references available.
- WHEN a value starts with `#`, THEN `DefaultSpelResolver` must evaluate it against the invoked method, named parameters, arguments, and a `SpelRootObject`.
- WHEN a value starts with `@`, THEN `DefaultSpelResolver` must evaluate it with Spring bean resolution enabled and return the String result.

**Root projection.**

- The `SpelRootObject` must expose the declaring class name, method name, and original argument array through `getClassName`, `getMethodName`, and `getArgs`.

**Annotation extraction.**

- WHEN `AnnotationExtractor.extract` receives a class, THEN it must prefer a directly present annotation and otherwise search implemented interfaces and superclass declarations.
- WHEN `AnnotationExtractor.extractAnnotationFromProxy` receives a proxy, THEN it must inspect the proxy interfaces for the requested annotation and return null when none is present.

## Timer and Extension Service Provider Behavior

Timer advice and extension service providers add optional return-type handling while preserving the common aspect contract.

**Timer projection.**

- WHEN Timer advice surrounds a successful synchronous, `CompletionStage`, Reactor, or RxJava invocation, THEN the selected Timer must record the successful execution and preserve the original value shape.
- WHEN Timer advice surrounds a failed synchronous or asynchronous invocation, THEN the selected Timer must record the failure before fallback processing projects a recovery value.

**Extension contracts.**

- The Circuit Breaker, Rate Limiter, Retry, Bulkhead, Time Limiter, and Timer aspect-extension interfaces must expose `canHandleReturnType` and `handle` as the return-type dispatch contract.
- The `FallbackDecorator` interface must expose `supports` and `decorate`, and `FallbackDecorators` must select the first supporting decorator or use `DefaultFallbackDecorator`.

**Classpath conditions.**

- WHEN a classpath condition checks for AspectJ, Reactor, RxJava 2, or RxJava 3, THEN `matches` must return whether the corresponding defining class is loadable.

**Utility contracts.**

- WHEN `AspectUtil.newHashSet` receives values, THEN it must return an unmodifiable set containing the distinct supplied values.

## State Model

The core state is one intercepted invocation joined to annotation metadata, resolved names, a registry component, its selected configuration, aspect precedence, primary execution, optional fallback execution, and a caller-facing synchronous or terminal projection.

- The core invocation state must project the resolved instance name, selected configuration key, registry component, aspect order, primary result or failure, fallback result or failure, and asynchronous or reactive terminal state consistently.
- WHEN an annotated invocation lazily creates a named component, THEN later registry lookup by that name must return the same configured component.
- WHILE an asynchronous or reactive invocation is incomplete, the returned value must preserve its declared family and expose policy or fallback completion only through its terminal signal.

## Error Semantics

| Condition | Required result |
|---|---|
| Time Limiter sees an unsupported return type | `IllegalReturnTypeException` |
| Thread-pool Bulkhead sees a non-stage return type | `IllegalStateException` |
| Thread-pool Bulkhead rejects a stage invocation | Exceptionally completed future carrying the rejection |
| `FallbackMethod.create` finds no compatible method | `NoSuchMethodException` |
| Duplicate fallback declarations cover one exception type incompatibly | `IllegalStateException` |
| No fallback overload accepts the primary failure | Original failure is rethrown or remains the terminal failure |
| Selected fallback throws | Fallback failure is propagated without an invocation wrapper |
| Invalid expression syntax, evaluation, or result conversion | The corresponding Spring expression or Java conversion exception is propagated |

## Cross-View Invariants

1. The name selected by annotation and expression resolution must equal the name visible in the corresponding registry instance and its emitted component events.
2. The configuration key selected by an annotation must determine the configuration visible from the lazily created registry component while the component retains the independently resolved instance name.
3. The synchronous primary failure accepted by fallback selection must produce the fallback return value while the selected resilience component still records the failed primary execution.
4. The asynchronous or reactive primary failure accepted by fallback selection must preserve the declared return family and complete with the fallback projection.
5. The aspect-order property setters, aspect `getOrder` results, and nesting of multiple annotations on one invocation must agree on the configured order.
6. The named registry configuration assembled from external properties and customizers must agree with the configuration used by the aspect-created component and its event-consumer registration.
7. The return type accepted by an aspect extension must agree with the adapter family of the returned value and with the fallback decorator selected for terminal failures.
8. The closing of Retry or Time Limiter advice must synchronize scheduler lifecycle with subsequent resource observation without changing previously completed invocation results.

## Public Interface

### Import Surface

```java
import io.github.resilience4j.spring6.bulkhead.configure.BulkheadAspect;
import io.github.resilience4j.spring6.bulkhead.configure.BulkheadAspectExt;
import io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfiguration;
import io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfigurationProperties;
import io.github.resilience4j.spring6.bulkhead.configure.ReactorBulkheadAspectExt;
import io.github.resilience4j.spring6.bulkhead.configure.RxJava2BulkheadAspectExt;
import io.github.resilience4j.spring6.bulkhead.configure.RxJava3BulkheadAspectExt;
```

```java
import io.github.resilience4j.spring6.bulkhead.configure.threadpool.ThreadPoolBulkheadConfiguration;
```

```java
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerAspect;
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerAspectExt;
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfiguration;
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfigurationProperties;
import io.github.resilience4j.spring6.circuitbreaker.configure.ReactorCircuitBreakerAspectExt;
import io.github.resilience4j.spring6.circuitbreaker.configure.RxJava2CircuitBreakerAspectExt;
import io.github.resilience4j.spring6.circuitbreaker.configure.RxJava3CircuitBreakerAspectExt;
```

```java
import io.github.resilience4j.spring6.fallback.CompletionStageFallbackDecorator;
import io.github.resilience4j.spring6.fallback.DefaultFallbackDecorator;
import io.github.resilience4j.spring6.fallback.FallbackDecorator;
import io.github.resilience4j.spring6.fallback.FallbackDecorators;
import io.github.resilience4j.spring6.fallback.FallbackExecutor;
import io.github.resilience4j.spring6.fallback.FallbackMethod;
import io.github.resilience4j.spring6.fallback.ReactorFallbackDecorator;
import io.github.resilience4j.spring6.fallback.RxJava2FallbackDecorator;
import io.github.resilience4j.spring6.fallback.RxJava3FallbackDecorator;
```

```java
import io.github.resilience4j.spring6.fallback.configure.FallbackConfiguration;
```

```java
import io.github.resilience4j.spring6.micrometer.configure.ReactorTimerAspectExt;
import io.github.resilience4j.spring6.micrometer.configure.RxJava2TimerAspectExt;
import io.github.resilience4j.spring6.micrometer.configure.RxJava3TimerAspectExt;
import io.github.resilience4j.spring6.micrometer.configure.TimerAspect;
import io.github.resilience4j.spring6.micrometer.configure.TimerAspectExt;
import io.github.resilience4j.spring6.micrometer.configure.TimerConfiguration;
import io.github.resilience4j.spring6.micrometer.configure.TimerConfigurationProperties;
```

```java
import io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterAspect;
import io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterAspectExt;
import io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfiguration;
import io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfigurationProperties;
import io.github.resilience4j.spring6.ratelimiter.configure.ReactorRateLimiterAspectExt;
import io.github.resilience4j.spring6.ratelimiter.configure.RxJava2RateLimiterAspectExt;
import io.github.resilience4j.spring6.ratelimiter.configure.RxJava3RateLimiterAspectExt;
```

```java
import io.github.resilience4j.spring6.retry.configure.ReactorRetryAspectExt;
import io.github.resilience4j.spring6.retry.configure.RetryAspect;
import io.github.resilience4j.spring6.retry.configure.RetryAspectExt;
import io.github.resilience4j.spring6.retry.configure.RetryConfiguration;
import io.github.resilience4j.spring6.retry.configure.RetryConfigurationProperties;
import io.github.resilience4j.spring6.retry.configure.RxJava2RetryAspectExt;
import io.github.resilience4j.spring6.retry.configure.RxJava3RetryAspectExt;
```

```java
import io.github.resilience4j.spring6.spelresolver.DefaultSpelResolver;
import io.github.resilience4j.spring6.spelresolver.SpelResolver;
import io.github.resilience4j.spring6.spelresolver.SpelRootObject;
```

```java
import io.github.resilience4j.spring6.spelresolver.configure.SpelResolverConfiguration;
```

```java
import io.github.resilience4j.spring6.timelimiter.configure.IllegalReturnTypeException;
import io.github.resilience4j.spring6.timelimiter.configure.ReactorTimeLimiterAspectExt;
import io.github.resilience4j.spring6.timelimiter.configure.RxJava2TimeLimiterAspectExt;
import io.github.resilience4j.spring6.timelimiter.configure.RxJava3TimeLimiterAspectExt;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterAspect;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterAspectExt;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfiguration;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfigurationProperties;
```

```java
import io.github.resilience4j.spring6.utils.AnnotationExtractor;
import io.github.resilience4j.spring6.utils.AspectJOnClasspathCondition;
import io.github.resilience4j.spring6.utils.AspectUtil;
import io.github.resilience4j.spring6.utils.ReactorOnClasspathCondition;
import io.github.resilience4j.spring6.utils.RxJava2OnClasspathCondition;
import io.github.resilience4j.spring6.utils.RxJava3OnClasspathCondition;
```

### Public Members

| Type | Public members |
|---|---|
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadAspect` | constructors, `matchAnnotatedClassOrMethod`, `bulkheadAroundAdvice`, `getOrder` |
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadAspectExt` | `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfiguration` | constructors, `compositeBulkheadCustomizer`, `bulkheadRegistry`, `bulkheadRegistryEventConsumer`, `bulkheadAspect`, `rxJava2BulkHeadAspectExt`, `rxJava3BulkHeadAspectExt`, `reactorBulkHeadAspectExt`, `bulkheadEventConsumerRegistry` |
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfigurationProperties` | constructors, `getBulkheadAspectOrder`, `setBulkheadAspectOrder` |
| `io.github.resilience4j.spring6.bulkhead.configure.ReactorBulkheadAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.bulkhead.configure.RxJava2BulkheadAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.bulkhead.configure.RxJava3BulkheadAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.bulkhead.configure.threadpool.ThreadPoolBulkheadConfiguration` | constructors, `compositeThreadPoolBulkheadCustomizer`, `threadPoolBulkheadRegistry`, `threadPoolBulkheadRegistryEventConsumer` |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerAspect` | constructors, `matchAnnotatedClassOrMethod`, `circuitBreakerAroundAdvice`, `getOrder` |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerAspectExt` | `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfiguration` | constructors, `compositeCircuitBreakerCustomizer`, `circuitBreakerRegistry`, `circuitBreakerRegistryEventConsumer`, `circuitBreakerAspect`, `rxJava2CircuitBreakerAspect`, `rxJava3CircuitBreakerAspect`, `reactorCircuitBreakerAspect`, `eventConsumerRegistry`, `registerEventConsumer` |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfigurationProperties` | constructors, `getCircuitBreakerAspectOrder`, `setCircuitBreakerAspectOrder` |
| `io.github.resilience4j.spring6.circuitbreaker.configure.ReactorCircuitBreakerAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.circuitbreaker.configure.RxJava2CircuitBreakerAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.circuitbreaker.configure.RxJava3CircuitBreakerAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.fallback.CompletionStageFallbackDecorator` | constructors, `supports`, `decorate` |
| `io.github.resilience4j.spring6.fallback.DefaultFallbackDecorator` | constructors, `supports`, `decorate` |
| `io.github.resilience4j.spring6.fallback.FallbackDecorator` | `supports`, `decorate` |
| `io.github.resilience4j.spring6.fallback.FallbackDecorators` | constructors, `decorate`, `getFallbackDecorators` |
| `io.github.resilience4j.spring6.fallback.FallbackExecutor` | constructors, `setBeanFactory`, `execute` |
| `io.github.resilience4j.spring6.fallback.FallbackMethod` | `create`, `fallback`, `getReturnType` |
| `io.github.resilience4j.spring6.fallback.ReactorFallbackDecorator` | constructors, `supports`, `decorate` |
| `io.github.resilience4j.spring6.fallback.RxJava2FallbackDecorator` | constructors, `supports`, `decorate` |
| `io.github.resilience4j.spring6.fallback.RxJava3FallbackDecorator` | constructors, `supports`, `decorate` |
| `io.github.resilience4j.spring6.fallback.configure.FallbackConfiguration` | constructors, `rxJava2FallbackDecorator`, `rxJava3FallbackDecorator`, `reactorFallbackDecorator`, `completionStageFallbackDecorator`, `fallbackDecorators`, `fallbackExecutor` |
| `io.github.resilience4j.spring6.micrometer.configure.ReactorTimerAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.micrometer.configure.RxJava2TimerAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.micrometer.configure.RxJava3TimerAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.micrometer.configure.TimerAspect` | constructors, `matchAnnotatedClassOrMethod`, `timerAroundAdvice`, `getOrder` |
| `io.github.resilience4j.spring6.micrometer.configure.TimerAspectExt` | `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.micrometer.configure.TimerConfiguration` | constructors, `compositeTimerCustomizer`, `timerRegistry`, `timerRegistryEventConsumer`, `timerAspect`, `rxJava2TimerAspectExt`, `rxJava3TimerAspectExt`, `reactorTimerAspectExt`, `timerEventsConsumerRegistry` |
| `io.github.resilience4j.spring6.micrometer.configure.TimerConfigurationProperties` | constructors, `getTimerAspectOrder`, `setTimerAspectOrder` |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterAspect` | constructors, `matchAnnotatedClassOrMethod`, `rateLimiterAroundAdvice`, `getOrder` |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterAspectExt` | `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfiguration` | constructors, `compositeRateLimiterCustomizer`, `rateLimiterRegistry`, `rateLimiterRegistryEventConsumer`, `rateLimiterAspect`, `rxJava2RateLimiterAspectExt`, `rxJava3RateLimiterAspectExt`, `reactorRateLimiterAspectExt`, `rateLimiterEventsConsumerRegistry` |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfigurationProperties` | constructors, `getRateLimiterAspectOrder`, `setRateLimiterAspectOrder` |
| `io.github.resilience4j.spring6.ratelimiter.configure.ReactorRateLimiterAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.ratelimiter.configure.RxJava2RateLimiterAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.ratelimiter.configure.RxJava3RateLimiterAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.retry.configure.ReactorRetryAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.retry.configure.RetryAspect` | constructors, `matchAnnotatedClassOrMethod`, `retryAroundAdvice`, `getOrder`, `close` |
| `io.github.resilience4j.spring6.retry.configure.RetryAspectExt` | `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.retry.configure.RetryConfiguration` | constructors, `compositeRetryCustomizer`, `retryRegistry`, `retryRegistryEventConsumer`, `retryAspect`, `rxJava2RetryAspectExt`, `rxJava3RetryAspectExt`, `reactorRetryAspectExt`, `retryEventConsumerRegistry` |
| `io.github.resilience4j.spring6.retry.configure.RetryConfigurationProperties` | constructors, `getRetryAspectOrder`, `setRetryAspectOrder` |
| `io.github.resilience4j.spring6.retry.configure.RxJava2RetryAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.retry.configure.RxJava3RetryAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.spelresolver.DefaultSpelResolver` | constructors, `resolve`, `setEmbeddedValueResolver` |
| `io.github.resilience4j.spring6.spelresolver.SpelResolver` | `resolve` |
| `io.github.resilience4j.spring6.spelresolver.SpelRootObject` | constructors, `getClassName`, `getMethodName`, `getArgs` |
| `io.github.resilience4j.spring6.spelresolver.configure.SpelResolverConfiguration` | constructors, `spelResolver`, `spelExpressionParser`, `parameterNameDiscoverer` |
| `io.github.resilience4j.spring6.timelimiter.configure.IllegalReturnTypeException` | constructors |
| `io.github.resilience4j.spring6.timelimiter.configure.ReactorTimeLimiterAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.timelimiter.configure.RxJava2TimeLimiterAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.timelimiter.configure.RxJava3TimeLimiterAspectExt` | constructors, `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterAspect` | constructors, `matchAnnotatedClassOrMethod`, `timeLimiterAroundAdvice`, `getOrder`, `close` |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterAspectExt` | `canHandleReturnType`, `handle` |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfiguration` | constructors, `compositeTimeLimiterCustomizer`, `timeLimiterRegistry`, `timeLimiterRegistryEventConsumer`, `timeLimiterAspect`, `rxJava2TimeLimiterAspectExt`, `rxJava3TimeLimiterAspectExt`, `reactorTimeLimiterAspectExt`, `timeLimiterEventsConsumerRegistry` |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfigurationProperties` | constructors, `getTimeLimiterAspectOrder`, `setTimeLimiterAspectOrder` |
| `io.github.resilience4j.spring6.utils.AnnotationExtractor` | `extract`, `extractAnnotationFromProxy` |
| `io.github.resilience4j.spring6.utils.AspectJOnClasspathCondition` | constructors, `matches` |
| `io.github.resilience4j.spring6.utils.AspectUtil` | `newHashSet` |
| `io.github.resilience4j.spring6.utils.ReactorOnClasspathCondition` | constructors, `matches` |
| `io.github.resilience4j.spring6.utils.RxJava2OnClasspathCondition` | constructors, `matches` |
| `io.github.resilience4j.spring6.utils.RxJava3OnClasspathCondition` | constructors, `matches` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadAspect` | class | Intercepts the matching annotation and applies a named registry component. |
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadAspectExt` | interface | Defines return-type detection and policy handling for an aspect extension. |
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfigurationProperties` | class | Carries inherited external component settings and the public aspect-order property. |
| `io.github.resilience4j.spring6.bulkhead.configure.ReactorBulkheadAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.bulkhead.configure.RxJava2BulkheadAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.bulkhead.configure.RxJava3BulkheadAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.bulkhead.configure.threadpool.ThreadPoolBulkheadConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerAspect` | class | Intercepts the matching annotation and applies a named registry component. |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerAspectExt` | interface | Defines return-type detection and policy handling for an aspect extension. |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfigurationProperties` | class | Carries inherited external component settings and the public aspect-order property. |
| `io.github.resilience4j.spring6.circuitbreaker.configure.ReactorCircuitBreakerAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.circuitbreaker.configure.RxJava2CircuitBreakerAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.circuitbreaker.configure.RxJava3CircuitBreakerAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.fallback.CompletionStageFallbackDecorator` | class | Adapts fallback completion for its supported return family. |
| `io.github.resilience4j.spring6.fallback.DefaultFallbackDecorator` | class | Adapts fallback completion for its supported return family. |
| `io.github.resilience4j.spring6.fallback.FallbackDecorator` | interface | Defines fallback adaptation for a return family. |
| `io.github.resilience4j.spring6.fallback.FallbackDecorators` | class | Adapts fallback completion for its supported return family. |
| `io.github.resilience4j.spring6.fallback.FallbackExecutor` | class | Resolves and applies configured fallback methods around a primary function. |
| `io.github.resilience4j.spring6.fallback.FallbackMethod` | class | Finds, selects, and invokes compatible fallback overloads. |
| `io.github.resilience4j.spring6.fallback.ReactorFallbackDecorator` | class | Adapts fallback completion for its supported return family. |
| `io.github.resilience4j.spring6.fallback.RxJava2FallbackDecorator` | class | Adapts fallback completion for its supported return family. |
| `io.github.resilience4j.spring6.fallback.RxJava3FallbackDecorator` | class | Adapts fallback completion for its supported return family. |
| `io.github.resilience4j.spring6.fallback.configure.FallbackConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.micrometer.configure.ReactorTimerAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.micrometer.configure.RxJava2TimerAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.micrometer.configure.RxJava3TimerAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.micrometer.configure.TimerAspect` | class | Intercepts the matching annotation and applies a named registry component. |
| `io.github.resilience4j.spring6.micrometer.configure.TimerAspectExt` | interface | Defines return-type detection and policy handling for an aspect extension. |
| `io.github.resilience4j.spring6.micrometer.configure.TimerConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.micrometer.configure.TimerConfigurationProperties` | class | Carries inherited external component settings and the public aspect-order property. |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterAspect` | class | Intercepts the matching annotation and applies a named registry component. |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterAspectExt` | interface | Defines return-type detection and policy handling for an aspect extension. |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfigurationProperties` | class | Carries inherited external component settings and the public aspect-order property. |
| `io.github.resilience4j.spring6.ratelimiter.configure.ReactorRateLimiterAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.ratelimiter.configure.RxJava2RateLimiterAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.ratelimiter.configure.RxJava3RateLimiterAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.retry.configure.ReactorRetryAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.retry.configure.RetryAspect` | class | Intercepts the matching annotation and applies a named registry component. |
| `io.github.resilience4j.spring6.retry.configure.RetryAspectExt` | interface | Defines return-type detection and policy handling for an aspect extension. |
| `io.github.resilience4j.spring6.retry.configure.RetryConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.retry.configure.RetryConfigurationProperties` | class | Carries inherited external component settings and the public aspect-order property. |
| `io.github.resilience4j.spring6.retry.configure.RxJava2RetryAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.retry.configure.RxJava3RetryAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.spelresolver.DefaultSpelResolver` | class | Resolves literals, placeholders, templates, method expressions, and bean expressions. |
| `io.github.resilience4j.spring6.spelresolver.SpelResolver` | interface | Defines method-aware String expression resolution. |
| `io.github.resilience4j.spring6.spelresolver.SpelRootObject` | class | Exposes invoked class, method, and arguments to expressions. |
| `io.github.resilience4j.spring6.spelresolver.configure.SpelResolverConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.timelimiter.configure.IllegalReturnTypeException` | class | Reports an unsupported Time Limiter return type. |
| `io.github.resilience4j.spring6.timelimiter.configure.ReactorTimeLimiterAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.timelimiter.configure.RxJava2TimeLimiterAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.timelimiter.configure.RxJava3TimeLimiterAspectExt` | class | Adapts the named aspect to an optional reactive library. |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterAspect` | class | Intercepts the matching annotation and applies a named registry component. |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterAspectExt` | interface | Defines return-type detection and policy handling for an aspect extension. |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfiguration` | class | Defines Spring beans for registries, customizers, events, aspects, or expression support. |
| `io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfigurationProperties` | class | Carries inherited external component settings and the public aspect-order property. |
| `io.github.resilience4j.spring6.utils.AnnotationExtractor` | class | Finds annotations across classes, interfaces, superclasses, and proxies. |
| `io.github.resilience4j.spring6.utils.AspectJOnClasspathCondition` | class | Reports whether the named optional integration API is loadable. |
| `io.github.resilience4j.spring6.utils.AspectUtil` | class | Provides the public distinct-value set helper used by aspect adapters. |
| `io.github.resilience4j.spring6.utils.ReactorOnClasspathCondition` | class | Reports whether the named optional integration API is loadable. |
| `io.github.resilience4j.spring6.utils.RxJava2OnClasspathCondition` | class | Reports whether the named optional integration API is loadable. |
| `io.github.resilience4j.spring6.utils.RxJava3OnClasspathCondition` | class | Reports whether the named optional integration API is loadable. |

### CLI Entry Points

There is no console script for this package. There is no executable main class or Maven plugin goal. Programmatic use is through Java imports and Spring configuration.

## Appendix A: Environment

The working environment runs Java 21 or newer on Linux without network access. Maven 3.9 or newer, the Java standard library, Spring Framework 6, AspectJ runtime, and the companion annotation, consumer, framework-common, metrics, Reactor, RxJava 2, and RxJava 3 artifacts needed by the selected workflows are available from the local Maven repository. Optional adapter checks run only with their corresponding locally available artifact. The assessment environment provides the same offline dependency set.

The project must provide a Maven `pom.xml` at its root with coordinate `io.github.resilience4j:resilience4j-spring6`. Java source must compile through the standard Maven lifecycle, and all dependency declarations must resolve without network access.

## Appendix B: Assessment Notes

Assessment exercises public Java and Spring behavior across annotation interception, expression resolution, named configuration and registry initialization, sync and `CompletionStage` execution, Reactor and RxJava adapters, fallback specificity, aspect order, Timer projection, conditional beans, lifecycle cleanup, and cross-view consistency. Checks compare public values, exception classes, registry/configuration state, component events, completion signals, and public SPI dispatch. They do not depend on private field layout, internal helper structure, timing races, exact diagnostic text, or external services.


