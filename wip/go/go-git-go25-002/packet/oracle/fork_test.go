package gogitv2_test

import (
	"context"
	"errors"
	"io"
	"os"
	"reflect"
	"testing"
	"time"

	"github.com/go-git/go-billy/v5"
	"github.com/go-git/go-billy/v5/memfs"
	git "github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/config"
	"github.com/go-git/go-git/v5/plumbing"
	"github.com/go-git/go-git/v5/plumbing/object"
	"github.com/go-git/go-git/v5/plumbing/storer"
	"github.com/go-git/go-git/v5/storage"
	"github.com/go-git/go-git/v5/storage/memory"
)

var testSignature = &object.Signature{
	Name: "Spec2Repo", Email: "spec2repo@example.invalid", When: time.Unix(1_700_000_000, 0),
}

func newRepository(t *testing.T) (*git.Repository, *memory.Storage, billy.Filesystem) {
	t.Helper()
	store := memory.NewStorage()
	filesystem := memfs.New()
	repository, err := git.Init(store, filesystem)
	if err != nil {
		t.Fatal(err)
	}
	return repository, store, filesystem
}

func newBareRepository(t *testing.T) (*git.Repository, *memory.Storage) {
	t.Helper()
	store := memory.NewStorage()
	repository, err := git.Init(store, nil)
	if err != nil {
		t.Fatal(err)
	}
	return repository, store
}

