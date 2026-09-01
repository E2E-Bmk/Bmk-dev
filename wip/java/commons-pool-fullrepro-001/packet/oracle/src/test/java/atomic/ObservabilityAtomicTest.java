package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.text.SimpleDateFormat;
import java.time.Instant;
import java.util.Date;
import org.apache.commons.pool3.impl.DefaultPooledObject;
import org.apache.commons.pool3.impl.DefaultPooledObjectInfo;
import org.junit.jupiter.api.Test;
import support.TestResource;

/** Atomic tests for statistics and per-object management views. */
class ObservabilityAtomicTest {

    /** Verifies: CP-OBS-009. */
    @Test void infoRejectsNullWrapper() {
        assertThrows(NullPointerException.class, () -> new DefaultPooledObjectInfo(null));
    }

    /** Verifies: CP-OBS-009. */
    @Test void pooledObjectOperationReturnsRepresentedWrapper() {
        DefaultPooledObject<TestResource> wrapped = wrapper("identity");
        DefaultPooledObjectInfo info = new DefaultPooledObjectInfo(wrapped);
        assertSame(wrapped, info.pooledObject());
    }

    /** Verifies: CP-OBS-007. */
    @Test void infoExposesConcreteWrappedObjectType() {
        DefaultPooledObjectInfo info = new DefaultPooledObjectInfo(wrapper("typed"));
        assertEquals(TestResource.class.getName(), info.getPooledObjectType());
    }

    /** Verifies: CP-OBS-007. */
    @Test void infoExposesWrappedObjectStringValue() {
        DefaultPooledObjectInfo info = new DefaultPooledObjectInfo(wrapper("visible-value"));
        assertEquals("visible-value", info.getPooledObjectToString());
    }

    /** Verifies: CP-OBS-007. */
    @Test void infoProjectsBorrowedCount() {
        DefaultPooledObject<TestResource> wrapped = wrapper("counted");
        wrapped.allocate();
        wrapped.deallocate();
        wrapped.allocate();
        DefaultPooledObjectInfo info = new DefaultPooledObjectInfo(wrapped);
        assertEquals(2L, info.getBorrowedCount());
    }

    /** Verifies: CP-OBS-007. */
    @Test void infoProjectsCreationAndLifecycleEpochTimes() {
        DefaultPooledObject<TestResource> wrapped = wrapper("timed");
        wrapped.allocate();
        wrapped.deallocate();
        DefaultPooledObjectInfo info = new DefaultPooledObjectInfo(wrapped);
        Instant created = wrapped.getCreateInstant();
        Instant borrowed = wrapped.getLastBorrowInstant();
        Instant returned = wrapped.getLastReturnInstant();
        assertEquals(created.toEpochMilli(), info.getCreateTime());
        assertEquals(borrowed.toEpochMilli(), info.getLastBorrowTime());
        assertEquals(returned.toEpochMilli(), info.getLastReturnTime());
    }

    /** Verifies: CP-OBS-008. */
    @Test void creationTimeUsesSpecifiedPublicFormat() {
        DefaultPooledObjectInfo info = new DefaultPooledObjectInfo(wrapper("formatted-create"));
        String expected = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z").format(new Date(info.getCreateTime()));
        assertEquals(expected, info.getCreateTimeFormatted());
    }

    /** Verifies: CP-OBS-008. */
    @Test void borrowAndReturnTimesUseSpecifiedPublicFormat() {
        DefaultPooledObject<TestResource> wrapped = wrapper("formatted-cycle");
        wrapped.allocate();
        wrapped.deallocate();
        DefaultPooledObjectInfo info = new DefaultPooledObjectInfo(wrapped);
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z");
        assertEquals(format.format(new Date(info.getLastBorrowTime())), info.getLastBorrowTimeFormatted());
        assertEquals(format.format(new Date(info.getLastReturnTime())), info.getLastReturnTimeFormatted());
    }

    private static DefaultPooledObject<TestResource> wrapper(final String id) {
        return new DefaultPooledObject<>(new TestResource(id));
    }
}

