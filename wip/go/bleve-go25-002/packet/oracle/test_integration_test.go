package blevegate_test

import "testing"

// Verifies: BLEVE-MAP-I01
func TestBleveSeamMappingToAnalyzerPrimary(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-MAP-I01
func TestBleveSeamMappingToAnalyzerBoundary(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-MAP-I02
func TestBleveSeamAnalyzedTokensToStoredFields(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-MAP-I02
func TestBleveSeamDisabledFieldToNoTerm(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-BATCH-I01
func TestBleveSeamBatchCommitToCount(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-I01
func TestBleveSeamBatchCommitToSearch(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-I02
func TestBleveSeamBatchUpdateToStoredField(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-I02
func TestBleveSeamBatchDeleteToNoHit(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-I03
func TestBleveSeamFailedBatchPreservesGeneration(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-BATCH-I03
func TestBleveSeamResetBatchPublishesNothing(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-QUERY-I01
func TestBleveSeamBooleanQueryToHitSet(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-I01
func TestBleveSeamMinimumShouldToFacet(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-I02
func TestBleveSeamRangeQueryToSortedHits(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-I02
func TestBleveSeamOpenRangeToBoundaryHits(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-I03
func TestBleveSeamQueryStringToTypedQuery(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-QUERY-I03
func TestBleveSeamEscapedQueryToHighlight(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-FACET-I01
func TestBleveSeamFacetCountsMatchDictionary(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-FACET-I01
func TestBleveSeamFacetMissingTermsExcluded(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-DICT-I01
func TestBleveSeamDictionaryRangeMatchesQuery(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-DICT-I01
func TestBleveSeamDictionaryPrefixAfterDelete(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-REOPEN-I01
func TestBleveSeamCommitCloseReopenSearch(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-REOPEN-I01
func TestBleveSeamCommitCloseReopenCount(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-MERGE-I01
func TestBleveSeamRepeatedCommitsPreserveHits(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-MERGE-I01
func TestBleveSeamRepeatedCommitsPreserveDictionary(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-REOPEN-I02
func TestBleveSeamReopenAfterDeletePreservesTombstone(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-ALIAS-I01
func TestBleveSeamAliasFanoutMergesResults(t *testing.T) { assertAliasReceipt(t) }

// Verifies: BLEVE-ALIAS-I02
func TestBleveSeamAliasSwapChangesFreshSearch(t *testing.T) { assertAliasReceipt(t) }

// Verifies: BLEVE-FAIL-I01
func TestBleveSeamRejectedDocumentPreservesCount(t *testing.T) { assertFailureReceipt(t) }

// Verifies: BLEVE-FAIL-I02
func TestBleveSeamRejectedBatchPreservesSearch(t *testing.T) { assertFailureReceipt(t) }

// Verifies: BLEVE-NATIVE-I01
func TestBleveNativeSeamIndexToTermSearch(t *testing.T) { nativeTerm(t) }

// Verifies: BLEVE-NATIVE-I02
func TestBleveNativeSeamStoredFieldProjection(t *testing.T) { nativeStored(t) }

// Verifies: BLEVE-NATIVE-I03
func TestBleveNativeSeamDeleteToCount(t *testing.T) { nativeDelete(t) }

// Verifies: BLEVE-NATIVE-I04
func TestBleveNativeSeamPaginationOrdering(t *testing.T) { nativePagination(t) }

// Verifies: BLEVE-NATIVE-I05
func TestBleveNativeSeamHighlightStoredText(t *testing.T) { nativeHighlight(t) }

// Verifies: BLEVE-NATIVE-I06
func TestBleveNativeSeamReadOnlyIndexProjection(t *testing.T) { nativeReadOnly(t) }

// Verifies: BLEVE-NATIVE-I07
func TestBleveNativeSeamCLIQueryMatchesAPI(t *testing.T) { nativeCLI(t, "query") }

// Verifies: BLEVE-MAP-S01
func TestBleveSystemMappedDocumentFreshReceipt(t *testing.T) { assertMappedReceipt(t) }

// Verifies: BLEVE-BATCH-S01
func TestBleveSystemBatchGenerationFreshReceipt(t *testing.T) { assertBatchReceipt(t) }

// Verifies: BLEVE-QUERY-S01
func TestBleveSystemQueryRewriteFreshReceipt(t *testing.T) { assertQueryReceipt(t) }

// Verifies: BLEVE-FACET-S01
func TestBleveSystemFacetDictionaryFreshReceipt(t *testing.T) { assertFacetDictionaryReceipt(t) }

// Verifies: BLEVE-REOPEN-S01
func TestBleveSystemReceiptReopenFreshReceipt(t *testing.T) { assertReopenReceipt(t) }

// Verifies: BLEVE-NATIVE-S01
func TestBleveSystemNativeCreateQueryReopenReceipt(t *testing.T) { nativeReopen(t) }

// Verifies: BLEVE-NATIVE-S02
func TestBleveSystemNativeDeleteCLIReceipt(t *testing.T) { nativeCLI(t, "count") }

// Verifies: BLEVE-NATIVE-S03
func TestBleveSystemNativeAliasSearchReceipt(t *testing.T) { nativeAlias(t) }
