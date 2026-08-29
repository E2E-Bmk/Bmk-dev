package integration;

import java.io.IOException;
import java.io.Serializable;

import org.jboss.forge.roaster.Roaster;
import org.jboss.forge.roaster.model.JavaUnit;
import org.jboss.forge.roaster.model.Visibility;
import org.jboss.forge.roaster.model.source.AnnotationElementSource;
import org.jboss.forge.roaster.model.source.AnnotationSource;
import org.jboss.forge.roaster.model.source.EnumConstantSource;
import org.jboss.forge.roaster.model.source.FieldSource;
import org.jboss.forge.roaster.model.source.Import;
import org.jboss.forge.roaster.model.source.InitializerSource;
import org.jboss.forge.roaster.model.source.JavaAnnotationSource;
import org.jboss.forge.roaster.model.source.JavaClassSource;
import org.jboss.forge.roaster.model.source.JavaEnumSource;
import org.jboss.forge.roaster.model.source.JavaRecordComponentSource;
import org.jboss.forge.roaster.model.source.JavaRecordSource;
import org.jboss.forge.roaster.model.source.MethodSource;
import org.jboss.forge.roaster.model.source.ParameterSource;
import org.jboss.forge.roaster.model.source.PropertySource;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GeneratedIntegrationOracleTest {

    /**
     * Verifies: ROASTER-TYPE-019, ROASTER-CVI-001.
     * Depends-On: fieldMutatorsExposeCompleteState, declarationKindPredicatesAreExclusive
     * Seam: state consistency between the public visibility helper and its field target.
     */
    @Test
    void visibilityHelperMutatesPublicTarget() {
        FieldSource<JavaClassSource> field = Roaster.create(JavaClassSource.class)
                .setName("VisibilityHost").addField().setName("token").setType(String.class);
        Visibility.set(field, Visibility.PROTECTED);
        assertAll(() -> assertTrue(field.isProtected()),
                () -> assertEquals(Visibility.PROTECTED, Visibility.getFrom(field)),
                () -> assertTrue(field.getOrigin().getField("token").isProtected()));
    }

    /**
     * Verifies: ROASTER-IMP-013, ROASTER-TYPE-013, ROASTER-TYPE-014, ROASTER-CVI-003.
     * Depends-On: directImportWinsSimpleNameResolution, fieldMutatorsExposeCompleteState
     * Seam: protocol handoff from a Class type carrier through field and import projections.
     */
    @Test
    void fieldTypeSetterAddsRequiredImport() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("TypedFieldHost");
        FieldSource<JavaClassSource> field = source.addField().setName("instant")
                .setType(java.time.Instant.class);
        assertAll(() -> assertTrue(source.hasImport(java.time.Instant.class)),
                () -> assertEquals("java.time.Instant", field.getType().getQualifiedName()),
                () -> assertEquals("Instant", field.getType().getSimpleName()));
    }

    /**
     * Verifies: ROASTER-MEM-001, ROASTER-CVI-005.
     * Depends-On: fieldMutatorsExposeCompleteState, absentLookupsAndRemovalsAreStable
     * Seam: state consistency between field lookup, specialized collection, and aggregate members.
     */
    @Test
    void addedFieldAppearsInAllOwnerViews() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("FieldHost");
        FieldSource<JavaClassSource> field = source.addField().setName("count").setType(int.class);
        assertAll(() -> assertEquals("count", source.getField("count").getName()),
                () -> assertTrue(source.hasField("count")),
                () -> assertTrue(source.getFields().contains(field)),
                () -> assertTrue(source.getMembers().contains(field)));
    }

    /**
     * Verifies: ROASTER-MEM-014, ROASTER-MEM-015, ROASTER-CVI-006.
     * Depends-On: duplicatePropertyComponentsAreRejected, methodLookupDistinguishesOverloads
     * Seam: state consistency across a property and its field, accessor, and mutator projections.
     */
    @Test
    void propertyCreatesCoordinatedComponents() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("PropertyHost");
        PropertySource<JavaClassSource> property = source.addProperty(String.class, "label");
        assertAll(() -> assertNotNull(source.getProperty("label")),
                () -> assertTrue(source.hasProperty("label")), () -> assertTrue(property.hasField()),
                () -> assertTrue(property.isAccessible()), () -> assertNotNull(property.getAccessor()),
                () -> assertTrue(property.isMutable()), () -> assertNotNull(property.getMutator()));
    }

    /**
     * Verifies: ROASTER-MEM-007, ROASTER-IMP-003, ROASTER-IMP-011, ROASTER-CVI-003.
     * Depends-On: methodStateTracksConstructorAndNativeRules, importLifecycleIsIdempotent
     * Seam: protocol handoff from method throws mutation to owner imports and type resolution.
     */
    @Test
    void thrownExceptionLifecycleUsesPublicTypeViews() {
        MethodSource<JavaClassSource> method = Roaster.create(JavaClassSource.class)
                .setName("ThrowsHost").addMethod().setName("load").setReturnTypeVoid();
        method.addThrows(IOException.class);
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class,
                method.getOrigin().toUnformattedString());
        assertAll(() -> assertTrue(method.getOrigin().hasImport(IOException.class)),
                () -> assertTrue(method.getOrigin().toUnformattedString().contains("throws IOException")),
                () -> assertNotNull(reparsed.getMethod("load")),
                () -> assertTrue(reparsed.toUnformattedString().contains("throws IOException")));
    }

    /**
     * Verifies: ROASTER-CVI-001, ROASTER-MEM-001, ROASTER-TYPE-016.
     * Depends-On: fieldMutatorsExposeCompleteState, absentLookupsAndRemovalsAreStable
     * Seam: state consistency between child mutation, owner lookup, and source projection.
     */
    @Test
    void fieldChildMutationUpdatesOwnerAndSource() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("FieldMutationHost");
        FieldSource<JavaClassSource> field = owner.addField().setName("before").setType(int.class);
        field.setName("after").setType(long.class).setPrivate();
        assertAll(() -> assertNull(owner.getField("before")),
                () -> assertEquals("after", owner.getField("after").getName()),
                () -> assertEquals("long", owner.getField("after").getType().getName()),
                () -> assertTrue(owner.toUnformattedString().contains("after")));
    }

    /**
     * Verifies: ROASTER-CVI-001, ROASTER-MEM-010, ROASTER-MEM-011.
     * Depends-On: methodLookupDistinguishesOverloads, parameterStatePreservesOrderAndFlags
     * Seam: state consistency between parameter child state and method signature views.
     */
    @Test
    void parameterChildMutationUpdatesMethodViews() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("ParameterMutationHost");
        MethodSource<JavaClassSource> method = owner.addMethod().setName("combine").setReturnTypeVoid();
        ParameterSource<JavaClassSource> parameter = method.addParameter(String.class, "left");
        parameter.setFinal(true).setVarArgs(true);
        assertAll(() -> assertEquals("left", method.getParameters().get(0).getName()),
                () -> assertTrue(method.getParameters().get(0).isFinal()),
                () -> assertTrue(method.getParameters().get(0).isVarArgs()),
                () -> assertTrue(method.toSignature().contains("combine")),
                () -> assertTrue(owner.toUnformattedString().contains("left")));
    }

    /**
     * Verifies: ROASTER-CVI-002, ROASTER-TYPE-017.
     * Depends-On: packageAndNameDefineTypeIdentity, fieldMutatorsExposeCompleteState
     * Seam: protocol handoff from mutable source rendering to typed parsing.
     */
    @Test
    void renderedFieldModelReparsesSemantically() {
        JavaClassSource original = Roaster.create(JavaClassSource.class)
                .setPackage("sample.roundtrip").setName("FieldRoundTrip");
        original.addField().setName("enabled").setType(boolean.class).setPrivate();
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, original.toString());
        assertAll(() -> assertEquals(original.getQualifiedName(), reparsed.getQualifiedName()),
                () -> assertTrue(reparsed.hasField("enabled")),
                () -> assertTrue(reparsed.getField("enabled").isPrivate()),
                () -> assertEquals("boolean", reparsed.getField("enabled").getType().getName()));
    }

    /**
     * Verifies: ROASTER-CVI-002, ROASTER-WF-001, ROASTER-MEM-005.
     * Depends-On: methodLookupDistinguishesOverloads, methodStateTracksConstructorAndNativeRules
     * Seam: protocol handoff from method mutation to reparsed signature lookup.
     */
    @Test
    void renderedMethodModelReparsesSemantically() {
        JavaClassSource original = Roaster.create(JavaClassSource.class)
                .setPackage("sample.methods").setName("MethodRoundTrip");
        original.addMethod().setName("measure").setReturnType(long.class)
                .setBody("return input.length();").addParameter(String.class, "input");
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, original.toString());
        assertAll(() -> assertEquals(original.getPackage(), reparsed.getPackage()),
                () -> assertEquals(original.getName(), reparsed.getName()),
                () -> assertNotNull(reparsed.getMethod("measure", String.class)),
                () -> assertEquals("long",
                        reparsed.getMethod("measure", String.class).getReturnType().getName()),
                () -> assertEquals("input",
                        reparsed.getMethod("measure", String.class).getParameters().get(0).getName()),
                () -> assertTrue(reparsed.getMethod("measure", String.class).getBody().contains("input.length")));
    }

    /**
     * Verifies: ROASTER-CVI-003, ROASTER-IMP-013, ROASTER-TYPE-014.
     * Depends-On: fieldMutatorsExposeCompleteState, directImportWinsSimpleNameResolution
     * Seam: protocol handoff across Class and qualified-string type carriers.
     */
    @Test
    void classAndQualifiedStringTypesProduceEquivalentFields() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("CarrierEquivalence");
        FieldSource<JavaClassSource> byClass = owner.addField().setName("classValue")
                .setType(java.time.Duration.class);
        FieldSource<JavaClassSource> byString = owner.addField().setName("stringValue")
                .setType("java.time.Duration");
        assertAll(() -> assertEquals(byClass.getType().getQualifiedName(),
                        byString.getType().getQualifiedName()),
                () -> assertTrue(owner.hasImport(java.time.Duration.class)));
    }

    /**
     * Verifies: ROASTER-CVI-003, ROASTER-IMP-013, ROASTER-TYPE-014.
     * Depends-On: directImportWinsSimpleNameResolution, parameterStatePreservesOrderAndFlags
     * Seam: protocol handoff from a public Type view into a parameter mutator.
     */
    @Test
    void publicTypeViewTransfersAcrossMemberKinds() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("TypeTransferHost");
        JavaClassSource transferredType = Roaster.create(JavaClassSource.class)
                .setPackage("sample.transfer").setName("TransferredSignal");
        FieldSource<JavaClassSource> field = owner.addField().setName("source")
                .setType(transferredType);
        MethodSource<JavaClassSource> method = owner.addMethod().setName("accept").setReturnTypeVoid();
        ParameterSource<JavaClassSource> parameter = method.addParameter(transferredType, "value");
        assertAll(() -> assertEquals(field.getType().getQualifiedName(),
                        parameter.getType().getQualifiedName()),
                () -> assertTrue(owner.hasImport("sample.transfer.TransferredSignal")));
    }

    /**
     * Verifies: ROASTER-CVI-004, ROASTER-IMP-001, ROASTER-IMP-003, ROASTER-IMP-006.
     * Depends-On: importLifecycleIsIdempotent, directImportWinsSimpleNameResolution
     * Seam: state consistency across import mutation and all import query projections.
     */
    @Test
    void addingImportSynchronizesQueriesAndResolution() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class)
                .setPackage("sample.imports").setName("ImportAgreement");
        Import added = owner.addImport("sample.foreign.Signal");
        assertAll(() -> assertEquals(added.getQualifiedName(),
                        owner.getImport("sample.foreign.Signal").getQualifiedName()),
                () -> assertTrue(owner.hasImport("sample.foreign.Signal")),
                () -> assertFalse(owner.requiresImport("sample.foreign.Signal")),
                () -> assertEquals("sample.foreign.Signal", owner.resolveType("Signal")),
                () -> assertTrue(owner.toUnformattedString().contains("Signal")));
    }

    /**
     * Verifies: ROASTER-CVI-004, ROASTER-IMP-003, ROASTER-IMP-004, ROASTER-IMP-006.
     * Depends-On: importLifecycleIsIdempotent, nonImportableReferencesLeaveImportsUnchanged
     * Seam: state consistency across import removal and resolution fallback.
     */
    @Test
    void removingImportSynchronizesQueriesAndResolution() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class)
                .setPackage("sample.fallback").setName("ImportRemoval");
        Import added = owner.addImport("sample.foreign.Signal");
        owner.removeImport(added);
        assertAll(() -> assertFalse(owner.hasImport("sample.foreign.Signal")),
                () -> assertNull(owner.getImport("sample.foreign.Signal")),
                () -> assertTrue(owner.requiresImport("sample.foreign.Signal")),
                () -> assertEquals("sample.fallback.Signal", owner.resolveType("Signal")));
    }

    /**
     * Verifies: ROASTER-CVI-005, ROASTER-MEM-001, ROASTER-MEM-003.
     * Depends-On: fieldMutatorsExposeCompleteState, absentLookupsAndRemovalsAreStable
     * Seam: state consistency between specialized and aggregate field collections.
     */
    @Test
    void fieldCollectionAndAggregateMembersStayAligned() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("FieldCollections");
        FieldSource<JavaClassSource> first = owner.addField().setName("first").setType(int.class);
        FieldSource<JavaClassSource> second = owner.addField().setName("second").setType(long.class);
        assertAll(() -> assertTrue(owner.getFields().contains(first)),
                () -> assertTrue(owner.getFields().contains(second)),
                () -> assertTrue(owner.getMembers().contains(first)),
                () -> assertTrue(owner.getMembers().contains(second)));
    }

    /**
     * Verifies: ROASTER-CVI-005, ROASTER-MEM-004, ROASTER-MEM-006.
     * Depends-On: methodLookupDistinguishesOverloads, methodStateTracksConstructorAndNativeRules
     * Seam: state consistency between specialized and aggregate method collections.
     */
    @Test
    void methodCollectionAndAggregateMembersStayAligned() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("MethodCollections");
        MethodSource<JavaClassSource> first = owner.addMethod().setName("first").setReturnTypeVoid();
        MethodSource<JavaClassSource> second = owner.addMethod().setName("second").setReturnType(int.class);
        assertAll(() -> assertTrue(owner.getMethods().contains(first)),
                () -> assertTrue(owner.getMethods().contains(second)),
                () -> assertTrue(owner.getMembers().contains(first)),
                () -> assertTrue(owner.getMembers().contains(second)));
    }

    /**
     * Verifies: ROASTER-CVI-006, ROASTER-MEM-015, ROASTER-MEM-016.
     * Depends-On: duplicatePropertyComponentsAreRejected, methodLookupDistinguishesOverloads
     * Seam: config interaction between property accessibility and owner method views.
     */
    @Test
    void propertyAccessibilityControlsOwnerAccessorView() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("AccessiblePropertyHost");
        PropertySource<JavaClassSource> property = owner.addProperty(String.class, "title");
        String accessorName = property.getAccessor().getName();
        property.setAccessible(false);
        assertAll(() -> assertFalse(property.isAccessible()),
                () -> assertNull(property.getAccessor()), () -> assertNull(owner.getMethod(accessorName)));
        property.setAccessible(true);
        assertAll(() -> assertTrue(property.isAccessible()),
                () -> assertNotNull(property.getAccessor()),
                () -> assertNotNull(owner.getMethod(property.getAccessor().getName())));
    }

    /**
     * Verifies: ROASTER-CVI-006, ROASTER-MEM-015, ROASTER-MEM-016.
     * Depends-On: duplicatePropertyComponentsAreRejected, methodLookupDistinguishesOverloads
     * Seam: config interaction between property mutability and owner method views.
     */
    @Test
    void propertyMutabilityControlsOwnerMutatorView() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("MutablePropertyHost");
        PropertySource<JavaClassSource> property = owner.addProperty(String.class, "title");
        String mutatorName = property.getMutator().getName();
        property.setMutable(false);
        assertAll(() -> assertFalse(property.isMutable()),
                () -> assertNull(property.getMutator()),
                () -> assertNull(owner.getMethod(mutatorName, String.class)));
        property.setMutable(true);
        assertAll(() -> assertTrue(property.isMutable()),
                () -> assertNotNull(property.getMutator()),
                () -> assertNotNull(owner.getMethod(property.getMutator().getName(), String.class)));
    }

    /**
     * Verifies: ROASTER-CVI-007, ROASTER-ANN-001, ROASTER-CVI-002.
     * Depends-On: annotationLifecycleUpdatesTargetView, annotationValuesDriveFormPredicates
     * Seam: protocol handoff from annotation child mutation through rendering and reparsing.
     */
    @Test
    void annotationMutationSurvivesReparse() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("AnnotationRoundTrip");
        owner.addAnnotation("sample.meta.Signal").setStringValue("mode", "steady");
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, owner.toString());
        AnnotationSource<JavaClassSource> annotation = reparsed.getAnnotation("Signal");
        assertAll(() -> assertNotNull(annotation),
                () -> assertEquals("steady", annotation.getStringValue("mode")),
                () -> assertTrue(reparsed.hasImport("sample.meta.Signal")));
    }

    /**
     * Verifies: ROASTER-CVI-007, ROASTER-ANN-007, ROASTER-ANN-009, ROASTER-CVI-002.
     * Depends-On: javaDocTextAndTagsRemainDistinct, methodStateTracksConstructorAndNativeRules
     * Seam: protocol handoff from documentation child mutation through reparsing.
     */
    @Test
    void javaDocMutationSurvivesReparse() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("DocRoundTrip");
        MethodSource<JavaClassSource> method = owner.addMethod().setName("signal").setReturnTypeVoid();
        method.getJavaDoc().setText("Emits a signal.").addTagValue("@since", "21");
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, owner.toString());
        assertAll(() -> assertEquals("Emits a signal.",
                        reparsed.getMethod("signal").getJavaDoc().getText()),
                () -> assertEquals("21",
                        reparsed.getMethod("signal").getJavaDoc()
                                .getTags("@since").get(0).getValue()));
    }

    /**
     * Verifies: ROASTER-CVI-008, ROASTER-FAC-007, ROASTER-FAC-008.
     * Depends-On: compilationUnitPreservesOrderAndIsImmutable, packageAndNameDefineTypeIdentity
     * Seam: state consistency between governing and ordered top-level unit views.
     */
    @Test
    void unitViewsSharePackageAndDeclarationOrder() {
        JavaUnit unit = Roaster.parseUnit(
                "package sample.shared; public class Primary {} interface Secondary {} enum Tertiary { ONE }");
        assertAll(() -> assertEquals("sample.shared", unit.getGoverningType().getPackage()),
                () -> assertEquals("Primary", unit.getTopLevelTypes().get(0).getName()),
                () -> assertEquals("Secondary", unit.getTopLevelTypes().get(1).getName()),
                () -> assertEquals("Tertiary", unit.getTopLevelTypes().get(2).getName()));
    }

    /**
     * Verifies: ROASTER-CVI-008, ROASTER-TYPE-002, ROASTER-TYPE-016.
     * Depends-On: compilationUnitPreservesOrderAndIsImmutable, packageAndNameDefineTypeIdentity
     * Seam: state consistency between governing mutation and complete unit rendering.
     */
    @Test
    void governingMutationUpdatesCompleteUnitRendering() {
        JavaUnit unit = Roaster.parseUnit("package sample.unitmut; public class Original {} class Companion {}");
        JavaClassSource governing = (JavaClassSource) unit.getGoverningType();
        governing.setName("Renamed");
        JavaUnit reparsed = Roaster.parseUnit(unit.toUnformattedString());
        assertAll(() -> assertEquals("Renamed", reparsed.getGoverningType().getName()),
                () -> assertEquals("Companion", reparsed.getTopLevelTypes().get(1).getName()));
    }

    /**
     * Verifies: ROASTER-CVI-009, ROASTER-TYPE-006, ROASTER-TYPE-008.
     * Depends-On: topLevelTypeEnclosesItself, declarationKindPredicatesAreExclusive
     * Seam: state consistency between nested child ownership and parent rendering.
     */
    @Test
    void nestedTypeOwnershipAndMutationStayLinked() {
        JavaClassSource parent = Roaster.create(JavaClassSource.class).setName("NestedParent");
        JavaClassSource nested = parent.addNestedType(JavaClassSource.class).setName("NestedChild");
        nested.addField().setName("value").setType(int.class);
        assertAll(() -> assertEquals("NestedParent", nested.getEnclosingType().getName()),
                () -> assertEquals("NestedChild", nested.getOrigin().getName()),
                () -> assertEquals("NestedChild", parent.getNestedType("NestedChild").getName()),
                () -> assertTrue(parent.toUnformattedString().contains("value")));
    }

    /**
     * Verifies: ROASTER-CVI-009, ROASTER-TYPE-007, ROASTER-TYPE-009.
     * Depends-On: topLevelTypeEnclosesItself, absentLookupsAndRemovalsAreStable
     * Seam: lifecycle crossing from nested creation through parent-side removal.
     */
    @Test
    void nestedTypeRemovalUpdatesParentAndReparse() {
        JavaClassSource parent = Roaster.create(JavaClassSource.class).setName("NestedRemovalParent");
        JavaClassSource nested = parent.addNestedType(JavaClassSource.class).setName("DisposableChild");
        parent.removeNestedType(nested);
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, parent.toString());
        assertAll(() -> assertNull(parent.getNestedType("DisposableChild")),
                () -> assertTrue(parent.getNestedTypes().isEmpty()),
                () -> assertNull(reparsed.getNestedType("DisposableChild")));
    }

    /**
     * Verifies: ROASTER-CVI-010, ROASTER-ANN-017, ROASTER-CVI-002.
     * Depends-On: recordComponentLifecyclePreservesOrderAndType, directImportWinsSimpleNameResolution
     * Seam: protocol handoff from record-component mutation through specialized reparsing.
     */
    @Test
    void recordComponentMutationSurvivesReparse() {
        JavaRecordSource record = Roaster.create(JavaRecordSource.class).setName("RecordRoundTrip");
        JavaRecordComponentSource component = record.addRecordComponent(java.time.Instant.class, "created");
        component.setVarArgs(true);
        JavaRecordSource reparsed = Roaster.parse(JavaRecordSource.class, record.toString());
        assertAll(() -> assertEquals("created", reparsed.getRecordComponents().get(0).getName()),
                () -> assertEquals("java.time.Instant",
                        reparsed.getRecordComponents().get(0).getType().getQualifiedName()),
                () -> assertTrue(reparsed.getRecordComponents().get(0).isVarArgs()));
    }

    /**
     * Verifies: ROASTER-CVI-010, ROASTER-ANN-011, ROASTER-ANN-012, ROASTER-CVI-002.
     * Depends-On: enumConstantLifecycleExposesBody, annotationLifecycleUpdatesTargetView
     * Seam: protocol handoff from enum-constant child views through rendering and reparsing.
     */
    @Test
    void enumConstantMutationSurvivesReparse() {
        JavaEnumSource enumeration = Roaster.create(JavaEnumSource.class).setName("EnumRoundTrip");
        EnumConstantSource constant = enumeration.addEnumConstant().setName("ACTIVE");
        constant.addAnnotation(Deprecated.class);
        constant.getJavaDoc().setText("Active state.");
        JavaEnumSource reparsed = Roaster.parse(JavaEnumSource.class, enumeration.toString());
        EnumConstantSource reparsedConstant = reparsed.getEnumConstant("ACTIVE");
        assertAll(() -> assertNotNull(reparsedConstant),
                () -> assertTrue(reparsedConstant.hasAnnotation(Deprecated.class)),
                () -> assertEquals("Active state.", reparsedConstant.getJavaDoc().getText()));
    }

    /**
     * Verifies: ROASTER-CVI-010, ROASTER-ANN-014, ROASTER-ANN-015, ROASTER-CVI-002.
     * Depends-On: annotationElementLifecyclePreservesTypeAndDefault, annotationLifecycleUpdatesTargetView
     * Seam: protocol handoff from annotation-element child views through reparsing.
     */
    @Test
    void annotationElementMutationSurvivesReparse() {
        JavaAnnotationSource annotation = Roaster.create(JavaAnnotationSource.class).setName("ElementRoundTrip");
        AnnotationElementSource element = annotation.addAnnotationElement(
                "long window() default 29L");
        element.addAnnotation(Deprecated.class);
        JavaAnnotationSource reparsed = Roaster.parse(JavaAnnotationSource.class, annotation.toString());
        AnnotationElementSource reparsedElement = reparsed.getAnnotationElement("window");
        assertAll(() -> assertEquals("long", reparsedElement.getType().getName()),
                () -> assertTrue(reparsed.toUnformattedString().contains("default 29L")),
                () -> assertTrue(reparsedElement.hasAnnotation(Deprecated.class)));
    }

    /**
     * Verifies: ROASTER-CVI-001, ROASTER-CVI-002.
     * Depends-On: packageAndNameDefineTypeIdentity, fieldMutatorsExposeCompleteState, parameterStatePreservesOrderAndFlags
     * Seam: protocol handoff across create, child mutation, rendering, and typed reparsing.
     */
    @Test
    void createEnrichRenderAndReparseWorkflowAgrees() {
        JavaClassSource source = Roaster.create(JavaClassSource.class)
                .setPackage("sample.workflow").setName("Envelope").addInterface(Serializable.class);
        source.addField().setName("id").setType(Long.class).setPrivate().setFinal(true);
        source.addMethod().setConstructor(true).setPublic().setBody("this.id = id;")
                .addParameter(Long.class, "id");
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, source.toString());
        assertAll(() -> assertEquals("sample.workflow.Envelope", reparsed.getQualifiedName()),
                () -> assertTrue(reparsed.getField("id").isFinal()),
                () -> assertNotNull(reparsed.getMethod("Envelope", Long.class)));
    }

    /**
     * Verifies: ROASTER-WF-001, ROASTER-CVI-002, ROASTER-CVI-005.
     * Depends-On: parsesStringCarrier, methodLookupDistinguishesOverloads, methodStateTracksConstructorAndNativeRules
     * Seam: lifecycle crossing from parse through mutation and semantic reparse.
     */
    @Test
    void parseModifyRenderAndReparseWorkflowAgrees() {
        JavaClassSource parsed = Roaster.parse(JavaClassSource.class,
                "package sample.flow; public class Greeting {}");
        parsed.addMethod().setPublic().setName("message").setReturnType(String.class)
                .setBody("return \"welcome\";");
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, parsed.toString());
        assertAll(() -> assertEquals("sample.flow.Greeting", reparsed.getQualifiedName()),
                () -> assertTrue(reparsed.hasMethodSignature("message")),
                () -> assertEquals("java.lang.String", reparsed.getMethod("message").getReturnType().getQualifiedName()),
                () -> assertTrue(reparsed.getMethod("message").getBody().contains("welcome")),
                () -> assertTrue(reparsed.getMembers().contains(reparsed.getMethod("message"))));
    }

    /**
     * Verifies: ROASTER-WF-002, ROASTER-CVI-008, ROASTER-FAC-008.
     * Depends-On: compilationUnitPreservesOrderAndIsImmutable, packageAndNameDefineTypeIdentity
     * Seam: protocol handoff between complete-unit rendering and ordered unit parsing.
     */
    @Test
    void completeCompilationUnitWorkflowRetainsAllTypes() {
        JavaUnit first = Roaster.parseUnit(
                "package sample.complete; public class Alpha {} interface Beta {} record Gamma(int code) {}");
        JavaUnit second = Roaster.parseUnit(first.toUnformattedString());
        assertAll(() -> assertEquals("Alpha", second.getGoverningType().getName()),
                () -> assertEquals(3, second.getTopLevelTypes().size()),
                () -> assertTrue(second.getTopLevelTypes().get(1).isInterface()),
                () -> assertTrue(second.getTopLevelTypes().get(2).isRecord()));
    }

    /**
     * Verifies: ROASTER-CVI-001, ROASTER-CVI-002, ROASTER-MEM-012, ROASTER-MEM-013.
     * Depends-On: initializerBodyAndStaticStateAreObservable, parsesStringCarrier
     * Seam: lifecycle crossing from initializer child mutation through source reparsing.
     */
    @Test
    void initializerMutationSurvivesOwnerReparse() {
        JavaClassSource owner = Roaster.create(JavaClassSource.class).setName("InitializerRoundTrip");
        InitializerSource<JavaClassSource> initializer = owner.addInitializer().setBody("int seed = 31;");
        initializer.setStatic(true);
        JavaClassSource reparsed = Roaster.parse(JavaClassSource.class, owner.toString());
        assertAll(() -> assertEquals(1, reparsed.getInitializers().size()),
                () -> assertTrue(reparsed.getInitializers().get(0).isStatic()),
                () -> assertTrue(reparsed.getInitializers().get(0).getBody().contains("seed")));
    }
}
