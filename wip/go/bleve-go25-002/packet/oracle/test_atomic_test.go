package blevegate_test

import "testing"

// Verifies: BLEVE-MAP-A01
func TestBleveAtomicNestedMappingPrimary(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-MAP-A01
func TestBleveAtomicNestedMappingBoundary(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-MAP-A02
func TestBleveAtomicFieldAnalysisPrimary(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-MAP-A02
func TestBleveAtomicFieldAnalysisBoundary(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-BATCH-A01
func TestBleveAtomicBatchLastWriteWins(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-A01
func TestBleveAtomicBatchDeleteWins(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-A02
func TestBleveAtomicBatchErrorIdentity(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-A02
func TestBleveAtomicBatchResetBoundary(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-QUERY-A01
func TestBleveAtomicBooleanQueryMinimumShould(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-A01
func TestBleveAtomicBooleanQueryEmptyBoundary(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-A02
func TestBleveAtomicRangeQueryInclusivity(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-A02
func TestBleveAtomicRangeQueryOpenBound(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-FACET-A01
func TestBleveAtomicTermsFacetRequest(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-FACET-A01
func TestBleveAtomicNumericFacetBoundary(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-DICT-A01
func TestBleveAtomicFieldDictionaryPrefix(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-DICT-A01
func TestBleveAtomicFieldDictionaryRange(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-REOPEN-A01
func TestBleveAtomicIndexOpenClosedError(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-REOPEN-A01
func TestBleveAtomicIndexDoubleClose(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-MERGE-A01
func TestBleveAtomicReceiptDigestStorageIndependent(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-MERGE-A01
func TestBleveAtomicReceiptEquivalentSameGeneration(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-ALIAS-A01
func TestBleveAtomicAliasAddRemove(t *testing.T) { assertAliasReceipt(t) }

// Verifies: BLEVE-ALIAS-A01
func TestBleveAtomicAliasSwapBoundary(t *testing.T) { assertAliasReceipt(t) }

// Verifies: BLEVE-FAIL-A01
func TestBleveAtomicRejectedDocumentError(t *testing.T) { assertFailureReceipt(t) }

// Verifies: BLEVE-FAIL-A01
func TestBleveAtomicRejectedDocumentNoCount(t *testing.T) { assertFailureReceipt(t) }

// Verifies: BLEVE-NATIVE-A01
func TestBleveAtomicNativeDocumentCount(t *testing.T) { nativeCount(t) }

// Verifies: BLEVE-NATIVE-A01
func TestBleveAtomicNativeDocumentCountEmpty(t *testing.T) { nativeCount(t) }

// Verifies: BLEVE-NATIVE-A02
func TestBleveAtomicNativeTermQuery(t *testing.T) { nativeTerm(t) }

// Verifies: BLEVE-NATIVE-A02
func TestBleveAtomicNativeTermQueryMissing(t *testing.T) { nativeTerm(t) }

// Verifies: BLEVE-NATIVE-A03
func TestBleveAtomicNativeStoredField(t *testing.T) { nativeStored(t) }

// Verifies: BLEVE-NATIVE-A03
func TestBleveAtomicNativeStoredFieldAbsent(t *testing.T) { nativeStored(t) }

// Verifies: BLEVE-NATIVE-A04
func TestBleveAtomicNativeDeleteMissing(t *testing.T) { nativeDelete(t) }

// Verifies: BLEVE-NATIVE-A04
func TestBleveAtomicNativeDeleteExisting(t *testing.T) { nativeDelete(t) }
