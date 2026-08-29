package support;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicLong;
import org.cache2k.Cache2kBuilder;

/** Shared construction helpers that use only the documented public cache API. */
public final class OracleSupport {
  private static final AtomicLong SEQUENCE = new AtomicLong();

  private OracleSupport() { }

  public static <K, V> Cache2kBuilder<K, V> builder(Class<K> keyType, Class<V> valueType) {
    return Cache2kBuilder.of(keyType, valueType)
      .name("generated-oracle-" + SEQUENCE.incrementAndGet());
  }

  public static String uniqueName(String prefix) {
    return prefix + "-" + SEQUENCE.incrementAndGet();
  }

  public static long count(Iterable<?> values) {
    long result = 0;
    for (Object ignored : values) {
      result++;
    }
    return result;
  }

  public static <T> T await(CompletableFuture<T> future) {
    return future.join();
  }
}
