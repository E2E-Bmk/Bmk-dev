package atomic;

import static fixtures.Xml.diffCount;
import static fixtures.Xml.resultOf;
import static fixtures.Xml.strictDiff;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.xmldiff.diff.ComparisonResult;
import org.xmldiff.diff.ComparisonType;
import org.junit.jupiter.api.Test;

/** Single-owner checks for the difference classification. */
class DiffTest {

    // MUTATED: F1_nsprefix
    @Test
    void aNamespacePrefixOnlyDifferenceIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a xmlns:p=\"u\"><p:b/></a>", "<a xmlns:q=\"u\"><q:b/></a>", ComparisonType.NAMESPACE_PREFIX));
    }

    // MUTATED: F1_nsprefix
    @Test
    void aRootNamespacePrefixChangeIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<p:a xmlns:p=\"u\"/>", "<q:a xmlns:q=\"u\"/>", ComparisonType.NAMESPACE_PREFIX));
    }

    // MUTATED: F2_childseq
    @Test
    void reorderedChildrenAreReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                fixtures.Xml.resultOfSeq("<a><b/><c/></a>", "<a><c/><b/></a>", ComparisonType.CHILD_NODELIST_SEQUENCE));
    }

    // MUTATED: F2_childseq
    @Test
    void reorderingThreeChildrenIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                fixtures.Xml.resultOfSeq("<a><b/><c/><d/></a>", "<a><d/><c/><b/></a>", ComparisonType.CHILD_NODELIST_SEQUENCE));
    }

    // MUTATED: F3_xmlenc
    @Test
    void aDifferentXmlEncodingIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<?xml version=\"1.0\" encoding=\"UTF-8\"?><a/>",
                         "<?xml version=\"1.0\" encoding=\"US-ASCII\"?><a/>", ComparisonType.XML_ENCODING));
    }

    // MUTATED: F3_xmlenc
    @Test
    void anotherXmlEncodingChangeIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<?xml version=\"1.0\" encoding=\"UTF-8\"?><r>x</r>",
                         "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?><r>x</r>", ComparisonType.XML_ENCODING));
    }

    // MUTATED: F4_nodetype
    @Test
    void aCdataVersusTextPairingIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><![CDATA[x]]></a>", "<a>x</a>", ComparisonType.NODE_TYPE));
    }

    // MUTATED: F4_nodetype
    @Test
    void aTextVersusCdataPairingIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a>hello</a>", "<a><![CDATA[hello]]></a>", ComparisonType.NODE_TYPE));
    }

    // ---- native: identical / value differences (not in the downgrade set) ----
    @Test
    void identicalDocumentsHaveNoDifferences() {
        assertFalse(strictDiff("<a><b>1</b></a>", "<a><b>1</b></a>").hasDifferences());
    }

    @Test
    void aTextValueDifferenceIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b>1</b></a>", "<a><b>2</b></a>", ComparisonType.TEXT_VALUE));
    }

    @Test
    void anElementTagNameDifferenceIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b/></a>", "<a><x/></a>", ComparisonType.ELEMENT_TAG_NAME));
    }

    @Test
    void anAttributeValueDifferenceIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a k=\"1\"/>", "<a k=\"2\"/>", ComparisonType.ATTR_VALUE));
    }

    @Test
    void aNamespaceUriDifferenceIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a xmlns=\"u1\"/>", "<a xmlns=\"u2\"/>", ComparisonType.NAMESPACE_URI));
    }

    @Test
    void aDifferingNumberOfAttributesIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a k=\"1\"/>", "<a k=\"1\" j=\"2\"/>", ComparisonType.ELEMENT_NUM_ATTRIBUTES));
    }

    @Test
    void aDifferingNumberOfChildrenIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b/></a>", "<a><b/><c/></a>", ComparisonType.CHILD_NODELIST_LENGTH));
    }

    @Test
    void aMissingElementIsDetectedAsAChildLookup() {
        assertTrue(strictDiff("<a><b/></a>", "<a><c/></a>").hasDifferences());
    }

    @Test
    void aTextValueChangeMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a>x</a>", "<a>y</a>").hasDifferences());
    }

    @Test
    void anIdenticalAttributedElementHasNoDifferences() {
        assertFalse(strictDiff("<a k=\"1\" j=\"2\"/>", "<a k=\"1\" j=\"2\"/>").hasDifferences());
    }

    @Test
    void attributeOrderDoesNotMatter() {
        assertFalse(strictDiff("<a k=\"1\" j=\"2\"/>", "<a j=\"2\" k=\"1\"/>").hasDifferences());
    }

    @Test
    void aDeepIdenticalTreeHasNoDifferences() {
        assertFalse(strictDiff("<a><b><c>t</c></b></a>", "<a><b><c>t</c></b></a>").hasDifferences());
    }

    @Test
    void aNestedTextChangeIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b><c>t</c></b></a>", "<a><b><c>u</c></b></a>", ComparisonType.TEXT_VALUE));
    }

    @Test
    void aChangedAttributeMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a k=\"1\"/>", "<a k=\"9\"/>").hasDifferences());
    }

    @Test
    void aRenamedRootIsReportedDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a/>", "<z/>", ComparisonType.ELEMENT_TAG_NAME));
    }

    @Test
    void identicalNamespacedDocumentsHaveNoDifferences() {
        assertFalse(strictDiff("<p:a xmlns:p=\"u\"><p:b/></p:a>", "<p:a xmlns:p=\"u\"><p:b/></p:a>").hasDifferences());
    }

    @Test
    void aDifferentNamespaceUriMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a xmlns=\"u1\"/>", "<a xmlns=\"u2\"/>").hasDifferences());
    }

    @Test
    void anAddedAttributeMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a/>", "<a k=\"1\"/>").hasDifferences());
    }

    @Test
    void aRemovedChildMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a><b/><c/></a>", "<a><b/></a>").hasDifferences());
    }

    @Test
    void identicalSelfClosingAndOpenTagsAreEqual() {
        assertFalse(strictDiff("<a></a>", "<a/>").hasDifferences());
    }

    @Test
    void aValueChangeInOneOfManyChildrenIsDifferent() {
        assertEquals(ComparisonResult.DIFFERENT,
                resultOf("<a><b>1</b><c>2</c></a>", "<a><b>1</b><c>3</c></a>", ComparisonType.TEXT_VALUE));
    }

    @Test
    void aDeeplyNestedStructureChangeMakesDocumentsDiffer() {
        assertTrue(strictDiff("<a><b><c><d>1</d></c></b></a>", "<a><b><c><d>2</d></c></b></a>").hasDifferences());
    }

    @Test
    void twoEmptyRootsAreEqual() {
        assertFalse(strictDiff("<a/>", "<a/>").hasDifferences());
    }

    @Test
    void aChangedTextAmongIdenticalSiblingsCountsOneTextDifference() {
        assertTrue(diffCount("<a><b>1</b><b>2</b></a>", "<a><b>1</b><b>9</b></a>") >= 1);
    }

    @Test
    void anAttributeNameChangeIsDetected() {
        assertTrue(strictDiff("<a k=\"1\"/>", "<a m=\"1\"/>").hasDifferences());
    }

    @Test
    void aWhitespaceOnlyTextChangeIsDetectedByDefault() {
        assertTrue(strictDiff("<a>x</a>", "<a>x </a>").hasDifferences());
    }

    @Test
    void identicalCommentsProduceNoDifferences() {
        assertFalse(strictDiff("<a><!-- c -->x</a>", "<a><!-- c -->x</a>").hasDifferences());
    }
}
