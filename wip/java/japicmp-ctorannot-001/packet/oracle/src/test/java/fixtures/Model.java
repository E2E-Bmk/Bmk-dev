package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtConstructor;
import javassist.bytecode.AnnotationsAttribute;
import javassist.bytecode.ConstPool;
import javassist.bytecode.MethodInfo;
import javassist.bytecode.annotation.Annotation;
import javassist.bytecode.annotation.IntegerMemberValue;
import javassist.bytecode.annotation.StringMemberValue;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiAnnotation;
import org.markline.model.JApiAnnotationElement;
import org.markline.model.JApiClass;
import org.markline.model.JApiConstructor;

/** Fixtures for the constructor-annotation oracle: synthesise constructors carrying runtime-visible annotations. */
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

    /** Parameter types for a constructor of the given arity: int parameters, so arity distinguishes signatures. */
    private static CtClass[] params(CtClass owner, int arity) throws Exception {
        CtClass[] p = new CtClass[arity];
        for (int i = 0; i < arity; i++) {
            p[i] = CtClass.intType;
        }
        return p;
    }

    private static CtConstructor make(CtClass owner, int arity) throws Exception {
        CtConstructor ctor = new CtConstructor(params(owner, arity), owner);
        ctor.setBody("{}");
        return ctor;
    }

    private static AnnotationsAttribute attr(MethodInfo mi) {
        AnnotationsAttribute a = (AnnotationsAttribute) mi.getAttribute(AnnotationsAttribute.visibleTag);
        if (a == null) {
            a = new AnnotationsAttribute(mi.getConstPool(), AnnotationsAttribute.visibleTag);
        }
        return a;
    }

    /** A constructor of the given arity with no annotations. */
    public static void plainCtor(CtClass owner, int arity) throws Exception {
        owner.addConstructor(make(owner, arity));
    }

    /** A constructor carrying a marker annotation (no members). */
    public static void markerCtor(CtClass owner, int arity, String annotationFqn) throws Exception {
        CtConstructor ctor = make(owner, arity);
        MethodInfo mi = ctor.getMethodInfo();
        AnnotationsAttribute a = attr(mi);
        a.addAnnotation(new Annotation(annotationFqn, mi.getConstPool()));
        mi.addAttribute(a);
        owner.addConstructor(ctor);
    }

    /** A constructor carrying an annotation with a single int member. */
    public static void intAnnoCtor(CtClass owner, int arity, String annotationFqn, String member, int value) throws Exception {
        CtConstructor ctor = make(owner, arity);
        MethodInfo mi = ctor.getMethodInfo();
        ConstPool cp = mi.getConstPool();
        AnnotationsAttribute a = attr(mi);
        Annotation an = new Annotation(annotationFqn, cp);
        an.addMemberValue(member, new IntegerMemberValue(cp, value));
        a.addAnnotation(an);
        mi.addAttribute(a);
        owner.addConstructor(ctor);
    }

    /** A constructor carrying an annotation with a single String member. */
    public static void stringAnnoCtor(CtClass owner, int arity, String annotationFqn, String member, String value) throws Exception {
        CtConstructor ctor = make(owner, arity);
        MethodInfo mi = ctor.getMethodInfo();
        ConstPool cp = mi.getConstPool();
        AnnotationsAttribute a = attr(mi);
        Annotation an = new Annotation(annotationFqn, cp);
        an.addMemberValue(member, new StringMemberValue(value, cp));
        a.addAnnotation(an);
        mi.addAttribute(a);
        owner.addConstructor(ctor);
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

    /** The constructor record whose parameter count equals the given arity, on whichever side carries it. */
    public static JApiConstructor ctorOfArity(JApiClass c, int arity) throws Exception {
        for (JApiConstructor ctor : c.getConstructors()) {
            if (arityOf(ctor) == arity) {
                return ctor;
            }
        }
        return null;
    }

    private static int arityOf(JApiConstructor ctor) throws Exception {
        if (ctor.getNewConstructor().isPresent()) {
            return ctor.getNewConstructor().get().getParameterTypes().length;
        }
        if (ctor.getOldConstructor().isPresent()) {
            return ctor.getOldConstructor().get().getParameterTypes().length;
        }
        return -1;
    }

    public static int ctorCount(JApiClass c) {
        return c.getConstructors().size();
    }

    public static JApiAnnotation annoOnCtor(JApiConstructor ctor, String fqn) {
        for (JApiAnnotation a : ctor.getAnnotations()) {
            if (a.getFullyQualifiedName().equals(fqn)) {
                return a;
            }
        }
        return null;
    }

    public static int annoCountOnCtor(JApiConstructor ctor) {
        return ctor.getAnnotations().size();
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
