package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import org.apache.commons.pool3.PooledObject;
import org.apache.commons.pool3.PooledObjectState;
import org.apache.commons.pool3.impl.DefaultPooledObject;
import org.junit.jupiter.api.Test;
import support.RecordingFactory;
import support.TestResource;

/** Atomic tests for factory and pooled-object lifecycle behavior. */
class FactoryWrapperAtomicTest {

    /** Verifies: CP-FACT-004. */
    @Test void makeObjectWrapsCreatedValue() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        PooledObject<TestResource> wrapped = factory.makeObject();
        TestResource object = wrapped.getObject();
        assertEquals("resource-1", object.id());
        assertEquals(List.of("create", "wrap:resource-1"), factory.callbacks());
    }

    /** Verifies: CP-FACT-005, CP-ERR-002. */
    @Test void makeObjectRejectsNullCreation() {
        RecordingFactory factory = new RecordingFactory();
        factory.setCreateNull(true);
        assertThrows(NullPointerException.class, factory::makeObject);
    }

    /** Verifies: CP-FACT-006. */
    @Test void baseFactoryDefaultsPreserveWrapperAndValidateTrue() throws Exception {
        var factory = new org.apache.commons.pool3.BasePooledObjectFactory<String, Exception>() {
            @Override public String create() { return "seed"; }
            @Override public PooledObject<String> wrap(String value) { return new DefaultPooledObject<>(value); }
        };
        PooledObject<String> wrapped = factory.makeObject();
        factory.activateObject(wrapped);
        factory.passivateObject(wrapped);
        factory.destroyObject(wrapped);
        assertEquals("seed", wrapped.getObject());
        assertTrue(factory.validateObject(wrapped));
    }

    /** Verifies: CP-FACT-007. */
    @Test void newWrapperStartsIdleWithCoincidentInstants() {
        TestResource value = new TestResource("initial");
        DefaultPooledObject<TestResource> wrapped = new DefaultPooledObject<>(value);
        assertSame(value, wrapped.getObject());
        assertEquals(PooledObjectState.IDLE, wrapped.getState());
        assertEquals(wrapped.getCreateInstant(), wrapped.getLastBorrowInstant());
        assertEquals(wrapped.getCreateInstant(), wrapped.getLastReturnInstant());
    }

    /** Verifies: CP-FACT-008, CP-FACT-015. */
    @Test void allocationUpdatesStateAndBorrowCount() {
        DefaultPooledObject<String> wrapped = new DefaultPooledObject<>("allocatable");
        assertTrue(wrapped.allocate());
        assertEquals(PooledObjectState.ALLOCATED, wrapped.getState());
        assertEquals(1L, wrapped.getBorrowedCount());
        assertFalse(wrapped.getLastBorrowInstant().isBefore(wrapped.getCreateInstant()));
    }

    /** Verifies: CP-FACT-009, CP-FACT-015. */
    @Test void repeatedAllocationFailsWithoutIncrementingCount() {
        DefaultPooledObject<String> wrapped = new DefaultPooledObject<>("single-lease");
        assertTrue(wrapped.allocate());
        assertFalse(wrapped.allocate());
        assertEquals(1L, wrapped.getBorrowedCount());
        assertEquals(PooledObjectState.ALLOCATED, wrapped.getState());
    }

    /** Verifies: CP-FACT-010. */
    @Test void returningThenDeallocatingRestoresIdleState() {
        DefaultPooledObject<String> wrapped = new DefaultPooledObject<>("returnable");
        wrapped.allocate();
        Instant borrowed = wrapped.getLastBorrowInstant();
        wrapped.markReturning();
        assertEquals(PooledObjectState.RETURNING, wrapped.getState());
        assertTrue(wrapped.deallocate());
        assertEquals(PooledObjectState.IDLE, wrapped.getState());
        assertFalse(wrapped.getLastReturnInstant().isBefore(borrowed));
    }

    /** Verifies: CP-FACT-011, CP-FACT-012, CP-FACT-013, CP-FACT-014. */
    @Test void invalidAndEvictionTransitionsPreserveSpecifiedStates() {
        DefaultPooledObject<String> idle = new DefaultPooledObject<>("evictable");
        assertFalse(idle.deallocate());
        assertTrue(idle.startEvictionTest());
        assertEquals(PooledObjectState.EVICTION, idle.getState());
        assertFalse(idle.startEvictionTest());
        assertEquals(PooledObjectState.EVICTION, idle.getState());
        DefaultPooledObject<String> invalid = new DefaultPooledObject<>("invalid");
        invalid.invalidate();
        assertEquals(PooledObjectState.INVALID, invalid.getState());
    }
}

