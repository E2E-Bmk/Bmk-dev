package support;

import javax.inject.Named;
import org.eclipse.sisu.Description;
import org.eclipse.sisu.Hidden;
import org.eclipse.sisu.Priority;
import org.eclipse.sisu.Typed;

/** Public component fixtures used to observe the documented discovery projections. */
public final class DiscoveredComponents {
    private DiscoveredComponents() {}

    public interface Contract { String marker(); }
    public interface Extra { String extra(); }

    @Named("indexed-alpha")
    @Description("indexed-alpha-description")
    @Priority(61)
    @Typed(Contract.class)
    public static final class IndexedAlpha implements Contract {
        public String marker() { return "indexed-alpha-61"; }
    }

    @Named("typed-contract")
    @Typed(Contract.class)
    public static final class TypedContract implements Contract, Extra {
        public String marker() { return "typed-contract"; }
        public String extra() { return "hidden-extra"; }
    }

    @Named("hidden-contract")
    @Hidden
    public static final class HiddenContract implements Contract {
        public String marker() { return "hidden-contract"; }
    }
}
