import { describe, it, expect, beforeEach, vi } from "vitest";
import { tracingChannel } from "node:diagnostics_channel";
import { createStorage } from "unstorage";
import { withTracing } from "unstorage/tracing";
import type { Storage } from "unstorage";
import memory from "unstorage/drivers/memory";
import type { TracedOperation, TraceContext } from "unstorage/tracing";

type TracingEvent = {
  start?: { data: TraceContext };
  end?: { data: TraceContext };
  asyncStart?: { data: TraceContext };
  asyncEnd?: { data: TraceContext; result?: any; error?: Error };
  error?: { data: TraceContext; error: Error };
};

function createTracingListener(operationName: TracedOperation) {
  const events: TracingEvent = {};

  // Create tracing channel
  const channel = tracingChannel(`unstorage.${operationName}`);

  // Create handlers
  const startHandler = vi.fn((message: any) => {
    events.start = { data: message };
  });

  const endHandler = vi.fn((message: any) => {
    events.end = { data: message };
  });

  const asyncStartHandler = vi.fn((message: any) => {
    events.asyncStart = { data: message };
  });

  const asyncEndHandler = vi.fn((message: any) => {
    events.asyncEnd = {
      data: message,
      result: message.result,
      error: message.error,
    };
  });

  const errorHandler = vi.fn((message: any) => {
    events.error = { data: message, error: message.error };
  });

  // Subscribe using the subscribe method which listens to all events
  channel.subscribe({
    start: startHandler,
    end: endHandler,
    asyncStart: asyncStartHandler,
    asyncEnd: asyncEndHandler,
    error: errorHandler,
  });

  return {
    events,
    handlers: {
      start: startHandler,
      end: endHandler,
      asyncStart: asyncStartHandler,
      asyncEnd: asyncEndHandler,
      error: errorHandler,
    },
    cleanup: () => {
      channel.unsubscribe({
        start: startHandler,
        end: endHandler,
        asyncStart: asyncStartHandler,
        asyncEnd: asyncEndHandler,
        error: errorHandler,
      });
    },
  };
}

describe("tracing", () => {
  let storage: Storage;

  beforeEach(() => {
    storage = withTracing(createStorage<any>({ driver: memory() }));
  });

  describe("opt-in behavior", () => {
  });

  describe("hasItem", () => {

  });

  describe("getItem", () => {

  });

  describe("setItem", () => {

  });

  describe("setItems", () => {

  });

  describe("removeItem", () => {

  });

  describe("getKeys", () => {

  });

  describe("getItems", () => {

  });

  describe("getItemRaw", () => {

  });

  describe("setItemRaw", () => {

  });

  describe("clear", () => {

  });

  describe("getMeta", () => {

  });

  describe("setMeta", () => {

  });

  describe("removeMeta", () => {

  });

  describe("base mount tracking", () => {
    it("should include correct base for different mount points", async () => {
      const listener = createTracingListener("getItem");

      // Create storage with multiple mounts
      const baseStorage = withTracing(createStorage<any>({ driver: memory() }));
      baseStorage.mount("/cache", memory());
      baseStorage.mount("/db", memory());
      const multiStorage = baseStorage;

      // Set items in different mounts
      await multiStorage.setItem("root:key", "root value");
      await multiStorage.setItem("cache:key", "cache value");
      await multiStorage.setItem("db:key", "db value");

      // Test root mount
      await multiStorage.getItem("root:key");
      expect(listener.events.start?.data.base).toBe("");

      // Test cache mount
      await multiStorage.getItem("cache:key");
      expect(listener.events.start?.data.base).toBe("cache:");

      // Test db mount
      await multiStorage.getItem("db:key");
      expect(listener.events.start?.data.base).toBe("db:");

      listener.cleanup();
    });
  });

  describe("driver information tracking", () => {
    it("should include driver name in tracing context", async () => {
      const listener = createTracingListener("getItem");

      await storage.setItem("test:key", "value");
      await storage.getItem("test:key");

      expect(listener.events.start?.data.driver).toBeDefined();
      expect(listener.events.start?.data.driver?.name).toBe("memory");

      listener.cleanup();
    });
  });
});