func writeFile(t *testing.T, filesystem billy.Filesystem, name, contents string) {
	t.Helper()
	if dir := pathDir(name); dir != "." {
		if err := filesystem.MkdirAll(dir, 0o755); err != nil {
			t.Fatal(err)
		}
	}
	file, err := filesystem.OpenFile(name, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o644)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := file.Write([]byte(contents)); err != nil {
		_ = file.Close()
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
}

func pathDir(name string) string {
	for i := len(name) - 1; i >= 0; i-- {
		if name[i] == '/' {
			return name[:i]
		}
	}
	return "."
}

func readFile(t *testing.T, filesystem billy.Filesystem, name string) string {
	t.Helper()
	file, err := filesystem.Open(name)
	if err != nil {
		t.Fatal(err)
	}
	data, err := io.ReadAll(file)
	if err != nil {
		_ = file.Close()
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
	return string(data)
}

func commitFile(t *testing.T, repository *git.Repository, filesystem billy.Filesystem, name, contents, message string) plumbing.Hash {
	t.Helper()
	writeFile(t, filesystem, name, contents)
	worktree, err := repository.Worktree()
	if err != nil {
		t.Fatal(err)
	}
	if _, err := worktree.Add(name); err != nil {
		t.Fatal(err)
	}
	hash, err := worktree.Commit(message, &git.CommitOptions{Author: testSignature, Committer: testSignature})
	if err != nil {
		t.Fatal(err)
	}
	return hash
}

func mustFork(t *testing.T, repository *git.Repository) *git.Repository {
	t.Helper()
	fork, err := repository.Fork(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if fork == nil {
		t.Fatal("nil fork")
	}
	return fork
}

func forkFilesystem(t *testing.T, repository *git.Repository) billy.Filesystem {
	t.Helper()
	worktree, err := repository.Worktree()
	if err != nil {
		t.Fatal(err)
	}
	return worktree.Filesystem
}

func TestGoGitV2A01(t *testing.T) {
	repository, _, _ := newRepository(t)
	head, err := repository.Reference(plumbing.HEAD, false)
	if err != nil || head.Type() != plumbing.SymbolicReference {
		t.Fatalf("head: %v %v", head, err)
	}
	if head.Target() != plumbing.Master {
		t.Fatalf("target %s", head.Target())
	}
}

func TestGoGitV2A02(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "alpha.txt", "alpha", "alpha")
	commit, err := repository.CommitObject(hash)
	if err != nil || commit.Message != "alpha" || commit.TreeHash.IsZero() {
		t.Fatalf("commit: %#v %v", commit, err)
	}
}

func TestGoGitV2A03(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	writeFile(t, filesystem, "staged.txt", "staged")
	worktree, _ := repository.Worktree()
	if _, err := worktree.Add("staged.txt"); err != nil {
		t.Fatal(err)
	}
	status, err := worktree.Status()
	if err != nil || status["staged.txt"].Staging != git.Added || status["staged.txt"].Worktree != git.Unmodified {
		t.Fatalf("status: %#v %v", status, err)
	}
}

func TestGoGitV2A04(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	writeFile(t, filesystem, "loose.txt", "loose")
	worktree, _ := repository.Worktree()
	status, err := worktree.Status()
	if err != nil || status["loose.txt"].Worktree != git.Untracked || status.IsClean() {
		t.Fatalf("status: %#v %v", status, err)
	}
}

func TestGoGitV2A05(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "branch.txt", "one", "one")
	name := plumbing.NewBranchReferenceName("topic")
	if err := repository.Storer.SetReference(plumbing.NewHashReference(name, hash)); err != nil {
		t.Fatal(err)
	}
	ref, err := repository.Reference(name, false)
	if err != nil || ref.Hash() != hash || ref.Name() != name {
		t.Fatalf("ref: %v %v", ref, err)
	}
}

func TestGoGitV2A06(t *testing.T) {
	repository, _, _ := newRepository(t)
	cfg, _ := repository.Config()
	cfg.User.Name = "Ada"
	cfg.User.Email = "ada@example.invalid"
	if err := repository.Storer.SetConfig(cfg); err != nil {
		t.Fatal(err)
	}
	fresh, err := repository.Config()
	if err != nil || fresh.User.Name != "Ada" || fresh.User.Email != "ada@example.invalid" {
		t.Fatalf("config: %#v %v", fresh, err)
	}
}

func TestGoGitV2A07(t *testing.T) {
	repository, _ := newBareRepository(t)
	if _, err := repository.Worktree(); !errors.Is(err, git.ErrIsBareRepository) {
		t.Fatalf("worktree error: %v", err)
	}
	head, err := repository.Reference(plumbing.HEAD, false)
	if err != nil || head.Target() != plumbing.Master {
		t.Fatalf("head: %v %v", head, err)
	}
}

func TestGoGitV2I01(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "history.txt", "one", "one")
	second := commitFile(t, repository, filesystem, "history.txt", "two", "two")
	commit, err := repository.CommitObject(second)
	if err != nil || len(commit.ParentHashes) != 1 || commit.ParentHashes[0] != first {
		t.Fatalf("lineage: %#v %v", commit, err)
	}
}

func TestGoGitV2I02(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, "tracked.txt", "tracked", "tracked")
	writeFile(t, filesystem, "untracked.txt", "untracked")
	worktree, _ := repository.Worktree()
	status, err := worktree.Status()
	_, trackedListed := status["tracked.txt"]
	if err != nil || trackedListed || status["untracked.txt"].Worktree != git.Untracked {
		t.Fatalf("status: %#v %v", status, err)
	}
}

func TestGoGitV2I03(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "checkout.txt", "one", "one")
	branch := plumbing.NewBranchReferenceName("old")
	_ = repository.Storer.SetReference(plumbing.NewHashReference(branch, first))
	commitFile(t, repository, filesystem, "checkout.txt", "two", "two")
	worktree, _ := repository.Worktree()
	if err := worktree.Checkout(&git.CheckoutOptions{Branch: branch}); err != nil {
		t.Fatal(err)
	}
	if readFile(t, filesystem, "checkout.txt") != "one" {
		t.Fatal("checkout did not restore old tree")
	}
}

