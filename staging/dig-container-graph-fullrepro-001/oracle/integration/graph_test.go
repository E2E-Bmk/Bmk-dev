package integration

import (
	"errors"
	"testing"

	"go.uber.org/dig"
)

type Config struct{ Verbose bool }
type Store struct{ Cfg *Config }
type Index struct{ Cfg *Config }
type Server struct {
	S *Store
	I *Index
}

func TestProvideOrderIrrelevantForResolution(t *testing.T) {
	c := dig.New()
	// dependents registered before their dependencies
	c.Provide(func(s *Store) *Server { return &Server{S: s} })
	c.Provide(func(cfg *Config) *Store { return &Store{Cfg: cfg} })
	c.Provide(func() *Config { return &Config{Verbose: true} })
	var verbose bool
	if err := c.Invoke(func(srv *Server) { verbose = srv.S.Cfg.Verbose }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if !verbose {
		t.Fatal("dependency chain did not deliver the configured value")
	}
}

func TestDiamondDependencyBuiltOnce(t *testing.T) {
	c := dig.New()
	cfgRuns := 0
	c.Provide(func() *Config { cfgRuns++; return &Config{} })
	c.Provide(func(cfg *Config) *Store { return &Store{Cfg: cfg} })
	c.Provide(func(cfg *Config) *Index { return &Index{Cfg: cfg} })
	c.Provide(func(s *Store, i *Index) *Server { return &Server{S: s, I: i} })
	var srv *Server
	if err := c.Invoke(func(x *Server) { srv = x }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if cfgRuns != 1 {
		t.Fatalf("shared dependency built %d times, want 1", cfgRuns)
	}
	if srv.S.Cfg != srv.I.Cfg {
		t.Fatal("both diamond branches must receive the identical shared instance")
	}
}

func TestDeferredCycleFailsEveryInvoke(t *testing.T) {
	c := dig.New(dig.DeferAcyclicVerification())
	if err := c.Provide(func(s *Store) *Index { return &Index{} }); err != nil {
		t.Fatalf("provide 1: %v", err)
	}
	if err := c.Provide(func(i *Index) *Store { return &Store{} }); err != nil {
		t.Fatalf("provide 2 must not fail under deferred verification: %v", err)
	}
	if err := c.Provide(func() *Config { return &Config{} }); err != nil {
		t.Fatalf("provide 3: %v", err)
	}
	// even a demand that does not touch the cycle fails while the cycle exists
	err := c.Invoke(func(cfg *Config) {})
	wantContains(t, err, "cycle detected in dependency graph")
	if !dig.IsCycleDetected(err) {
		t.Fatal("IsCycleDetected must be true for deferred cycle rejection")
	}
	err = c.Invoke(func(s *Store) {})
	if !dig.IsCycleDetected(err) {
		t.Fatal("later invokes must keep failing while the cycle remains")
	}
}

func TestDefaultCycleRejectionLeavesGraphUsable(t *testing.T) {
	c := dig.New()
	c.Provide(func(s *Store) *Index { return &Index{} })
	err := c.Provide(func(i *Index) *Store { return &Store{} })
	if !dig.IsCycleDetected(err) {
		t.Fatalf("expected cycle rejection, got %v", err)
	}
	c.Provide(func() *Config { return &Config{Verbose: true} })
	var v bool
	if err := c.Invoke(func(cfg *Config) { v = cfg.Verbose }); err != nil {
		t.Fatalf("unrelated invoke after rejection: %v", err)
	}
	if !v {
		t.Fatal("unrelated key did not resolve after a rejected registration")
	}
	// the rejected constructor's key must not have been registered
	wantContains(t, c.Invoke(func(s *Store) {}), "missing type:")
}

func TestConstructorFailureChainsToInvoke(t *testing.T) {
	c := dig.New()
	sentinel := errors.New("store down")
	c.Provide(func() *Config { return &Config{} })
	c.Provide(func(cfg *Config) (*Store, error) { return nil, sentinel })
	c.Provide(func(s *Store) *Server { return &Server{S: s} })
	ran := false
	err := c.Invoke(func(srv *Server) { ran = true })
	wantContains(t, err, "received non-nil error from function")
	if dig.RootCause(err) != sentinel {
		t.Fatalf("RootCause = %v, want the mid-chain constructor error", dig.RootCause(err))
	}
	if ran {
		t.Fatal("invoked function must not run when the chain fails")
	}
}

func TestTransitiveMissingDependencyReported(t *testing.T) {
	c := dig.New()
	c.Provide(func(cfg *Config) *Store { return &Store{Cfg: cfg} })
	c.Provide(func(s *Store) *Server { return &Server{S: s} })
	err := c.Invoke(func(srv *Server) {})
	wantContains(t, err, "missing type:")
	wantContains(t, err, "integration.Config")
}

func TestSuccessfulDependencyMemoizedDespiteDownstreamFailure(t *testing.T) {
	c := dig.New()
	cfgRuns, storeRuns := 0, 0
	c.Provide(func() *Config { cfgRuns++; return &Config{} })
	c.Provide(func(cfg *Config) (*Store, error) { storeRuns++; return nil, errors.New("nope") })
	if err := c.Invoke(func(s *Store) {}); err == nil {
		t.Fatal("first invoke should fail")
	}
	if err := c.Invoke(func(s *Store) {}); err == nil {
		t.Fatal("second invoke should fail")
	}
	if cfgRuns != 1 {
		t.Fatalf("successful dependency ran %d times, want 1 (memoized on success)", cfgRuns)
	}
	if storeRuns != 2 {
		t.Fatalf("failing constructor ran %d times, want 2 (failure never memoized)", storeRuns)
	}
}
