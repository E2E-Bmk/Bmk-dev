package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.bytecode.AnnotationsAttribute;
import javassist.bytecode.ClassFile;
import javassist.bytecode.ConstPool;
import javassist.bytecode.annotation.Annotation;
import javassist.bytecode.annotation.BooleanMemberValue;
import javassist.bytecode.annotation.IntegerMemberValue;
import javassist.bytecode.annotation.StringMemberValue;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiAnnotation;
import org.markline.model.JApiAnnotationElement;
import org.markline.model.JApiClass;

/** Fixtures for the annotation-value oracle: synthesise class annotations carrying member values. */
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

    private static Annotation ensure(CtClass owner, String annotationFqn) {
        ClassFile cf = owner.getClassFile();
        ConstPool cp = cf.getConstPool();
        AnnotationsAttribute attr = (AnnotationsAttribute) cf.getAttribute(AnnotationsAttribute.visibleTag);
        if (attr == null) {
            attr = new AnnotationsAttribute(cp, AnnotationsAttribute.visibleTag);
        }
        Annotation a = attr.getAnnotation(annotationFqn);
        if (a == null) {
            a = new Annotation(annotationFqn, cp);
        }
        return a;
    }

    private static void put(CtClass owner, String annotationFqn, Annotation a) {
        ClassFile cf = owner.getClassFile();
        AnnotationsAttribute attr = (AnnotationsAttribute) cf.getAttribute(AnnotationsAttribute.visibleTag);
        if (attr == null) {
            attr = new AnnotationsAttribute(cf.getConstPool(), AnnotationsAttribute.visibleTag);
        }
        attr.addAnnotation(a);
        cf.addAttribute(attr);
    }

    /** Attach a marker annotation with no members. */
    public static void marker(CtClass owner, String annotationFqn) {
        put(owner, annotationFqn, ensure(owner, annotationFqn));
    }

    /** Add a plain method (a second, independent owner for cross-view checks). */
    public static void method(CtClass owner, String source) throws Exception {
        owner.addMethod(javassist.CtNewMethod.make(source, owner));
    }

    public static org.markline.model.JApiMethod methodNamed(JApiClass c, String name) {
        for (org.markline.model.JApiMethod m : c.getMethods()) {
            if (m.getName().equals(name)) {
                return m;
            }
        }
        return null;
    }

    /** Attach (or extend) an annotation with an int member. */
    public static void intMember(CtClass owner, String annotationFqn, String member, int value) {
        ConstPool cp = owner.getClassFile().getConstPool();
        Annotation a = ensure(owner, annotationFqn);
        a.addMemberValue(member, new IntegerMemberValue(cp, value));
        put(owner, annotationFqn, a);
    }

    /** Attach (or extend) an annotation with a String member. */
    public static void stringMember(CtClass owner, String annotationFqn, String member, String value) {
        ConstPool cp = owner.getClassFile().getConstPool();
        Annotation a = ensure(owner, annotationFqn);
        a.addMemberValue(member, new StringMemberValue(value, cp));
        put(owner, annotationFqn, a);
    }

    /** Attach (or extend) an annotation with a boolean member. */
    public static void boolMember(CtClass owner, String annotationFqn, String member, boolean value) {
        ConstPool cp = owner.getClassFile().getConstPool();
        Annotation a = ensure(owner, annotationFqn);
        a.addMemberValue(member, new BooleanMemberValue(value, cp));
        put(owner, annotationFqn, a);
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

    public static JApiAnnotationElement elementNamed(JApiAnnotation a, String name) {
        for (JApiAnnotationElement e : a.getElements()) {
            if (name.equals(e.getName())) {
                return e;
            }
        }
        return null;
    }

    public static int elementCount(JApiAnnotation a) {
        return a.getElements().size();
    }
}