func TestGoGitV2I04(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "reset.txt", "one", "one")
	commitFile(t, repository, filesystem, "reset.txt", "two", "two")
	worktree, _ := repository.Worktree()
	if err := worktree.Reset(&git.ResetOptions{Commit: first, Mode: git.HardReset}); err != nil {
		t.Fatal(err)
	}
	head, _ := repository.Head()
	if head.Hash() != first || readFile(t, filesystem, "reset.txt") != "one" {
		t.Fatalf("reset: %s", head.Hash())
	}
}

func TestGoGitV2I05(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "tag.txt", "tag", "tag")
	ref, err := repository.CreateTag("v1", hash, &git.CreateTagOptions{Tagger: testSignature, Message: "release"})
	if err != nil || ref.Name() != plumbing.NewTagReferenceName("v1") {
		t.Fatalf("tag: %v %v", ref, err)
	}
	resolved, err := repository.ResolveRevision(plumbing.Revision("v1"))
	if err != nil || *resolved != hash {
		t.Fatalf("resolve: %v %v", resolved, err)
	}
}

func TestGoGitV2I06(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, "log.txt", "one", "one")
	commitFile(t, repository, filesystem, "log.txt", "two", "two")
	iter, err := repository.Log(&git.LogOptions{})
	if err != nil {
		t.Fatal(err)
	}
	count := 0
	_ = iter.ForEach(func(*object.Commit) error { count++; return nil })
	if count != 2 {
		t.Fatalf("count %d", count)
	}
}

func TestGoGitV2I07(t *testing.T) {
	repository, store, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "open.txt", "open", "open")
	reopened, err := git.Open(store, filesystem)
	if err != nil {
		t.Fatal(err)
	}
	head, err := reopened.Head()
	if err != nil || head.Hash() != hash || readFile(t, filesystem, "open.txt") != "open" {
		t.Fatalf("reopen: %v %v", head, err)
	}
}

func TestGoGitV2A08(t *testing.T) {
	repository, _, _ := newRepository(t)
	fork := mustFork(t, repository)
	if fork == repository || fork.Storer == repository.Storer {
		t.Fatal("fork aliases source")
	}
	if _, err := fork.Worktree(); err != nil {
		t.Fatal(err)
	}
}

func TestGoGitV2A09(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "head.txt", "head", "head")
	fork := mustFork(t, repository)
	head, err := fork.Reference(plumbing.HEAD, false)
	resolved, resolveErr := fork.Head()
	if err != nil || resolveErr != nil || head.Type() != plumbing.SymbolicReference || head.Target() != plumbing.Master || resolved.Hash() != hash {
		t.Fatalf("head: %v %v %v", head, resolved, err)
	}
}

func TestGoGitV2A10(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "ref.txt", "ref", "ref")
	name := plumbing.NewBranchReferenceName("feature")
	_ = repository.Storer.SetReference(plumbing.NewHashReference(name, hash))
	fork := mustFork(t, repository)
	ref, err := fork.Reference(name, false)
	if err != nil || ref.Type() != plumbing.HashReference || ref.Hash() != hash || ref.Name() != name {
		t.Fatalf("ref: %v %v", ref, err)
	}
}

func TestGoGitV2A11(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "objects.txt", "payload", "objects")
	fork := mustFork(t, repository)
	commit, err := fork.CommitObject(hash)
	if err != nil {
		t.Fatal(err)
	}
	tree, err := fork.TreeObject(commit.TreeHash)
	if err != nil || len(tree.Entries) != 1 {
		t.Fatalf("tree: %#v %v", tree, err)
	}
	blob, err := fork.BlobObject(tree.Entries[0].Hash)
	if err != nil || blob.Size != int64(len("payload")) {
		t.Fatalf("blob: %#v %v", blob, err)
	}
}

func TestGoGitV2A12(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "tagged.txt", "tagged", "tagged")
	ref, err := repository.CreateTag("release", hash, &git.CreateTagOptions{Tagger: testSignature, Message: "release notes"})
	if err != nil {
		t.Fatal(err)
	}
	fork := mustFork(t, repository)
	forkRef, err := fork.Reference(ref.Name(), false)
	tag, tagErr := fork.TagObject(forkRef.Hash())
	if err != nil || tagErr != nil || tag.Target != hash || tag.Message != "release notes\n" {
		t.Fatalf("tag: %v %#v %v", forkRef, tag, tagErr)
	}
}

