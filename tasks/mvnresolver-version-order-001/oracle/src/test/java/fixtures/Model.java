package fixtures;

import org.versionway.util.version.GenericVersionScheme;
import org.versionway.version.Version;
import org.versionway.version.VersionConstraint;
import org.versionway.version.VersionRange;

/** Fixtures for the version-ordering oracle: parse versions/ranges and compare them. */
public final class Model {

    private static final GenericVersionScheme SCHEME = new GenericVersionScheme();

    private Model() {}

    public static Version v(String s) throws Exception {
        return SCHEME.parseVersion(s);
    }

    /** Sign of comparing a to b: -1, 0, or +1. */
    public static int cmp(String a, String b) throws Exception {
        return Integer.signum(SCHEME.parseVersion(a).compareTo(SCHEME.parseVersion(b)));
    }

    public static boolean eq(String a, String b) throws Exception {
        return cmp(a, b) == 0;
    }

    public static VersionRange range(String s) throws Exception {
        return SCHEME.parseVersionRange(s);
    }

    public static boolean rangeContains(String rangeSpec, String version) throws Exception {
        return SCHEME.parseVersionRange(rangeSpec).containsVersion(SCHEME.parseVersion(version));
    }

    public static VersionConstraint constraint(String s) throws Exception {
        return SCHEME.parseVersionConstraint(s);
    }

    public static boolean constraintContains(String spec, String version) throws Exception {
        return SCHEME.parseVersionConstraint(spec).containsVersion(SCHEME.parseVersion(version));
    }
}
