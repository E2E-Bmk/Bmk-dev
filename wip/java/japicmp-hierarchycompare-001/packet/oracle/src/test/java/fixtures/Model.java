package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtNewConstructor;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import org.markline.model.JApiConstructor;
import org.markline.model.JApiImplementedInterface;
import org.markline.model.JApiSuperclass;

/** Fixtures for the hierarchy oracle: synthesise class versions and read the change tree. */
public final class Model {

    private Model() {}

    /** A fresh pool that can resolve JDK types (needed for superclass/interface anchors). */
    public static ClassPool pool() {
        return new ClassPool(true);
    }

    public static CtClass publicClass(ClassPool pool, String name) throws Exception {
        CtClass c = pool.makeClass(name);
        c.setModifiers(java.lang.reflect.Modifier.PUBLIC);
        return c;
    }

    /** Set a resolvable JDK type as the superclass (e.g. "java.util.ArrayList"). */
    public static void superclass(CtClass owner, String jdkType) throws Exception {
        owner.setSuperclass(owner.getClassPool().get(jdkType));
    }

    /** Add a resolvable JDK interface (e.g. "java.io.Serializable"). */
    public static void iface(CtClass owner, String jdkType) throws Exception {
        owner.addInterface(owner.getClassPool().get(jdkType));
    }

    /** Add a constructor from source (e.g. "public C(int x){}"). */
    public static void constructor(CtClass owner, String source) throws Exception {
        owner.addConstructor(CtNewConstructor.make(source, owner));
    }

    /** Compare two single-class versions (either may be null for a one-sided class). */
    public static List<JApiClass> compare(CtClass oldClass, CtClass newClass) {
        JarArchiveComparatorOptions o = new JarArchiveComparatorOptions();
        return new JarArchiveComparator(o).compareClassLists(o, list(oldClass), list(newClass));
    }

    public static List<JApiClass> compareAll(List<CtClass> oldClasses, List<CtClass> newClasses) {
        JarArchiveComparatorOptions o = new JarArchiveComparatorOptions();
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

    public static JApiSuperclass superOf(JApiClass c) {
        return c.getSuperclass();
    }

    public static JApiImplementedInterface interfaceNamed(JApiClass c, String fqn) {
        for (JApiImplementedInterface i : c.getInterfaces()) {
            if (i.getFullyQualifiedName().equals(fqn)) {
                return i;
            }
        }
        return null;
    }

    public static int constructorCount(JApiClass c) {
        return c.getConstructors().size();
    }

    public static JApiConstructor firstConstructor(JApiClass c) {
        return c.getConstructors().isEmpty() ? null : c.getConstructors().get(0);
    }
}