func TestGoGitV2A13(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	writeFile(t, filesystem, "index.txt", "index")
	worktree, _ := repository.Worktree()
	_, _ = worktree.Add("index.txt")
	fork := mustFork(t, repository)
	idx, err := fork.Storer.Index()
	if err != nil || len(idx.Entries) != 1 || idx.Entries[0].Name != "index.txt" || idx.Entries[0].Hash.IsZero() {
		t.Fatalf("index: %#v %v", idx, err)
	}
}

func TestGoGitV2A14(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, "dirty.txt", "clean", "clean")
	writeFile(t, filesystem, "dirty.txt", "dirty")
	fork := mustFork(t, repository)
	forkWorktree, _ := fork.Worktree()
	status, err := forkWorktree.Status()
	if err != nil || readFile(t, forkWorktree.Filesystem, "dirty.txt") != "dirty" || status["dirty.txt"].Worktree != git.Modified {
		t.Fatalf("dirty fork: %#v %v", status, err)
	}
}

func TestGoGitV2A15(t *testing.T) {
	repository, _, _ := newRepository(t)
	cfg, _ := repository.Config()
	cfg.User.Name = "Grace"
	cfg.User.Email = "grace@example.invalid"
	_ = repository.Storer.SetConfig(cfg)
	fork := mustFork(t, repository)
	forkConfig, err := fork.Config()
	if err != nil || forkConfig.User.Name != "Grace" || forkConfig.User.Email != "grace@example.invalid" || forkConfig == cfg {
		t.Fatalf("config: %#v %v", forkConfig, err)
	}
}

func TestGoGitV2A16(t *testing.T) {
	repository, _, _ := newRepository(t)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	fork, err := repository.Fork(ctx)
	if fork != nil || !errors.Is(err, context.Canceled) {
		t.Fatalf("canceled fork: %v %v", fork, err)
	}
}

func TestGoGitV2I08(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "lineage.txt", "one", "one")
	second := commitFile(t, repository, filesystem, "lineage.txt", "two", "two")
	fork := mustFork(t, repository)
	head, _ := fork.Head()
	commit, err := fork.CommitObject(second)
	if err != nil || head.Hash() != second || len(commit.ParentHashes) != 1 || commit.ParentHashes[0] != first {
		t.Fatalf("lineage: %v %#v %v", head, commit, err)
	}
}

func TestGoGitV2I09(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	base := commitFile(t, repository, filesystem, "branches.txt", "base", "base")
	left := plumbing.NewBranchReferenceName("left")
	right := plumbing.NewBranchReferenceName("right")
	_ = repository.Storer.SetReference(plumbing.NewHashReference(left, base))
	_ = repository.Storer.SetReference(plumbing.NewHashReference(right, base))
	fork := mustFork(t, repository)
	leftRef, leftErr := fork.Reference(left, false)
	rightRef, rightErr := fork.Reference(right, false)
	if leftErr != nil || rightErr != nil || leftRef.Hash() != base || rightRef.Hash() != base || leftRef.Name() == rightRef.Name() {
		t.Fatalf("branches: %v %v %v %v", leftRef, rightRef, leftErr, rightErr)
	}
}

func TestGoGitV2I10(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "detached.txt", "detached", "detached")
	_ = repository.Storer.SetReference(plumbing.NewHashReference(plumbing.HEAD, hash))
	fork := mustFork(t, repository)
	head, err := fork.Reference(plumbing.HEAD, false)
	resolved, resolveErr := fork.Head()
	if err != nil || resolveErr != nil || head.Type() != plumbing.HashReference || head.Hash() != hash || resolved.Hash() != hash {
		t.Fatalf("detached: %v %v %v", head, resolved, err)
	}
}

