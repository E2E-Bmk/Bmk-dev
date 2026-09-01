package fixtures;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.CtNewConstructor;
import javassist.CtNewMethod;
import javassist.Modifier;

/**
 * Synthesises the two compared class versions in memory.
 *
 * <p>The comparison takes two {@code List<CtClass>} and the spec names javassist's
 * {@code ClassPool} and {@code CtClass} in its Declared Signatures, so a fixture
 * needs no files on disk and no jars: it builds the old and new shape of a type
 * directly. That keeps every test hermetic and offline, which matters because
 * scoring runs with the network disconnected.
 *
 * <p>Each version gets its own {@link ClassPool}. A pool caches by name, so the
 * old and new {@code com.acme.Service} cannot coexist in one pool -- the second
 * {@code makeClass} would return the first one and the comparison would see two
 * identical inputs and report {@code UNCHANGED} for every test.
 */
public final class Bytecode {

    private Bytecode() {
    }

    /** A fresh pool that can also resolve JDK types, needed for method signatures. */
    public static ClassPool pool() {
        return new ClassPool(true);
    }

    /** A public class in a fresh pool. */
    public static CtClass publicClass(ClassPool pool, String name) {
        CtClass declared = pool.makeClass(name);
        declared.setModifiers(Modifier.PUBLIC);
        return declared;
    }

    /** A public interface in a fresh pool. */
    public static CtClass publicInterface(ClassPool pool, String name) {
        CtClass declared = pool.makeInterface(name);
        declared.setModifiers(Modifier.PUBLIC | Modifier.INTERFACE | Modifier.ABSTRACT);
        return declared;
    }

    /** Adds a member from Java source, e.g. {@code "public void run() {}"}. */
    public static void method(CtClass owner, String source) throws Exception {
        owner.addMethod(CtNewMethod.make(source, owner));
    }

    /** Adds a field from Java source, e.g. {@code "public int count;"}. */
    public static void field(CtClass owner, String source) throws Exception {
        owner.addField(CtField.make(source, owner));
    }

    /** Adds a constructor from Java source. */
    public static void constructor(CtClass owner, String source) throws Exception {
        owner.addConstructor(CtNewConstructor.make(source, owner));
    }

    /** Marks the class final. */
    public static void makeFinal(CtClass owner) {
        owner.setModifiers(owner.getModifiers() | Modifier.FINAL);
    }

    /** Marks the class abstract. */
    public static void makeAbstract(CtClass owner) {
        owner.setModifiers(owner.getModifiers() | Modifier.ABSTRACT);
    }

    /** Drops the class to package-private visibility. */
    public static void makePackagePrivate(CtClass owner) {
        owner.setModifiers(owner.getModifiers() & ~Modifier.PUBLIC & ~Modifier.PROTECTED & ~Modifier.PRIVATE);
    }
}
