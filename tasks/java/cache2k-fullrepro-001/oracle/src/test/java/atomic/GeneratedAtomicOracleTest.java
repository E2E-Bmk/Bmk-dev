package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletionException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.cache2k.Cache;
import org.cache2k.Cache2kBuilder;
import org.cache2k.CacheEntry;
import org.cache2k.CacheManager;
import org.cache2k.expiry.Expiry;
import org.cache2k.expiry.ExpiryTimeValues;
import org.cache2k.io.CacheWriter;
import org.cache2k.io.CacheWriterException;
import org.cache2k.operation.CacheInfo;
import org.cache2k.processor.EntryProcessingException;
import org.cache2k.processor.EntryProcessingResult;
import org.junit.jupiter.api.Test;
import support.OracleSupport;

class GeneratedAtomicOracleTest {

  /** Verifies: C2K-LIFE-003 */
  @Test void typedBuilderRetainsKeyAndValueTypes() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      CacheInfo info = CacheInfo.of(cache);
      assertEquals(Integer.class, info.getKeyType().getType());
      assertEquals(String.class, info.getValueType().getType());
    }
  }

  /** Verifies: C2K-LIFE-006 */
  @Test void unnamedCacheGetsGeneratedName() {
    try (Cache<Integer, String> cache = Cache2kBuilder.of(Integer.class, String.class).build()) {
      String generatedName = cache.getName();
      assertFalse(generatedName.isEmpty());
      assertEquals('_', generatedName.charAt(0));
    }
  }

  /** Verifies: C2K-LIFE-006 */
  @Test void explicitCacheNameIsPreserved() {
    String name = OracleSupport.uniqueName("named");
    try (Cache<Integer, String> cache = Cache2kBuilder.of(Integer.class, String.class).name(name).build()) {
      assertEquals(name, cache.getName());
    }
  }

  /** Verifies: C2K-LIFE-007 */
  @Test void duplicateActiveCacheNameIsRejected() {
    String name = OracleSupport.uniqueName("duplicate");
    try (Cache<Integer, String> first = Cache2kBuilder.of(Integer.class, String.class).name(name).build()) {
      assertThrows(IllegalStateException.class,
        () -> Cache2kBuilder.of(Integer.class, String.class).name(name).build());
      assertFalse(first.isClosed());
    }
  }

  /** Verifies: C2K-LIFE-008 */
  @Test void entryCapacityBoundsRetainedSize() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).entryCapacity(1).build()) {
      cache.put(1, "one");
      cache.put(2, "two");
      assertTrue(CacheInfo.of(cache).getSize() <= 1);
    }
  }

  /** Verifies: C2K-LIFE-009 */
  @Test void eternalAndExpireAfterWriteKeepFiniteDuration() {
    try (Cache<Integer, String> first = OracleSupport.builder(Integer.class, String.class)
           .eternal(true).expireAfterWrite(Duration.ofSeconds(1)).build();
         Cache<Integer, String> second = OracleSupport.builder(Integer.class, String.class)
           .expireAfterWrite(Duration.ofSeconds(1)).eternal(true).build()) {
      long firstTicks = CacheInfo.of(first).getExpiryAfterWriteTicks();
      long secondTicks = CacheInfo.of(second).getExpiryAfterWriteTicks();
      assertTrue(firstTicks > 0);
      assertEquals(firstTicks, secondTicks);
    }
  }

  /** Verifies: C2K-LIFE-010 */
  @Test void managerLookupReusesOpenNamedManager() {
    String name = OracleSupport.uniqueName("manager");
    CacheManager first = CacheManager.getInstance(name);
    try {
      assertEquals(first, CacheManager.getInstance(name));
    } finally {
      first.close();
    }
  }

  /** Verifies: C2K-LIFE-010 */
  @Test void distinctManagerNamesProduceDistinctManagers() {
    CacheManager first = CacheManager.getInstance(OracleSupport.uniqueName("manager-a"));
    CacheManager second = CacheManager.getInstance(OracleSupport.uniqueName("manager-b"));
    try {
      assertNotEquals(first, second);
    } finally {
      first.close();
      second.close();
    }
  }

  /** Verifies: C2K-LIFE-012 */
  @Test void cacheCloseIsIdempotentAndObservable() {
    Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build();
    cache.close();
    cache.close();
    assertTrue(cache.isClosed());
  }

  /** Verifies: C2K-LIFE-013 */
  @Test void ordinaryOperationAfterCloseFails() {
    Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build();
    cache.close();
    assertThrows(IllegalStateException.class, () -> cache.put(1, "one"));
    assertTrue(cache.isClosed());
    assertNotNull(cache.getName());
  }

  /** Verifies: C2K-ENTRY-002 */
  @Test void missingGetWithoutLoaderMatchesPeek() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertEquals(cache.peek(7), cache.get(7));
      assertNull(cache.get(7));
    }
  }

  /** Verifies: C2K-ENTRY-005 */
  @Test void nullKeyIsRejected() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertThrows(NullPointerException.class, () -> cache.get(null));
    }
  }

  /** Verifies: C2K-ENTRY-005 */
  @Test void nullValueIsRejectedByDefault() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertThrows(NullPointerException.class, () -> cache.put(1, null));
    }
  }

  /** Verifies: C2K-ENTRY-008 */
  @Test void putMakesValueVisible() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      assertEquals("one", cache.peek(1));
      assertTrue(cache.containsKey(1));
    }
  }

  /** Verifies: C2K-ENTRY-004 */
  @Test void peekEntryDescribesVisibleMapping() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(3, "three");
      CacheEntry<Integer, String> entry = cache.peekEntry(3);
      assertNotNull(entry);
      assertEquals(3, entry.getKey());
      assertEquals("three", entry.getValue());
      assertNull(entry.getException());
    }
  }

  /** Verifies: C2K-ENTRY-003 */
  @Test void peekDoesNotInvokeLoader() {
    AtomicInteger loads = new AtomicInteger();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> { loads.incrementAndGet(); return "v" + key; }).build()) {
      assertNull(cache.peek(9));
      assertNull(cache.peekEntry(9));
      assertFalse(cache.containsKey(9));
      assertEquals(0, loads.get());
    }
  }

  /** Verifies: C2K-ENTRY-009 */
  @Test void peekAndPutReturnsPreviousValue() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertEquals("old", cache.peekAndPut(1, "new"));
      assertEquals("new", cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-010 */
  @Test void peekAndReplaceMissingPreservesAbsence() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertNull(cache.peekAndReplace(1, "new"));
      assertFalse(cache.containsKey(1));
    }
  }

  /** Verifies: C2K-ENTRY-009 */
  @Test void peekAndReplaceReturnsOldValue() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertEquals("old", cache.peekAndReplace(1, "new"));
      assertEquals("new", cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-010 */
  @Test void replaceMissingReturnsFalse() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertFalse(cache.replace(1, "new"));
      assertNull(cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-009 */
  @Test void replacePresentReturnsTrue() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertTrue(cache.replace(1, "new"));
      assertEquals("new", cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-010 */
  @Test void failedCompareReplacePreservesMapping() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertFalse(cache.replaceIfEquals(1, "wrong", "new"));
      assertEquals("old", cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-010 */
  @Test void failedCompareRemovePreservesMapping() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertFalse(cache.removeIfEquals(1, "wrong"));
      assertEquals("old", cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-009 */
  @Test void successfulCompareRemoveDeletesMapping() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertTrue(cache.removeIfEquals(1, "old"));
      assertFalse(cache.containsKey(1));
    }
  }

  /** Verifies: C2K-ENTRY-009 */
  @Test void peekAndRemoveReturnsRemovedValue() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertEquals("old", cache.peekAndRemove(1));
      assertNull(cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-009 */
  @Test void containsAndRemoveReportsPresence() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "old");
      assertTrue(cache.containsAndRemove(1));
      assertFalse(cache.containsAndRemove(1));
    }
  }

  /** Verifies: C2K-ENTRY-009 */
  @Test void putIfAbsentDoesNotReplace() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertTrue(cache.putIfAbsent(1, "first"));
      assertFalse(cache.putIfAbsent(1, "second"));
      assertEquals("first", cache.peek(1));
    }
  }

  /** Verifies: C2K-ENTRY-008 */
  @Test void computeIfAbsentStoresProducedValueOnce() {
    AtomicInteger calls = new AtomicInteger();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertEquals("v1", cache.computeIfAbsent(1, key -> "v" + calls.incrementAndGet()));
      assertEquals("v1", cache.computeIfAbsent(1, key -> "v" + calls.incrementAndGet()));
      assertEquals(1, calls.get());
    }
  }

  /** Verifies: C2K-ENTRY-008 */
  @Test void putAllStoresEveryMapping() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      Map<Integer, String> values = new LinkedHashMap<>();
      values.put(1, "one");
      values.put(2, "two");
      cache.putAll(values);
      assertEquals(values, cache.peekAll(values.keySet()));
    }
  }

  /** Verifies: C2K-ENTRY-016 */
  @Test void peekAllReturnsOnlyVisibleRequestedMappings() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      Map<Integer, String> result = cache.peekAll(Arrays.asList(1, 2));
      assertEquals(Map.of(1, "one"), result);
      assertThrows(UnsupportedOperationException.class, () -> result.put(2, "two"));
    }
  }

  /** Verifies: C2K-ENTRY-016 */
  @Test void bulkAccessRejectsNullKey() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertThrows(NullPointerException.class, () -> cache.peekAll(Arrays.asList(1, null)));
    }
  }

  /** Verifies: C2K-LOAD-001 */
  @Test void loaderReceivesRequestedKey() {
    AtomicReference<Integer> seen = new AtomicReference<>();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> { seen.set(key); return "loaded-" + key; }).build()) {
      assertEquals("loaded-4", cache.get(4));
      assertEquals(4, seen.get());
    }
  }

  /** Verifies: C2K-LOAD-006 */
  @Test void loadAllWithoutLoaderFailsImmediately() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertThrows(UnsupportedOperationException.class, () -> cache.loadAll(Set.of(1)));
    }
  }

  /** Verifies: C2K-LOAD-006 */
  @Test void reloadAllWithoutLoaderFailsImmediately() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      assertThrows(UnsupportedOperationException.class, () -> cache.reloadAll(Set.of(1)));
    }
  }

  /** Verifies: C2K-LOAD-004 */
  @Test void loadAllSkipsPresentKeys() {
    AtomicInteger loads = new AtomicInteger();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> { loads.incrementAndGet(); return "v" + key; }).build()) {
      cache.put(1, "present");
      OracleSupport.await(cache.loadAll(Arrays.asList(1, 2)));
      assertEquals(1, loads.get());
      assertEquals("v2", cache.peek(2));
    }
  }

  /** Verifies: C2K-LOAD-005 */
  @Test void reloadAllLoadsPresentKeys() {
    AtomicInteger loads = new AtomicInteger();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> "v" + loads.incrementAndGet()).build()) {
      cache.put(1, "present");
      OracleSupport.await(cache.reloadAll(Set.of(1)));
      assertEquals(1, loads.get());
      assertEquals("v1", cache.peek(1));
    }
  }

  /** Verifies: C2K-LOAD-010 */
  @Test void writerRunsBeforeSuccessfulCommit() {
    AtomicReference<String> written = new AtomicReference<>();
    CacheWriter<Integer, String> writer = new CacheWriter<>() {
      public void write(Integer key, String value) { written.set(key + ":" + value); }
      public void delete(Integer key) { }
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).writer(writer).build()) {
      cache.put(2, "two");
      assertEquals("2:two", written.get());
      assertEquals("two", cache.peek(2));
    }
  }

  /** Verifies: C2K-LOAD-012 */
  @Test void writerFailurePreservesPreviousValue() {
    AtomicInteger writes = new AtomicInteger();
    CacheWriter<Integer, String> writer = new CacheWriter<>() {
      public void write(Integer key, String value) throws Exception {
        if (writes.incrementAndGet() > 1) { throw new Exception(); }
      }
      public void delete(Integer key) { }
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).writer(writer).build()) {
      cache.put(1, "old");
      assertThrows(CacheWriterException.class, () -> cache.put(1, "new"));
      assertEquals("old", cache.peek(1));
    }
  }

  /** Verifies: C2K-PROC-001 */
  @Test void invokeReturnsProcessorResultAndCommits() {
    try (Cache<String, Integer> cache = OracleSupport.builder(String.class, Integer.class).build()) {
      Integer result = cache.invoke("jobs", entry -> { entry.setValue(3); return 7; });
      assertEquals(7, result);
      assertEquals(3, cache.peek("jobs"));
    }
  }

  /** Verifies: C2K-PROC-003 */
  @Test void processorFailureRollsBackMapping() {
    try (Cache<String, Integer> cache = OracleSupport.builder(String.class, Integer.class).build()) {
      cache.put("jobs", 2);
      assertThrows(EntryProcessingException.class, () -> cache.invoke("jobs", entry -> {
        entry.setValue(9);
        throw new IllegalArgumentException();
      }));
      assertEquals(2, cache.peek("jobs"));
    }
  }

  /** Verifies: C2K-PROC-006 */
  @Test void finalStagedMutationDeterminesState() {
    try (Cache<String, Integer> cache = OracleSupport.builder(String.class, Integer.class).build()) {
      cache.invoke("jobs", entry -> { entry.setValue(1); entry.remove(); entry.setValue(4); return null; });
      assertEquals(4, cache.peek("jobs"));
    }
  }

  /** Verifies: C2K-PROC-007 */
  @Test void processorLoadWithoutLoaderFails() {
    try (Cache<String, Integer> cache = OracleSupport.builder(String.class, Integer.class).build()) {
      assertThrows(EntryProcessingException.class,
        () -> cache.invoke("jobs", entry -> { entry.load(); return null; }));
    }
  }

  /** Verifies: C2K-PROC-010, C2K-PROC-011 */
  @Test void invokeAllReturnsSuccessfulResultPerKey() {
    try (Cache<Integer, Integer> cache = OracleSupport.builder(Integer.class, Integer.class).build()) {
      Map<Integer, EntryProcessingResult<Integer>> results =
        cache.invokeAll(Arrays.asList(1, 2), entry -> { entry.setValue(entry.getKey()); return entry.getKey() * 2; });
      assertEquals(Set.of(1, 2), results.keySet());
      assertEquals(2, results.get(1).getResult());
      assertNull(results.get(1).getException());
    }
  }

  /** Verifies: C2K-PROC-012 */
  @Test void invokeAllCapturesProcessorFailure() {
    try (Cache<Integer, Integer> cache = OracleSupport.builder(Integer.class, Integer.class).build()) {
      Map<Integer, EntryProcessingResult<Integer>> results =
        cache.invokeAll(Set.of(1), entry -> { throw new IllegalStateException(); });
      assertTrue(results.get(1).getException() instanceof IllegalStateException);
      assertThrows(EntryProcessingException.class, () -> results.get(1).getResult());
    }
  }

  /** Verifies: C2K-EXP-008 */
  @Test void expireAtNowMakesEntryInvisible() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      cache.expireAt(1, ExpiryTimeValues.NOW);
      assertNull(cache.peek(1));
      assertFalse(cache.containsKey(1));
    }
  }
}
