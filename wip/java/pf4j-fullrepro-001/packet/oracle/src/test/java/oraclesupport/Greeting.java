package oraclesupport;

import org.pf4j.ExtensionPoint;

public interface Greeting extends ExtensionPoint {
    String text();
}
