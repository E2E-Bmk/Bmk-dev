package support;

import java.io.IOException;
import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Repeatable;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.util.List;
import java.util.Map;

/** Benchmark-owned classfile fixtures for local scans. */
public final class FixtureTypes {
    private FixtureTypes() {
    }

    public enum Mode {
        ALPHA,
        BETA
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.ANNOTATION_TYPE)
    public @interface MetaTag {
    }

    @MetaTag
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD, ElementType.PARAMETER})
    public @interface Tagged {
        String value();

        int rank() default 7;

        Class<?> target() default String.class;

        Mode mode() default Mode.BETA;
    }

    @Inherited
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    public @interface InheritedTag {
        String value() default "root";
    }

    @Repeatable(Labels.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    public @interface Label {
        String value();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    public @interface Labels {
        Label[] value();
    }

    public interface Plugin {
        String id();
    }

    public interface AdvancedPlugin extends Plugin {
        int level();
    }

    public interface ExpertPlugin extends AdvancedPlugin {
    }

    public abstract static class AbstractPlugin implements Plugin {
        @Override
        public String id() {
            return "abstract";
        }
    }

    @Tagged(value = "base", rank = 11)
    public static class BasePlugin {
        @Tagged("base-field")
        public String baseField = "base";

        @Tagged("base-method")
        public Number convert(@Tagged("input") final String input) {
            return input.length();
        }
    }

    @Tagged(value = "direct", rank = 13, target = Integer.class, mode = Mode.ALPHA)
    public static class DirectPlugin extends BasePlugin implements Plugin {
        public static final int MAGIC = 41;
        public static final String LABEL = "fixture-label";
        public final List<String> names = List.of("red", "blue");
        public String[][] matrix;
        private int hidden = 9;

        public DirectPlugin() {
        }

        public DirectPlugin(final String ignored) {
        }

        @Override
        public String id() {
            return "direct";
        }

        @Override
        @Tagged(value = "override", rank = 17)
        public Integer convert(@Tagged("child-input") final String input) throws IllegalStateException {
            return input.length() + 1;
        }

        public Map<String, Integer> indexed(final String prefix, final int... values) throws IOException {
            return Map.of(prefix, values.length);
        }

        public GenericBox<Integer> box() {
            return new GenericBox<>();
        }

        private String hiddenMethod() {
            return "hidden";
        }
    }

    public static class ChildPlugin extends DirectPlugin implements AdvancedPlugin {
        @Override
        public String id() {
            return "child";
        }

        @Override
        public int level() {
            return 2;
        }
    }

    public static final class LeafPlugin extends ChildPlugin implements ExpertPlugin {
    }

    @InheritedTag("ancestor")
    public static class AnnotatedBase {
    }

    public static final class AnnotatedChild extends AnnotatedBase {
    }

    @Label("north")
    @Label("south")
    public static final class RepeatableTarget {
    }

    public enum Shade {
        RED,
        GREEN
    }

    public record Point(int x, int y) {
    }

    public static class GenericBox<T extends Number & Comparable<T>> {
        public T value;
        public List<? extends Number> upper;
        public List<? super Integer> lower;

        public T getValue() {
            return value;
        }

        public <X extends CharSequence> X echo(final X input) {
            return input;
        }
    }
}