func TestGoGitV2I11(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, "tracked.txt", "tracked", "tracked")
	writeFile(t, filesystem, "scratch/deep/untracked.txt", "scratch")
	fork := mustFork(t, repository)
	forkWorktree, _ := fork.Worktree()
	status, err := forkWorktree.Status()
	if err != nil || readFile(t, forkWorktree.Filesystem, "scratch/deep/untracked.txt") != "scratch" || status["scratch/deep/untracked.txt"].Worktree != git.Untracked {
		t.Fatalf("untracked: %#v %v", status, err)
	}
}

func TestGoGitV2I12(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, ".gitignore", "*.tmp\n", "ignore")
	writeFile(t, filesystem, "private.tmp", "private")
	fork := mustFork(t, repository)
	forkWorktree, _ := fork.Worktree()
	status, err := forkWorktree.Status()
	_, listed := status["private.tmp"]
	if err != nil || listed || readFile(t, forkWorktree.Filesystem, "private.tmp") != "private" || readFile(t, forkWorktree.Filesystem, ".gitignore") != "*.tmp\n" {
		t.Fatalf("ignored: %#v %v", status, err)
	}
}

func TestGoGitV2I13(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, "gone.txt", "gone", "gone")
	if err := filesystem.Remove("gone.txt"); err != nil {
		t.Fatal(err)
	}
	fork := mustFork(t, repository)
	forkWorktree, _ := fork.Worktree()
	status, err := forkWorktree.Status()
	_, statErr := forkWorktree.Filesystem.Stat("gone.txt")
	if err != nil || status["gone.txt"].Worktree != git.Deleted || !os.IsNotExist(statErr) {
		t.Fatalf("deleted: %#v %v %v", status, err, statErr)
	}
}

func TestGoGitV2I14(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, "layers.txt", "one", "one")
	writeFile(t, filesystem, "layers.txt", "two")
	worktree, _ := repository.Worktree()
	_, _ = worktree.Add("layers.txt")
	writeFile(t, filesystem, "layers.txt", "three")
	fork := mustFork(t, repository)
	forkWorktree, _ := fork.Worktree()
	status, err := forkWorktree.Status()
	if err != nil || status["layers.txt"].Staging != git.Modified || status["layers.txt"].Worktree != git.Modified || readFile(t, forkWorktree.Filesystem, "layers.txt") != "three" {
		t.Fatalf("layers: %#v %v", status, err)
	}
}

func TestGoGitV2I15(t *testing.T) {
	repository, _, _ := newRepository(t)
	cfg, _ := repository.Config()
	cfg.Remotes["origin"] = &config.RemoteConfig{Name: "origin", URLs: []string{"file:///source"}}
	cfg.Branches["main"] = &config.Branch{Name: "main", Remote: "origin", Merge: plumbing.Master}
	_ = repository.Storer.SetConfig(cfg)
	fork := mustFork(t, repository)
	forkConfig, err := fork.Config()
	if err != nil || forkConfig.Remotes["origin"].URLs[0] != "file:///source" || forkConfig.Branches["main"].Remote != "origin" || forkConfig.Branches["main"] == cfg.Branches["main"] {
		t.Fatalf("config graph: %#v %v", forkConfig, err)
	}
}

func TestGoGitV2I16(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "shallow.txt", "one", "one")
	commitFile(t, repository, filesystem, "shallow.txt", "two", "two")
	_ = repository.Storer.SetShallow([]plumbing.Hash{first})
	fork := mustFork(t, repository)
	shallow, err := fork.Storer.Shallow()
	if err != nil || len(shallow) != 1 || shallow[0] != first || &shallow[0] == nil {
		t.Fatalf("shallow: %#v %v", shallow, err)
	}
}

