package integration;

import static fixtures.Xml.diff;
import static fixtures.Xml.diffCount;
import static fixtures.Xml.resultOf;
import static fixtures.Xml.strictDiff;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.xmldiff.builder.DiffBuilder;
import org.xmldiff.diff.ComparisonControllers;
import org.xmldiff.diff.ComparisonResult;
import org.xmldiff.diff.ComparisonType;
import org.xmldiff.diff.Diff;
import org.xmldiff.diff.DifferenceEvaluators;
import org.junit.jupiter.api.Test;

/** Cross-owner checks over the comparison engine. */
class EngineTest {

    // Depends-On: atomic::DiffTest::aNamespacePrefixOnlyDifferenceIsReportedDifferent
    // MUTATED: F1_nsprefix
    @Test
    void aPrefixOnlyDifferenceAloneMakesTheDocumentsDiffer() {
        assertEquals(ComparisonResult.DIFFERENT, resultOf(
                "<r><a xmlns:p=\"u\"><p:b/></a></r>", "<r><a xmlns:q=\"u\"><q:b/></a></r>",
                ComparisonType.NAMESPACE_PREFIX));
    }

    // Depends-On: atomic::DiffTest::reorderedChildrenAreReportedDifferent
    // MUTATED: F2_childseq
    @Test
    void reorderedChildrenAloneMakeTheDocumentsDiffer() {
        assertEquals(ComparisonResult.DIFFERENT, fixtures.Xml.resultOfSeq(
                "<r><a><b/><c/></a></r>", "<r><a><c/><b/></a></r>", ComparisonType.CHILD_NODELIST_SEQUENCE));
    }

    // Depends-On: atomic::DiffTest::aDifferentXmlEncodingIsReportedDifferent
    // MUTATED: F3_xmlenc
    @Test
    void aDifferentEncodingAloneMakesTheDocumentsDiffer() {
        assertEquals(ComparisonResult.DIFFERENT, resultOf(
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?><a>x</a>",
                "<?xml version=\"1.0\" encoding=\"US-ASCII\"?><a>x</a>", ComparisonType.XML_ENCODING));
    }

    // Depends-On: atomic::DiffTest::aCdataVersusTextPairingIsReportedDifferent
    // MUTATED: F4_nodetype
    @Test
    void aCdataVersusTextPairingAloneMakesTheDocumentsDiffer() {
        assertEquals(ComparisonResult.DIFFERENT, resultOf(
                "<r><a><![CDATA[x]]></a></r>", "<r><a>x</a></r>", ComparisonType.NODE_TYPE));
    }

