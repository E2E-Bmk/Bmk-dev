import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import s3Driver from "unstorage/drivers/s3";

const DEFAULT_OBJECTS = [
  "foo/a.json",
  "foo/b.json",
  "foo/nested/c.json",
  "foobar/d.json",
  "other/e.json",
];

let pageSize = 2;
let objects: string[] = [];
let requests: string[] = [];
let deleted: string[] = [];
let echoStaleToken = false;
/** Canned list responses, consumed one per list request. A number is returned as a bare status. */
let listOverrides: Array<string | number> = [];

function decodeXml(value: string) {
  return value.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
}

function listResponse(keys: string[], nextToken?: string) {
  return /* xml */ `<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
<Name>test-bucket</Name>
<IsTruncated>${nextToken ? "true" : "false"}</IsTruncated>
${nextToken || echoStaleToken ? `<NextContinuationToken>${nextToken || "0"}</NextContinuationToken>` : ""}
${keys.map((key) => `<Contents><Key>${key}</Key></Contents>`).join("\n")}
</ListBucketResult>`;
}

const driver = (opts?: Partial<Parameters<typeof s3Driver>[0]>) =>
  s3Driver({
    accessKeyId: "test",
    secretAccessKey: "test",
    bucket: "test-bucket",
    endpoint: "https://s3.test",
    region: "auto",
    ...opts,
  });

describe("drivers: s3 (listObjects)", () => {
  beforeEach(() => {
    pageSize = 2;
    objects = [...DEFAULT_OBJECTS];
    requests = [];
    deleted = [];
    echoStaleToken = false;
    listOverrides = [];
    vi.stubGlobal("fetch", async (req: Request) => {
      const url = new URL(req.url);
      requests.push(`${req.method} ${url.pathname}${url.search}`);
      if (url.search === "?delete") {
        const body = await req.text();
        deleted.push(...[...body.matchAll(/<Key>(.+?)<\/Key>/g)].map((m) => decodeXml(m[1]!)));
        return new Response("", { status: 200 });
      }
      if (req.method === "DELETE") {
        deleted.push(decodeURIComponent(url.pathname.slice("/test-bucket/".length)));
        return new Response(null, { status: 204 });
      }
      if (listOverrides.length > 0) {
        const next = listOverrides.shift()!;
        return typeof next === "number"
          ? new Response(null, { status: next })
          : new Response(next, { status: 200 });
      }
      const prefix = url.searchParams.get("prefix") || "";
      const matched = objects.filter((key) => key.startsWith(prefix));
      const offset = Number(url.searchParams.get("continuation-token") || 0);
      const page = matched.slice(offset, offset + pageSize);
      const nextOffset = offset + pageSize;
      return new Response(listResponse(page, nextOffset < matched.length ? `${nextOffset}` : ""), {
        status: 200,
      });
    });
  });

  afterEach(() => vi.unstubAllGlobals());





  it("only clears keys under the given base", async () => {
    await driver().clear!("foo", {});
    expect(deleted).toMatchObject(["foo/a.json", "foo/b.json", "foo/nested/c.json"]);
  });










});
