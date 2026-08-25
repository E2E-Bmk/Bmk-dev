package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtMethod;
import javassist.CtNewMethod;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.BridgeModifier;
import org.markline.model.JApiClass;
import org.markline.model.JApiMethod;
import org.markline.model.JApiModifier;
import org.markline.model.SyntheticModifier;

/** Fixtures for the special-modifier oracle: synthesise methods carrying the bridge/synthetic access flags. */
public final class Model {

    private static final int ACC_BRIDGE = 0x0040;
    private static final int ACC_SYNTHETIC = 0x1000;

    private Model() {}

    public static ClassPool pool() {
        return new ClassPool(true);
    }

    public static CtClass publicClass(ClassPool pool, String name) throws Exception {
        CtClass c = pool.makeClass(name);
        c.setModifiers(java.lang.reflect.Modifier.PUBLIC);
        return c;
    }

    private static void add(CtClass owner, String source, int extraFlags) throws Exception {
        CtMethod m = CtNewMethod.make(source, owner);
        if (extraFlags != 0) {
            m.getMethodInfo().setAccessFlags(m.getMethodInfo().getAccessFlags() | extraFlags);
        }
        owner.addMethod(m);
    }

    /** Add a plain method with no special access flags. */
    public static void plainMethod(CtClass owner, String source) throws Exception {
        add(owner, source, 0);
    }

    /** Add a method carrying the ACC_BRIDGE access flag. */
    public static void bridgeMethod(CtClass owner, String source) throws Exception {
        add(owner, source, ACC_BRIDGE);
    }

    /** Add a method carrying the ACC_SYNTHETIC access flag. */
    public static void syntheticMethod(CtClass owner, String source) throws Exception {
        add(owner, source, ACC_SYNTHETIC);
    }

    public static List<JApiClass> compare(CtClass oldClass, CtClass newClass) {
        JarArchiveComparatorOptions o = new JarArchiveComparatorOptions();
        o.setIncludeSynthetic(true);
        return new JarArchiveComparator(o).compareClassLists(o, list(oldClass), list(newClass));
    }

    public static List<JApiClass> compareAll(List<CtClass> oldClasses, List<CtClass> newClasses) {
        JarArchiveComparatorOptions o = new JarArchiveComparatorOptions();
        o.setIncludeSynthetic(true);
        return new JarArchiveComparator(o).compareClassLists(o, oldClasses, newClasses);
    }

    private static List<CtClass> list(CtClass c) {
        return c == null ? java.util.Collections.<CtClass>emptyList() : Arrays.asList(c);
    }

    public static JApiClass onlyClass(List<JApiClass> classes) {
        return classes.get(0);
    }

    public static JApiClass classNamed(List<JApiClass> classes, String fqn) {
        for (JApiClass c : classes) {
            if (c.getFullyQualifiedName().equals(fqn)) {
                return c;
            }
        }
        return null;
    }

    public static JApiMethod methodNamed(JApiClass c, String name) {
        for (JApiMethod m : c.getMethods()) {
            if (m.getName().equals(name)) {
                return m;
            }
        }
        return null;
    }

    public static JApiModifier<BridgeModifier> bridgeOf(JApiMethod m) {
        return m.getBridgeModifier();
    }

    public static JApiModifier<SyntheticModifier> syntheticOf(JApiMethod m) {
        return m.getSyntheticModifier();
    }
}
