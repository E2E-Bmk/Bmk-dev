package support;

import java.time.Instant;
import org.apache.commons.pool3.TrackedUse;

/** Public test value with an observable identifier and tracked-use instant. */
public final class TestResource implements TrackedUse {
    private final String id;
    private volatile Instant lastUsedInstant;

    public TestResource(final String id) {
        this.id = id;
        this.lastUsedInstant = Instant.now();
    }

    public String id() {
        return id;
    }

    public void touch(final Instant instant) {
        lastUsedInstant = instant;
    }

    @Override
    public Instant getLastUsedInstant() {
        return lastUsedInstant;
    }

    @Override
    public String toString() {
        return id;
    }
}


