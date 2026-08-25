package fixtures;

import javassist.ClassPool;
import javassist.CtClass;
import org.plumbline.cmp.JarArchiveComparator;
import org.plumbline.cmp.JarArchiveComparatorOptions;
import org.plumbline.model.AccessModifier;
import org.plumbline.model.JApiClass;
import org.plumbline.model.JApiCompatibilityChange;
import org.plumbline.model.JApiCompatibilityChangeType;
import org.plumbline.model.JApiField;
import org.plumbline.model.JApiMethod;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

/**
 * Drives a comparison and reads it back, so the tests state expectations rather
 * than plumbing.
 *
 * <p>Everything here goes through the entry points the spec's Representative
 * Workflows use -- {@code new JarArchiveComparator(options)} then
 * {@code compareClassLists(options, oldList, newList)} -- and reads only declared
 * accessors. No test reaches into the comparison's internals, so a correct
 * reimplementation with different internal structures passes.
 */
public final class Compare {

    private Compare() {
    }

    /** Options at the spec's documented default access level for a public API audit. */
    public static JarArchiveComparatorOptions publicOnly() {
        JarArchiveComparatorOptions options = new JarArchiveComparatorOptions();
        options.setAccessModifier(AccessModifier.PUBLIC);
        return options;
    }

    /** Compares one old shape against one new shape and returns the tree. */
    public static List<JApiClass> compare(CtClass oldVersion, CtClass newVersion) {
        return compare(publicOnly(), oldVersion, newVersion);
    }

    public static List<JApiClass> compare(
            JarArchiveComparatorOptions options, CtClass oldVersion, CtClass newVersion) {
        List<CtClass> oldList =
                oldVersion == null ? Collections.emptyList() : Collections.singletonList(oldVersion);
        List<CtClass> newList =
                newVersion == null ? Collections.emptyList() : Collections.singletonList(newVersion);
        return new JarArchiveComparator(options).compareClassLists(options, oldList, newList);
    }

    /** The single compared class, failing loudly when the tree is not a single entry. */
    public static JApiClass only(List<JApiClass> tree) {
        if (tree.size() != 1) {
            throw new IllegalStateException("expected exactly one class, got " + tree.size());
        }
        return tree.get(0);
    }

    /** The named class from a multi-class tree. */
    public static JApiClass named(List<JApiClass> tree, String fullyQualifiedName) {
        for (JApiClass candidate : tree) {
            if (fullyQualifiedName.equals(candidate.getFullyQualifiedName())) {
                return candidate;
            }
        }
        throw new IllegalStateException("no class named " + fullyQualifiedName);
    }

    public static Optional<JApiMethod> method(JApiClass owner, String name) {
        for (JApiMethod candidate : owner.getMethods()) {
            if (name.equals(candidate.getName())) {
                return Optional.of(candidate);
            }
        }
        return Optional.empty();
    }

    public static Optional<JApiField> field(JApiClass owner, String name) {
        for (JApiField candidate : owner.getFields()) {
            if (name.equals(candidate.getName())) {
                return Optional.of(candidate);
            }
        }
        return Optional.empty();
    }

    /** Change types on a class, as a list so a test can assert membership or exact content. */
    public static List<JApiCompatibilityChangeType> changeTypes(JApiClass subject) {
        List<JApiCompatibilityChangeType> types = new ArrayList<>();
        for (JApiCompatibilityChange change : subject.getCompatibilityChanges()) {
            types.add(change.getType());
        }
        return types;
    }

    public static List<JApiCompatibilityChangeType> changeTypes(JApiMethod subject) {
        List<JApiCompatibilityChangeType> types = new ArrayList<>();
        for (JApiCompatibilityChange change : subject.getCompatibilityChanges()) {
            types.add(change.getType());
        }
        return types;
    }

    public static List<JApiCompatibilityChangeType> changeTypes(JApiField subject) {
        List<JApiCompatibilityChangeType> types = new ArrayList<>();
        for (JApiCompatibilityChange change : subject.getCompatibilityChanges()) {
            types.add(change.getType());
        }
        return types;
    }

    /** Two independent pools, so the old and new shape of one name can coexist. */
    public static ClassPool[] pools() {
        return new ClassPool[] {Bytecode.pool(), Bytecode.pool()};
    }
}
