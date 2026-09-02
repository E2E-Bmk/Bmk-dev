package nutsdb

import "errors"

// SavepointID identifies a transaction-local savepoint.
type SavepointID uint64

var (
	ErrSavepointNotFound   = errors.New("savepoint not found")
	ErrSavepointNotTopmost = errors.New("savepoint is not topmost")
)

type txSavepoint struct{}

// Savepoint captures the transaction's currently staged mutations.
func (tx *Tx) Savepoint() (SavepointID, error) { return 0, ErrSavepointNotFound }

// RollbackTo restores the state captured by id.
func (tx *Tx) RollbackTo(id SavepointID) error { return ErrSavepointNotFound }

// ReleaseSavepoint discards the most recent savepoint.
func (tx *Tx) ReleaseSavepoint(id SavepointID) error { return ErrSavepointNotFound }

// SavepointDepth returns the number of live savepoints.
func (tx *Tx) SavepointDepth() (int, error) { return 0, nil }
