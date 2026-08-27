package koanf_oracle_test

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"testing"

	jsonparser "github.com/knadh/koanf/parsers/json"
	"github.com/knadh/koanf/providers/confmap"
	"github.com/knadh/koanf/providers/rawbytes"
	koanf "github.com/knadh/koanf/v2"
)

type failingProvider struct{ err error }

func (p failingProvider) Read() (map[string]any, error) { return nil, p.err }
func (p failingProvider) ReadBytes() ([]byte, error)    { return nil, p.err }

type mapProvider struct{ facts map[string]any }

func (p mapProvider) Read() (map[string]any, error) { return p.facts, nil }
func (p mapProvider) ReadBytes() ([]byte, error)    { return nil, errors.New("bytes unavailable") }

type lineParser struct{}

func (lineParser) Unmarshal(b []byte) (map[string]any, error) {
	out := map[string]any{}
	for _, line := range splitLines(string(b)) {
		parts := splitPair(line)
		if len(parts) != 2 {
			return nil, errors.New("invalid line")
		}
		out[parts[0]] = parts[1]
	}
	return out, nil
}

func (lineParser) Marshal(mp map[string]any) ([]byte, error) {
	keys := make([]string, 0, len(mp))
	for key := range mp {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	out := ""
	for _, key := range keys {
		out += fmt.Sprintf("%s=%v\n", key, mp[key])
	}
	return []byte(out), nil
}

func splitLines(s string) []string {
	out := []string{}
	start := 0
	for i := 0; i <= len(s); i++ {
		if i == len(s) || s[i] == '\n' {
			if i > start {
				out = append(out, s[start:i])
			}
			start = i + 1
		}
	}
	return out
}

func splitPair(s string) []string {
	for i := range s {
		if s[i] == '=' {
			return []string{s[:i], s[i+1:]}
		}
	}
	return nil
}

func loaded(t *testing.T, delim string, facts map[string]any) *koanf.Koanf {
	t.Helper()
	k := koanf.New(delim)
	mustNoErr(t, k.Load(confmap.Provider(facts, ""), nil))
	return k
}

func loadedJSON(t *testing.T, data string) *koanf.Koanf {
	t.Helper()
	k := koanf.New(".")
	mustNoErr(t, k.Load(rawbytes.Provider([]byte(data)), jsonparser.Parser()))
	return k
}

func mustNoErr(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func mustErrIs(t *testing.T, err, target error) {
	t.Helper()
	if !errors.Is(err, target) {
		t.Fatalf("error %v does not match %v", err, target)
	}
}

func equal(t *testing.T, want, got any) {
	t.Helper()
	if !reflect.DeepEqual(want, got) {
		t.Fatalf("want %#v, got %#v", want, got)
	}
}

func truth(t *testing.T, ok bool, msg string) {
	t.Helper()
	if !ok {
		t.Fatal(msg)
	}
}

func asMap(t *testing.T, value any) map[string]any {
	t.Helper()
	out, ok := value.(map[string]any)
	if !ok {
		t.Fatalf("want map projection, got %T", value)
	}
	return out
}

func asSlice(t *testing.T, value any) []any {
	t.Helper()
	out, ok := value.([]any)
	if !ok {
		t.Fatalf("want slice projection, got %T", value)
	}
	return out
}

func changePaths(receipt koanf.MergeReceipt) []string {
	out := make([]string, len(receipt.Changes))
	for i, change := range receipt.Changes {
		out[i] = string(change.Kind) + ":" + change.Path
	}
	return out
}

func tempFile(t *testing.T, name, body string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), name)
	mustNoErr(t, os.WriteFile(path, []byte(body), 0o600))
	return path
}

func requireDigest(t *testing.T, digest koanf.ProjectionDigest) {
	t.Helper()
	truth(t, len(digest) == 64, "digest must be 64 lowercase hexadecimal characters")
	for _, r := range digest {
		truth(t, r >= '0' && r <= '9' || r >= 'a' && r <= 'f', "digest is not lowercase hexadecimal")
	}
}

var _ koanf.Provider = failingProvider{}
var _ koanf.Provider = mapProvider{}
var _ koanf.Parser = lineParser{}
