import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const appRoot = path.resolve(__dirname, "../src/app");

describe("approved frontend route surfaces", () => {
  it.each([
    "page.tsx",
    "app/onboarding/page.tsx",
    "app/benefits/page.tsx",
    "management/onboarding/page.tsx",
    "management/notifications/page.tsx",
    "management/profile/page.tsx",
  ])("keeps %s present", (relativePath) => {
    expect(existsSync(path.join(appRoot, relativePath))).toBe(true);
  });

  it("keeps the public entry wired to authentication actions", () => {
    const landing = readFileSync(path.join(appRoot, "page.tsx"), "utf8");
    expect(landing).toContain('href="/login"');
    expect(landing).toContain('href="/register"');
    expect(landing).toContain("ThemeControl");
  });

  it("keeps current live work routes and new navigation entries in the shell", () => {
    const shell = readFileSync(path.resolve(appRoot, "../components/app-shell.tsx"), "utf8");
    for (const route of ["/app/chat", "/app/tickets", "/management/tickets", "/management/assistant", "/app/onboarding", "/management/notifications"]) {
      expect(shell).toContain(route);
    }
  });

  it("keeps resident information onboarding items actionable", () => {
    const onboarding = readFileSync(path.join(appRoot, "app/onboarding/page.tsx"), "utf8");
    expect(onboarding).toContain('item.status === "read" ? "unread" : "read"');
    expect(onboarding).toContain('"Mark as read"');
    expect(onboarding).toContain('"Mark unread"');
  });
});
