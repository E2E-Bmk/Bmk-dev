package oraclesupport;

import org.pf4j.Extension;

@Extension(ordinal = 5)
public class AlphaGreeting implements Greeting {
    public String text() { return "alpha-value"; }
}
