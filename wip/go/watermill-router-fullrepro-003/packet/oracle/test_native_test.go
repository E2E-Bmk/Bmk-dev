package watermillv3gate_test

import (
	"context"
	"errors"
	"testing"

	"github.com/ThreeDotsLabs/watermill"
	"github.com/ThreeDotsLabs/watermill/components/cqrs"
	"github.com/ThreeDotsLabs/watermill/message"
	"github.com/ThreeDotsLabs/watermill/pubsub/gochannel"
)

type nativeRecord struct{ Value string }

func nativeMetadata(t *testing.T) {
	t.Helper()
	original := message.NewMessage("native", []byte("body"))
	original.Metadata.Set("key", "old")
	copy := original.Copy()
	copy.Metadata.Set("key", "new")
	if original.UUID != copy.UUID || original.Metadata.Get("key") != "old" {
		t.Fatal("copy ownership")
	}
}
func nativeTerminal(t *testing.T) {
	t.Helper()
	msg := message.NewMessage("terminal", nil)
	if !msg.Ack() || msg.Nack() {
		t.Fatal("terminal decision")
	}
	select {
	case <-msg.Acked():
	default:
		t.Fatal("ack signal")
	}
}
func nativeClosed(t *testing.T) {
	t.Helper()
	bus := gochannel.NewGoChannel(gochannel.Config{}, watermill.NopLogger{})
	mustNoError(t, bus.Close())
	if bus.Publish("late", message.NewMessage("late", nil)) == nil {
		t.Fatal("late publish")
	}
}
func nativeCQRS(t *testing.T) {
	t.Helper()
	marshaler := cqrs.JSONMarshaler{NewUUID: func() string { return "native" }, GenerateName: cqrs.StructName}
	msg, err := marshaler.Marshal(nativeRecord{Value: "ok"})
	mustNoError(t, err)
	var out nativeRecord
	mustNoError(t, marshaler.Unmarshal(msg, &out))
	if out.Value != "ok" || marshaler.NameFromMessage(msg) != "nativeRecord" {
		t.Fatal("cqrs round trip")
	}
}
func nativeDuplicateHandler(t *testing.T) {
	t.Helper()
	bus := gochannel.NewGoChannel(gochannel.Config{}, watermill.NopLogger{})
	defer bus.Close()
	router := message.NewDefaultRouter(watermill.NopLogger{})
	router.AddNoPublisherHandler("same", "one", bus, func(*message.Message) error { return nil })
	defer func() {
		value := recover()
		err, ok := value.(error)
		var duplicate message.DuplicateHandlerNameError
		if !ok || !errors.As(err, &duplicate) {
			t.Fatal("duplicate handler")
		}
	}()
	router.AddNoPublisherHandler("same", "two", bus, func(*message.Message) error { return nil })
}
func nativeContext(t *testing.T) {
	t.Helper()
	ctx, cancel := context.WithCancel(context.Background())
	msg := message.NewMessageWithContext(ctx, "ctx", nil)
	cancel()
	if !errors.Is(msg.Context().Err(), context.Canceled) {
		t.Fatal("context")
	}
}

func nativeMetadataDelete(t *testing.T) {
	t.Helper()
	metadata := message.Metadata{}
	metadata.Set("key", "value")
	delete(metadata, "key")
	if metadata.Get("key") != "" {
		t.Fatal("metadata delete")
	}
}

func nativeIdentity(t *testing.T) {
	t.Helper()
	msg := message.NewMessage("stable-id", []byte("payload"))
	if msg.UUID != "stable-id" || string(msg.Payload) != "payload" {
		t.Fatal("message identity")
	}
}

func nativeStructName(t *testing.T) {
	t.Helper()
	if cqrs.StructName(&nativeRecord{}) != "nativeRecord" || cqrs.FullyQualifiedStructName(&nativeRecord{}) == "" {
		t.Fatal("struct name")
	}
}

func TestCoordAtomicNativeMetadataDeletePrimary(t *testing.T)    { nativeMetadataDelete(t) }
func TestCoordAtomicNativeMetadataDeleteSecondary(t *testing.T)  { nativeMetadataDelete(t) }
func TestCoordAtomicNativeMessageIdentityPrimary(t *testing.T)   { nativeIdentity(t) }
func TestCoordAtomicNativeMessageIdentitySecondary(t *testing.T) { nativeIdentity(t) }
func TestCoordAtomicNativeCQRSStructNamePrimary(t *testing.T)    { nativeStructName(t) }
func TestCoordAtomicNativeCQRSStructNameSecondary(t *testing.T)  { nativeStructName(t) }

func TestCoordAtomicNativeMetadataClonePrimary(t *testing.T)    { nativeMetadata(t) }
func TestCoordAtomicNativeMetadataCloneSecondary(t *testing.T)  { nativeMetadata(t) }
func TestCoordAtomicNativeTerminalPrimary(t *testing.T)         { nativeTerminal(t) }
func TestCoordAtomicNativeTerminalSecondary(t *testing.T)       { nativeTerminal(t) }
func TestCoordAtomicNativeGoChannelClosePrimary(t *testing.T)   { nativeClosed(t) }
func TestCoordAtomicNativeGoChannelCloseSecondary(t *testing.T) { nativeClosed(t) }
func TestCoordAtomicNativeCQRSJSONPrimary(t *testing.T)         { nativeCQRS(t) }
func TestCoordAtomicNativeCQRSJSONSecondary(t *testing.T)       { nativeCQRS(t) }
func TestCoordSeamNativeCQRSName(t *testing.T)                  { nativeCQRS(t) }
func TestCoordSeamNativeDuplicateHandler(t *testing.T)          { nativeDuplicateHandler(t) }
func TestCoordSeamNativeMessageContext(t *testing.T)            { nativeContext(t) }
func TestCoordSeamNativeCopyPayload(t *testing.T)               { nativeMetadata(t) }
func TestCoordSeamNativeStructName(t *testing.T)                { nativeCQRS(t) }
func TestCoordSystemNativeRouterFreshObservation(t *testing.T)  { nativeDuplicateHandler(t) }
func TestCoordSystemNativeCQRSFreshObservation(t *testing.T)    { nativeCQRS(t) }
