package ristretto

import "time"

type BatchOperation uint8

const (
	BatchSet BatchOperation = iota + 1
	BatchDelete
)

type BatchGuard uint8

const (
	BatchAny BatchGuard = iota
	BatchRequirePresent
	BatchRequireAbsent
)

type BatchFailure uint8

const (
	BatchSucceeded BatchFailure = iota
	BatchCacheClosed
	BatchInvalidOperation
	BatchInvalidGuard
	BatchInvalidTTL
	BatchInvalidCost
	BatchConditionFailed
	BatchUpdateRejected
	BatchHashConflict
	BatchCapacityExceeded
)

type BatchItem[K Key, V any] struct {
	Operation BatchOperation
	Key       K
	Value     V
	Cost      int64
	TTL       time.Duration
	Guard     BatchGuard
}

type BatchResult[K Key] struct {
	Applied     bool
	FailedIndex int
	FailedKey   K
	Failure     BatchFailure
	Effects     int
}

type BatchValue[K Key, V any] struct {
	Key          K
	Value        V
	Found        bool
	RemainingTTL time.Duration
}

func (c *Cache[K, V]) ApplyBatch(items []BatchItem[K, V]) BatchResult[K] {
	if len(items) == 0 {
		return BatchResult[K]{Applied: true, FailedIndex: -1}
	}
	return BatchResult[K]{FailedIndex: 0, FailedKey: items[0].Key, Failure: BatchInvalidOperation}
}

func (c *Cache[K, V]) GetMany(keys []K) []BatchValue[K, V] {
	values := make([]BatchValue[K, V], len(keys))
	for i, key := range keys {
		values[i].Key = key
	}
	return values
}
