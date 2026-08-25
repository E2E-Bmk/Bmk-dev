package support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.commons.pool3.BasePooledObjectFactory;
import org.apache.commons.pool3.DestroyMode;
import org.apache.commons.pool3.PooledObject;
import org.apache.commons.pool3.impl.DefaultPooledObject;

/** Deterministic public-API factory used by the oracle proposal. */
public class RecordingFactory extends BasePooledObjectFactory<TestResource, Exception> {
    private final AtomicInteger sequence = new AtomicInteger();
    private final List<String> callbacks = Collections.synchronizedList(new ArrayList<>());
    private final List<DestroyMode> destroyModes = Collections.synchronizedList(new ArrayList<>());
    private volatile boolean createNull;
    private volatile boolean valid = true;
    private volatile boolean failActivation;
    private volatile boolean failPassivation;

    @Override
    public TestResource create() {
        callbacks.add("create");
        return createNull ? null : new TestResource("resource-" + sequence.incrementAndGet());
    }

    @Override
    public PooledObject<TestResource> wrap(final TestResource value) {
        callbacks.add("wrap:" + value.id());
        return new DefaultPooledObject<>(value);
    }

    @Override
    public void activateObject(final PooledObject<TestResource> value) throws Exception {
        TestResource object = value.getObject();
        callbacks.add("activate:" + object.id());
        if (failActivation) {
            throw new Exception("activation rejected by test factory");
        }
    }

    @Override
    public boolean validateObject(final PooledObject<TestResource> value) {
        TestResource object = value.getObject();
        callbacks.add("validate:" + object.id());
        return valid;
    }

    @Override
    public void passivateObject(final PooledObject<TestResource> value) throws Exception {
        TestResource object = value.getObject();
        callbacks.add("passivate:" + object.id());
        if (failPassivation) {
            throw new Exception("passivation rejected by test factory");
        }
    }

    @Override
    public void destroyObject(final PooledObject<TestResource> value, final DestroyMode mode) {
        TestResource object = value.getObject();
        callbacks.add("destroy:" + object.id());
        destroyModes.add(mode);
    }

    public List<String> callbacks() {
        synchronized (callbacks) {
            return List.copyOf(callbacks);
        }
    }

    public long callbackCount(final String prefix) {
        synchronized (callbacks) {
            return callbacks.stream().filter(callback -> callback.startsWith(prefix)).count();
        }
    }

    public List<DestroyMode> destroyModes() {
        synchronized (destroyModes) {
            return List.copyOf(destroyModes);
        }
    }

    public void clearCallbacks() {
        callbacks.clear();
    }

    public void setCreateNull(final boolean value) {
        createNull = value;
    }

    public void setValid(final boolean value) {
        valid = value;
    }

    public void setFailActivation(final boolean value) {
        failActivation = value;
    }

    public void setFailPassivation(final boolean value) {
        failPassivation = value;
    }
}

