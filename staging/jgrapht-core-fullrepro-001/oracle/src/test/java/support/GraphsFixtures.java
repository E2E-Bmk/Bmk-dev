package support;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/** Shared helpers for the graph oracle. */
public final class GraphsFixtures {

    private GraphsFixtures() {
    }

    /** Drains an iterator into a list, preserving order. */
    public static <V> List<V> drain(Iterator<V> iterator) {
        List<V> out = new ArrayList<>();
        while (iterator.hasNext()) {
            out.add(iterator.next());
        }
        return out;
    }
}
