package oraclesupport;

import org.pf4j.Extension;

@Extension(ordinal = 1)
public class BetaGreeting implements Greeting {
    public String text() { return "beta-value"; }
}
