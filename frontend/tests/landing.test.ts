import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const frontendRoot = path.resolve(__dirname, "..");
const page = readFileSync(path.join(frontendRoot, "src/app/page.tsx"), "utf8");
const rail = readFileSync(path.join(frontendRoot, "src/components/landing-feature-rail.tsx"), "utf8");
const styles = readFileSync(path.join(frontendRoot, "src/app/globals.css"), "utf8");
const layout = readFileSync(path.join(frontendRoot, "src/app/layout.tsx"), "utf8");

describe("landing feature journey", () => {
  it("discovers .jpg galleries without filenames in page code", () => {
    expect(page).toContain('endsWith(".jpg")');
    expect(page).toContain("await readdir");
    for (const folder of ["onboarding", "benefits", "assistant", "tickets", "announcements", "operations"]) {
      expect(existsSync(path.join(frontendRoot, "public/landing", folder))).toBe(true);
    }
  });

  it("keeps scene-specific asset caps and image compositions", () => {
    for (const entry of ['["onboarding", 2]', '["benefits", 4]', '["assistant", 2]', '["tickets", 3]', '["announcements", 4]', '["operations", 3]']) {
      expect(page).toContain(entry);
    }
    for (const scene of ["scene-welcome", "scene-benefits", "scene-assistant", "scene-tickets", "scene-noticeboard", "scene-operations"]) {
      expect(rail).toContain(scene);
    }
  });

  it("keeps the landing to a horizontal single-viewport rail", () => {
    expect(styles).toContain("height: 100dvh");
    expect(styles).toContain("overflow: hidden");
    expect(styles).toContain("overflow-x: auto");
    expect(styles).toContain("scroll-snap-type: x mandatory");
  });

  it("offers manual navigation and honors reduced motion", () => {
    expect(rail).toContain("AUTO_ADVANCE_MS = 20_000");
    expect(rail).toContain("IMAGE_ADVANCE_MS = 11_000");
    expect(rail).toContain("onPointerDown={pauseForInteraction}");
    expect(rail).toContain('event.key === "ArrowRight"');
    expect(rail).toContain('event.key === "ArrowLeft"');
    expect(rail).toContain("prefersReducedMotion");
    expect(styles).toContain("prefers-reduced-motion: reduce");
  });

  it("defaults to Vietnamese dark mode and introduces Hommie in the chat scene", () => {
    expect(layout).toContain('lang="vi" data-theme="dark"');
    expect(layout).toContain("stored === 'dark' || stored === 'light' ? stored : 'dark'");
    expect(rail).toContain("Xin chào, mình là trợ lý Hommie Agent.");
    expect(rail).toContain("Xin hân hạnh làm quen nha!");
  });
});