    // ---- native compositions ----
    // Depends-On: atomic::DiffTest::identicalDocumentsHaveNoDifferences
    @Test
    void identicalComplexTreesProduceNoDifferences() {
        assertFalse(strictDiff("<a k=\"1\"><b>t</b><c/></a>", "<a k=\"1\"><b>t</b><c/></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aTextValueDifferenceIsReportedDifferent
    @Test
    void aStopWhenDifferentControllerRecordsAtMostOneDifference() {
        Diff d = DiffBuilder.compare("<a><b>1</b><c>2</c></a>").withTest("<a><b>9</b><c>8</c></a>")
                .withComparisonController(ComparisonControllers.StopWhenDifferent).build();
        int diffs = 0;
        for (Object ignored : d.getDifferences()) {
            diffs++;
        }
        assertEquals(1, diffs);
    }

    // Depends-On: atomic::DiffTest::aTextValueDifferenceIsReportedDifferent
    @Test
    void aDefaultControllerRecordsEveryValueDifference() {
        Diff d = DiffBuilder.compare("<a><b>1</b><c>2</c></a>").withTest("<a><b>9</b><c>8</c></a>").build();
        int diffs = 0;
        for (Object ignored : d.getDifferences()) {
            diffs++;
        }
        assertTrue(diffs >= 2);
    }

    // Depends-On: atomic::DiffTest::aTextValueDifferenceIsReportedDifferent
    @Test
    void aCustomEvaluatorCanDowngradeATextDifferenceToEqual() {
        Diff d = DiffBuilder.compare("<a>1</a>").withTest("<a>2</a>")
                .withDifferenceEvaluator(DifferenceEvaluators.downgradeDifferencesToEqual(ComparisonType.TEXT_VALUE))
                .build();
        assertFalse(d.hasDifferences());
    }

    // Depends-On: atomic::DiffTest::anElementTagNameDifferenceIsReportedDifferent
    @Test
    void aTagNameDifferenceIsRecordedInAComplexTree() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b><x/></b></a>", "<a><b><y/></b></a>", ComparisonType.ELEMENT_TAG_NAME));
    }

    // Depends-On: atomic::DiffTest::anAttributeValueDifferenceIsReportedDifferent
    @Test
    void anAttributeDifferenceIsFoundOnANestedElement() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b k=\"1\"/></a>", "<a><b k=\"2\"/></a>", ComparisonType.ATTR_VALUE));
    }

    // Depends-On: atomic::DiffTest::aNamespaceUriDifferenceIsReportedDifferent
    @Test
    void aNamespaceUriDifferenceIsFoundOnAChild() {
        assertTrue(strictDiff("<a><b xmlns=\"u1\"/></a>", "<a><b xmlns=\"u2\"/></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aDifferingNumberOfChildrenIsReportedDifferent
    @Test
    void aMissingChildIsReflectedInTheChildCount() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b/><c/><d/></a>", "<a><b/></a>", ComparisonType.CHILD_NODELIST_LENGTH));
    }

    // Depends-On: atomic::DiffTest::attributeOrderDoesNotMatter
    @Test
    void attributeOrderIsIgnoredInANestedElement() {
        assertFalse(strictDiff("<a><b k=\"1\" j=\"2\"/></a>", "<a><b j=\"2\" k=\"1\"/></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aTextValueDifferenceIsReportedDifferent
    @Test
    void multipleValueDifferencesAreAllRecordedUnderTheDefaultController() {
        assertTrue(diffCount("<a><b>1</b><c>2</c><d>3</d></a>", "<a><b>4</b><c>5</c><d>6</d></a>") >= 3);
    }

    // Depends-On: atomic::DiffTest::identicalDocumentsHaveNoDifferences
    @Test
    void aDeepIdenticalTreeWithAttributesHasNoDifferences() {
        String x = "<a><b k=\"1\"><c>t</c></b><d/></a>";
        assertFalse(strictDiff(x, x).hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aTextValueDifferenceIsReportedDifferent
    @Test
    void aStopWhenDifferentControllerReportsHasDifferences() {
        Diff d = DiffBuilder.compare("<a>1</a>").withTest("<a>2</a>")
                .withComparisonController(ComparisonControllers.StopWhenDifferent).build();
        assertTrue(d.hasDifferences());
    }

    // Depends-On: atomic::DiffTest::anElementTagNameDifferenceIsReportedDifferent
    @Test
    void aRenamedDeepElementMakesTheTreeDiffer() {
        assertTrue(strictDiff("<a><b><c/></b></a>", "<a><b><z/></b></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::anAttributeValueDifferenceIsReportedDifferent
    @Test
    void aChainedEvaluatorPreservesUnrelatedDifferences() {
        Diff d = DiffBuilder.compare("<a k=\"1\"/>").withTest("<a k=\"2\"/>")
                .withDifferenceEvaluator(DifferenceEvaluators.chain(DifferenceEvaluators.Default))
                .build();
        assertTrue(d.hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aDeepIdenticalTreeHasNoDifferences
    @Test
    void aLargeIdenticalDocumentIsEqual() {
        String x = "<root><a>1</a><b>2</b><c><d>3</d><e>4</e></c></root>";
        assertFalse(strictDiff(x, x).hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aNestedTextChangeIsReportedDifferent
    @Test
    void aSingleNestedChangeInALargeDocumentIsFound() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<root><a>1</a><c><d>3</d></c></root>", "<root><a>1</a><c><d>9</d></c></root>",
                        ComparisonType.TEXT_VALUE));
    }

    // Depends-On: atomic::DiffTest::aDifferingNumberOfAttributesIsReportedDifferent
    @Test
    void anExtraAttributeOnANestedElementIsDetected() {
        assertTrue(strictDiff("<a><b k=\"1\"/></a>", "<a><b k=\"1\" j=\"2\"/></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::identicalSelfClosingAndOpenTagsAreEqual
    @Test
    void mixedSelfClosingFormsAreEqualInATree() {
        assertFalse(strictDiff("<a><b></b><c/></a>", "<a><b/><c></c></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aTextValueChangeMakesDocumentsDiffer
    @Test
    void aTextChangeUnderTwoLevelsMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a><b><c>x</c></b></a>", "<a><b><c>y</c></b></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aChangedAttributeMakesDocumentsDiffer
    @Test
    void aChangedNestedAttributeMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a><b k=\"1\"/></a>", "<a><b k=\"7\"/></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::twoEmptyRootsAreEqual
    @Test
    void twoIdenticalNestedEmptyStructuresAreEqual() {
        assertFalse(strictDiff("<a><b/><c/></a>", "<a><b/><c/></a>").hasDifferences());
    }

    // Depends-On: atomic::DiffTest::aRemovedChildMakesDocumentsDiffer
    @Test
    void addingAChildDeepInTheTreeMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a><b><c/></b></a>", "<a><b><c/><d/></b></a>").hasDifferences());
    }
}
