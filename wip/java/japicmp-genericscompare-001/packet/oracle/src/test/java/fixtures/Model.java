package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtNewMethod;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiClass;
import org.markline.model.JApiGenericTemplate;
import org.markline.model.JApiMethod;

/** Fixtures for the generics oracle: synthesise class versions carrying JVM generic signatures. */
public final class Model {

    private Model() {}

    public static ClassPool pool() {
        return new ClassPool(true);
    }

    public static CtClass publicClass(ClassPool pool, String name) throws Exception {
        CtClass c = pool.makeClass(name);
        c.setModifiers(java.lang.reflect.Modifier.PUBLIC);
        return c;
    }

    /** Attach a class-level generic signature (e.g. "&lt;T:Ljava/lang/Object;&gt;Ljava/lang/Object;"). */
    public static void generic(CtClass owner, String signature) {
        owner.setGenericSignature(signature);
    }

    public static void method(CtClass owner, String source) throws Exception {
        owner.addMethod(CtNewMethod.make(source, owner));
    }

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

    public static JApiGenericTemplate templateNamed(JApiClass c, String name) {
        for (JApiGenericTemplate t : c.getGenericTemplates()) {
            if (t.getName().equals(name)) {
                return t;
            }
        }
        return null;
    }

    public static int templateCount(JApiClass c) {
        return c.getGenericTemplates().size();
    }

    public static JApiMethod methodNamed(JApiClass c, String name) {
        for (JApiMethod m : c.getMethods()) {
            if (m.getName().equals(name)) {
                return m;
            }
        }
        return null;
    }
}
