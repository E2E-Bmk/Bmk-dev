package support;

import com.zaxxer.hikari.metrics.PoolStats;

import java.util.concurrent.atomic.AtomicInteger;

/** Caller-defined PoolStats projection for atomic refresh-cache checks. */
public final class ObservedPoolStats extends PoolStats {
   public final AtomicInteger updates = new AtomicInteger();

   public ObservedPoolStats(long timeoutMs) {
      super(timeoutMs);
   }

   @Override
   protected void update() {
      int value = updates.incrementAndGet();
      totalConnections = value + 5;
      idleConnections = value + 2;
      activeConnections = 3;
      pendingThreads = 1;
      maxConnections = 11;
      minConnections = 2;
   }
}
