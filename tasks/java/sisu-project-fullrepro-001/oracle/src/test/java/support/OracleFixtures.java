package support;

import java.util.ArrayList;
import java.util.List;
import javax.inject.Named;
import org.eclipse.sisu.Description;
import org.eclipse.sisu.Hidden;
import org.eclipse.sisu.PostConstruct;
import org.eclipse.sisu.PreDestroy;
import org.eclipse.sisu.Priority;
import org.eclipse.sisu.Typed;

public final class OracleFixtures {
    private OracleFixtures() {}

    public interface Service { String value(); }

    public static class AlphaService implements Service {
        public String value() { return "alpha-37"; }
    }

    public static class BetaService implements Service {
        public String value() { return "beta-41"; }
    }

    @Priority(73)
    @Description("ranked-service-73")
    public static class RankedService implements Service {
        public String value() { return "ranked-73"; }
    }

    @Hidden
    public static class HiddenService implements Service {
        public String value() { return "hidden-19"; }
    }

    @Typed(Service.class)
    public static class TypedService implements Service {
        public String value() { return "typed-23"; }
    }

    public static class ManagedService {
        public int starts;
        public int stops;
        @PostConstruct public void start() { starts++; }
        @PreDestroy public void stop() { stops++; }
    }

    public static class PlainService {}

    public static class FailingManagedService {
        @PostConstruct public void start() { throw new IllegalStateException("probe"); }
    }

    public static class EventWatcher {
        public final List<String> events = new ArrayList<String>();
    }

    @Named("fixture-named")
    public static class NamedService implements Service {
        public String value() { return "named-29"; }
    }
}
