package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtNewMethod;
import javassist.bytecode.AnnotationsAttribute;
import javassist.bytecode.ClassFile;
import javassist.bytecode.ConstPool;
import javassist.bytecode.annotation.Annotation;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiAnnotation;
import org.markline.model.JApiClass;
import org.markline.model.JApiMethod;

/** Fixtures for the annotation oracle: synthesise class versions carrying runtime-visible annotations. */
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

    /** Attach a runtime-visible annotation (by fully-qualified type name) to the class. */
    public static void classAnnotation(CtClass owner, String annotationFqn) {
        ClassFile cf = owner.getClassFile();
        ConstPool cp = cf.getConstPool();
        AnnotationsAttribute attr = (AnnotationsAttribute) cf.getAttribute(AnnotationsAttribute.visibleTag);
        if (attr == null) {
            attr = new AnnotationsAttribute(cp, AnnotationsAttribute.visibleTag);
        }
        attr.addAnnotation(new Annotation(annotationFqn, cp));
        cf.addAttribute(attr);
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

    public static JApiAnnotation annotationNamed(JApiClass c, String fqn) {
        for (JApiAnnotation a : c.getAnnotations()) {
            if (a.getFullyQualifiedName().equals(fqn)) {
                return a;
            }
        }
        return null;
    }

    public static int annotationCount(JApiClass c) {
        return c.getAnnotations().size();
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
