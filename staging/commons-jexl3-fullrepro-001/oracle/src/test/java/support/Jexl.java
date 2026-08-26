package support;

import org.apache.commons.jexl3.JexlBuilder;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.JexlEngine;
import org.apache.commons.jexl3.MapContext;

/** Shared engines and evaluation shorthand for the expression-language oracle. */
public final class Jexl {

    /** Default engine: strict, throwing, safe navigation. */
    public static final JexlEngine DEFAULT = new JexlBuilder().create();

    private Jexl() {
    }

    /** Evaluates one expression under the default engine and a fresh context. */
    public static Object eval(String source) {
        return DEFAULT.createExpression(source).evaluate(new MapContext());
    }

    /** Evaluates one expression under the default engine and the given context. */
    public static Object eval(String source, JexlContext context) {
        return DEFAULT.createExpression(source).evaluate(context);
    }

    /** Executes one script under the default engine and a fresh context. */
    public static Object run(String source) {
        return DEFAULT.createScript(source).execute(new MapContext());
    }

    /** Executes one script under the default engine and the given context. */
    public static Object run(String source, JexlContext context) {
        return DEFAULT.createScript(source).execute(context);
    }
}
