package support;

import com.zaxxer.hikari.metrics.IMetricsTracker;
import com.zaxxer.hikari.metrics.MetricsTrackerFactory;
import com.zaxxer.hikari.metrics.PoolStats;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/** Public metrics extension used to observe lifecycle callbacks. */
public final class RecordingMetrics implements MetricsTrackerFactory {
   public final AtomicInteger createCalls = new AtomicInteger();
   public final AtomicInteger timeoutCalls = new AtomicInteger();
   public final AtomicInteger closeCalls = new AtomicInteger();
   public final AtomicInteger acquiredCalls = new AtomicInteger();
   public final AtomicInteger createdCalls = new AtomicInteger();
   public final AtomicInteger usageCalls = new AtomicInteger();
   public final AtomicLong lastAcquiredNanos = new AtomicLong(-1);
   public volatile String poolName;
   public volatile PoolStats poolStats;

   @Override
   public IMetricsTracker create(String name, PoolStats stats) {
      createCalls.incrementAndGet();
      poolName = name;
      poolStats = stats;
      return new IMetricsTracker() {
         @Override public void recordConnectionAcquiredNanos(long elapsedAcquiredNanos) {
            acquiredCalls.incrementAndGet();
            lastAcquiredNanos.set(elapsedAcquiredNanos);
         }
         @Override public void recordConnectionUsageMillis(long elapsedBorrowedMillis) {
            usageCalls.incrementAndGet();
         }
         @Override public void recordConnectionCreatedMillis(long connectionCreatedMillis) {
            createdCalls.incrementAndGet();
         }
         @Override public void recordConnectionTimeout() { timeoutCalls.incrementAndGet(); }
         @Override public void close() { closeCalls.incrementAndGet(); }
      };
   }
}
