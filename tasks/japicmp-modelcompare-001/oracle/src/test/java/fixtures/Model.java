package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.CtNewConstructor;
import javassist.CtNewMethod;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import org.markline.model.JApiField;
import org.markline.model.JApiMethod;

/** Fixtures for the markline oracle: synthesise class versions and read the change tree. */
public final class Model {

    private Model() {}

    /** A fresh pool that can resolve JDK types (needed for method signatures). */
    public static ClassPool pool() {
        return new ClassPool(true);
    }

    public static CtClass publicClass(ClassPool pool, String name) throws Exception {
        CtClass c = pool.makeClass(name);
        c.setModifiers(java.lang.reflect.Modifier.PUBLIC);
        return c;
    }

    public static CtClass publicInterface(ClassPool pool, String name) {
        CtClass c = pool.makeInterface(name);
        return c;
    }

    public static void method(CtClass owner, String source) throws Exception {
        owner.addMethod(CtNewMethod.make(source, owner));
    }

    public static void field(CtClass owner, String source) throws Exception {
        owner.addField(CtField.make(source, owner));
    }

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

    public static JApiMethod methodNamed(JApiClass c, String name) {
        for (JApiMethod m : c.getMethods()) {
            if (m.getName().equals(name)) {
                return m;
            }
        }
        return null;
    }

    public static JApiField fieldNamed(JApiClass c, String name) {
        for (JApiField f : c.getFields()) {
            if (f.getName().equals(name)) {
                return f;
            }
        }
        return null;
    }
}
