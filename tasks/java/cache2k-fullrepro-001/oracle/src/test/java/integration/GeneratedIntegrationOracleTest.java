package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.cache2k.Cache;
import org.cache2k.Cache2kBuilder;
import org.cache2k.CacheEntry;
import org.cache2k.CacheManager;
import org.cache2k.event.CacheClosedListener;
import org.cache2k.event.CacheEntryCreatedListener;
import org.cache2k.event.CacheEntryRemovedListener;
import org.cache2k.event.CacheEntryUpdatedListener;
import org.cache2k.expiry.ExpiryTimeValues;
import org.cache2k.io.AdvancedCacheLoader;
import org.cache2k.io.BulkCacheLoader;
import org.cache2k.io.CacheLoaderException;
import org.cache2k.io.CacheWriter;
import org.cache2k.io.ResiliencePolicy;
import org.cache2k.operation.CacheControl;
import org.cache2k.operation.CacheInfo;
import org.cache2k.operation.CacheStatistics;
import org.junit.jupiter.api.Test;
import support.OracleSupport;

class GeneratedIntegrationOracleTest {

  /**
   * Verifies: C2K-INV-001, C2K-ENTRY-008
   * Depends-On: putMakesValueVisible, peekEntryDescribesVisibleMapping
   */
  @Test void cachePutIsConsistentAcrossAllReadViews() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      assertEquals("one", cache.peekEntry(1).getValue());
      assertEquals("one", cache.asMap().get(1));
      assertTrue(cache.keys().contains(1));
      boolean entryFound = false;
      for (CacheEntry<Integer, String> entry : cache.entries()) {
        if (entry.getKey().equals(1) && entry.getValue().equals("one")) {
          entryFound = true;
        }
      }
      assertTrue(entryFound);
      assertEquals(1, CacheInfo.of(cache).getSize());
    }
  }

  /**
   * Verifies: C2K-INV-001, C2K-ENTRY-008
   * Depends-On: putAllStoresEveryMapping, peekEntryDescribesVisibleMapping
   */
  @Test void cachePutAllIsConsistentAcrossReadViews() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.putAll(Map.of(1, "one", 2, "two"));
      assertEquals(Map.of(1, "one", 2, "two"), cache.peekAll(Set.of(1, 2)));
      assertEquals(Map.of(1, "one", 2, "two"), new LinkedHashMap<>(cache.asMap()));
      assertEquals(Set.of(1, 2), cache.keys());
      assertEquals(2, CacheInfo.of(cache).getSize());
    }
  }

  /**
   * Verifies: C2K-INV-002, C2K-ENTRY-013, C2K-ENTRY-014
   * Depends-On: putMakesValueVisible, peekDoesNotInvokeLoader
   */
  @Test void mapPutProjectsToCacheWithoutLoading() {
    AtomicInteger loads = new AtomicInteger();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> { loads.incrementAndGet(); return "loaded"; }).build()) {
      cache.asMap().put(1, "manual");
      assertEquals("manual", cache.peek(1));
      assertEquals("manual", cache.peekEntry(1).getValue());
      assertEquals(0, loads.get());
    }
  }

  /**
   * Verifies: C2K-INV-002, C2K-ENTRY-013, C2K-ENTRY-014
   * Depends-On: replacePresentReturnsTrue, peekDoesNotInvokeLoader
   */
  @Test void mapReplaceProjectsToEntrySnapshotWithoutLoading() {
    AtomicInteger loads = new AtomicInteger();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> { loads.incrementAndGet(); return "loaded"; }).build()) {
      cache.put(1, "old");
      assertEquals("old", cache.asMap().replace(1, "new"));
      assertEquals("new", cache.getEntry(1).getValue());
      assertEquals(0, loads.get());
    }
  }

  /**
   * Verifies: C2K-ENTRY-009, C2K-INV-001
   * Depends-On: successfulCompareRemoveDeletesMapping, peekAndRemoveReturnsRemovedValue
   */
  @Test void directRemovalDisappearsFromEveryProjection() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      cache.remove(1);
      assertNull(cache.peek(1));
      assertNull(cache.asMap().get(1));
      assertFalse(cache.keys().contains(1));
      assertEquals(0, CacheInfo.of(cache).getSize());
    }
  }

  /**
   * Verifies: C2K-ENTRY-013, C2K-INV-002
   * Depends-On: containsAndRemoveReportsPresence, peekEntryDescribesVisibleMapping
   */
  @Test void mapRemovalDisappearsFromCacheAndEntryViews() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      assertEquals("one", cache.asMap().remove(1));
      assertFalse(cache.containsKey(1));
      assertNull(cache.peekEntry(1));
      assertTrue(cache.entries().isEmpty());
    }
  }

  /**
   * Verifies: C2K-ENTRY-001, C2K-EVT-004, C2K-STAT-001
   * Depends-On: loaderReceivesRequestedKey, peekEntryDescribesVisibleMapping
   */
  @Test void loadedValueAgreesAcrossListenerEntryMapAndStatistics() {
    AtomicReference<String> created = new AtomicReference<>();
    CacheEntryCreatedListener<Integer, String> listener =
      (cache, entry) -> created.set(entry.getValue());
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> "loaded-" + key).addListener(listener).build()) {
      assertEquals("loaded-3", cache.get(3));
      assertEquals("loaded-3", created.get());
      assertEquals("loaded-3", cache.peekEntry(3).getValue());
      assertEquals("loaded-3", cache.asMap().get(3));
      assertEquals(1, CacheControl.of(cache).sampleStatistics().getLoadCount());
    }
  }

  /**
   * Verifies: C2K-LOAD-004, C2K-STAT-001, C2K-INV-001
   * Depends-On: loadAllSkipsPresentKeys, putAllStoresEveryMapping
   */
  @Test void loadAllCommitsEachValueToEveryProjection() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> "v" + key).build()) {
      OracleSupport.await(cache.loadAll(Arrays.asList(1, 2)));
      assertEquals(Map.of(1, "v1", 2, "v2"), cache.peekAll(Set.of(1, 2)));
      assertEquals(Map.of(1, "v1", 2, "v2"), new LinkedHashMap<>(cache.asMap()));
      assertEquals(2, CacheControl.of(cache).sampleStatistics().getLoadCount());
    }
  }

  /**
   * Verifies: C2K-PROC-001, C2K-PROC-006, C2K-INV-001
   * Depends-On: invokeReturnsProcessorResultAndCommits, finalStagedMutationDeterminesState
   */
  @Test void processorCommitProjectsFinalValueAcrossViews() {
    try (Cache<String, Integer> cache = OracleSupport.builder(String.class, Integer.class).build()) {
      int result = cache.invoke("jobs", entry -> { entry.setValue(1); entry.setValue(5); return 5; });
      assertEquals(5, result);
      assertEquals(5, cache.peek("jobs"));
      assertEquals(5, cache.asMap().get("jobs"));
      assertEquals(5, cache.peekEntry("jobs").getValue());
      assertEquals(1, CacheInfo.of(cache).getSize());
    }
  }

  /**
   * Verifies: C2K-PROC-006, C2K-INV-001
   * Depends-On: finalStagedMutationDeterminesState, successfulCompareRemoveDeletesMapping
   */
  @Test void processorRemovalProjectsAbsenceAcrossViews() {
    try (Cache<String, Integer> cache = OracleSupport.builder(String.class, Integer.class).build()) {
      cache.put("jobs", 2);
      cache.mutate("jobs", entry -> entry.remove());
      assertNull(cache.peek("jobs"));
      assertFalse(cache.asMap().containsKey("jobs"));
      assertNull(cache.peekEntry("jobs"));
      assertEquals(0, CacheInfo.of(cache).getSize());
    }
  }

  /**
   * Verifies: C2K-ENTRY-007, C2K-EXP-015, C2K-INV-003
   * Depends-On: loaderReceivesRequestedKey, peekEntryDescribesVisibleMapping
   */
  @Test void loaderFailurePreservesCauseAcrossEntryAccessAndStatistics() {
    IllegalArgumentException original = new IllegalArgumentException();
    ResiliencePolicy<Integer, String> policy = new ResiliencePolicy<>() {
      public long suppressExceptionUntil(Integer key, org.cache2k.io.LoadExceptionInfo<Integer, String> info,
                                         CacheEntry<Integer, String> cachedEntry) { return ExpiryTimeValues.NOW; }
      public long retryLoadAfter(Integer key, org.cache2k.io.LoadExceptionInfo<Integer, String> info) {
        return ExpiryTimeValues.ETERNAL;
      }
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> { throw original; }).resiliencePolicy(policy).build()) {
      assertThrows(CacheLoaderException.class, () -> cache.get(1));
      CacheEntry<Integer, String> entry = cache.peekEntry(1);
      assertNotNull(entry);
      assertSame(original, entry.getException());
      assertSame(original, entry.getExceptionInfo().getException());
      assertEquals(1, CacheControl.of(cache).sampleStatistics().getLoadExceptionCount());
    }
  }

  /**
   * Verifies: C2K-ENTRY-007, C2K-EXP-016, C2K-INV-003
   * Depends-On: loaderReceivesRequestedKey, peekEntryDescribesVisibleMapping
   */
  @Test void customPropagationRetainsOriginalFailureObservation() {
    IllegalStateException original = new IllegalStateException();
    ResiliencePolicy<Integer, String> policy = new ResiliencePolicy<>() {
      public long suppressExceptionUntil(Integer key, org.cache2k.io.LoadExceptionInfo<Integer, String> info,
                                         CacheEntry<Integer, String> cachedEntry) { return ExpiryTimeValues.NOW; }
      public long retryLoadAfter(Integer key, org.cache2k.io.LoadExceptionInfo<Integer, String> info) {
        return ExpiryTimeValues.ETERNAL;
      }
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> { throw original; })
      .exceptionPropagator(info -> new UnsupportedOperationException(info.getException()))
      .resiliencePolicy(policy).build()) {
      UnsupportedOperationException propagated =
        assertThrows(UnsupportedOperationException.class, () -> cache.get(1));
      assertSame(original, propagated.getCause());
      assertSame(original, cache.peekEntry(1).getException());
    }
  }

  /**
   * Verifies: C2K-INV-004, C2K-LIFE-011
   * Depends-On: managerLookupReusesOpenNamedManager, explicitCacheNameIsPreserved
   */
  @Test void activeCacheAgreesWithManagerAndInfoViews() {
    CacheManager manager = CacheManager.getInstance(OracleSupport.uniqueName("active-manager"));
    try (Cache<Integer, String> cache = Cache2kBuilder.of(Integer.class, String.class)
      .manager(manager).name(OracleSupport.uniqueName("managed-cache")).build()) {
      assertTrue(manager.getActiveCaches().iterator().hasNext());
      assertSame(manager, cache.getCacheManager());
      assertEquals(manager.getName(), CacheInfo.of(cache).getManagerName());
      assertSame(cache, manager.getCache(cache.getName()));
    } finally {
      manager.close();
    }
  }

  /**
   * Verifies: C2K-INV-004, C2K-LIFE-012
   * Depends-On: cacheCloseIsIdempotentAndObservable, managerLookupReusesOpenNamedManager
   */
  @Test void closedCacheDisappearsFromAllManagerLifecycleViews() {
    CacheManager manager = CacheManager.getInstance(OracleSupport.uniqueName("closed-manager"));
    Cache<Integer, String> cache = Cache2kBuilder.of(Integer.class, String.class)
      .manager(manager).name(OracleSupport.uniqueName("managed-cache")).build();
    String cacheName = cache.getName();
    try {
      cache.close();
      assertTrue(cache.isClosed());
      assertFalse(manager.getActiveCaches().iterator().hasNext());
      assertNull(manager.getCache(cacheName));
    } finally {
      manager.close();
    }
  }

  /**
   * Verifies: C2K-INV-005, C2K-ENTRY-012, C2K-LOAD-011
   * Depends-On: putAllStoresEveryMapping, putMakesValueVisible
   */
  @Test void clearEmptiesViewsWithoutWriterDeletes() {
    AtomicInteger deletes = new AtomicInteger();
    CacheWriter<Integer, String> writer = new CacheWriter<>() {
      public void write(Integer key, String value) { }
      public void delete(Integer key) { deletes.incrementAndGet(); }
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).writer(writer).build()) {
      cache.putAll(Map.of(1, "one", 2, "two"));
      cache.clear();
      assertTrue(cache.asMap().isEmpty());
      assertTrue(cache.keys().isEmpty());
      assertEquals(0, deletes.get());
    }
  }

  /**
   * Verifies: C2K-INV-005, C2K-ENTRY-012, C2K-LOAD-010
   * Depends-On: putAllStoresEveryMapping, containsAndRemoveReportsPresence
   */
  @Test void removeAllEmptiesViewsAndCallsWriterDeletePerEntry() {
    AtomicInteger deletes = new AtomicInteger();
    CacheWriter<Integer, String> writer = new CacheWriter<>() {
      public void write(Integer key, String value) { }
      public void delete(Integer key) { deletes.incrementAndGet(); }
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).writer(writer).build()) {
      cache.putAll(Map.of(1, "one", 2, "two"));
      cache.removeAll();
      assertTrue(cache.asMap().isEmpty());
      assertTrue(cache.entries().isEmpty());
      assertEquals(2, deletes.get());
    }
  }

  /**
   * Verifies: C2K-EXP-011, C2K-ENTRY-003
   * Depends-On: expireAtNowMakesEntryInvisible, loaderReceivesRequestedKey
   */
  @Test void expiredRetainedValueIsHiddenButPassedToAdvancedLoader() {
    AtomicReference<String> priorValue = new AtomicReference<>();
    AdvancedCacheLoader<Integer, String> loader = (key, start, current) -> {
      if (current != null && priorValue.get() == null) {
        priorValue.set(current.getValue());
      }
      return "new";
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .keepDataAfterExpired(true).loader(loader).build()) {
      cache.put(1, "old");
      cache.expireAt(1, ExpiryTimeValues.NOW);
      assertNull(cache.peek(1));
      assertFalse(cache.asMap().containsKey(1));
      assertEquals("new", cache.get(1));
      assertEquals("old", priorValue.get());
    }
  }

  /**
   * Verifies: C2K-EXP-011, C2K-LOAD-002
   * Depends-On: expireAtNowMakesEntryInvisible, reloadAllLoadsPresentKeys
   */
  @Test void retainedExpiredEntrySuppliesPriorContextOnReload() {
    AtomicReference<String> priorValue = new AtomicReference<>();
    AdvancedCacheLoader<Integer, String> loader = (key, start, current) -> {
      if (current != null && priorValue.get() == null) {
        priorValue.set(current.getValue());
      }
      return "replacement";
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .keepDataAfterExpired(true).loader(loader).build()) {
      cache.put(2, "stale");
      cache.expireAt(2, ExpiryTimeValues.NOW);
      assertNull(cache.peekEntry(2));
      OracleSupport.await(cache.reloadAll(Set.of(2)));
      assertEquals("replacement", cache.peek(2));
      assertEquals("stale", priorValue.get());
    }
  }

  /**
   * Verifies: C2K-STAT-002
   * Depends-On: putMakesValueVisible, peekDoesNotInvokeLoader
   */
  @Test void presenceAndIterationChecksAreHitMissNeutral() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      cache.get(1);
      cache.get(2);
      CacheStatistics before = CacheControl.of(cache).sampleStatistics();
      long beforeGets = before.getGetCount();
      long beforeMisses = before.getMissCount();
      cache.containsKey(1);
      cache.keys().iterator().hasNext();
      cache.entries().iterator().hasNext();
      CacheStatistics after = CacheControl.of(cache).sampleStatistics();
      assertEquals(beforeGets, after.getGetCount());
      assertEquals(beforeMisses, after.getMissCount());
    }
  }

  /**
   * Verifies: C2K-STAT-001, C2K-ENTRY-008
   * Depends-On: putMakesValueVisible, missingGetWithoutLoaderMatchesPeek
   */
  @Test void statisticsDescribeCommittedPutGetAndMissOperations() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.put(1, "one");
      assertEquals("one", cache.get(1));
      assertNull(cache.get(2));
      CacheStatistics stats = CacheControl.of(cache).sampleStatistics();
      assertTrue(stats.getPutCount() >= 1);
      assertEquals(2, stats.getGetCount());
      assertEquals(1, stats.getMissCount());
    }
  }

  /**
   * Verifies: C2K-ENTRY-001, C2K-ENTRY-013
   * Depends-On: loaderReceivesRequestedKey, putMakesValueVisible
   */
  @Test void representativeReadThroughThenMapOverrideWorkflow() {
    AtomicInteger loads = new AtomicInteger();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .loader(key -> "v" + loads.incrementAndGet()).build()) {
      assertEquals("v1", cache.get(7));
      assertEquals("v1", cache.get(7));
      cache.asMap().put(7, "manual");
      assertEquals("manual", cache.peek(7));
      assertEquals(1, loads.get());
    }
  }

  /**
   * Verifies: C2K-PROC-001, C2K-CTL-001
   * Depends-On: invokeReturnsProcessorResultAndCommits, typedBuilderRetainsKeyAndValueTypes
   */
  @Test void representativeProcessorEntryAndControlWorkflow() {
    try (Cache<String, Integer> cache = OracleSupport.builder(String.class, Integer.class).build()) {
      int result = cache.invoke("jobs", entry -> {
        int next = entry.exists() ? entry.getValue() + 1 : 1;
        entry.setValue(next);
        entry.setExpiryTime(ExpiryTimeValues.ETERNAL);
        return next;
      });
      assertEquals(1, result);
      assertEquals(1, cache.peekEntry("jobs").getValue());
      assertEquals(1, cache.asMap().get("jobs"));
      assertEquals(1, CacheControl.of(cache).getSize());
    }
  }

  /**
   * Verifies: C2K-ENTRY-006, C2K-INV-001
   * Depends-On: nullValueIsRejectedByDefault, peekEntryDescribesVisibleMapping
   */
  @Test void permittedNullMappingIsDistinguishedAcrossViews() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .permitNullValues(true).build()) {
      cache.put(1, null);
      assertTrue(cache.containsKey(1));
      assertNotNull(cache.peekEntry(1));
      assertNull(cache.peekEntry(1).getValue());
      assertTrue(cache.asMap().containsKey(1));
      assertNull(cache.asMap().get(1));
    }
  }

  /**
   * Verifies: C2K-LOAD-003, C2K-LOAD-008
   * Depends-On: loaderReceivesRequestedKey, putAllStoresEveryMapping
   */
  @Test void bulkLoaderReceivesOutstandingSetAndCommitsResult() {
    AtomicReference<Set<? extends Integer>> seen = new AtomicReference<>();
    BulkCacheLoader<Integer, String> loader = keys -> {
      seen.set(keys);
      Map<Integer, String> result = new LinkedHashMap<>();
      keys.forEach(key -> result.put(key, "v" + key));
      return result;
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .bulkLoader(loader).build()) {
      assertEquals(Map.of(1, "v1", 2, "v2"), cache.getAll(Set.of(1, 2)));
      assertEquals(Set.of(1, 2), seen.get());
      assertEquals("v1", cache.peek(1));
    }
  }

  /**
   * Verifies: C2K-EVT-001, C2K-EVT-004
   * Depends-On: putMakesValueVisible, replacePresentReturnsTrue
   */
  @Test void synchronousListenersObserveCreateUpdateAndRemoveSequence() {
    AtomicInteger creates = new AtomicInteger();
    AtomicInteger updates = new AtomicInteger();
    AtomicInteger removes = new AtomicInteger();
    CacheEntryCreatedListener<Integer, String> created = (cache, entry) -> creates.incrementAndGet();
    CacheEntryUpdatedListener<Integer, String> updated = (cache, oldEntry, newEntry) -> updates.incrementAndGet();
    CacheEntryRemovedListener<Integer, String> removed = (cache, entry) -> removes.incrementAndGet();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .addListener(created).addListener(updated).addListener(removed).build()) {
      cache.put(1, "one");
      cache.put(1, "uno");
      cache.remove(1);
      assertEquals(List.of(1, 1, 1), List.of(creates.get(), updates.get(), removes.get()));
    }
  }

  /**
   * Verifies: C2K-EVT-002, C2K-EVT-004
   * Depends-On: putMakesValueVisible, explicitCacheNameIsPreserved
   */
  @Test void asyncListenerUsesConfiguredExecutor() {
    AtomicInteger executorCalls = new AtomicInteger();
    AtomicInteger listenerCalls = new AtomicInteger();
    CacheEntryCreatedListener<Integer, String> listener = (cache, entry) -> listenerCalls.incrementAndGet();
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .asyncListenerExecutor(command -> { executorCalls.incrementAndGet(); command.run(); })
      .addAsyncListener(listener).build()) {
      cache.put(1, "one");
      assertEquals(1, executorCalls.get());
      assertEquals(1, listenerCalls.get());
    }
  }

  /**
   * Verifies: C2K-EVT-005, C2K-LIFE-012
   * Depends-On: cacheCloseIsIdempotentAndObservable, explicitCacheNameIsPreserved
   */
  @Test void cacheClosedListenerParticipatesInClose() {
    AtomicReference<Cache<?, ?>> observed = new AtomicReference<>();
    CacheClosedListener listener = cache -> {
      observed.set(cache);
      return CompletableFuture.completedFuture(null);
    };
    Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .addCacheClosedListener(listener).build();
    cache.close();
    assertSame(cache, observed.get());
    assertTrue(cache.isClosed());
  }

  /**
   * Verifies: C2K-CTL-003, C2K-ENTRY-012
   * Depends-On: putAllStoresEveryMapping, cacheCloseIsIdempotentAndObservable
   */
  @Test void controlClearFutureCompletesAfterViewsAreEmpty() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build()) {
      cache.putAll(Map.of(1, "one", 2, "two"));
      OracleSupport.await(CacheControl.of(cache).clear());
      assertTrue(cache.asMap().isEmpty());
      assertTrue(cache.keys().isEmpty());
    }
  }

  /**
   * Verifies: C2K-CTL-003, C2K-LIFE-012
   * Depends-On: cacheCloseIsIdempotentAndObservable, explicitCacheNameIsPreserved
   */
  @Test void controlCloseFutureCompletesAfterLifecycleTransition() {
    Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).build();
    OracleSupport.await(CacheControl.of(cache).close());
    assertTrue(cache.isClosed());
    assertThrows(IllegalStateException.class, () -> cache.put(1, "one"));
  }

  /**
   * Verifies: C2K-CTL-004, C2K-LIFE-008
   * Depends-On: entryCapacityBoundsRetainedSize, putAllStoresEveryMapping
   */
  @Test void controlCapacityChangeUpdatesLimitAndBoundsSize() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).entryCapacity(10).build()) {
      cache.putAll(Map.of(1, "one", 2, "two", 3, "three"));
      OracleSupport.await(CacheControl.of(cache).changeCapacity(1));
      assertEquals(1, CacheInfo.of(cache).getCapacityLimit());
      assertTrue(CacheInfo.of(cache).getSize() <= 1);
    }
  }

  /**
   * Verifies: C2K-STAT-003, C2K-CTL-001
   * Depends-On: typedBuilderRetainsKeyAndValueTypes, putMakesValueVisible
   */
  @Test void disabledStatisticsAgreeAcrossInfoAndControlViews() {
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class)
      .disableStatistics(true).build()) {
      cache.put(1, "one");
      assertFalse(CacheInfo.of(cache).isStatisticsEnabled());
      assertNull(CacheControl.of(cache).sampleStatistics());
      assertEquals("one", cache.peek(1));
    }
  }

  /**
   * Verifies: C2K-LIFE-014, C2K-INV-004
   * Depends-On: managerLookupReusesOpenNamedManager, cacheCloseIsIdempotentAndObservable
   */
  @Test void managerCloseClosesOwnedCachesAndFreshLookupReopensName() {
    String managerName = OracleSupport.uniqueName("reopen-manager");
    CacheManager manager = CacheManager.getInstance(managerName);
    Cache<Integer, String> cache = Cache2kBuilder.of(Integer.class, String.class)
      .manager(manager).name(OracleSupport.uniqueName("managed-cache")).build();
    manager.close();
    assertTrue(manager.isClosed());
    assertTrue(cache.isClosed());
    CacheManager fresh = CacheManager.getInstance(managerName);
    try {
      assertFalse(fresh.isClosed());
      assertFalse(fresh == manager);
    } finally {
      fresh.close();
    }
  }

  /**
   * Verifies: C2K-LOAD-010, C2K-ENTRY-013
   * Depends-On: writerRunsBeforeSuccessfulCommit, putMakesValueVisible
   */
  @Test void writerCommitIsVisibleThroughCacheAndMapViews() {
    AtomicReference<String> written = new AtomicReference<>();
    CacheWriter<Integer, String> writer = new CacheWriter<>() {
      public void write(Integer key, String value) { written.set(value); }
      public void delete(Integer key) { }
    };
    try (Cache<Integer, String> cache = OracleSupport.builder(Integer.class, String.class).writer(writer).build()) {
      cache.asMap().put(1, "one");
      assertEquals("one", written.get());
      assertEquals("one", cache.peek(1));
      assertEquals("one", cache.peekEntry(1).getValue());
    }
  }

  /**
   * Verifies: C2K-PROC-010, C2K-PROC-011
   * Depends-On: invokeAllReturnsSuccessfulResultPerKey, putAllStoresEveryMapping
   */
  @Test void invokeAllResultsAndCommittedMappingsAgreePerKey() {
    try (Cache<Integer, Integer> cache = OracleSupport.builder(Integer.class, Integer.class).build()) {
      Map<Integer, org.cache2k.processor.EntryProcessingResult<Integer>> results =
        cache.invokeAll(Set.of(1, 2), entry -> { int v = entry.getKey() * 10; entry.setValue(v); return v + 1; });
      assertEquals(11, results.get(1).getResult());
      assertEquals(21, results.get(2).getResult());
      assertEquals(Map.of(1, 10, 2, 20), cache.peekAll(Set.of(1, 2)));
    }
  }
}
