package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtMethod;
import javassist.CtNewMethod;
import javassist.bytecode.AnnotationsAttribute;
import javassist.bytecode.ConstPool;
import javassist.bytecode.MethodInfo;
import javassist.bytecode.annotation.Annotation;
import javassist.bytecode.annotation.ArrayMemberValue;
import javassist.bytecode.annotation.EnumMemberValue;
import javassist.bytecode.annotation.IntegerMemberValue;
import javassist.bytecode.annotation.MemberValue;
import javassist.bytecode.annotation.StringMemberValue;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiAnnotation;
import org.markline.model.JApiAnnotationElement;
import org.markline.model.JApiClass;
import org.markline.model.JApiMethod;

/** Fixtures for the member-value oracle: annotation members whose values are enum constants or arrays. */
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

    public static void plainMethod(CtClass owner, String source) throws Exception {
        owner.addMethod(CtNewMethod.make(source, owner));
    }

    private static AnnotationsAttribute attr(MethodInfo mi) {
        AnnotationsAttribute a = (AnnotationsAttribute) mi.getAttribute(AnnotationsAttribute.visibleTag);
        if (a == null) {
            a = new AnnotationsAttribute(mi.getConstPool(), AnnotationsAttribute.visibleTag);
        }
        return a;
    }

    public static void markerMethod(CtClass owner, String source, String annotationFqn) throws Exception {
        CtMethod m = CtNewMethod.make(source, owner);
        MethodInfo mi = m.getMethodInfo();
        AnnotationsAttribute a = attr(mi);
        a.addAnnotation(new Annotation(annotationFqn, mi.getConstPool()));
        mi.addAttribute(a);
        owner.addMethod(m);
    }

    /** A method carrying an annotation whose member is an enum constant. */
    public static void enumAnnoMethod(CtClass owner, String source, String annotationFqn, String member, String enumType, String constant) throws Exception {
        CtMethod m = CtNewMethod.make(source, owner);
        MethodInfo mi = m.getMethodInfo();
        ConstPool cp = mi.getConstPool();
        EnumMemberValue emv = new EnumMemberValue(cp);
        emv.setType(enumType);
        emv.setValue(constant);
        AnnotationsAttribute a = attr(mi);
        Annotation an = new Annotation(annotationFqn, cp);
        an.addMemberValue(member, emv);
        a.addAnnotation(an);
        mi.addAttribute(a);
        owner.addMethod(m);
    }

    /** A method carrying an annotation whose member is an int array with the given elements. */
    public static void arrayAnnoMethod(CtClass owner, String source, String annotationFqn, String member, int... values) throws Exception {
        CtMethod m = CtNewMethod.make(source, owner);
        MethodInfo mi = m.getMethodInfo();
        ConstPool cp = mi.getConstPool();
        MemberValue[] elems = new MemberValue[values.length];
        for (int i = 0; i < values.length; i++) {
            elems[i] = new IntegerMemberValue(cp, values[i]);
        }
        ArrayMemberValue amv = new ArrayMemberValue(cp);
        amv.setValue(elems);
        AnnotationsAttribute a = attr(mi);
        Annotation an = new Annotation(annotationFqn, cp);
        an.addMemberValue(member, amv);
        a.addAnnotation(an);
        mi.addAttribute(a);
        owner.addMethod(m);
    }

    /** A method carrying an annotation with a single String member. */
    public static void stringAnnoMethod(CtClass owner, String source, String annotationFqn, String member, String value) throws Exception {
        CtMethod m = CtNewMethod.make(source, owner);
        MethodInfo mi = m.getMethodInfo();
        ConstPool cp = mi.getConstPool();
        AnnotationsAttribute a = attr(mi);
        Annotation an = new Annotation(annotationFqn, cp);
        an.addMemberValue(member, new StringMemberValue(value, cp));
        a.addAnnotation(an);
        mi.addAttribute(a);
        owner.addMethod(m);
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

    public static JApiMethod methodNamed(JApiClass c, String name) {
        for (JApiMethod m : c.getMethods()) {
            if (m.getName().equals(name)) {
                return m;
            }
        }
        return null;
    }

    public static JApiAnnotation annoOnMethod(JApiMethod m, String fqn) {
        for (JApiAnnotation a : m.getAnnotations()) {
            if (a.getFullyQualifiedName().equals(fqn)) {
                return a;
            }
        }
        return null;
    }

    public static int annoCountOnMethod(JApiMethod m) {
        return m.getAnnotations().size();
    }

    public static JApiAnnotationElement elementNamed(JApiAnnotation a, String name) {
        for (JApiAnnotationElement e : a.getElements()) {
            if (name.equals(e.getName())) {
                return e;
            }
        }
        return null;
    }
}