func TestGoGitV2I17(t *testing.T) {
	repository, _ := newBareRepository(t)
	fork := mustFork(t, repository)
	if _, err := fork.Worktree(); !errors.Is(err, git.ErrIsBareRepository) {
		t.Fatalf("fork is not bare: %v", err)
	}
	head, err := fork.Reference(plumbing.HEAD, false)
	if err != nil || head.Target() != plumbing.Master || fork.Storer == repository.Storer {
		t.Fatalf("bare fork: %v %v", head, err)
	}
}

func TestGoGitV2I18(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "source-only.txt", "one", "one")
	fork := mustFork(t, repository)
	second := commitFile(t, repository, filesystem, "source-only.txt", "two", "two")
	forkHead, _ := fork.Head()
	sourceHead, _ := repository.Head()
	if forkHead.Hash() != first || sourceHead.Hash() != second || readFile(t, forkFilesystem(t, fork), "source-only.txt") != "one" || readFile(t, filesystem, "source-only.txt") != "two" {
		t.Fatalf("source divergence: %s %s", forkHead.Hash(), sourceHead.Hash())
	}
}

func TestGoGitV2I19(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "child-only.txt", "one", "one")
	fork := mustFork(t, repository)
	forkFS := forkFilesystem(t, fork)
	second := commitFile(t, fork, forkFS, "child-only.txt", "child", "child")
	sourceHead, _ := repository.Head()
	forkHead, _ := fork.Head()
	if sourceHead.Hash() != first || forkHead.Hash() != second || readFile(t, filesystem, "child-only.txt") != "one" || readFile(t, forkFS, "child-only.txt") != "child" {
		t.Fatalf("child divergence: %s %s", sourceHead.Hash(), forkHead.Hash())
	}
}

func TestGoGitV2I20(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "identity.txt", "identity", "identity")
	fork := mustFork(t, repository)
	sourceObject, sourceErr := repository.Storer.EncodedObject(plumbing.CommitObject, hash)
	forkObject, forkErr := fork.Storer.EncodedObject(plumbing.CommitObject, hash)
	if sourceErr != nil || forkErr != nil || sourceObject.Hash() != forkObject.Hash() || reflect.ValueOf(sourceObject).Pointer() == reflect.ValueOf(forkObject).Pointer() {
		t.Fatalf("object ownership: %v %v", sourceErr, forkErr)
	}
}

func TestGoGitV2I21(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "generations.txt", "one", "one")
	one := mustFork(t, repository)
	second := commitFile(t, repository, filesystem, "generations.txt", "two", "two")
	two := mustFork(t, repository)
	oneHead, _ := one.Head()
	twoHead, _ := two.Head()
	if oneHead.Hash() != first || twoHead.Hash() != second || readFile(t, forkFilesystem(t, one), "generations.txt") != "one" || readFile(t, forkFilesystem(t, two), "generations.txt") != "two" {
		t.Fatalf("generations: %s %s", oneHead.Hash(), twoHead.Hash())
	}
}

func TestGoGitV2I22(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	writeFile(t, filesystem, "target.txt", "target")
	if err := filesystem.Symlink("target.txt", "link.txt"); err != nil {
		t.Fatal(err)
	}
	fork := mustFork(t, repository)
	forkFS := forkFilesystem(t, fork)
	target, err := forkFS.Readlink("link.txt")
	info, statErr := forkFS.Lstat("link.txt")
	if err != nil || statErr != nil || target != "target.txt" || info.Mode()&os.ModeSymlink == 0 {
		t.Fatalf("symlink: %q %#v %v %v", target, info, err, statErr)
	}
}

func TestGoGitV2I23(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	writeFile(t, filesystem, "a/b/c/deep.txt", "deep")
	fork := mustFork(t, repository)
	forkFS := forkFilesystem(t, fork)
	info, err := forkFS.Stat("a/b/c/deep.txt")
	dir, dirErr := forkFS.Stat("a/b/c")
	if err != nil || dirErr != nil || info.IsDir() || !dir.IsDir() || readFile(t, forkFS, "a/b/c/deep.txt") != "deep" {
		t.Fatalf("nested: %#v %#v %v %v", info, dir, err, dirErr)
	}
}

