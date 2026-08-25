package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.concurrent.atomic.AtomicInteger;
import org.apache.commons.pool3.DestroyMode;
import org.apache.commons.pool3.PooledObject;
import org.apache.commons.pool3.PooledObjectFactory;
import org.apache.commons.pool3.impl.DefaultEvictionPolicy;
import org.apache.commons.pool3.impl.DefaultPooledObject;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.junit.jupiter.api.Test;
import support.RecordingFactory;
import support.TestResource;

/** Atomic tests for validation, invalidation, and destruction controls. */
class ValidationAtomicTest {

    /** Verifies: CP-VALID-001. */
    @Test void testOnCreateFlagRoundTrips() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setTestOnCreate(true);
        assertTrue(config.getTestOnCreate());
        config.setTestOnCreate(false);
        assertFalse(config.getTestOnCreate());
    }

    /** Verifies: CP-VALID-003. */
    @Test void testOnBorrowFlagRoundTrips() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setTestOnBorrow(true);
        assertTrue(config.getTestOnBorrow());
        config.setTestOnBorrow(false);
        assertFalse(config.getTestOnBorrow());
    }

    /** Verifies: CP-VALID-005. */
    @Test void testOnReturnFlagRoundTrips() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setTestOnReturn(true);
        assertTrue(config.getTestOnReturn());
        config.setTestOnReturn(false);
        assertFalse(config.getTestOnReturn());
    }

    /** Verifies: CP-EVICT-006. */
    @Test void testWhileIdleFlagRoundTrips() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setTestWhileIdle(true);
        assertTrue(config.getTestWhileIdle());
        config.setTestWhileIdle(false);
        assertFalse(config.getTestWhileIdle());
    }

    /** Verifies: CP-EVICT-005. */
    @Test void concreteEvictionPolicyCanBeSelected() {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory)) {
            pool.setEvictionPolicyClassName(DefaultEvictionPolicy.class.getName());
            assertEquals(DefaultEvictionPolicy.class.getName(), pool.getEvictionPolicyClassName());
        }
    }

    /** Verifies: CP-ERR-008. */
    @Test void invalidEvictionPolicyClassRaisesIllegalArgument() {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory)) {
            assertThrows(IllegalArgumentException.class,
                    () -> pool.setEvictionPolicyClassName(String.class.getName()));
        }
    }

    /** Verifies: CP-FACT-003. */
    @Test void twoArgumentDestroyDefaultsToSingleArgumentDestroy() throws Exception {
        AtomicInteger destroys = new AtomicInteger();
        PooledObjectFactory<String, Exception> factory = new PooledObjectFactory<>() {
            @Override public PooledObject<String> makeObject() { return new DefaultPooledObject<>("x"); }
            @Override public void destroyObject(PooledObject<String> value) { destroys.incrementAndGet(); }
            @Override public boolean validateObject(PooledObject<String> value) { return true; }
            @Override public void activateObject(PooledObject<String> value) { }
            @Override public void passivateObject(PooledObject<String> value) { }
        };
        factory.destroyObject(factory.makeObject(), DestroyMode.ABANDONED);
        assertEquals(1, destroys.get());
    }

    /** Verifies: CP-FACT-003, CP-ABAND-005. */
    @Test void destroyModeVocabularyDistinguishesNormalAndAbandoned() {
        assertNotEquals(DestroyMode.NORMAL, DestroyMode.ABANDONED);
        assertEquals("NORMAL", DestroyMode.NORMAL.name());
        assertEquals("ABANDONED", DestroyMode.ABANDONED.name());
    }
}


