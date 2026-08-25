package fixtures;

import java.util.Arrays;
import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.bytecode.AnnotationsAttribute;
import javassist.bytecode.ConstPool;
import javassist.bytecode.FieldInfo;
import javassist.bytecode.annotation.Annotation;
import javassist.bytecode.annotation.IntegerMemberValue;
import javassist.bytecode.annotation.StringMemberValue;

import org.markline.cmp.JarArchiveComparator;
import org.markline.cmp.JarArchiveComparatorOptions;
import org.markline.model.JApiAnnotation;
import org.markline.model.JApiAnnotationElement;
import org.markline.model.JApiClass;
import org.markline.model.JApiField;

/** Fixtures for the field-annotation oracle: synthesise fields carrying runtime-visible annotations. */
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

    /** A field with no annotations. */
    public static void plainField(CtClass owner, String source) throws Exception {
        owner.addField(CtField.make(source, owner));
    }

    private static AnnotationsAttribute attr(FieldInfo fi) {
        AnnotationsAttribute a = (AnnotationsAttribute) fi.getAttribute(AnnotationsAttribute.visibleTag);
        if (a == null) {
            a = new AnnotationsAttribute(fi.getConstPool(), AnnotationsAttribute.visibleTag);
        }
        return a;
    }

    /** A field carrying a marker annotation (no members). */
    public static void markerField(CtClass owner, String source, String annotationFqn) throws Exception {
        CtField f = CtField.make(source, owner);
        FieldInfo fi = f.getFieldInfo();
        AnnotationsAttribute a = attr(fi);
        a.addAnnotation(new Annotation(annotationFqn, fi.getConstPool()));
        fi.addAttribute(a);
        owner.addField(f);
    }

    /** A field carrying an annotation with a single int member. */
    public static void intAnnoField(CtClass owner, String source, String annotationFqn, String member, int value) throws Exception {
        CtField f = CtField.make(source, owner);
        FieldInfo fi = f.getFieldInfo();
        ConstPool cp = fi.getConstPool();
        AnnotationsAttribute a = attr(fi);
        Annotation an = new Annotation(annotationFqn, cp);
        an.addMemberValue(member, new IntegerMemberValue(cp, value));
        a.addAnnotation(an);
        fi.addAttribute(a);
        owner.addField(f);
    }

    /** A field carrying an annotation with a single String member. */
    public static void stringAnnoField(CtClass owner, String source, String annotationFqn, String member, String value) throws Exception {
        CtField f = CtField.make(source, owner);
        FieldInfo fi = f.getFieldInfo();
        ConstPool cp = fi.getConstPool();
        AnnotationsAttribute a = attr(fi);
        Annotation an = new Annotation(annotationFqn, cp);
        an.addMemberValue(member, new StringMemberValue(value, cp));
        a.addAnnotation(an);
        fi.addAttribute(a);
        owner.addField(f);
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

    public static JApiField fieldNamed(JApiClass c, String name) {
        for (JApiField f : c.getFields()) {
            if (f.getName().equals(name)) {
                return f;
            }
        }
        return null;
    }

    public static JApiAnnotation annoOnField(JApiField f, String fqn) {
        for (JApiAnnotation a : f.getAnnotations()) {
            if (a.getFullyQualifiedName().equals(fqn)) {
                return a;
            }
        }
        return null;
    }

    public static int annoCountOnField(JApiField f) {
        return f.getAnnotations().size();
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
