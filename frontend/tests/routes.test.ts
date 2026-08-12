import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

const approvedRoutes = [
  "app/(public)/login/page.tsx",
  "app/(public)/register/page.tsx",
  "app/(public)/recovery/page.tsx",
  "app/(resident)/resident/onboarding/page.tsx",
  "app/(resident)/resident/benefits/page.tsx",
  "app/(resident)/resident/assistant/page.tsx",
  "app/(resident)/resident/tickets/page.tsx",
  "app/(resident)/resident/tickets/new/page.tsx",
  "app/(resident)/resident/tickets/[ticketId]/page.tsx",
  "app/(resident)/resident/notifications/page.tsx",
  "app/(resident)/resident/profile/page.tsx",
  "app/(manager)/manager/dashboard/page.tsx",
  "app/(manager)/manager/residents/page.tsx",
  "app/(manager)/manager/onboarding/page.tsx",
  "app/(manager)/manager/tickets/page.tsx",
  "app/(manager)/manager/tickets/[ticketId]/page.tsx",
  "app/(manager)/manager/notifications/page.tsx",
  "app/(manager)/manager/profile/page.tsx",
];

function pageFiles(directory: string): string[] {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? pageFiles(target) : entry.name === "page.tsx" ? [path.relative(process.cwd(), target).replaceAll(path.sep, "/")] : [];
  });
}

function webRoute(file: string) {
  const segments = file.replace(/^app\//, "").replace(/(?:^|\/)page\.tsx$/, "").split("/").filter((segment) => segment && !segment.startsWith("("));
  return `/${segments.join("/")}`;
}

describe("route inventory", () => {
  it("ships exactly the 18 approved MVP pages", () => {
    const discovered = pageFiles(path.resolve("app"));
    expect(discovered.filter((file) => webRoute(file) === "/")).toEqual(["app/page.tsx"]);
    expect(discovered.filter((file) => webRoute(file) !== "/").sort()).toEqual([...approvedRoutes].sort());
  });

  it("does not add an Administrator route", () => {
    const discovered = pageFiles(path.resolve("app"));
    expect(discovered.some((file) => file.toLowerCase().includes("admin"))).toBe(false);
    expect(discovered.map(webRoute).some((route) => route.toLowerCase().includes("admin"))).toBe(false);
  });
});
