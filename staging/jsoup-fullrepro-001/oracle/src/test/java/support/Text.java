package support;

/** Shared text helpers for the tree-serialization tests. */
public final class Text {
    private Text() {}

    /** Joins the given lines with {@code \n}, with no trailing newline. */
    public static String join(String... lines) {
        return String.join("\n", lines);
    }
}