func TestGoGitV2I24(t *testing.T) {
	var nilRepository *git.Repository
	fork, err := nilRepository.Fork(context.Background())
	if fork != nil || !errors.Is(err, git.ErrInvalidForkRequest) {
		t.Fatalf("nil receiver: %v %v", fork, err)
	}
	repository, _, _ := newRepository(t)
	fork, err = repository.Fork(nil)
	if fork != nil || !errors.Is(err, git.ErrInvalidForkRequest) {
		t.Fatalf("nil context: %v %v", fork, err)
	}
}

func TestGoGitV2S01(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	base := commitFile(t, repository, filesystem, "graph/base.txt", "base", "base")
	branch := plumbing.NewBranchReferenceName("release")
	_ = repository.Storer.SetReference(plumbing.NewHashReference(branch, base))
	head := commitFile(t, repository, filesystem, "graph/head.txt", "head", "head")
	_, _ = repository.CreateTag("stable", base, &git.CreateTagOptions{Tagger: testSignature, Message: "stable"})
	fork := mustFork(t, repository)
	forkHead, _ := fork.Head()
	forkBranch, branchErr := fork.Reference(branch, false)
	resolved, resolveErr := fork.ResolveRevision(plumbing.Revision("stable"))
	if branchErr != nil || resolveErr != nil || forkHead.Hash() != head || forkBranch.Hash() != base || *resolved != base {
		t.Fatalf("graph system: %v %v %v", forkHead, forkBranch, resolved)
	}
}

func TestGoGitV2S02(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	base := commitFile(t, repository, filesystem, "split.txt", "base", "base")
	fork := mustFork(t, repository)
	childHash := commitFile(t, fork, forkFilesystem(t, fork), "split.txt", "child", "child")
	sourceHash := commitFile(t, repository, filesystem, "split.txt", "source", "source")
	childCommit, childErr := fork.CommitObject(childHash)
	sourceCommit, sourceErr := repository.CommitObject(sourceHash)
	if childErr != nil || sourceErr != nil || childCommit.ParentHashes[0] != base || sourceCommit.ParentHashes[0] != base || childHash == sourceHash {
		t.Fatalf("split lineage: %v %v", childErr, sourceErr)
	}
}

func TestGoGitV2S03(t *testing.T) {
	repository, store := newBareRepository(t)
	encoded := store.NewEncodedObject()
	encoded.SetType(plumbing.BlobObject)
	writer, _ := encoded.Writer()
	_, _ = writer.Write([]byte("bare object"))
	_ = writer.Close()
	hash, _ := store.SetEncodedObject(encoded)
	name := plumbing.NewTagReferenceName("archive")
	_ = store.SetReference(plumbing.NewHashReference(name, hash))
	fork := mustFork(t, repository)
	ref, refErr := fork.Reference(name, false)
	objectCopy, objectErr := fork.Storer.EncodedObject(plumbing.BlobObject, hash)
	_, worktreeErr := fork.Worktree()
	if refErr != nil || objectErr != nil || ref.Hash() != hash || objectCopy.Hash() != hash || !errors.Is(worktreeErr, git.ErrIsBareRepository) {
		t.Fatalf("bare graph: %v %v %v", refErr, objectErr, worktreeErr)
	}
}

func TestGoGitV2S04(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	commitFile(t, repository, filesystem, "matrix.txt", "base", "base")
	writeFile(t, filesystem, "matrix.txt", "staged")
	worktree, _ := repository.Worktree()
	_, _ = worktree.Add("matrix.txt")
	writeFile(t, filesystem, "matrix.txt", "working")
	writeFile(t, filesystem, "extra.txt", "extra")
	fork := mustFork(t, repository)
	forkWorktree, _ := fork.Worktree()
	status, statusErr := forkWorktree.Status()
	idx, indexErr := fork.Storer.Index()
	if statusErr != nil || indexErr != nil || len(idx.Entries) != 1 || status["matrix.txt"].Staging != git.Modified || status["matrix.txt"].Worktree != git.Modified || status["extra.txt"].Worktree != git.Untracked {
		t.Fatalf("matrix: %#v %#v %v %v", status, idx, statusErr, indexErr)
	}
}

