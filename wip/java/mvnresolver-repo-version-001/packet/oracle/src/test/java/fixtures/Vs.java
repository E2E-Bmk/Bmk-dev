package fixtures;

import org.eclipse.aether.version.VersionConstraint;
import org.eclipse.aether.version.VersionRange;
import org.versionsmith.GenericVersion;
import org.versionsmith.GenericVersionScheme;
import org.versionsmith.UnionVersionRange;

/** Test fixtures: a shared generic scheme and thin parse helpers. */
public final class Vs {

    private static final GenericVersionScheme S = new GenericVersionScheme();

    private Vs() {}

    public static GenericVersion v(String s) throws Exception {
        return S.parseVersion(s);
    }

    public static VersionRange range(String s) throws Exception {
        return S.parseVersionRange(s);
    }

    public static VersionConstraint constraint(String s) throws Exception {
        return S.parseVersionConstraint(s);
    }

    public static VersionRange union(VersionRange... ranges) {
        return UnionVersionRange.from(ranges);
    }
}
