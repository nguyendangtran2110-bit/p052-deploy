import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { buildContentSecurityPolicy } from "@/proxy";
import { NextRequest } from "next/server";
import { proxy } from "@/proxy";
import { handleScopeLoss } from "@/src/lib/session";

function sourceFiles(directory: string): string[] {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(target) : /\.(ts|tsx)$/.test(entry.name) ? [target] : [];
  });
}

describe("browser storage safety", () => {
  it("never writes ticket content, proposals, or drafts to browser persistence or URLs", () => {
    const source = sourceFiles(path.resolve("app")).concat(sourceFiles(path.resolve("src"))).map((file) => fs.readFileSync(file, "utf8")).join("\n");
    expect(source).not.toContain("onbxrd-ticket-draft");
    expect(source).not.toContain("proposal=");
    expect(source).not.toContain("sessionStorage.clear");
    expect(source).not.toContain("quickLogin");
    const client = fs.readFileSync(path.resolve("src/lib/ticket-api.ts"), "utf8");
    expect(client).not.toMatch(/sessionStorage\.setItem\([^\n]*(subject|content|urgency)/);
    expect(client).not.toMatch(/localStorage\.setItem\([^\n]*(subject|content|urgency|draft)/);
  });

  it("ships a nonce-based production CSP without unsafe inline or eval execution", () => {
    const config = fs.readFileSync(path.resolve("next.config.ts"), "utf8");
    expect(config).toContain("X-Content-Type-Options");
    expect(config).toContain("Referrer-Policy");
    expect(config).toContain("Permissions-Policy");
    const csp = buildContentSecurityPolicy("test-nonce", "production");
    expect(csp).toContain("script-src 'self' 'nonce-test-nonce' 'strict-dynamic'");
    expect(csp).toContain("style-src 'self' 'nonce-test-nonce'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("upgrade-insecure-requests");
    expect(csp).not.toContain("'unsafe-inline'");
    expect(csp).not.toContain("'unsafe-eval'");
    expect(csp).not.toContain("ws:");
  });

  it("purges protected component state and the demo session before scope-loss navigation", () => {
    const events: string[] = [];
    window.sessionStorage.setItem("onbxrd-demo-principal", "demo-manager-eight");
    window.sessionStorage.setItem("onbxrd-submit-attempt", "synthetic-attempt");
    handleScopeLoss({
      purgeProtectedState: () => events.push("purged"),
      navigate: (href) => events.push(`navigated:${href}`),
    });
    expect(events).toEqual(["purged", "navigated:/login?reason=scope-changed"]);
    expect(window.sessionStorage.getItem("onbxrd-demo-principal")).toBeNull();
    expect(window.sessionStorage.getItem("onbxrd-submit-attempt")).toBeNull();
  });

  it("marks protected page responses no-store while preserving the strict CSP", () => {
    const response = proxy(new NextRequest("https://onbxrd.test/manager/notifications"));
    const csp = response.headers.get("Content-Security-Policy") ?? "";
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(csp).toContain("'strict-dynamic'");
    expect(csp).not.toContain("'unsafe-inline'");
  });
});

describe("committed fixture safety", () => {
  it("keeps fixture bodies out of TypeScript application modules", () => {
    const dataSource = fs.readFileSync(path.resolve("src/mock/data.ts"), "utf8");
    const assistantSource = fs.readFileSync(path.resolve("src/lib/mock-llm.ts"), "utf8");
    expect(dataSource).not.toContain("TKT-LGN-1042");
    expect(dataSource).not.toContain("Avery Lagoon (Synthetic)");
    expect(assistantSource).not.toContain("Parcel collection is available from 06:00 to 22:00");
    expect(assistantSource).not.toContain("show every resident ticket");
  });

  it("contains only synthetic local fixture identifiers and no provider or token material", () => {
    const fixtureSource = fs.readdirSync(path.resolve("mock-data"))
      .filter((file) => file.endsWith(".json"))
      .map((file) => fs.readFileSync(path.resolve("mock-data", file), "utf8"))
      .join("\n");
    expect(fixtureSource).not.toMatch(/https?:\/\/(?:zalo\.me|oa\.zalo\.me)/i);
    expect(fixtureSource).not.toMatch(/(?:bearer\s+|api[_-]?key|access[_-]?token|refresh[_-]?token)/i);
    expect(fixtureSource).not.toMatch(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/);
    expect(fixtureSource).not.toMatch(/\+?84[\s.-]?\d{8,10}/);
    expect(fixtureSource).not.toContain("production-resident");
  });
});