func TestGoGitV2S05(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "shallow-system.txt", "one", "one")
	second := commitFile(t, repository, filesystem, "shallow-system.txt", "two", "two")
	_ = repository.Storer.SetShallow([]plumbing.Hash{first})
	cfg, _ := repository.Config()
	cfg.User.Name = "Shallow User"
	_ = repository.Storer.SetConfig(cfg)
	fork := mustFork(t, repository)
	shallow, shallowErr := fork.Storer.Shallow()
	forkConfig, configErr := fork.Config()
	head, headErr := fork.Head()
	if shallowErr != nil || configErr != nil || headErr != nil || len(shallow) != 1 || shallow[0] != first || forkConfig.User.Name != "Shallow User" || head.Hash() != second {
		t.Fatalf("shallow system: %#v %#v %v", shallow, forkConfig, head)
	}
}

func TestGoGitV2S06(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	hash := commitFile(t, repository, filesystem, "recover.txt", "recover", "recover")
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	failed, firstErr := repository.Fork(ctx)
	recovered, secondErr := repository.Fork(context.Background())
	if failed != nil || !errors.Is(firstErr, context.Canceled) || secondErr != nil || recovered == nil {
		t.Fatalf("recovery setup: %v %v %v", failed, firstErr, secondErr)
	}
	head, headErr := recovered.Head()
	if headErr != nil || head.Hash() != hash {
		t.Fatalf("recovery: %v %v %v %v", failed, firstErr, secondErr, headErr)
	}
}

func TestGoGitV2S07(t *testing.T) {
	repository, _, filesystem := newRepository(t)
	first := commitFile(t, repository, filesystem, "timeline.txt", "one", "one")
	one := mustFork(t, repository)
	second := commitFile(t, repository, filesystem, "timeline.txt", "two", "two")
	two := mustFork(t, repository)
	third := commitFile(t, two, forkFilesystem(t, two), "timeline.txt", "three", "three")
	oneHead, _ := one.Head()
	sourceHead, _ := repository.Head()
	twoHead, _ := two.Head()
	if oneHead.Hash() != first || sourceHead.Hash() != second || twoHead.Hash() != third || readFile(t, forkFilesystem(t, one), "timeline.txt") != "one" || readFile(t, filesystem, "timeline.txt") != "two" || readFile(t, forkFilesystem(t, two), "timeline.txt") != "three" {
		t.Fatalf("timeline: %s %s %s", oneHead.Hash(), sourceHead.Hash(), twoHead.Hash())
	}
}

type flippingStorer struct {
	storage.Storer
	a, b  plumbing.Hash
	calls int
}

func (store *flippingStorer) IterReferences() (storer.ReferenceIter, error) {
	store.calls++
	hash := store.a
	if store.calls%2 == 0 {
		hash = store.b
	}
	if err := store.Storer.SetReference(plumbing.NewHashReference(plumbing.HEAD, hash)); err != nil {
		return nil, err
	}
	return store.Storer.IterReferences()
}

func TestGoGitV2S08(t *testing.T) {
	base := memory.NewStorage()
	_, _ = git.Init(base, nil)
	changing := &flippingStorer{
		Storer: base,
		a:      plumbing.NewHash("1111111111111111111111111111111111111111"),
		b:      plumbing.NewHash("2222222222222222222222222222222222222222"),
	}
	repository := &git.Repository{Storer: changing}
	fork, err := repository.Fork(context.Background())
	if fork != nil || !errors.Is(err, git.ErrRepositoryChanged) || changing.calls < 4 {
		t.Fatalf("unstable generation: %v %v calls=%d", fork, err, changing.calls)
	}
}
